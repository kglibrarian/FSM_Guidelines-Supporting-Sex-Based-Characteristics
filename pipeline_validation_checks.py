# ============================================================================
# PIPELINE VALIDATION CHECKS - COMPREHENSIVE DATA QUALITY VALIDATION
# ============================================================================
# Purpose: Detect cartesian products, duplicates, and data quality issues
# Usage: Run after each phase to validate pipeline integrity
# Note: No hard-coded numbers - all checks are dynamic and relative
# ============================================================================

import pandas as pd
import numpy as np
import os
from collections import Counter

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_FOLDER = 'output'
WARNINGS = []  # Track all warnings
ERRORS = []    # Track all errors

# Tolerance levels for unexpected row counts
TOLERANCE_STRICT = 0.01   # 1% - for phases that should match exactly
TOLERANCE_NORMAL = 0.05   # 5% - for phases with some expected variation
TOLERANCE_LOOSE = 0.10    # 10% - for phases with more variation

# ============================================================================
# CORE VALIDATION FUNCTIONS
# ============================================================================

def check_row_count_match(actual_df, expected_count, phase_name, tolerance=TOLERANCE_NORMAL, 
                          explanation="rows should match"):
    """
    Compare actual row count against expected count with tolerance
    
    Parameters:
    - actual_df: DataFrame to check
    - expected_count: Expected number of rows
    - phase_name: Name of phase for reporting
    - tolerance: Acceptable percentage difference
    - explanation: Human-readable explanation of what's being checked
    
    Returns: (passed: bool, message: str)
    """
    actual_count = len(actual_df)
    
    if expected_count == 0:
        return True, f"✓ {phase_name}: {actual_count:,} rows (no expected count to compare)"
    
    diff = abs(actual_count - expected_count)
    pct_diff = (diff / expected_count * 100) if expected_count > 0 else 0
    
    if pct_diff > (tolerance * 100):
        msg = f"⚠️ {phase_name}: Row count mismatch!\n"
        msg += f"   Expected: {expected_count:,} rows ({explanation})\n"
        msg += f"   Actual: {actual_count:,} rows\n"
        msg += f"   Difference: {diff:,} rows ({pct_diff:.1f}%)\n"
        msg += f"   Threshold: {tolerance * 100:.1f}%"
        WARNINGS.append(msg)
        return False, msg
    else:
        msg = f"✓ {phase_name}: Row count OK ({actual_count:,} rows, {pct_diff:.1f}% diff from expected)"
        return True, msg

def check_no_duplicates(df, columns, phase_name, description=""):
    """
    Check for duplicate rows on specified columns
    
    Parameters:
    - df: DataFrame to check
    - columns: List of columns to check for duplicates
    - phase_name: Name of phase for reporting
    - description: What these columns represent
    
    Returns: (passed: bool, message: str)
    """
    if len(df) == 0:
        return True, f"✓ {phase_name}: Empty dataframe (no duplicates possible)"
    
    # Check if columns exist
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        msg = f"⚠️ {phase_name}: Cannot check duplicates - missing columns: {missing_cols}"
        WARNINGS.append(msg)
        return False, msg
    
    # Check for duplicates
    before = len(df)
    dups_mask = df.duplicated(subset=columns, keep=False)
    dup_count = dups_mask.sum()
    
    if dup_count > 0:
        msg = f"⚠️ {phase_name}: Found {dup_count:,} duplicate rows on {columns}"
        if description:
            msg += f" ({description})"
        msg += f"\n   This suggests a cartesian product or merge issue!"
        
        # Show examples
        dup_rows = df[dups_mask]
        msg += f"\n   Example duplicates:"
        for idx, row in dup_rows[columns].head(3).iterrows():
            msg += f"\n     {dict(row)}"
        
        ERRORS.append(msg)
        return False, msg
    else:
        msg = f"✓ {phase_name}: No duplicates on {columns}"
        if description:
            msg += f" ({description})"
        return True, msg

def check_cartesian_product(df, expected_unique_counts, phase_name):
    """
    Check if row count suggests cartesian product
    
    Parameters:
    - df: DataFrame to check
    - expected_unique_counts: Dict of {column: expected_unique_count}
    - phase_name: Name of phase
    
    Returns: (passed: bool, message: str)
    """
    actual_rows = len(df)
    
    # Calculate expected max rows (product of unique counts)
    expected_max = 1
    for col, expected_unique in expected_unique_counts.items():
        if col in df.columns:
            actual_unique = df[col].nunique()
            expected_max *= expected_unique
            
            # Also check if unique count is suspicious
            if actual_unique > expected_unique * 1.5:
                msg = f"⚠️ {phase_name}: Column '{col}' has {actual_unique:,} unique values\n"
                msg += f"   Expected: ~{expected_unique:,}\n"
                msg += f"   This is {actual_unique / expected_unique:.1f}x more than expected!"
                WARNINGS.append(msg)
    
    # Check if actual rows suggests cartesian product
    if actual_rows > expected_max * 1.2:
        msg = f"⚠️ {phase_name}: Possible cartesian product detected!\n"
        msg += f"   Actual rows: {actual_rows:,}\n"
        msg += f"   Expected max: {expected_max:,}\n"
        msg += f"   Ratio: {actual_rows / expected_max:.1f}x\n"
        msg += f"   Check for merge issues!"
        ERRORS.append(msg)
        return False, msg
    
    return True, f"✓ {phase_name}: Row count suggests no cartesian product"

