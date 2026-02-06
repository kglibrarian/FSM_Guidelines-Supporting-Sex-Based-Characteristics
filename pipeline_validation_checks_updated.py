# ============================================================================
# PIPELINE VALIDATION CHECKS - UPDATED FOR CURRENT PIPELINE
# ============================================================================
# Purpose: Detect cartesian products, duplicates, and data quality issues
# Usage: Run after each phase to validate pipeline integrity
# Note: No hard-coded numbers - all checks are dynamic and relative
#
# UPDATED: 2025-01-30
# - Removed obsolete Phase 5, 6, 7b validators (phases don't exist)
# - Added Phase 8 validator (multi-scenario analysis)
# - Updated run_all_validations() to match current pipeline
# - Updated quick_check_after_phase() to handle Phase 8
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
        for i, row in dup_rows.head(3).iterrows():
            vals = [f"{col}={row[col]}" for col in columns]
            msg += f"\n     {', '.join(vals)}"
        
        WARNINGS.append(msg)
        return False, msg
    else:
        msg = f"✓ {phase_name}: No duplicates on {columns}"
        return True, msg

def check_cartesian_product(df, groupby_col, phase_name, expected_ratio=1.0, tolerance=0.2):
    """
    Check if a merge created a cartesian product by checking group sizes
    
    Parameters:
    - df: DataFrame to check
    - groupby_col: Column to group by (e.g., 'PMID')
    - phase_name: Name of phase for reporting
    - expected_ratio: Expected average group size
    - tolerance: Acceptable deviation from expected ratio
    
    Returns: (passed: bool, message: str)
    """
    if len(df) == 0:
        return True, f"✓ {phase_name}: Empty dataframe (no cartesian product)"
    
    if groupby_col not in df.columns:
        msg = f"⚠️ {phase_name}: Cannot check cartesian product - missing column: {groupby_col}"
        WARNINGS.append(msg)
        return False, msg
    
    # Calculate group sizes
    group_sizes = df.groupby(groupby_col).size()
    avg_size = group_sizes.mean()
    max_size = group_sizes.max()
    
    # Check if average size is suspiciously high
    if avg_size > expected_ratio * (1 + tolerance):
        msg = f"⚠️ {phase_name}: Possible cartesian product!\n"
        msg += f"   Average rows per {groupby_col}: {avg_size:.1f}\n"
        msg += f"   Expected: ~{expected_ratio:.1f}\n"
        msg += f"   Maximum: {max_size:,} rows for one {groupby_col}"
        WARNINGS.append(msg)
        return False, msg
    else:
        msg = f"✓ {phase_name}: No cartesian product detected (avg {avg_size:.1f} rows per {groupby_col})"
        return True, msg

def check_column_values(df, column, pattern, phase_name, description=""):
    """
    Check if column values match expected pattern (regex)
    
    Parameters:
    - df: DataFrame to check
    - column: Column name to check
    - pattern: Regex pattern values should match
    - phase_name: Name of phase for reporting
    - description: What the column represents
    
    Returns: (passed: bool, message: str)
    """
    if len(df) == 0:
        return True, f"✓ {phase_name}: Empty dataframe (no values to check)"
    
    if column not in df.columns:
        msg = f"⚠️ {phase_name}: Cannot check values - missing column: {column}"
        WARNINGS.append(msg)
        return False, msg
    
    # Check pattern
    valid_mask = df[column].astype(str).str.match(pattern, na=False)
    invalid_count = (~valid_mask).sum()
    
    if invalid_count > 0:
        msg = f"⚠️ {phase_name}: Found {invalid_count:,} invalid values in {column}"
        if description:
            msg += f" ({description})"
        
        # Show examples
        invalid_vals = df.loc[~valid_mask, column].head(5).tolist()
        msg += f"\n   Examples: {invalid_vals}"
        WARNINGS.append(msg)
        return False, msg
    else:
        msg = f"✓ {phase_name}: All {column} values are valid"
        return True, msg

