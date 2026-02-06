# Sex-Based Considerations in Clinical Practice Guidelines

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Developed with Claude](https://img.shields.io/badge/Developed%20with-Claude%20Sonnet%204-blueviolet)](https://claude.ai)

A comprehensive pipeline for evaluating how clinical practice guidelines incorporate sex-based evidence from clinical trials and full-text guideline documents.

> **Note:** Developed with assistance from **Claude (Sonnet 4.5)**, Anthropic's AI assistant.

---

## 📋 Overview

This repository contains **two complementary analysis pipelines**:

### 1. Citation-Level Analysis (Main Pipeline)
Analyzes how guidelines cite and incorporate sex-based evidence from clinical trials:
- Extracts all citations from guidelines via PubMed and CrossRef
- Identifies clinical trials through multiple methods
- Links trials to ClinicalTrials.gov registry data
- Analyzes titles, abstracts, and registry fields for sex considerations
- Generates multi-scenario analyses with 6 different trial definitions
- Produces comprehensive Excel reports with recommendations

### 2. Full-Text Analysis
Analyzes the actual text of guideline PDFs:
- Extracts text from guideline PDF files
- Searches for sex-based language throughout guideline text
- Captures evidence snippets with page numbers
- Complements citation analysis with direct guideline content assessment
- Identifies where guidelines explicitly discuss sex considerations

Together, these pipelines provide **both citation behavior** (what trials guidelines cite) and **content analysis** (what guidelines actually say about sex).

---

## ✨ Key Features

**Citation-Level Analysis:**
- 🔢 **6 scenario definitions** - Compare results under different trial classification methods
- 📊 **Multi-source text analysis** - Examines titles, abstracts, and registry data
- 🎯 **Validated scoring** - Composite 0-10 sex consideration score
- 📈 **Professional reports** - Multi-tab Excel workbooks with color-coded categories
- 🔄 **Fully reproducible** - Documented methodology and extensible design

**Full-Text Analysis:**
- 📄 **PDF text extraction** - Works with any guideline PDF corpus
- 🔍 **Pattern-based detection** - Same search patterns as citation analysis
- 📝 **Evidence capture** - Actual text snippets with page numbers
- ✅ **Quality filtering** - High-confidence vs. all mentions
- 📊 **Excel deliverables** - Summary statistics and detailed evidence

---

## 🚀 Installation

### Requirements
```bash
Python 3.8+
pandas >= 2.0.0
numpy >= 1.20.0
biopython >= 1.80
requests >= 2.26.0
openpyxl >= 3.0.0
xlsxwriter >= 3.0.0
tqdm >= 4.60.0
```

### Setup

1. **Clone and create environment:**
```bash
git clone https://github.com/yourusername/sex-based-guidelines-analysis.git
cd sex-based-guidelines-analysis
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure API access:**
```python
# Create config.py with:
ENTREZ_EMAIL = "your.email@institution.edu"
ENTREZ_API_KEY = "your_ncbi_api_key"  # Optional but recommended
```

3. **Prepare data:**
```bash
# For citation analysis:
data/all_final_guidelines.csv  # Guideline PMIDs

# For full-text analysis:
data/final_guidelines.csv       # PMID → PDF filename mapping
data/guidelines_full_text/*.pdf # PDF files of guidelines
```

---

## 🏃 Quick Start

### Citation-Level Analysis

**Run the main Jupyter notebook:**
```bash
jupyter notebook Guidelines_Supporting_Sex_Based_Characteristics.ipynb
```

**Pipeline phases:**
1. **Phase 1-2:** Extract citations from guidelines (~1-2 hours)
2. **Phase 3-4:** Identify trials and fetch registry data (~2-3 hours)
3. **Phase 7:** Analyze sex considerations (~10-30 minutes)
4. **Phase 8-10:** Multi-scenario analysis and Excel report (~10 minutes)

**Total runtime:** ~4-6 hours (mostly API calls with rate limits)

**Key output:** `Sex_Based_Guidelines_Multi_Scenario_Analysis.xlsx`

### Full-Text Analysis

**Run the full-text notebook:**
```bash
jupyter notebook Guidelines_Supporting_Sex_Based_Characteristics_Full_Text_Analysis.ipynb
```

**What it does:**
- Extracts text from all guideline PDFs
- Searches for sex-based patterns
- Generates evidence snippets with page numbers
- Creates filtered high-confidence results

**Runtime:** ~10-20 minutes (depends on PDF count and size)

**Key output:** `guideline_fulltext_analysis_COMPLETE.xlsx`

---

## 📊 Citation Pipeline Overview

### Multi-Scenario Framework

The pipeline analyzes citations under **6 different scenario definitions**:

| Scenario | Definition | Use Case |
|----------|------------|----------|
| **S1: PubMed PT** | PubMed "Clinical Trial" publication type | Conservative, comparison with other studies |
| **S2: PubMed OR Registry** | PT type OR has NCT number | Most comprehensive total counts |
| **S3: Unique Trials** | Deduplicated trial-level | Each trial counted once |
| **S4: Registry Verified** ⭐ | NCT-registered only | **Recommended** - verifiable sex inclusion |
| **S5: All NCTs** | All with NCT numbers | Registry-linked subset |
| **S6: High Quality** | Quality-filtered NCT trials | Stringent criteria |

**Why multiple scenarios?** Different studies and stakeholders define "clinical trial" differently. This framework shows how definition choice affects results and allows readers to choose the most appropriate definition for their purpose.

### Sex Consideration Detection

**18+ pattern groups** detect sex-based language across:
- Sex/gender differences or disparities
- Sex-stratified analysis or reporting
- Sex-based subgroup analysis
- Pregnancy, lactation, contraception
- Menopause and reproductive health
- Sex hormones (estrogen, testosterone, etc.)
- Women-specific conditions (PCOS, endometriosis, etc.)
- Gender identity terms (transgender, gender dysphoria)
- Sex-biased language

**Scoring:**
- **0-10 composite score** with transparent calculation
- **Boolean flags** for each consideration type
- **Evidence snippets** showing actual matching text
- **Three-tier confidence:** High (substantial), Medium (brief mention), Low (ambiguous)

---

## 📁 Repository Structure

```
sex-based-guidelines-analysis/
├── Guidelines_Supporting_Sex_Based_Characteristics.ipynb  # Main pipeline
├── Guidelines_Supporting_Sex_Based_Characteristics_Full_Text_Analysis.ipynb  # Full-text
├── config.py                           # API keys (create this)
├── normalized_checkpoint_system.py     # Checkpoint system for API phases
├── pipeline_validation_checks.py       # Data quality validation
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
│
├── data/
│   ├── all_final_guidelines.csv       # Input: Guideline PMIDs
│   ├── final_guidelines.csv           # Input: PMID → PDF mapping
│   └── guidelines_full_text/          # Input: Guideline PDFs
│       └── *.pdf
│
└── output/
    ├── phase1_pubmed_guidelines.csv              # Guideline metadata
    ├── phase2_crossref_...csv                    # Citations
    ├── phase3_references_with_trials.csv         # Trial detection
    ├── phase4_ctgov_trials_detailed.csv          # Registry data
    ├── phase7_*_ANALYZED.csv                     # Sex analysis
    ├── phase8_*.csv                              # Scenario results
    ├── phase9_recommendations.csv                # Action items
    ├── Sex_Based_Guidelines_Multi_Scenario_Analysis.xlsx  # Main report
    └── guideline_fulltext_analysis_COMPLETE.xlsx         # Full-text report
```

---

## 🎯 Using the Results

### For Researchers
- **Methods section:** Use data dictionary and scenario definitions
- **Results:** Choose primary scenario (S4 recommended) and report sensitivity across scenarios
- **Supplementary materials:** Include scenario comparison tables

### For Guideline Developers
- **Identify gaps:** See which guidelines lack sex consideration
- **Best practices:** Learn from high-performing guidelines
- **Recommendations:** Review Phase 9 action items

### For Policy Makers
- **Aggregate patterns:** Overall trends in sex consideration
- **Priority areas:** Where improvement is most needed
- **Evidence-based mandates:** Data to support policy requirements

---

## 🔧 Extending the Analysis

### Adding New Scenarios (Citation Pipeline)

Edit Phase 8 scenarios dictionary:
```python
scenarios = {
    'S7_Your_Scenario': {
        'name': 'Your Scenario Name',
        'filter': lambda df: df['your_condition'] == True,
        'description': 'What this scenario represents',
        # ... other metadata
    }
}
```

Re-run Phase 8-10 only. All analyses automatically regenerate.

### Customizing Sex Detection Patterns

Edit Phase 7 pattern definitions:
```python
PATTERNS = {
    'your_new_pattern': {
        'terms': ['term1', 'term2'],
        'context': r'your_regex_pattern',
        'category': 'HIGH_CONFIDENCE',
    }
}
```

### Adapting to Your Corpus

**For different guidelines:**
- Modify Phase 1 PubMed query
- Update `data/all_final_guidelines.csv`

**For different trial registries:**
- Extend Phase 4 to query other registries (EudraCT, ISRCTN, etc.)
- Add registry-specific field parsers

**For other languages:**
- Translate pattern terms in Phase 7
- Adjust regex patterns for language-specific grammar

---

## 📖 Citation

```bibtex
@software{sex_guidelines_analysis_2026,
  author = {[Your Name]},
  title = {Sex-Based Considerations in Clinical Practice Guidelines: Analysis Pipeline},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/yourusername/sex-based-guidelines-analysis},
  note = {Developed with assistance from Claude (Sonnet 4.5), Anthropic}
}
```

**Acknowledgment for papers:**
> "Analysis pipeline development was assisted by Claude (Sonnet 4.5), an AI assistant created by Anthropic, for code implementation and documentation. All research design decisions and result interpretations were made by the research team."

---

## 🐛 Known Limitations

1. **API rate limits** - ClinicalTrials.gov: 1 req/sec, PubMed: 10 req/sec with key
2. **English-only** - Pattern matching works for English text only
3. **Registry coverage** - Only ClinicalTrials.gov trials are verifiable for sex inclusion
4. **Pattern-based** - May miss implicit or novel phrasing of sex considerations
5. **Snapshot in time** - Results reflect data state at extraction date
6. **PDF extraction** - Full-text analysis quality depends on PDF text layer

---

## 📄 License

MIT License - See LICENSE file for details.

**Copyright (c) 2026 Northwestern University, Galter Health Sciences Library**

---

## 👥 Contact

**Maintainer:** [Your Name]  
**Email:** [your.email@northwestern.edu]  
**Institution:** Northwestern University, Galter Health Sciences Library

**For questions:**
- Technical issues → Open a GitHub issue
- Collaboration → Email directly
- Data requests → See paper data availability statement

---

## 🙏 Acknowledgments

### Development
- **Claude (Sonnet 4.5)** by Anthropic - AI-assisted development
- **Northwestern University** Galter Health Sciences Library

### Data Sources
- **PubMed/NCBI** - E-utilities API
- **ClinicalTrials.gov** - Registry API
- **CrossRef** - Citation extraction API

### Note on AI Assistance

This pipeline was developed with substantial assistance from Claude (Sonnet 4.5) for:
- Code architecture and modular design
- Documentation and commenting
- Debugging and optimization
- Best practices implementation

**However:** All research design decisions, analytical choices, pattern definitions, and interpretation of results were made by the research team. Claude served as a programming assistant, not a research collaborator. The code is fully standalone and deterministic - no AI components are required for execution.

---

**Last Updated:** 2026-01-30  
**Version:** 1.0.0  
**Status:** ✅ Production Ready

---

*This pipeline was developed to promote transparency and reproducibility in assessing sex-based evidence in clinical guidelines. We hope it serves as a valuable tool for researchers, guideline developers, and policy makers working to improve health equity.*