def check_column_values(df, column, valid_pattern, phase_name, description=""):
    """
    Check if column values match expected pattern
    
    Parameters:
    - df: DataFrame to check
    - column: Column name to validate
    - valid_pattern: Regex pattern for valid values
    - phase_name: Name of phase
    - description: What this column represents
    
    Returns: (passed: bool, message: str)
    """
    if column not in df.columns:
        return True, f"ℹ️ {phase_name}: Column '{column}' not present"
    
    # Check for invalid values
    valid_mask = df[column].notna() & df[column].astype(str).str.match(valid_pattern, na=False)
    invalid_count = (~valid_mask & df[column].notna()).sum()
    
    if invalid_count > 0:
        msg = f"⚠️ {phase_name}: Found {invalid_count:,} invalid values in '{column}'"
        if description:
            msg += f" ({description})"
        
        invalid_vals = df[~valid_mask & df[column].notna()][column].unique()
        msg += f"\n   Examples: {list(invalid_vals[:5])}"
        
        WARNINGS.append(msg)
        return False, msg
    
    return True, f"✓ {phase_name}: All '{column}' values valid"

def check_merge_integrity(left_df, right_df, merge_keys, expected_result_count, phase_name):
    """
    Check if merge will produce expected results
    
    Parameters:
    - left_df: Left dataframe
    - right_df: Right dataframe  
    - merge_keys: List of columns to merge on
    - expected_result_count: Expected number of rows after merge
    - phase_name: Name of phase
    
    Returns: (passed: bool, message: str, predicted_count: int)
    """
    # Count matching keys
    left_keys = left_df[merge_keys].drop_duplicates()
    right_keys = right_df[merge_keys].drop_duplicates()
    
    # Predict merge result
    matching_keys = pd.merge(left_keys, right_keys, on=merge_keys, how='inner')
    predicted_count = len(matching_keys)
    
    # Check for many-to-many joins (cartesian risk)
    left_duplicates = left_df.duplicated(subset=merge_keys, keep=False).sum()
    right_duplicates = right_df.duplicated(subset=merge_keys, keep=False).sum()
    
    messages = []
    passed = True
    
    if left_duplicates > 0 and right_duplicates > 0:
        msg = f"⚠️ {phase_name}: Many-to-many join detected!\n"
        msg += f"   Left duplicates: {left_duplicates:,}\n"
        msg += f"   Right duplicates: {right_duplicates:,}\n"
        msg += f"   Risk of cartesian product!"
        WARNINGS.append(msg)
        messages.append(msg)
        passed = False
    
    # Check if predicted count is reasonable
    if expected_result_count > 0:
        diff_pct = abs(predicted_count - expected_result_count) / expected_result_count * 100
        if diff_pct > 10:
            msg = f"⚠️ {phase_name}: Predicted merge result differs from expected\n"
            msg += f"   Expected: {expected_result_count:,}\n"
            msg += f"   Predicted: {predicted_count:,}\n"
            msg += f"   Difference: {diff_pct:.1f}%"
            WARNINGS.append(msg)
            messages.append(msg)
            passed = False
    
    if passed:
        msg = f"✓ {phase_name}: Merge integrity check passed (predicted: {predicted_count:,} rows)"
        messages.append(msg)
    
    return passed, "\n".join(messages), predicted_count

# ============================================================================
# PHASE-SPECIFIC VALIDATION FUNCTIONS
# ============================================================================