def check_merge_integrity(merged_df, left_df, right_df, on_cols, phase_name, 
                         expected_loss_pct=0, tolerance=0.05):
    """
    Check if merge lost or gained unexpected rows
    
    Parameters:
    - merged_df: Result of merge
    - left_df: Left dataframe in merge
    - right_df: Right dataframe in merge
    - on_cols: Columns used for merge
    - phase_name: Name of phase for reporting
    - expected_loss_pct: Expected percentage of rows lost (0-100)
    - tolerance: Acceptable deviation from expected loss
    
    Returns: (passed: bool, message: str)
    """
    left_count = len(left_df)
    right_count = len(right_df)
    merged_count = len(merged_df)
    
    # Calculate actual loss
    actual_loss_pct = ((left_count - merged_count) / left_count * 100) if left_count > 0 else 0
    
    # Check if loss is within tolerance
    if abs(actual_loss_pct - expected_loss_pct) > (tolerance * 100):
        msg = f"⚠️ {phase_name}: Unexpected row loss in merge!\n"
        msg += f"   Left: {left_count:,} rows\n"
        msg += f"   Right: {right_count:,} rows\n"
        msg += f"   Merged: {merged_count:,} rows\n"
        msg += f"   Loss: {actual_loss_pct:.1f}% (expected: {expected_loss_pct:.1f}%)"
        WARNINGS.append(msg)
        return False, msg
    else:
        msg = f"✓ {phase_name}: Merge OK ({merged_count:,} rows, {actual_loss_pct:.1f}% loss)"
        return True, msg


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
        'Each guideline should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: All required columns present
    required_cols = ['PMID', 'ArticleTitle', 'Abstract', 'date_year', 'JournalTitle']
    missing = [col for col in required_cols if col not in phase1_df.columns]
    
    if missing:
        msg = f"❌ Phase 1: Missing required columns: {missing}"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 1: All required columns present")
        checks_passed.append(True)
    
    # Check 3: No null PMIDs
    null_pmids = phase1_df['PMID'].isna().sum()
    if null_pmids > 0:
        msg = f"⚠️ Phase 1: Found {null_pmids:,} null PMIDs"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 1: No null PMIDs")
        checks_passed.append(True)
    
    return all(checks_passed)


