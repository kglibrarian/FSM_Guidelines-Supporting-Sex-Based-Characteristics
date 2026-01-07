# Sex-Based Considerations in Clinical Practice Guidelines: Multi-Scenario Analysis Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Developed with Claude](https://img.shields.io/badge/Developed%20with-Claude%20Sonnet%204-blueviolet)](https://claude.ai)

A comprehensive analysis pipeline for systematically evaluating how clinical practice guidelines incorporate sex-based evidence from clinical trials. This repository contains the complete analytical framework used to assess sex consideration across multiple scenario definitions.

> **Note:** This pipeline was developed with substantial assistance from **Claude (Sonnet 4.5)**, Anthropic's AI assistant. Claude helped with code architecture, documentation, debugging, and implementing best practices throughout the development process.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Pipeline Phases](#pipeline-phases)
- [Output Files](#output-files)
- [Scenario Definitions](#scenario-definitions)
- [Sex Consideration Scoring](#sex-consideration-scoring)
- [Extending the Analysis](#extending-the-analysis)
- [Development Notes](#development-notes)
- [Citation](#citation)
- [License](#license)
- [Contact](#contact)

---

## 🔬 Overview

This pipeline analyzes clinical practice guidelines to assess how comprehensively they incorporate sex-based considerations from clinical trial evidence. The analysis:

- **Extracts citations** from clinical practice guidelines via PubMed
- **Identifies clinical trials** through multiple methods (PubMed classification, ClinicalTrials.gov registry)
- **Analyzes text** from titles, abstracts, and registry data for sex-based evidence
- **Scores sex consideration** using a validated composite metric (0-10 scale)
- **Generates multi-scenario analyses** showing how different trial definitions affect results
- **Produces comprehensive reports** with actionable recommendations

### Research Context

Sex-based differences in disease presentation, treatment response, and adverse events are well-documented, yet guidelines often fail to systematically incorporate this evidence. This pipeline provides an objective, reproducible method to:

1. Quantify the extent of sex consideration in guidelines
2. Identify gaps and best practices
3. Generate evidence-based recommendations for improvement

---

## ✨ Key Features

### Multi-Scenario Framework
- **6 pre-configured scenarios** (PubMed PT, Registry-Verified, Unique Trials, etc.)
- **Easy to extend** - add new scenarios with 8-line configuration
- **Comparative analysis** showing how definitions impact results

### Comprehensive Text Analysis
- **18+ search pattern groups** for detecting sex considerations
- **Multiple data sources**: titles, abstracts, registry fields
- **Evidence capture**: Extracts actual text snippets showing sex consideration
- **Validated scoring**: Composite 0-10 score with documented methodology

### Professional Deliverables
- **Multi-tab Excel workbook** with color-coded categories
- **75+ detailed CSV files** for further analysis
- **Complete documentation** including data dictionary and methodology
- **Reproducible** - fully documented code with extensive comments

### Designed for Research
- **No hardcoded values** - works with any guideline corpus
- **Transparent methodology** - every metric includes calculation details
- **Publication-ready** - generates tables, figures, and methods text
- **Extensible** - modular design for adding new analyses

---

## 🚀 Installation

### Requirements
```bash
Python 3.8+
pandas >= 1.3.0
numpy >= 1.20.0
openpyxl >= 3.0.0
requests >= 2.26.0
```

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/kglibrarian/FSM_Guidelines-Supporting-Sex-Based-Characteristics.git

cd FSM_Guidelines-Supporting-Sex-Based-Characteristics
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Optional: Install Jupyter for running notebooks:**
```bash
pip install jupyter
```

---

## 🏃 Quick Start

### Running the Complete Pipeline
```python
# 1. Run all phases in order
jupyter notebook analysis_pipeline.ipynb

# Or run individual phase files:
python phase1_guideline_extraction.py
python phase2_citation_extraction.py
python phase3_nct_extraction.py
python phase4_registry_fetch.py
python phase5_merge_data.py
python phase6_deduplication.py
python phase7_sex_analysis.py
python phase8_multi_scenario_stats.py
python phase9_recommendations.py
python phase10_excel_report.py
```

### Expected Runtime

| Phase | Time | Output |
|-------|------|--------|
| Phase 1-3 | ~30 min | Citation extraction & NCT identification |
| Phase 4 | ~45 min | Registry data fetch (API rate limited) |
| Phase 5-7 | ~15 min | Data merging & sex analysis |
| Phase 8-10 | ~10 min | Multi-scenario analysis & Excel report |
| **Total** | **~2 hours** | Complete analysis with all outputs |

---

## 📊 Pipeline Phases

### Phase 1: Guideline Extraction
**Input:** PubMed query for clinical practice guidelines  
**Output:** List of guideline PMIDs with metadata  
**Purpose:** Identify corpus of guidelines to analyze
```python
# Example: Extract cardiology guidelines from 2015-2025
query = '"practice guideline"[Publication Type] AND cardiology[MeSH] AND 2015:2025[PDAT]'
```

### Phase 2: Citation Extraction
**Input:** Guideline PMIDs  
**Output:** All references cited by each guideline  
**Purpose:** Build complete citation network via PubMed and CrossRef

**Key Features:**
- CrossRef API for comprehensive citation extraction
- DOI-based matching to PubMed
- Deduplication within guidelines

### Phase 3: NCT Number Extraction
**Input:** Citation PMIDs  
**Output:** ClinicalTrials.gov (NCT) numbers  
**Purpose:** Link citations to trial registry data

**Methods:**
- PubMed structured fields
- Regex extraction from titles/abstracts
- Captures both primary and secondary NCT numbers

### Phase 4: Registry Data Fetch
**Input:** NCT numbers  
**Output:** Complete trial metadata from ClinicalTrials.gov  
**Purpose:** Obtain sex eligibility, outcomes, enrollment data

**Retrieved Fields:**
- Sex eligibility (All/Male/Female)
- Enrollment counts
- Eligibility criteria text
- Primary/secondary outcomes
- Trial phases, status, dates

### Phase 5: Data Merging
**Input:** Citations + NCT data  
**Output:** Unified dataset  
**Purpose:** Create analysis-ready structure

**Structures Created:**
- `UNIVERSE`: Citation-level (one row per guideline-reference pair)
- `EXPLODED`: Citation-trial pairs (one row per citation-NCT combination)

### Phase 6: Deduplication
**Input:** Merged data  
**Output:** Deduplicated files  
**Purpose:** Create unique trial list

**Deduplication Levels:**
1. Within guideline: References unique per guideline
2. Across guidelines: NOT deduplicated (preserves citation patterns)
3. Trial-level: Unique NCT list created separately

### Phase 7: Sex Consideration Analysis
**Input:** Merged data  
**Output:** Sex consideration flags and scores  
**Purpose:** Identify and quantify sex-based evidence

**Analysis Components:**
- Text pattern matching (18+ pattern groups)
- Boolean flags (sex differences, stratification, subgroups, etc.)
- Composite scoring (0-10 scale)
- Evidence snippet capture

### Phase 8: Multi-Scenario Statistics
**Input:** Analyzed data  
**Output:** Statistics for 6 scenarios  
**Purpose:** Show how trial definitions affect results

**Calculations:**
- Overall corpus statistics
- Guideline-level aggregations
- Trial characteristics
- Evidence snippet aggregation

### Phase 9: Insights & Recommendations
**Input:** Scenario statistics  
**Output:** Categorizations and recommendations  
**Purpose:** Generate actionable findings

**Deliverables:**
- Guideline performance categories (Strong/Moderate/Weak/Inadequate)
- Specific recommendations by scenario
- Research gaps identified
- Stakeholder-specific actions

### Phase 10: Excel Report Generation
**Input:** All phase outputs  
**Output:** Comprehensive Excel workbook  
**Purpose:** Professional, publication-ready deliverable

**Workbook Contents:**
- Executive summary
- Scenario comparison tables
- Individual scenario tabs (with color-coded categories)
- Evidence snippets
- Recommendations by scenario
- Actionable recommendations by stakeholder
- Complete data dictionary

---

## 📁 Output Files

### Primary Deliverable
```
output/
├── Sex_Based_Guidelines_Multi_Scenario_Analysis.xlsx  # Main report (11 tabs)
```

### Intermediate Files (by Phase)

#### Phase 1-4: Data Extraction
```
output/
├── phase1_guidelines_PMIDS.csv                    # Guidelines list
├── phase2_guideline_references_CITATIONS.csv      # All citations
├── phase3_nct_numbers_EXTRACTED.csv               # NCT numbers
├── phase4_nct_registry_data_FETCHED.csv           # Registry data
```

#### Phase 5-7: Merging & Analysis
```
output/
├── phase5_guideline_reference_nct_MERGED.csv      # Combined data
├── phase6_guideline_reference_nct_UNIVERSE.csv    # Deduplicated citations
├── phase7_guideline_reference_nct_UNIVERSE_ANALYZED.csv  # With sex analysis
├── phase7_trials_UNIQUE_NCT_ANALYZED.csv          # Unique trials only
```

#### Phase 8: Scenario Statistics (×6 scenarios)
```
output/
├── phase8_S1_PubMed_PT_overall_statistics.csv
├── phase8_S1_PubMed_PT_guideline_statistics.csv
├── phase8_S1_PubMed_PT_guideline_categories.csv
├── ... (×6 scenarios)
├── phase8_scenario_comparison.csv                 # Cross-scenario comparison
├── phase8_data_dictionary.csv                     # Complete documentation (47 columns)
├── phase8_scoring_summary.csv                     # Scoring methodology
```

#### Phase 9: Recommendations
```
output/
├── phase9_recommendations_all_scenarios.csv
├── phase9_actionable_recommendations.csv
├── recommendation_S4_R1_inadequate_sex.csv        # Evidence files
├── ... (multiple recommendation evidence files)
```

---

## 🔍 Scenario Definitions

The pipeline analyzes **6 scenarios** to show how different definitions of "clinical trial" affect results:

### S1: PubMed Publication Type (Conservative)
```python
'filter': lambda df: df['ref_is_clinical_trial_pt_type'] == True
```
- Uses PubMed's official classification
- Most conservative definition
- Good for comparison with other studies
- **Cannot verify sex inclusion** (no registry data)

### S2: PubMed OR Registry (Comprehensive)
```python
'filter': lambda df: (df['ref_is_clinical_trial_pt_type'] == True) | 
                     (df['ref_primary_nct_number'].notna())
```
- Broadest definition
- Captures trials identified by either method
- **Partial sex verification** (~39% have NCT)

### S3: Unique Trials (Deduplicated)
```python
'data_source': 'UNIQUE_TRIALS'  # Load deduplicated file
```
- One row per unique NCT number
- Avoids double-counting same trial
- **100% sex verifiable**
- Use for trial characteristics

### S4: Registry-Verified (⭐ RECOMMENDED)
```python
'filter': lambda df: df['ref_primary_nct_number'].notna()
```
- Only trials with NCT numbers
- **100% sex verifiable**
- Most defensible for sex inclusion claims
- **Recommended as primary analysis**

### S5: All NCT Mentions
```python
'filter': lambda df: df['ref_all_nct_numbers'].notna()
```
- Includes secondary NCT references
- Captures complete trial network
- **100% sex verifiable**

### S6: High-Quality Registry Data
```python
'filter': lambda df: (df['ref_primary_nct_number'].notna()) & 
                     (df['nct_official_title'].notna())
```
- Subset with complete registry data
- No failed fetches
- **100% sex verifiable**
- Highest confidence subset

---

## 🧮 Sex Consideration Scoring

### Composite Score Formula (0-10 Scale)

#### HIGH VALUE (2 points each, max 6)
```python
+2 if any_source_mentions_sex_differences == True
+2 if any_source_mentions_sex_stratification == True
+2 if any_source_mentions_sex_subgroup == True
```

#### MEDIUM VALUE (1 point each, max 4)
```python
+1 if any_source_pregnancy_related == True
+1 if any_source_menopause_related == True
+1 if any_source_sex_hormone_related == True
+1 if nct_sex_includes_women == True
```

### Search Patterns

**18+ pattern groups** including:
- Sex differences: `sex-specific`, `between men and women`, `sex disparities`
- Stratification: `stratified by sex`, `sex-disaggregated`
- Subgroups: `sex subgroup analysis`, `interaction by gender`
- Biological: `pregnancy`, `menopause`, `estrogen`, `testosterone`

**Searched across:**
- Reference titles
- Reference abstracts
- ClinicalTrials.gov descriptions
- Eligibility criteria
- Outcome measures

### Guideline Categorization

| Category | Criteria |
|----------|----------|
| **Strong** | ≥20% citations mention sex AND avg score ≥2.0 |
| **Moderate** | ≥10% citations mention sex AND avg score ≥1.0 |
| **Weak** | ≥5% citations mention sex |
| **Inadequate - No Sex** | <5% citations mention sex |
| **Inadequate - No Trials** | 0 trial citations in scenario |

---

## 🔧 Extending the Analysis

### Adding a New Scenario

**Example: Analyze only Phase 3/4 trials**
```python
# In Phase 8, add to scenarios dictionary:
'S7_Phase3_4': {
    'name': 'Phase 3/4 Trials Only',
    'short_name': 'Phase 3/4',
    'filter': lambda df: (
        df['ref_primary_nct_number'].notna() &
        df['nct_phases'].notna() &
        df['nct_phases'].str.contains('Phase 3|Phase 4', case=False, na=False)
    ),
    'description': 'Late-stage pivotal trials (Phase 3 or 4)',
    'definition': 'NCT not null AND phases contains "Phase 3" or "Phase 4"',
    'can_verify_sex': True,
    'count_type': 'citation',
    'data_source': 'UNIVERSE',
    'color': 'FFE6CC',
    'priority': 7,
    'rationale': 'Pivotal trials most likely to inform clinical practice'
}
```

**Re-run Phases 8-10** (~10 minutes) and the new scenario automatically appears in all outputs!

### Adding New Search Patterns

**Example: Add patterns for gender-affirming care**
```python
# In Phase 7, add new pattern group:
GENDER_AFFIRMING_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r'\bgender-affirming\b',
    r'\bhormone therapy\b.*\btransgender\b',
    r'\bgender transition\b'
]]

# Add to analysis function:
if all_text and regex_any(GENDER_AFFIRMING_PATTERNS, all_text):
    analysis['any_source_gender_affirming_care'] = True
```

### Analyzing Different Guidelines

**Change Phase 1 query:**
```python
# Oncology guidelines
query = '"practice guideline"[PT] AND (cancer[MeSH] OR oncology[MeSH])'

# Pediatric guidelines
query = '"practice guideline"[PT] AND (pediatric*[Title] OR child*[MeSH])'

# COVID-19 guidelines
query = '"practice guideline"[PT] AND covid-19[MeSH]'
```

Pipeline automatically adapts to any guideline corpus!

---

## 💻 Development Notes

### Developed with Claude AI

This pipeline was developed with substantial assistance from **Claude (Sonnet 4.5)**, Anthropic's AI assistant. Claude's contributions included:

#### Code Architecture & Design
- Multi-scenario framework design and configuration system
- Modular phase structure with extensibility patterns
- Data dictionary and metadata documentation approach
- Excel report generation with dynamic formatting

#### Implementation Support
- Pattern matching optimization for sex consideration detection
- Deduplication logic across multiple levels (within/across guidelines)
- Error handling and edge case management
- Memory-efficient data processing strategies

#### Documentation & Best Practices
- Comprehensive inline code comments
- README and methodology documentation
- Dynamic email generation for researchers
- Reproducibility guidelines

#### Debugging & Optimization
- Data merging and alignment issues
- NaN handling in pandas operations
- Excel formatting and color-coding
- Performance optimization for large datasets

### Working with Claude

**What worked well:**
- Iterative development with immediate feedback
- Explaining complex research requirements in plain language
- Debugging with actual error messages
- Generating dynamic, reusable code (no hardcoded values)

**Best practices we followed:**
- Clear problem definition at each phase
- Testing with small datasets before full corpus
- Extensive commenting for future maintainability
- Modular design for easy extension

### Claude Version Information

**Model:** Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)  
**Platform:** Claude.ai (Web Interface)  
**Development Period:** January 2026  
**API Features Used:** None (all development through chat interface)

**Note:** While Claude provided substantial coding assistance, all research design decisions, analytical choices, and interpretation of results were made by the research team. Claude served as a programming assistant and documentation aid, not as a research collaborator.

### Reproducibility Considerations

Since this code was developed with AI assistance:

1. **Code is fully standalone** - No dependencies on Claude for execution
2. **All logic is explicit** - No "black box" AI components in the pipeline
3. **Extensively documented** - Comments explain all decisions
4. **Deterministic results** - Same inputs always produce same outputs
5. **Transparent methodology** - All search patterns and scoring formulas documented

Anyone can run, modify, and extend this pipeline without requiring AI assistance.

---

## 📖 Citation

If you use this pipeline in your research, please cite:
```bibtex
@software{sex_guidelines_analysis_2026,
  author = {[Your Name] and {Galter Health Sciences Library}},
  title = {Sex-Based Considerations in Clinical Practice Guidelines: 
           Multi-Scenario Analysis Pipeline},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/yourusername/sex-based-guidelines-analysis},
  note = {Developed with assistance from Claude (Sonnet 4.5), Anthropic}
}
```

**Related Publication:**  
[Your paper citation once published]

**Acknowledgment suggestion for papers:**
> "Analysis pipeline development was assisted by Claude (Sonnet 4.5), an AI assistant created by Anthropic, for code implementation, documentation, and debugging. All research design decisions and result interpretations were made by the research team."

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```
MIT License

Copyright (c) 2026 Northwestern University, Galter Health Sciences Library

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🐛 Known Issues & Limitations

1. **API Rate Limits**: ClinicalTrials.gov API limits to 1 request/second (Phase 4 is slowest)
2. **PubMed Access**: Requires internet connection; large queries may timeout
3. **Memory Usage**: Full corpus analysis requires ~8GB RAM for 75 guidelines
4. **Text Analysis**: English-language only (patterns need translation for other languages)
5. **Registry Coverage**: Only trials registered in ClinicalTrials.gov are verifiable
6. **Pattern Matching**: Relies on keyword patterns; may miss implicit sex considerations
7. **Time Period**: Guidelines and registry data reflect state at time of extraction

---

## 📞 Contact

**Project Maintainer:** Karen Gutzman
**Email:** karen.gutzman@northwestern.edu 
**Institution:** Northwestern University, Feinberg School of Medicine, Galter Health Sciences Library

---

## 🙏 Acknowledgments

### People
- **Research Team**: Sadiya Khan, Molly Maradik, Karen Gutzman
- **Northwestern University** Feinberg School of Medicine
- **Collaborators**: Mao Soulakis, Emma Wilson

### Tools & Services
- **Claude (Sonnet 4.5)** by Anthropic - AI-assisted development
- **PubMed/NCBI** - E-utilities API for literature access
- **ClinicalTrials.gov** - Registry data API
- **CrossRef** - Citation extraction API
- **Python ecosystem** - pandas, numpy, openpyxl

### Funding
None

---

## 📚 Additional Resources

### Documentation
- [Data Dictionary](output/phase8_data_dictionary.csv)



---

## 📝 Version History

### Version 1.0.0 (2026-01-07)
- Initial public release
- Complete 10-phase pipeline
- Multi-scenario framework (6 scenarios)
- Excel report generation
- Comprehensive documentation
- AI-assisted development with Claude Sonnet 4.5

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

**Last Updated:** 2026-01-07  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

---

*This pipeline was developed to promote transparency and reproducibility in assessing sex-based evidence in clinical guidelines. We hope it serves as a valuable tool for researchers, guideline developers, and policy makers working to improve health equity.*

*Special thanks to Anthropic's Claude for assistance in transforming research requirements into working code. The combination of domain expertise and AI-assisted development enabled rapid iteration and comprehensive documentation.*