def validate_phase1(phase1_df):
    """Validate Phase 1: PubMed Guidelines Collection"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 1: PubMed Guidelines Collection")
    print("="*70)
    
    checks_passed = []
    
    # Check 1: No duplicate PMIDs
    passed, msg = check_no_duplicates(
        phase1_df, 
        ['PMID'], 
        'Phase 1',
        'Each PMID should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: Required columns present (flexible - check actual column names)
    required_base_cols = ['PMID']  # Only PMID is truly required
    
    # Check for title column (might be 'Title', 'title', 'ArticleTitle', etc.)
    title_cols = [col for col in phase1_df.columns if 'title' in col.lower()]
    
    # Check for journal column
    journal_cols = [col for col in phase1_df.columns if 'journal' in col.lower() or 'source' in col.lower()]
    
    missing_base = [col for col in required_base_cols if col not in phase1_df.columns]
    
    if missing_base:
        msg = f"❌ Phase 1: Missing critical columns: {missing_base}"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 1: Critical columns present (PMID)")
        checks_passed.append(True)
    
    # Report on optional columns
    if not title_cols:
        print(f"  ℹ️ No title column found (looked for columns with 'title')")
    else:
        print(f"  ✓ Title column(s) found: {title_cols}")
    
    if not journal_cols:
        print(f"  ℹ️ No journal column found (looked for columns with 'journal' or 'source')")
    else:
        print(f"  ✓ Journal column(s) found: {journal_cols}")
    
    # Check 3: Basic data quality
    null_pmids = phase1_df['PMID'].isna().sum()
    if null_pmids > 0:
        msg = f"⚠️ Phase 1: Found {null_pmids:,} rows with null PMIDs"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 1: No null PMIDs")
        checks_passed.append(True)
    
    return all(checks_passed)

def validate_phase2(phase2_df, phase1_df):
    """Validate Phase 2: CrossRef References"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 2: CrossRef References")
    print("="*70)
    
    checks_passed = []
    
    # Expected: Multiple references per guideline (one-to-many relationship)
    expected_guidelines = phase1_df['PMID'].nunique()
    actual_guidelines = phase2_df['guideline_pmid'].nunique()
    
    # Check 1: Most guidelines should have references
    coverage_pct = (actual_guidelines / expected_guidelines * 100) if expected_guidelines > 0 else 0
    
    if coverage_pct < 50:
        msg = f"⚠️ Phase 2: Low guideline coverage!\n"
        msg += f"   Expected guidelines: {expected_guidelines:,}\n"
        msg += f"   Guidelines with references: {actual_guidelines:,} ({coverage_pct:.1f}%)\n"
        msg += f"   Check if CrossRef extraction is working"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        msg = f"✓ Phase 2: Guideline coverage good ({actual_guidelines:,}/{expected_guidelines:,} = {coverage_pct:.1f}%)"
        print(msg)
        checks_passed.append(True)
    
    # Check 2: Multiple citations of same article within guidelines (informational)
    identifiable_refs = phase2_df[
        phase2_df['ref_doi'].notna() | phase2_df['ref_title'].notna()
    ].copy()
    
    # Check for articles cited multiple times within same guideline
    refs_with_doi = identifiable_refs[identifiable_refs['ref_doi'].notna()]
    multi_cited = refs_with_doi.duplicated(subset=['guideline_pmid', 'ref_doi'], keep=False).sum()
    
    if multi_cited > 0:
        # Count unique (guideline, DOI) pairs that appear >1 time
        cite_counts = refs_with_doi.groupby(['guideline_pmid', 'ref_doi']).size()
        num_multi_cited = (cite_counts > 1).sum()
        
        print(f"\nℹ️ Phase 2: {multi_cited:,} references are cited multiple times within their guideline")
        print(f"   {num_multi_cited:,} unique articles cited 2+ times in same guideline")
        print(f"   This is normal - guidelines often cite key papers in multiple sections")
        print(f"   These will be preserved in Phase 2 (shows citation importance)")
    else:
        print(f"\nℹ️ Phase 2: No articles cited multiple times within same guideline")

    checks_passed.append(True)  # This is NOT an error condition
    
    # Check 3: Reference count sanity (NOT a cartesian product check!)
    # Phase 2 is a one-to-many extraction, so many rows per guideline is EXPECTED
    refs_per_guideline = phase2_df.groupby('guideline_pmid').size()
    mean_refs = refs_per_guideline.mean()
    median_refs = refs_per_guideline.median()
    max_refs = refs_per_guideline.max()
    
    print(f"\n📊 Phase 2: Reference Distribution")
    print(f"   Total references: {len(phase2_df):,}")
    print(f"   Guidelines with references: {actual_guidelines:,}")
    print(f"   Mean refs per guideline: {mean_refs:.1f}")
    print(f"   Median refs per guideline: {median_refs:.0f}")
    print(f"   Max refs per guideline: {max_refs:,}")
    
    # Only flag if one guideline has suspiciously more than others
    if max_refs > mean_refs * 10:
        msg = f"⚠️ Phase 2: One guideline has {max_refs:,} references (mean: {mean_refs:.0f})\n"
        msg += f"   This is {max_refs / mean_refs:.1f}x the average - possible duplicate issue\n"
        msg += f"   Check guideline PMID: {refs_per_guideline.idxmax()}"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 2: Reference distribution looks normal")
        checks_passed.append(True)
    
    # Check 4: Reasonable total count (not too low, not absurdly high)
    # Typical guidelines have 50-200 references
    expected_min = expected_guidelines * 20  # At least 20 refs per guideline
    expected_max = expected_guidelines * 500  # At most 500 refs per guideline
    
    if len(phase2_df) < expected_min:
        msg = f"⚠️ Phase 2: Unusually low reference count\n"
        msg += f"   Total: {len(phase2_df):,} references\n"
        msg += f"   Expected minimum: {expected_min:,} (20 refs/guideline)\n"
        msg += f"   Check if extraction is working correctly"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    elif len(phase2_df) > expected_max:
        msg = f"⚠️ Phase 2: Unusually high reference count\n"
        msg += f"   Total: {len(phase2_df):,} references\n"
        msg += f"   Expected maximum: {expected_max:,} (500 refs/guideline)\n"
        msg += f"   Possible duplicate issue or extraction error"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 2: Total reference count reasonable ({len(phase2_df):,} references)")
        checks_passed.append(True)
    
    return all(checks_passed)