def validate_phase2(phase2_df, phase1_df):
    """Validate Phase 2: CrossRef Citations Collection - FLEXIBLE"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 2: CrossRef Citations Collection")
    print("="*70)
    
    checks_passed = []
    expected_min = len(phase1_df)
    
    # Check 1: Should have more rows than Phase 1
    if len(phase2_df) <= expected_min:
        msg = f"⚠️ Phase 2: Has {len(phase2_df):,} rows (expected more than Phase 1: {expected_min:,})\n"
        msg += f"   Phase 2 should add references, resulting in more rows"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        added = len(phase2_df) - expected_min
        print(f"✓ Phase 2: Has {len(phase2_df):,} rows ({added:,} more than Phase 1)")
        checks_passed.append(True)
    
    # Check 2: No duplicates (flexible column names)
    if 'guideline_pmid' in phase2_df.columns and 'ref_pmid' in phase2_df.columns:
        passed, msg = check_no_duplicates(phase2_df, ['guideline_pmid', 'ref_pmid'], 'Phase 2', 'Each guideline-reference pair should be unique')
        print(msg)
        checks_passed.append(passed)
    else:
        print(f"ℹ️ Phase 2: Skipping duplicate check (columns not found)")
    
    # Check 3: PMID coverage (flexible)
    phase1_pmid_col = None
    for col in ['PMID', 'pmid', 'guideline_pmid']:
        if col in phase1_df.columns:
            phase1_pmid_col = col
            break
    
    phase2_guideline_col = None
    for col in ['guideline_pmid', 'guideline_PMID', 'PMID']:
        if col in phase2_df.columns:
            phase2_guideline_col = col
            break
    
    if phase1_pmid_col and phase2_guideline_col:
        phase1_pmids = set(phase1_df[phase1_pmid_col].astype(str))
        phase2_guideline_pmids = set(phase2_df[phase2_guideline_col].astype(str))
        missing_pmids = phase1_pmids - phase2_guideline_pmids
        
        if missing_pmids:
            msg = f"⚠️ Phase 2: {len(missing_pmids)} guideline PMIDs from Phase 1 are missing\n"
            msg += f"   Examples: {list(missing_pmids)[:5]}"
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            print(f"✓ Phase 2: All Phase 1 guideline PMIDs are present")
            checks_passed.append(True)
    else:
        print(f"ℹ️ Phase 2: Skipping PMID coverage check")
    
    # Check 4: Reference coverage
    if phase2_guideline_col:
        refs_per_guideline = phase2_df.groupby(phase2_guideline_col).size()
        avg_refs = refs_per_guideline.mean()
        
        print(f"\nℹ️ Phase 2: Reference Statistics")
        print(f"  Average references per guideline: {avg_refs:.1f}")
        print(f"  Min: {refs_per_guideline.min()}, Max: {refs_per_guideline.max()}")
        
        if avg_refs < 10:
            msg = f"⚠️ Phase 2: Low average references per guideline ({avg_refs:.1f})"
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            checks_passed.append(True)
    
    return all(checks_passed) if checks_passed else True


def validate_phase3(phase3_df, phase2_df, *, use_all_ncts=None, multi_nct_info_threshold=10):
    """
    Validate Phase 3: Identify Clinical Trials
    
    Parameters:
    -----------
    phase3_df : DataFrame
        Phase 3 output (references with trial detection)
    phase2_df : DataFrame
        Phase 2 output (all references)
    use_all_ncts : bool or None
        How multi-NCT rows are handled:
        - True: All NCTs stored in 'nct_numbers_list' column (semicolon-separated)
        - False: Multi-NCT rows EXPLODED (one row per NCT)
        - None: Auto-detect based on columns
    multi_nct_info_threshold : int
        Number of multi-NCT rows to show in info messages (default: 10)
    """
    print("\n" + "="*70)
    print("VALIDATING PHASE 3: Clinical Trial Identification (Updated for multi-NCT + NCT flags)")
    print("="*70)
    
    checks_passed = []
    
    # Auto-detect use_all_ncts if not specified
    if use_all_ncts is None:
        use_all_ncts = 'nct_numbers_list' in phase3_df.columns
        print(f"ℹ️ Auto-detected: use_all_ncts={use_all_ncts}")
    
    # Expected: Should match Phase 2 row count (trials detected but no rows added/removed)
    expected_count = len(phase2_df)
    
    # Check 1: Row count should match Phase 2
    if use_all_ncts:
        # Original format: should match exactly
        passed, msg = check_row_count_match(
            phase3_df,
            expected_count,
            'Phase 3',
            tolerance=TOLERANCE_STRICT,
            explanation="should match Phase 2 (trials detected but no rows added)"
        )
        print(msg)
        checks_passed.append(passed)
    else:
        # Exploded format: should have more rows (multi-NCT citations create multiple rows)
        if len(phase3_df) < expected_count:
            msg = f"⚠️ Phase 3: Has FEWER rows than Phase 2 ({len(phase3_df):,} < {expected_count:,})\n"
            msg += f"   This suggests rows were lost during processing!"
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            extra = len(phase3_df) - expected_count
            print(f"✓ Phase 3: Has {len(phase3_df):,} rows ({extra:,} more than Phase 2 due to NCT explosion)")
            checks_passed.append(True)
    
    # Check 2: No duplicates on guideline_pmid + ref_pmid
    if use_all_ncts:
        # Original format: Each (guideline, reference) pair should be unique
        passed, msg = check_no_duplicates(
            phase3_df,
            ['guideline_pmid', 'ref_pmid'],
            'Phase 3',
            'Each guideline-reference pair should be unique (use_all_ncts=True)'
        )
        print(msg)
        checks_passed.append(passed)
    else:
        # Exploded format: Each (guideline, reference, NCT) tuple should be unique
        passed, msg = check_no_duplicates(
            phase3_df,
            ['guideline_pmid', 'ref_pmid', 'ref_nct_number'],
            'Phase 3',
            'Each guideline-reference-NCT combination should be unique (use_all_ncts=False)'
        )
        print(msg)
        checks_passed.append(passed)
    
    # Check 3: Trial detection rate
    if use_all_ncts:
        # Check 'is_clinical_trial' column
        if 'is_clinical_trial' not in phase3_df.columns:
            msg = f"❌ Phase 3: Missing 'is_clinical_trial' column!"
            print(msg)
            ERRORS.append(msg)
            checks_passed.append(False)
        else:
            is_trial = phase3_df['is_clinical_trial'].fillna(False)
            trial_count = is_trial.sum()
            trial_pct = (trial_count / len(phase3_df) * 100) if len(phase3_df) > 0 else 0
            
            print(f"\nℹ️ Phase 3: Trial Detection")
            print(f"  Trials detected: {trial_count:,} / {len(phase3_df):,} ({trial_pct:.1f}%)")
            
            if trial_pct < 5:
                msg = f"⚠️ Phase 3: Very low trial detection rate ({trial_pct:.1f}%)"
                print(msg)
                WARNINGS.append(msg)
                checks_passed.append(False)
            else:
                checks_passed.append(True)
    else:
        # In exploded format, all rows should have NCT numbers
        has_nct = phase3_df['ref_nct_number'].notna()
        nct_pct = (has_nct.sum() / len(phase3_df) * 100) if len(phase3_df) > 0 else 0
        
        print(f"\nℹ️ Phase 3: NCT Coverage")
        print(f"  Rows with NCT: {has_nct.sum():,} / {len(phase3_df):,} ({nct_pct:.1f}%)")
        
        if nct_pct < 95:
            msg = f"⚠️ Phase 3: Some rows missing NCT numbers ({100-nct_pct:.1f}% missing)"
            print(msg)
            WARNINGS.append(msg)
            checks_passed.append(False)
        else:
            checks_passed.append(True)
    
    # Check 4: Valid NCT numbers
    if use_all_ncts and 'nct_numbers_list' in phase3_df.columns:
        # Check format of nct_numbers_list (semicolon-separated NCTs)
        trials_only = phase3_df[phase3_df['is_clinical_trial'] == True]
        if len(trials_only) > 0:
            # Sample check on first few rows
            sample = trials_only['nct_numbers_list'].head(100)
            invalid = []
            for val in sample:
                if pd.notna(val):
                    ncts = str(val).split(';')
                    for nct in ncts:
                        nct = nct.strip()
                        if nct and not nct.startswith('NCT') or len(nct) != 11:
                            invalid.append(nct)
            
            if invalid:
                msg = f"⚠️ Phase 3: Found {len(invalid)} invalid NCT numbers in sample\n"
                msg += f"   Examples: {invalid[:5]}"
                print(msg)
                WARNINGS.append(msg)
                checks_passed.append(False)
            else:
                print(f"✓ Phase 3: NCT number format looks valid (sample check)")
                checks_passed.append(True)
    elif 'ref_nct_number' in phase3_df.columns:
        # Check individual NCT numbers
        passed, msg = check_column_values(
            phase3_df[phase3_df['ref_nct_number'].notna()],
            'ref_nct_number',
            r'^NCT\d{8}$',
            'Phase 3',
            'NCT numbers should be valid'
        )
        print(msg)
        checks_passed.append(passed)
    
    # Check 5: Multi-NCT handling
    if use_all_ncts and 'nct_numbers_list' in phase3_df.columns:
        trials_only = phase3_df[phase3_df['is_clinical_trial'] == True].copy()
        if len(trials_only) > 0:
            # Count NCTs per row
            trials_only['nct_count'] = trials_only['nct_numbers_list'].apply(
                lambda x: len(str(x).split(';')) if pd.notna(x) else 0
            )
            
            single_nct = (trials_only['nct_count'] == 1).sum()
            multi_nct = (trials_only['nct_count'] > 1).sum()
            
            print(f"\nℹ️ Phase 3: Multi-NCT Statistics")
            print(f"  Single NCT: {single_nct:,}")
            print(f"  Multi-NCT: {multi_nct:,}")
            
            if multi_nct > 0:
                multi_pct = (multi_nct / len(trials_only) * 100)
                print(f"  Multi-NCT rate: {multi_pct:.1f}%")
                
                # Show examples of multi-NCT rows (limit to threshold)
                if multi_nct <= multi_nct_info_threshold:
                    print(f"\n  All {multi_nct} multi-NCT rows:")
                    multi_rows = trials_only[trials_only['nct_count'] > 1][['ref_pmid', 'nct_numbers_list', 'nct_count']]
                    for idx, row in multi_rows.iterrows():
                        print(f"    PMID {row['ref_pmid']}: {row['nct_count']} NCTs - {row['nct_numbers_list']}")
                else:
                    print(f"\n  Example multi-NCT rows (showing {multi_nct_info_threshold} of {multi_nct}):")
                    multi_rows = trials_only[trials_only['nct_count'] > 1][['ref_pmid', 'nct_numbers_list', 'nct_count']].head(multi_nct_info_threshold)
                    for idx, row in multi_rows.iterrows():
                        print(f"    PMID {row['ref_pmid']}: {row['nct_count']} NCTs - {row['nct_numbers_list']}")
                    print(f"    ... and {multi_nct - multi_nct_info_threshold} more")
    
    # Check 6: Detection flags consistency
    detection_flags = ['has_nct_in_title', 'has_nct_in_abstract', 'has_pubtype_clinicaltrial']
    present_flags = [f for f in detection_flags if f in phase3_df.columns]
    
    if present_flags and 'is_clinical_trial' in phase3_df.columns:
        # Trials should have at least one flag set
        trials_only = phase3_df[phase3_df['is_clinical_trial'] == True]
        if len(trials_only) > 0:
            no_flags = trials_only[~trials_only[present_flags].any(axis=1)]
            if len(no_flags) > 0:
                msg = f"⚠️ Phase 3: {len(no_flags)} trials have no detection flags set\n"
                msg += f"   This suggests is_clinical_trial was set without flag evidence"
                print(msg)
                WARNINGS.append(msg)
                checks_passed.append(False)
            else:
                print(f"✓ Phase 3: All trials have at least one detection flag")
                checks_passed.append(True)
    
    return all(checks_passed)


def validate_phase4(phase4_df, phase3_df=None):
    """Validate Phase 4: ClinicalTrials.gov Registry Data - FLEXIBLE"""
    print("\n" + "="*70)
    print("VALIDATING PHASE 4: ClinicalTrials.gov Registry Data")
    print("="*70)
    
    checks_passed = []
    
    # Find NCT column - flexible
    nct_col = None
    for col in ['nct_number', 'NCT', 'nct_id', 'trial_id']:
        if col in phase4_df.columns:
            nct_col = col
            break
    
    if not nct_col:
        msg = "❌ Phase 4: Could not find NCT column!"
        print(msg)
        ERRORS.append(msg)
        return False
    
    print(f"ℹ️ Phase 4: Using NCT column: {nct_col}")
    
    # Check 1: Should have data
    if len(phase4_df) == 0:
        msg = "⚠️ Phase 4: No trial data!"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 4: Has {len(phase4_df):,} trials")
        checks_passed.append(True)
    
    # Check 2: No duplicates
    passed, msg = check_no_duplicates(phase4_df, [nct_col], 'Phase 4', 'Each trial should appear once')
    print(msg)
    checks_passed.append(passed)
    
    # Check 3: Key fields (flexible)
    key_fields = {
        'Sex': ['nct_sex', 'sex', 'nct_eligibility_sex', 'eligibility_sex'],
        'Status': ['nct_status', 'nct_overall_status', 'status'],
        'Enrollment': ['nct_enrollment', 'enrollment'],
        'Phase': ['nct_phase', 'phase'],
    }
    
    print(f"\nℹ️ Phase 4: Checking key fields:")
    for field_name, possible_cols in key_fields.items():
        found = None
        for col in possible_cols:
            if col in phase4_df.columns:
                found = col
                break
        if found:
            non_null = phase4_df[found].notna().sum()
            pct = (non_null / len(phase4_df) * 100) if len(phase4_df) > 0 else 0
            print(f"  ✓ {field_name}: '{found}' ({pct:.1f}% coverage)")
        else:
            print(f"  ⚠️ {field_name}: not found")
    
    # Check 4: Compare to Phase 3
    if phase3_df is not None:
        phase3_nct_col = None
        for col in ['ref_primary_nct_number', 'nct_number', 'primary_nct', 'ref_nct_number']:
            if col in phase3_df.columns:
                phase3_nct_col = col
                break
        
        if phase3_nct_col:
            expected_min = phase3_df[phase3_nct_col].nunique()
            if len(phase4_df) < expected_min * 0.5:
                msg = f"\n⚠️ Phase 4: Only {len(phase4_df):,} trials (expected ~{expected_min:,})"
                print(msg)
                WARNINGS.append(msg)
                checks_passed.append(False)
            else:
                print(f"\n✓ Phase 4: Trial count reasonable")
                checks_passed.append(True)
    
    return all(checks_passed) if checks_passed else True


def validate_phase7(phase7_citations_df, phase7_trials_df, phase4_df):
    """
    Validate Phase 7: Sex Considerations Analysis
    
    Parameters:
    -----------
    phase7_citations_df : DataFrame
        UNIVERSE file (citation-level, with duplicates)
        File: phase7_guideline_reference_nct_UNIVERSE_ANALYZED.csv
    phase7_trials_df : DataFrame
        UNIQUE_TRIALS file (trial-level, deduplicated)
        File: phase7_trials_UNIQUE_NCT_ANALYZED.csv
    phase4_df : DataFrame
        Phase 4 output (for comparison)
    """
    print("\n" + "="*70)
    print("VALIDATING PHASE 7: Sex Considerations Analysis")
    print("="*70)
    
    checks_passed = []
    
    # Expected: Trial-level should have one row per unique trial
    if phase4_df is not None:
        expected_unique = phase4_df['nct_number'].nunique()
    else:
        expected_unique = 0
    
    print(f"\nℹ️ Phase 7 Baseline:")
    if phase4_df is not None:
        print(f"  Phase 4 total rows: {len(phase4_df):,}")
        print(f"  Phase 4 UNIQUE NCT numbers: {expected_unique:,}")
    print(f"  Phase 7 trials (unique): {len(phase7_trials_df):,}")
    print(f"  Phase 7 citations (with dups): {len(phase7_citations_df):,}")
    
    # Check 1: Trial-level has no duplicate NCT numbers
    passed, msg = check_no_duplicates(
        phase7_trials_df,
        ['nct_number'],
        'Phase 7 (Trials)',
        'Each trial should appear once in UNIQUE_TRIALS file'
    )
    print(msg)
    checks_passed.append(passed)
    
    # Check 2: Trial-level count matches expected unique trials
    if expected_unique > 0:
        passed, msg = check_row_count_match(
            phase7_trials_df,
            expected_unique,
            'Phase 7 (Trials)',
            tolerance=TOLERANCE_NORMAL,
            explanation="should match unique NCT numbers from Phase 4"
        )
        print(msg)
        checks_passed.append(passed)
    
    # Check 3: Citation-level should have more or equal rows than trial-level
    if len(phase7_citations_df) < len(phase7_trials_df):
        msg = f"❌ Phase 7: Citations ({len(phase7_citations_df):,}) has FEWER rows than Trials ({len(phase7_trials_df):,})!"
        msg += f"\n   UNIVERSE file should have at least as many rows as UNIQUE_TRIALS"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 7: Citations has {len(phase7_citations_df):,} rows (trials: {len(phase7_trials_df):,})")
        checks_passed.append(True)
    
    # Check 4: Citation ratio (average citations per trial)
    ratio = len(phase7_citations_df) / len(phase7_trials_df) if len(phase7_trials_df) > 0 else 0
    
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
    
    # Check 5: Sex analysis columns present
    sex_cols = ['sex_consideration_score', 'has_sex_differences', 'has_sex_stratification']
    present_sex_cols = [col for col in sex_cols if col in phase7_citations_df.columns]
    
    if len(present_sex_cols) == 0:
        msg = f"⚠️ Phase 7: No sex analysis columns found in Citations file!"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 7: Found {len(present_sex_cols)} sex analysis columns")
        checks_passed.append(True)
    
    # Check 6: Sex consideration score distribution
    if 'sex_consideration_score' in phase7_citations_df.columns:
        scores = phase7_citations_df['sex_consideration_score'].dropna()
        if len(scores) > 0:
            avg_score = scores.mean()
            has_any_sex = (scores > 0).sum()
            pct_with_sex = (has_any_sex / len(scores) * 100)
            
            print(f"\nℹ️ Phase 7: Sex Consideration Statistics")
            print(f"  Average score: {avg_score:.2f}")
            print(f"  Citations with sex consideration: {has_any_sex:,} / {len(scores):,} ({pct_with_sex:.1f}%)")
            
            if pct_with_sex < 5:
                msg = f"⚠️ Phase 7: Very low sex consideration rate ({pct_with_sex:.1f}%)"
                print(msg)
                WARNINGS.append(msg)
                checks_passed.append(False)
            else:
                checks_passed.append(True)
    
    return all(checks_passed)


def validate_phase8(phase8_folder, phase7_citations_df):
    """
    Validate Phase 8: Multi-Scenario Analysis
    
    Parameters:
    -----------
    phase8_folder : str
        Path to output folder containing Phase 8 files
    phase7_citations_df : DataFrame
        Phase 7 UNIVERSE file (input to Phase 8)
    """
    print("\n" + "="*70)
    print("VALIDATING PHASE 8: Multi-Scenario Analysis")
    print("="*70)
    
    checks_passed = []
    
    # Expected files
    required_files = [
        'phase8_scenario_comparison.csv',
        'phase8_key_metrics_comparison.csv',
        'phase8_data_dictionary.csv'
    ]
    
    # Check 1: Required comparison files exist
    missing_files = []
    for filename in required_files:
        filepath = os.path.join(phase8_folder, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
    
    if missing_files:
        msg = f"❌ Phase 8: Missing required files: {missing_files}"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
        return False  # Can't continue without these files
    else:
        print(f"✓ Phase 8: All required comparison files exist")
        checks_passed.append(True)
    
    # Load scenario comparison
    scenario_comp = pd.read_csv(os.path.join(phase8_folder, 'phase8_scenario_comparison.csv'))
    
    # Check 2: Should have 6 scenarios (S1-S6)
    expected_scenarios = 6
    actual_scenarios = len(scenario_comp)
    
    if actual_scenarios != expected_scenarios:
        msg = f"⚠️ Phase 8: Found {actual_scenarios} scenarios (expected {expected_scenarios})"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 8: All {expected_scenarios} scenarios generated")
        checks_passed.append(True)
    
    # Check 3: Each scenario has required columns
    required_cols = ['scenario_id', 'name', 'count', 'definition']
    missing_cols = [col for col in required_cols if col not in scenario_comp.columns]
    
    if missing_cols:
        msg = f"⚠️ Phase 8: Scenario comparison missing columns: {missing_cols}"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 8: Scenario comparison has all required columns")
        checks_passed.append(True)
    
    # Check 4: No scenario has zero rows (data loss check)
    zero_count_scenarios = scenario_comp[scenario_comp['count'] == 0]
    
    if len(zero_count_scenarios) > 0:
        msg = f"❌ Phase 8: {len(zero_count_scenarios)} scenarios have ZERO rows!\n"
        msg += f"   Scenarios: {zero_count_scenarios['scenario_id'].tolist()}"
        print(msg)
        ERRORS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 8: All scenarios have data")
        checks_passed.append(True)
    
    # Check 5: Scenario counts make sense relative to Phase 7
    if phase7_citations_df is not None:
        phase7_count = len(phase7_citations_df)
        print(f"\nℹ️ Phase 8: Scenario Sizes")
        print(f"  Phase 7 input: {phase7_count:,} citations")
        
        for _, row in scenario_comp.iterrows():
            scenario_id = row['scenario_id']
            count = row['count']
            pct = (count / phase7_count * 100) if phase7_count > 0 else 0
            print(f"  {scenario_id}: {count:,} ({pct:.1f}% of Phase 7)")
            
            # Check if any scenario is suspiciously large (>110% of Phase 7)
            if count > phase7_count * 1.1:
                msg = f"⚠️ Phase 8: {scenario_id} has MORE rows than Phase 7 input ({count:,} > {phase7_count:,})"
                msg += f"\n   This might indicate a cartesian product"
                print(msg)
                WARNINGS.append(msg)
                checks_passed.append(False)
    
    # Check 6: Individual scenario files exist
    print(f"\nℹ️ Phase 8: Checking individual scenario files...")
    missing_scenario_files = []
    
    for _, row in scenario_comp.iterrows():
        scenario_id = row['scenario_id']
        # Check for at least the overall statistics file
        stats_file = os.path.join(phase8_folder, f'phase8_{scenario_id}_overall_statistics.csv')
        if not os.path.exists(stats_file):
            missing_scenario_files.append(f"{scenario_id}_overall_statistics.csv")
    
    if missing_scenario_files:
        msg = f"⚠️ Phase 8: Missing scenario files: {missing_scenario_files[:5]}"
        if len(missing_scenario_files) > 5:
            msg += f" ... and {len(missing_scenario_files) - 5} more"
        print(msg)
        WARNINGS.append(msg)
        checks_passed.append(False)
    else:
        print(f"✓ Phase 8: All scenario files exist")
        checks_passed.append(True)
    
    # Check 7: No duplicate scenario IDs
    passed, msg = check_no_duplicates(
        scenario_comp,
        ['scenario_id'],
        'Phase 8',
        'Each scenario should appear once'
    )
    print(msg)
    checks_passed.append(passed)
    
    return all(checks_passed)


# ============================================================================
# OBSOLETE VALIDATORS (phases no longer in pipeline)
# ============================================================================
# The following validators are commented out because these phases were removed
# from the pipeline. Keeping them here for reference in case they're needed.
# ============================================================================

# def validate_phase5(phase5_df, phase1_df):
#     """[OBSOLETE] Validate Phase 5: Guidelines Summary - PHASE REMOVED"""
#     pass

# def validate_phase6(phase6_df, phase3_df):
#     """[OBSOLETE] Validate Phase 6: References with Abstracts - PHASE REMOVED"""
#     pass

# def validate_phase7b(phase7b_dedup_df, phase7b_citations_df, phase3_df, phase7_dedup_df):
#     """[OBSOLETE] Validate Phase 7B: All Trials Analysis - PHASE REMOVED"""
#     pass


# ============================================================================
# MASTER VALIDATION FUNCTION
# ============================================================================

def run_all_validations(output_folder=None):
    """
    Run all phase validations in sequence for current pipeline
    
    Parameters:
    -----------
    output_folder : str, optional
        Path to output folder. If None, uses OUTPUT_FOLDER global.
    
    Returns:
    --------
    tuple : (all_passed: bool, results: dict)
    """
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE PIPELINE VALIDATION")
    print("="*70)
    
    global OUTPUT_FOLDER, WARNINGS, ERRORS
    
    if output_folder:
        OUTPUT_FOLDER = output_folder
    
    WARNINGS = []
    ERRORS = []
    
    results = {}
    
    # Load all phase data
    print("\nLoading phase data...")
    try:
        phase1 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase1_pubmed_guidelines.csv'))
        print(f"  ✓ Phase 1: {len(phase1):,} rows")
    except FileNotFoundError as e:
        print(f"  ❌ Phase 1 not found: {e}")
        return False, {}
    
    try:
        phase2 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase2_crossref_guidelines_and_references.csv'))
        print(f"  ✓ Phase 2: {len(phase2):,} rows")
    except FileNotFoundError as e:
        print(f"  ❌ Phase 2 not found: {e}")
        return False, {}
    
    try:
        phase3 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase3_references_with_trials.csv'))
        print(f"  ✓ Phase 3: {len(phase3):,} rows")
    except FileNotFoundError as e:
        print(f"  ❌ Phase 3 not found: {e}")
        return False, {}
    
    try:
        phase4 = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase4_ctgov_trials_detailed.csv'))
        print(f"  ✓ Phase 4: {len(phase4):,} rows")
    except FileNotFoundError as e:
        print(f"  ❌ Phase 4 not found: {e}")
        phase4 = None
    
    # Phase 7 has two files
    try:
        phase7_citations = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase7_guideline_reference_nct_UNIVERSE_ANALYZED.csv'))
        print(f"  ✓ Phase 7 (Citations): {len(phase7_citations):,} rows")
    except FileNotFoundError as e:
        print(f"  ❌ Phase 7 Citations not found: {e}")
        phase7_citations = None
    
    try:
        phase7_trials = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase7_trials_UNIQUE_NCT_ANALYZED.csv'))
        print(f"  ✓ Phase 7 (Trials): {len(phase7_trials):,} rows")
    except FileNotFoundError as e:
        print(f"  ❌ Phase 7 Trials not found: {e}")
        phase7_trials = None
    
    # Phase 8 - check for scenario comparison file
    try:
        phase8_comp = pd.read_csv(os.path.join(OUTPUT_FOLDER, 'phase8_scenario_comparison.csv'))
        print(f"  ✓ Phase 8: {len(phase8_comp)} scenarios")
        has_phase8 = True
    except FileNotFoundError:
        print(f"  ⊘ Phase 8 not found (run if needed)")
        has_phase8 = False
    
    # Run validations
    print("\n" + "="*70)
    print("Running validations...")
    print("="*70)
    
    results['Phase 1'] = validate_phase1(phase1)
    results['Phase 2'] = validate_phase2(phase2, phase1)
    results['Phase 3'] = validate_phase3(phase3, phase2)
    
    if phase4 is not None:
        results['Phase 4'] = validate_phase4(phase4, phase3)
    
    if phase7_citations is not None and phase7_trials is not None:
        results['Phase 7'] = validate_phase7(phase7_citations, phase7_trials, phase4)
    
    if has_phase8:
        results['Phase 8'] = validate_phase8(OUTPUT_FOLDER, phase7_citations)
    
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
    -----------
    phase_num : int
        Phase number (1, 2, 3, 4, 7, or 8)
    df : DataFrame
        Current phase dataframe
    prev_df : DataFrame, optional
        Previous phase dataframe (for comparison)
    expected_count : int, optional
        Expected row count
    
    Returns:
    --------
    bool : True if check passed, False if issues found
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