def validate_phase3(phase3_df, phase2_df, *, use_all_ncts=None, multi_nct_info_threshold=10):
    """
    Validate Phase 3: Clinical Trial Identification (Citation-Level Structure)

    UPDATED for your new model:
      - You may have *many* NCTs per PMID (reviews/meta-analyses/pooled analyses).
      - NCT presence does NOT necessarily imply PubMed PublicationType == "Clinical Trial".
      - Validation distinguishes:
          (A) trial publication flag (PubMed publication type logic)  -> is_clinical_trial
          (B) trial linkage flag (has any NCT parsed)                 -> has_nct
          (C) analysis flag (either A or B)                           -> is_clinical_trial_for_analysis

    Expected structure:
      - One row per (guideline_pmid, ref_pmid) citation pair
      - guideline_pmid is a single scalar value (not list-like)
      - ref_pmid is a scalar value (PMID-like)
      - Columns typically include:
          guideline_pmid, ref_pmid, is_clinical_trial, nct_number,
          all_nct_numbers (optional), publication_types (optional)

    Parameters
    ----------
    phase3_df : pd.DataFrame
        Phase 3 citation-level table (output of your Step 5 join).
    phase2_df : pd.DataFrame
        Phase 2 citation-level reference table.
    use_all_ncts : bool | None
        If you pass None, we infer it: True if 'all_nct_numbers' exists, else False.
        This only controls how we *message* multi-NCT behavior (it’s not an error either way).
    multi_nct_info_threshold : int
        Count threshold at which we treat a PMID as "multi-trial article" (informational).

    Returns
    -------
    bool
        True if all critical checks passed (errors == 0). Warnings/information may still print.
    """
    import re

    print("\n" + "=" * 70)
    print("VALIDATING PHASE 3: Clinical Trial Identification (Updated for multi-NCT + NCT flags)")
    print("=" * 70)

    checks_passed = []
    phase_name = "Phase 3"

    # -----------------------------
    # Helper: robust NCT parsing
    # -----------------------------
    nct_regex = re.compile(r"\bNCT\d{8}\b", flags=re.IGNORECASE)

    def _parse_ncts_from_row(row):
        """
        Returns a list of unique NCTs found in:
          - all_nct_numbers (preferred if present)
          - else nct_number
          - else empty
        Keeps order of first appearance.
        """
        candidates = []

        if "all_nct_numbers" in row.index and pd.notna(row.get("all_nct_numbers")):
            candidates.append(str(row.get("all_nct_numbers")))
        if "nct_number" in row.index and pd.notna(row.get("nct_number")):
            candidates.append(str(row.get("nct_number")))

        if not candidates:
            return []

        text = " ; ".join(candidates)
        found = [m.upper() for m in nct_regex.findall(text)]
        # unique-preserving order
        seen = set()
        uniq = []
        for n in found:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        return uniq

    # Infer USE_ALL_NCTS if not provided
    if use_all_ncts is None:
        use_all_ncts = "all_nct_numbers" in phase3_df.columns

    # -----------------------------
    # Baseline expected row count
    # -----------------------------
    phase2_with_pmids = phase2_df[phase2_df["ref_pmid"].notna()].copy()
    expected_count = len(phase2_with_pmids)

    print(f"\nℹ️ Baseline row counts:")
    print(f"  Phase 2 total rows:           {len(phase2_df):,}")
    print(f"  Phase 2 rows WITH ref_pmid:   {expected_count:,}")
    print(f"  Phase 3 citation rows:        {len(phase3_df):,}")

    if expected_count > 0:
        diff = len(phase3_df) - expected_count
        pct = diff / expected_count * 100
        print(f"  Difference (Phase3 - Phase2): {diff:+,} rows ({pct:+.1f}%)")

    # Row count should be close to Phase2 rows with PMIDs
    passed, msg = check_row_count_match(
        phase3_df,
        expected_count,
        phase_name,
        tolerance=TOLERANCE_NORMAL,
        explanation="should approximately match Phase 2 rows with PMIDs (may be slightly less due to cleaning)"
    )
    print(msg)
    checks_passed.append(passed)

    # -----------------------------
    # Structure checks
    # -----------------------------
    print(f"\n📦 Structure checks:")

    required_cols = ["guideline_pmid", "ref_pmid"]
    missing_required = [c for c in required_cols if c not in phase3_df.columns]
    if missing_required:
        msg = f"❌ {phase_name}: Missing required columns: {missing_required}"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
        # Without these, further checks are meaningless
        return False
    else:
        print(f"  ✓ Required columns present: {required_cols}")
        checks_passed.append(True)

    # Guard against unique-ref structure
    if "guideline_pmids" in phase3_df.columns:
        msg = (
            f"⚠️ {phase_name}: Found column 'guideline_pmids' (plural).\n"
            f"   This suggests a unique-ref structure rather than citation-level structure.\n"
            f"   Expected 'guideline_pmid' (singular) per row."
        )
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)  # treat as issue because it breaks downstream assumptions
    else:
        print("  ✓ No 'guideline_pmids' column (consistent with citation-level structure)")
        checks_passed.append(True)

    # -----------------------------
    # Duplicate check on (guideline_pmid, ref_pmid)
    # -----------------------------
    passed, msg = check_no_duplicates(
        phase3_df,
        ["guideline_pmid", "ref_pmid"],
        phase_name,
        "Each guideline–reference pair should be unique (cartesian products show up here)"
    )
    print(msg)
    checks_passed.append(passed)

    # -----------------------------
    # Compute parsed NCTs + counts
    # -----------------------------
    # Do this on a copy to avoid mutating caller DF
    tmp = phase3_df.copy()

    tmp["parsed_ncts"] = tmp.apply(_parse_ncts_from_row, axis=1)
    tmp["parsed_nct_count"] = tmp["parsed_ncts"].apply(len)
    tmp["has_nct"] = tmp["parsed_nct_count"] > 0

    # Ensure is_clinical_trial exists and is boolean-like
    if "is_clinical_trial" not in tmp.columns:
        msg = f"⚠️ {phase_name}: Missing 'is_clinical_trial' column; defaulting to False for validation."
        print(msg)
        WARNINGS.append(msg)
        tmp["is_clinical_trial"] = False

    # Normalize is_clinical_trial to bool safely
    tmp["is_clinical_trial"] = tmp["is_clinical_trial"].fillna(False).astype(bool)

    # New: analysis flag that matches your new intent
    tmp["is_clinical_trial_for_analysis"] = tmp["is_clinical_trial"] | tmp["has_nct"]

    # -----------------------------
    # Citation statistics
    # -----------------------------
    unique_refs = tmp["ref_pmid"].nunique(dropna=True)
    unique_guidelines = tmp["guideline_pmid"].nunique(dropna=True)
    citation_ratio = len(tmp) / unique_refs if unique_refs else 0

    print(f"\n📊 Citation statistics:")
    print(f"  Total citation rows:         {len(tmp):,}")
    print(f"  Unique ref_pmid:             {unique_refs:,}")
    print(f"  Unique guideline_pmid:       {unique_guidelines:,}")
    print(f"  Citations per reference avg: {citation_ratio:.2f}")

    if citation_ratio < 1.0:
        msg = f"❌ {phase_name}: Citation ratio < 1.0 ({citation_ratio:.2f}) - impossible (data corruption likely)."
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        # High ratios can be real; keep warning loose/informational.
        if citation_ratio > 5.0:
            msg = (
                f"ℹ️ {phase_name}: High citations/reference ratio ({citation_ratio:.2f}x). "
                f"Some references may be cited by many guidelines; not necessarily a problem."
            )
            print(msg)
            checks_passed.append(True)
        else:
            print("  ✓ Citation ratio looks reasonable")
            checks_passed.append(True)

    # -----------------------------
    # Clinical trial vs NCT linkage stats (separated properly)
    # -----------------------------
    ct_citation_rows = int(tmp["is_clinical_trial"].sum())
    ct_unique_refs = tmp.loc[tmp["is_clinical_trial"], "ref_pmid"].nunique(dropna=True)

    nct_citation_rows = int(tmp["has_nct"].sum())
    nct_unique_refs = tmp.loc[tmp["has_nct"], "ref_pmid"].nunique(dropna=True)

    analysis_citation_rows = int(tmp["is_clinical_trial_for_analysis"].sum())
    analysis_unique_refs = tmp.loc[tmp["is_clinical_trial_for_analysis"], "ref_pmid"].nunique(dropna=True)

    ct_pct_unique = (ct_unique_refs / unique_refs * 100) if unique_refs else 0
    nct_pct_unique = (nct_unique_refs / unique_refs * 100) if unique_refs else 0
    analysis_pct_unique = (analysis_unique_refs / unique_refs * 100) if unique_refs else 0

    print(f"\n🧪 Trial classification vs NCT linkage:")
    print(f"  PubMed-labeled clinical trial (is_clinical_trial=True):")
    print(f"    - Citation rows: {ct_citation_rows:,}")
    print(f"    - Unique refs:   {ct_unique_refs:,} ({ct_pct_unique:.1f}% of unique refs)")
    print(f"  NCT-linked articles (has_nct=True):")
    print(f"    - Citation rows: {nct_citation_rows:,}")
    print(f"    - Unique refs:   {nct_unique_refs:,} ({nct_pct_unique:.1f}% of unique refs)")
    print(f"  Analysis trial universe (is_clinical_trial OR has_nct):")
    print(f"    - Citation rows: {analysis_citation_rows:,}")
    print(f"    - Unique refs:   {analysis_unique_refs:,} ({analysis_pct_unique:.1f}% of unique refs)")

    # Keep old "reasonableness" checks but apply only to PubMed trial label, and make them softer
    if unique_refs:
        if ct_pct_unique < 1.0:
            msg = f"ℹ️ {phase_name}: Very low PubMed-labeled clinical trial rate ({ct_pct_unique:.1f}%). This can be normal."
            print(msg)
            checks_passed.append(True)
        elif ct_pct_unique > 60.0:
            msg = f"⚠️ {phase_name}: Very high PubMed-labeled clinical trial rate ({ct_pct_unique:.1f}%). Check classification logic."
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            print("  ✓ PubMed clinical trial rate looks plausible")
            checks_passed.append(True)

    # -----------------------------
    # NCT validity checks (format + duplication risks)
    # -----------------------------
    print(f"\n🔎 NCT format + duplication checks:")

    # Format: all parsed NCTs should match NCT########
    # (They should, because regex enforces it; but we still check raw columns for weirdness.)
    if "all_nct_numbers" in tmp.columns or "nct_number" in tmp.columns:
        # Raw invalid patterns: things that look like NCT but wrong length, etc.
        raw_text = (
            tmp.get("all_nct_numbers", pd.Series("", index=tmp.index)).fillna("").astype(str)
            + " ; "
            + tmp.get("nct_number", pd.Series("", index=tmp.index)).fillna("").astype(str)
        )
        suspicious = raw_text.str.contains(r"\bNCT\d+\b", regex=True) & ~raw_text.str.contains(r"\bNCT\d{8}\b", regex=True)

        suspicious_count = int(suspicious.sum())
        if suspicious_count > 0:
            examples = tmp.loc[suspicious, ["guideline_pmid", "ref_pmid"]].head(5)
            msg = (
                f"⚠️ {phase_name}: Found {suspicious_count:,} rows with suspicious NCT-like strings "
                f"(e.g., wrong length).\n"
                f"   Examples (guideline_pmid, ref_pmid):\n{examples.to_string(index=False)}"
            )
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            print("  ✓ No suspicious NCT-like strings found in raw NCT fields")
            checks_passed.append(True)
    else:
        print("  ℹ️ No NCT columns found to validate (nct_number / all_nct_numbers missing).")
        checks_passed.append(True)

    # Duplicate NCT mentions within the same PMID (this CAN indicate merge duplication)
    # We'll compute duplicates on an exploded view
    exploded = tmp[["ref_pmid", "parsed_ncts"]].explode("parsed_ncts")
    exploded = exploded.dropna(subset=["ref_pmid", "parsed_ncts"])

    if len(exploded) > 0:
        dup_within_pmid = exploded.duplicated(subset=["ref_pmid", "parsed_ncts"]).sum()
        if dup_within_pmid > 0:
            msg = (
                f"⚠️ {phase_name}: Found {dup_within_pmid:,} duplicate NCTs within the same PMID.\n"
                f"   This may indicate merge duplication or concatenation artifacts."
            )
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            print("  ✓ No duplicate NCTs within the same PMID (good)")
            checks_passed.append(True)
    else:
        print("  ℹ️ No parsed NCTs to check for within-PMID duplication.")
        checks_passed.append(True)

    # -----------------------------
    # Multi-NCT articles (informational; NOT an error)
    # -----------------------------
    multi_nct_rows = tmp[tmp["parsed_nct_count"] >= multi_nct_info_threshold]
    if not multi_nct_rows.empty:
        # Count unique PMIDs and show top offenders
        multi_refs = multi_nct_rows["ref_pmid"].nunique(dropna=True)
        top = (
            tmp.groupby("ref_pmid")["parsed_nct_count"]
            .max()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        print(f"\nℹ️ Multi-NCT articles (expected with reviews/meta-analyses):")
        print(f"  USE_ALL_NCTS inferred/passed: {use_all_ncts}")
        print(f"  Unique references with ≥{multi_nct_info_threshold} NCTs: {multi_refs:,}")
        print("  Top references by parsed_nct_count (max per PMID):")
        print(top.to_string(index=False))
        # informational only
        checks_passed.append(True)
    else:
        print(f"\nℹ️ No references with ≥{multi_nct_info_threshold} NCTs parsed.")
        checks_passed.append(True)

    # -----------------------------
    # NCT present but is_clinical_trial=False (informational, not warning)
    # -----------------------------
    mismatch = tmp[tmp["has_nct"] & (~tmp["is_clinical_trial"])]
    if not mismatch.empty:
        # This is expected: reviews/meta analyses etc.
        uniq_refs_mismatch = mismatch["ref_pmid"].nunique(dropna=True)
        print(
            f"\nℹ️ NCT-linked but not PubMed-labeled Clinical Trial:\n"
            f"  Citation rows: {len(mismatch):,}\n"
            f"  Unique refs:   {uniq_refs_mismatch:,}\n"
            f"  This is expected for reviews, meta-analyses, pooled analyses, and secondary reports."
        )
        # Show a small sample to help debugging if needed
        sample_cols = [c for c in ["guideline_pmid", "ref_pmid", "all_nct_numbers", "nct_number", "publication_types"] if c in tmp.columns]
        if sample_cols:
            print("  Examples:")
            print(mismatch[sample_cols].head(5).to_string(index=False))
        checks_passed.append(True)
    else:
        print("\n✓ No NCT-linked rows where is_clinical_trial=False (fine, but not required).")
        checks_passed.append(True)

    # -----------------------------
    # Guideline coverage (trial universe can be chosen)
    # -----------------------------
    print(f"\n📊 Guideline coverage:")

    guidelines_total = unique_guidelines
    guidelines_with_any_trial_universe = tmp.loc[tmp["is_clinical_trial_for_analysis"], "guideline_pmid"].nunique(dropna=True)
    cov_pct = (guidelines_with_any_trial_universe / guidelines_total * 100) if guidelines_total else 0

    print(f"  Guidelines total:                         {guidelines_total:,}")
    print(f"  Guidelines citing trial-universe refs:     {guidelines_with_any_trial_universe:,} ({cov_pct:.1f}%)")
    print("  (trial-universe = is_clinical_trial OR has_nct)")

    # informational only: not all guidelines cite trials
    checks_passed.append(True)

    # -----------------------------
    # Final pass/fail criteria
    # -----------------------------
    # This function returns True if no ERRORS were added during Phase 3 checks
    # and core checks passed. Warnings may exist.
    critical_ok = all(checks_passed)
    if critical_ok:
        print("\n" + "-" * 70)
        print("✓ Phase 3 validation complete (no critical errors).")
        print("-" * 70)
    else:
        print("\n" + "-" * 70)
        print("⚠️ Phase 3 validation found issues (review warnings/errors above).")
        print("-" * 70)

    # Consider errors critical regardless of checks_passed booleans
    return critical_ok and (len(ERRORS) == 0)


def validate_phase4(phase4_df, phase3_df):
    """Validate Phase 4: ClinicalTrials.gov Details"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 4: ClinicalTrials.gov Details")
    print("="*70)
    
    checks_passed = []
    
    # Expected: Number of unique NCT numbers from Phase 3
    expected_count = phase3_df['nct_number'].nunique() if 'nct_number' in phase3_df.columns else 0
    
    # Check 1: One row per unique trial
    passed, msg = check_no_duplicates(
        phase4_df,
        ['nct_number'],
        'Phase 4',
        'Each trial should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: Row count matches expected unique trials
    passed, msg = check_row_count_match(
        phase4_df,
        expected_count,
        'Phase 4',
        tolerance=TOLERANCE_NORMAL,
        explanation="should match unique NCT numbers from Phase 3"
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 3: Valid NCT number format
    passed, msg = check_column_values(
        phase4_df,
        'nct_number',
        r'^NCT\d{8}$',
        'Phase 4',
        'NCT numbers should be NCT########'
    )
    print(msg)
    checks_passed.append(passed)
    
    return all(checks_passed)

def validate_phase5(phase5_df, phase1_df):
    """Validate Phase 5: Guidelines Summary"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 5: Guidelines Summary")
    print("="*70)
    
    checks_passed = []
    
    # Expected: One row per guideline
    expected_count = len(phase1_df)
    
    # Check 1: Row count matches Phase 1
    passed, msg = check_row_count_match(
        phase5_df,
        expected_count,
        'Phase 5',
        tolerance=TOLERANCE_STRICT,
        explanation="should have one row per guideline from Phase 1"
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: No duplicate PMIDs
    passed, msg = check_no_duplicates(
        phase5_df,
        ['PMID'],
        'Phase 5',
        'Each guideline should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    return all(checks_passed)

def validate_phase6(phase6_df, phase3_df):
    """Validate Phase 6: References with Abstracts"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 6: References with Abstracts")
    print("="*70)
    
    checks_passed = []
    
    # Expected: Same as Phase 3 (abstracts added but no rows removed/added)
    expected_count = len(phase3_df)
    
    # Check 1: Row count should match Phase 3 exactly
    passed, msg = check_row_count_match(
        phase6_df,
        expected_count,
        'Phase 6',
        tolerance=TOLERANCE_STRICT,
        explanation="should have same rows as Phase 3 (just with abstracts added)"
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: No duplicates
    passed, msg = check_no_duplicates(
        phase6_df,
        ['guideline_pmid', 'ref_pmid'],
        'Phase 6',
        'Each guideline-reference pair should be unique'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 3: Abstract coverage
    if 'article_abstract' in phase6_df.columns:
        abstract_pct = phase6_df['article_abstract'].notna().sum() / len(phase6_df) * 100
        print(f"ℹ️ Phase 6: Abstract coverage: {abstract_pct:.1f}%")
    
    return all(checks_passed)

def validate_phase7(phase7_dedup_df, phase7_with_dups_df, phase4_df):

    """Validate Phase 7: Sex Analysis"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 7: Sex Analysis")
    print("="*70)
    
    checks_passed = []
    
    # Expected: Deduplicated should match Phase 4 UNIQUE trials (not total rows)
    expected_unique = phase4_df['nct_number'].nunique()
    
    print(f"\nℹ️ Phase 7 Baseline:")
    print(f"  Phase 4 total rows: {len(phase4_df):,}")
    print(f"  Phase 4 UNIQUE NCT numbers: {expected_unique:,}")
    print(f"  Phase 7 deduplicated rows: {len(phase7_dedup_df):,}")
    print(f"  Phase 7 with-duplicates rows: {len(phase7_with_dups_df):,}")
    
    # Check 1: Deduplicated version has one row per trial
    passed, msg = check_no_duplicates(
        phase7_dedup_df,
        ['nct_number'],
        'Phase 7 (Deduplicated)',
        'Each trial should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: Deduplicated count matches Phase 4 UNIQUE trials
    passed, msg = check_row_count_match(
        phase7_dedup_df,
        expected_unique,
        'Phase 7 (Deduplicated)',
        tolerance=TOLERANCE_NORMAL,
        explanation="should match unique NCT numbers from Phase 4"
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 3: With-duplicates version should have more or equal rows
    if len(phase7_with_dups_df) < len(phase7_dedup_df):
        msg = f"❌ Phase 7: With-duplicates ({len(phase7_with_dups_df):,}) has FEWER rows than deduplicated ({len(phase7_dedup_df):,})!"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 7: With-duplicates has {len(phase7_with_dups_df):,} rows (deduplicated: {len(phase7_dedup_df):,})")
        checks_passed.append(True)
    
    # Check 4: No invalid NCT numbers in with-duplicates
    passed, msg = check_column_values(
        phase7_with_dups_df,
        'nct_number',
        r'^NCT\d{8}$',
        'Phase 7 (With Citations)',
        'NCT numbers should be valid'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 5: Check for excessive cartesian products in with-duplicates
    # Typical: 1-5 citations per trial
    ratio = len(phase7_with_dups_df) / len(phase7_dedup_df) if len(phase7_dedup_df) > 0 else 0
    
    print(f"\n📊 Phase 7: Citation Statistics")
    print(f"  Citation ratio: {ratio:.2f}x")
    print(f"  Average citations per trial: {ratio:.1f}")
    
    if ratio > 10:
        msg = f"⚠️ Phase 7: Citation ratio very high ({ratio:.1f}x)\n"
        msg += f"   Possible cartesian product in merge!"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"  ✓ Citation ratio looks reasonable")
        checks_passed.append(True)
    
    return all(checks_passed)

def validate_phase7b(phase7b_dedup_df, phase7b_citations_df, phase3_df, phase7_dedup_df):
    """Validate Phase 7B: All Trials Analysis"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 7B: All Trials Analysis")
    print("="*70)
    
    checks_passed = []
    
    # Expected: Should have more trials than Phase 7
    expected_min = len(phase7_dedup_df)
    
    # Check 1: Should have more trials than Phase 7
    if len(phase7b_dedup_df) <= expected_min:
        msg = f"⚠️ Phase 7B: Has {len(phase7b_dedup_df):,} trials (same or less than Phase 7: {expected_min:,})\n"
        msg += f"   Phase 7B should analyze MORE trials (including non-registered)"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        additional = len(phase7b_dedup_df) - expected_min
        print(f"✓ Phase 7B: Has {len(phase7b_dedup_df):,} trials ({additional:,} more than Phase 7)")
        checks_passed.append(True)
    
    # Check 2: No duplicates on ref_pmid
    passed, msg = check_no_duplicates(
        phase7b_dedup_df,
        ['ref_pmid'],
        'Phase 7B (Deduplicated)',
        'Each trial reference should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 3: Citations version should have more rows
    if len(phase7b_citations_df) < len(phase7b_dedup_df):
        msg = f"❌ Phase 7B: Citations ({len(phase7b_citations_df):,}) has FEWER rows than deduplicated ({len(phase7b_dedup_df):,})!"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 7B: Citations has {len(phase7b_citations_df):,} rows (deduplicated: {len(phase7b_dedup_df):,})")
        checks_passed.append(True)
    
    return all(checks_passed)

# ============================================================================
# MASTER VALIDATION FUNCTION
# ============================================================================

def run_all_validations():
    """
    Run all phase validations in sequence
    Returns: (all_passed: bool, summary: dict)
    """
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE PIPELINE VALIDATION")
    print("="*70)
    
    global WARNINGS, ERRORS
    WARNINGS = []
    ERRORS = []
    
    results = {}
    
    # Load all phase data
    try:
        phase1 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase1_pubmed_guidelines.csv'))
        phase2 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase2_crossref_guidelines_and_references.csv'))
        phase3 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase3_references_with_trials.csv'))
        phase4 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase4_ctgov_trials_detailed.csv'))
        phase5 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase5_guidelines_summary.csv'))
        phase6 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase6_references_with_abstracts.csv'))
        phase7_dedup = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase7_trials_sex_analysis_deduplicated.csv'))
        phase7_with_dups = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase7_trials_sex_analysis_with_duplicates.csv'))
        
        # Optional Phase 7B
        try:
            phase7b_dedup = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase7b_all_trials_deduplicated.csv'))
            phase7b_citations = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase7b_all_trials_with_citations.csv'))
            has_phase7b = True
        except FileNotFoundError:
            has_phase7b = False
            print("\nℹ️ Phase 7B not found (optional)")
        
    except FileNotFoundError as e:
        print(f"❌ Error loading phase data: {e}")
        return False, {}
    
    # Run validations
    results['Phase 1'] = validate_phase1(phase1)
    results['Phase 2'] = validate_phase2(phase2, phase1)
    results['Phase 3'] = validate_phase3(phase3, phase2)
    results['Phase 4'] = validate_phase4(phase4, phase3)
    results['Phase 5'] = validate_phase5(phase5, phase1)
    results['Phase 6'] = validate_phase6(phase6, phase3)
    results['Phase 7'] = validate_phase7(phase7_dedup, phase7_with_dups, phase4)
    
    if has_phase7b:
        results['Phase 7B'] = validate_phase7b(phase7b_dedup, phase7b_citations, phase3, phase7_dedup)
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    for phase, passed in results.items():
        status = "✓ PASSED" if passed else "⚠️ ISSUES FOUND"
        print(f"{phase}: {status}")
    
    print(f"\nTotal Warnings: {len(WARNINGS)}")
    print(f"Total Errors: {len(ERRORS)}")
    
    if ERRORS:
        print("\n" + "="*70)
        print("CRITICAL ERRORS:")
        print("="*70)
        for error in ERRORS:
            print(error)
    
    if WARNINGS:
        print("\n" + "="*70)
        print("WARNINGS:")
        print("="*70)
        for warning in WARNINGS:
            print(warning)
    
    all_passed = all(results.values()) and len(ERRORS) == 0
    
    if all_passed:
        print("\n" + "="*70)
        print("🎉 ALL VALIDATIONS PASSED!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("⚠️ SOME VALIDATIONS FAILED - REVIEW ABOVE")
        print("="*70)
    
    return all_passed, results

# ============================================================================
# QUICK CHECK FUNCTIONS (for use after specific phases)
# ============================================================================

def quick_check_after_phase(phase_num, df, prev_df=None, expected_count=None):
    """
    Quick validation check to run immediately after a phase completes
    
    Parameters:
    - phase_num: Phase number (1-7)
    - df: Current phase dataframe
    - prev_df: Previous phase dataframe (for comparison)
    - expected_count: Expected row count (optional)
    """
    print(f"\n{'='*50}")
    print(f"QUICK CHECK: Phase {phase_num}")
    print(f"{'='*50}")
    
    # Basic stats
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    
    # Check for completely empty
    if len(df) == 0:
        print("⚠️ WARNING: DataFrame is empty!")
        return False
    
    # Compare to previous if provided
    if prev_df is not None:
        diff = len(df) - len(prev_df)
        pct_change = (diff / len(prev_df) * 100) if len(prev_df) > 0 else 0
        print(f"Change from previous: {diff:+,} rows ({pct_change:+.1f}%)")
        
        # Flag suspicious changes
        if abs(pct_change) > 50:
            print(f"⚠️ WARNING: Large change in row count!")
    
    # Compare to expected if provided
    if expected_count is not None:
        diff = len(df) - expected_count
        pct_diff = (abs(diff) / expected_count * 100) if expected_count > 0 else 0
        if pct_diff > 10:
            print(f"⚠️ WARNING: {diff:+,} rows different from expected ({pct_diff:.1f}%)")
        else:
            print(f"✓ Row count matches expected (±{pct_diff:.1f}%)")
    
    print(f"{'='*50}\n")
    return True
