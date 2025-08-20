# LLM-Powered Literature Mining System for MARVEL

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)
[![MARVEL Compatible](https://img.shields.io/badge/MARVEL-Compatible-orange.svg)](https://marvel.readthedocs.io)

## Project Overview

**LLM-Powered Literature Mining System for MARVEL** is an intelligent literature mining system based on large language models, specifically designed for the MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm. The system provides an automated workflow for literature retrieval and analysis, starting from natural language queries and progressing through metadata filtering and content classification.

For data extraction, since the original literature can only be mannualy fetched, this project offers carefully designed prompts to guide the LLM in extracting high quality experimental molecular spectroscopy data.

### Core Features

- **Intelligent Literature Retrieval**: Automatically extracts keywords from natural language queries and searches relevant academic literature
- **Deep Content Analysis**: Utilizes large language models for in-depth content analysis of the relevance between MARVEL research and the literature
- **High Quality Data Extraction**: Provides optimized prompts contribute to the extraction of high-quality data in a format compatible with MARVEL
- **Quality Control**: Intelligently filters theoretical calculation data, old data and imcomplete data, ensuring new experimental observations are extracted

### Application Scenarios

- Molecular spectroscopy database construction and maintenance
- Data source expansion for MARVEL algorithm

## Quick Start

### System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, Linux
- **Network**: Stable internet connection (for API calls)

### Installation Steps

1. **Clone the Repository**

```bash
git clone https://github.com/Songzx07/LLM_MARVEL.git
cd "LLM_MARVEL_Mining"
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### API Configuration

Before running the system, users need to configure the following API keys:

1. **Edit Configuration Files**

   - Navigate to `llm_literature_search/config/settings.py`
   - Navigate to `llm_literature_analysis/config/settings.py`

2. **Set API Keys**

```python
# LLM API Configuration
GROQ_API_KEY = "your_groq_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"

# Elsevier API Configuration (for literature retrieval)
ELSEVIER_API_KEY = "your_elsevier_api_key_here"
```

3. **Obtain API Keys**
   - **Groq API**: Visit [Groq Console](https://console.groq.com/) for free access
   - **Gemini API**: Visit [Google AI Studio](https://makersuite.google.com/) for free access
   - **Elsevier API**: Visit [Elsevier Developer Portal](https://dev.elsevier.com/) to apply for academic license

## Usage Guide

### 1. Literature Retrieval Module

Retrieve relevant academic literature using natural language queries:

```bash
cd llm_literature_search
python search.py
```

#### Compulsory Inputs:

- IUPAC Name of the Molecule
- Molecular Formula
- Search Year Range (10-year range per search is recommended)

#### Optional Inputs:

- Isotopic Molecular Formula
- Additional Keywords
- Citation Count

**Interface Example of CH4-literature Retrieval**:

```
======================================================================
Please enter the name and chemical formula of the molecule you want to search for:
Enter the molecule name (e.g., 'methane'): methane
Enter the molecular formula (e.g., 'CH4'): CH4

If you want to search for a specific isotope of the molecule, please specify it as well. Only one isotope can be specified at a time.
Enter the isotope (e.g., '12CH4', press Enter to skip): 12CH4

======================================================================
Any specifically required keywords:
(Specify keywords that can help search for more relvant papers)

Please enter required keywords (comma-separated, press Enter to skip):

======================================================================
Set year range for searching (minimum valid year is 1900):

Please enter year range (e.g., 2000-2023, press Enter for no restriction): 2010-2019

Year range set: 2010-2019

======================================================================
Restriction on citation count:

1. No restriction on citation count (0 citations allowed)
2. At least 1 citation (low impact)
3. At least 5 citations (medium impact)
4. At least 20 citations (high impact)
5. At least 50 citations (very high impact)

Please choose (1-5, defaults to 3): 3

======================================================================
```

The output files containing the analysis results are stored in a folder named with the search timestamp inside the **retrieval_results** directory, which is located under the llm_literature_search project folder.

The fetched Elsevier XML files are saved stored in a folder named with the analysis timestamp inside the **article_xmls** directory, which is placed at the same directory level as llm_literature_search.

### 2. Literature Analysis Module

Perform in-depth analysis and data extraction on retrieved literature:

```bash
cd llm_literature_analysis
python analysis.py
```

#### Compulsory Inputs:

- Directory of folder containing XML file under **article_xmls**

#### Optional Inputs:

- Output folder name

**Interface Example of Benchmark Analysis**:

```
Enter the folder path containing XML files (or press Enter to use default '../article_xmls'): Test_files_F

======================================================================
Output settings:
Output filename (defaults to paper_analysis_results_20250817_162927.json):

======================================================================
ANALYSIS CONFIGURATION:
LLM Service: Gemini API using model gemini-2.5-flash
Target Folder: ../article_xmls/Test_files_F
XML Files Found: 19
Output File: paper_analysis_results_20250817_162927.json
======================================================================

Starting analysis...
```

## Project Structure Details

```
LLM_MARVEL_Mining/
├── llm_literature_search/          # Literature Retrieval Module
│   ├── search.py                      # Main retrieval program entry
│   ├── src/                           # Retrieval functionality source code
│   │   └── core/
│   │       ├── llm_processor.py       # LLM processing logic
│   │       ├── elsevier_article_retrieval.py  # Elsevier API interface
│   │       ├── keyword_extractor.py   # Keyword extraction
│   │       ├── literature_searcher.py # Literature search engine
│   │       └── paper_filter.py        # Paper filtering logic
│   ├── config/
│   │   └── settings.py                # API keys and parameter configuration
│   └── retrieval_results/             # Retrieval results output directory
│
├── llm_literature_analysis/        # Literature Analysis Module
│   ├── analysis.py                    # Main analysis program entry
│   ├── src/                           # Analysis functionality source code
│   │   └── core/
│   │       ├── llm_client.py          # LLM-powered analysis tool
│   │       ├── paper_analyzer.py      # Paper analysis engine
│   │       └── xml_processor.py       # XML document processor
│   ├── config/
│   │   └── settings.py                # LLM model configuration
│   └── analysis_results/              # Analysis results output directory
│
├── prompts_for_content_extraction/ # LLM Prompt Templates
│   ├── USE.md                         # Prompt usage instructions
│   ├── General_Prompts/               # General data extraction templates
│   └── CH4-Prompts/                   # Methane-specific templates
│
├── article_xmls/                   # Fetched XML Files
│
│
├── project_results/                # Final Results Output Directory
│   ├── Retrieval/                     # Statistical results of retrieved literature
│   ├── Analysis/                      # Statistical results of analysed literature
│   ├── Content_Extraction/            # Extracted molecular data(The specific content is not displayed for copyright reasons)
│   └── Benchmark/                     # Performance evaluation data
│
├── requirements.txt                # Python dependencies list
└── README.md                       # Project documentation
```

### Core Module Functionality

#### llm_literature_search

- **Automatic Keyword Extraction**: Intelligently identifies scientific keywords from natural language queries

- **Result Filtering and Ranking**: Filters literature based on relevance and quality metrics

#### llm_literature_analysis

- **XML Document Parsing**: Processes academic literature XML files in various formats

- **Semantic Content Understanding**: Uses large language models to understand literature content structure

#### prompts_for_content_extraction

- **MARVEL-Compatible Prompt Templates**: Specially designed data extraction prompts
- **Molecule-Specific Versions**: Templates optimized for different molecular types
- **Quality Control Instructions**: Ensures accuracy and completeness of extracted data

## Result Format Description

### Retrieval Results (retrieval_results/)

- Results of Filtered Papers (Sample of a paper)

```json
{
    "title": "Improved line list of 12CH4 in the 8850–9180 cm−1 region",
    "authors": [
      "A.V. Nikitin",
      "A.E. Protasevich",
      "M. Rey",
      "......"
    ],
    "year": 2019,
    "venue": "Journal of Quantitative Spectroscopy and Radiative Transfer",
    "doi": "10.1016/j.jqsrt.2019.106646",
    "abstract": "",
    "publisher": "Elsevier BV",
    "citation_count": 15,
    "url": "https://doi.org/10.1016/j.jqsrt.2019.106646",
    "type": "journal-article",
    "page": "106646",
    "volume": "239",
    "issue": "",
    "source": "crossref",
    "llm_analysis": {
      "relevance_score": 1.0,
      "reasoning": "The title explicitly states......",
      "is_relevant": true,
      "analysis_type": "title",
      "llm_service": "gemini"
    }
},
```

- BiBTeX Results (Sample of a paper)

```BiBTeX
@article{19NiPrRe,
  title = {{Improved line list of 12CH4 in the 8850–9180 cm−1 region}},
  author = {Nikitin, A.V. and Protasevich, A.E. and Rey, M. and Serdyukov, V.I. and Sinitsa, L.N. and Lugovskoy, A. and Tyuterev, V.I.G.},
  year = {2019},
  journal = {Journal of Quantitative Spectroscopy and Radiative Transfer},
  doi = {10.1016/j.jqsrt.2019.106646},
  publisher = {Elsevier BV},
  volume = {239},
  pages = {106646}
}
```

- CSV Results (Sample)

| title                                                    | doi                         |
| -------------------------------------------------------- | --------------------------- |
| Improved line list of 12CH4 in the 8850–9180 cm−1 region | 10.1016/j.jqsrt.2019.106646 |
| Improved line list of 12CH4 in the 3760–4100 cm−1 region | 10.1016/j.jqsrt.2018.12.034 |

### Analysis Results (analysis_results/)

- Analysis Summary (Sample of a paper)

```json
{
      "file_path": "..\\article_xmls\\Test_files_T\\10.1016_j.jqsrt.2019.106646.xml",
      "llm_analysis": {
        "success": true,
        "analysis": {
          "marvel_relevance": {
            "is_relevant": true,
            "explanation": "The paper reports ......"
          },
          "experimental_data": {
            "has_data": true,
            "data_format": "The paper explicitly states that ......",
            "need_pdf": true,
            "has_uncertainty": true,
            "uncertainty_description": "The paper indicates ......",
            "uncertainty_value": "not available",
            "table_info": {
              "table_title": [
                "Table 3: ......"
              ],
              "description": "This table ......"
            },
            "has_supplementary_data": true
          },
          "summary": {
            "Evaluation": "This paper......"
          }
        },
        "model": "gemini-2.5-flash"
      }
    },
```

### MARVEL-Compatible TSV Format

```bash
# General Template Output Format:
WaveNumber_cm-1    Uncertainty    Upper_State    Lower_State    Source_tag.rownumber
8736.2987          0.005	      (6,5,A2,239)	 (0,6,A1,1)	    19NiPrRe.1


# CH₄-Specific Template Output Format (for comparison):
WaveNumber_cm-1    Uncertainty    Upper_P  Upper_J  Upper_C  Upper_α  Lower_P  Lower_J  Lower_C  Lower_α  Source_tag.rownumber
8736.2987	       0.005	      6	       5	    A2	     239      0 	   6	    A1	     1	      19NiPrRe.1

```

## ⚙️ Customization Configuration

### Adjusting LLM Model Parameters

```python
# config/settings.py
GROQ_MODEL = "gemma2-9b-it"     # Select different models
GEMINI_MODEL = "gemini-2.5-flash"  # Adjust model version
```

### Adjusting Prompts for Keywords Generation

1. Users who want to adjust the prompts used for keyword generation need to access
   `llm_literature_search/src/core/keyword_extractor.py` and edit the following section

```python
user_prompt = f"Extract academic search keywords from this description:\n\nI am looking for research papers that provide high-quality experimental spectroscopic data suitable for input into the MARVEL......"
```

2. Users who want to adjust the prompts used for paper filtering need to access
   `llm_literature_search/src/core/paper_filter.py` and edit the following section

```python
system_prompt = f"""You are an expert academic literature reviewer. Analyze if research papers are......
```

3. Users who want to adjust the prompts used for in-depth analysis need to access `llm_literature_analysis/src/core/llm_client.py`

```python
user_prompt = f"""MARVEL is an algorithm that reconstructs molecular energy level structures......
```

## Important Notes

### Runtime Environment

- **Network Connection**: Requires stable internet connection to access LLM API services
- **API Limitations**: Pay attention to call frequency and quota limits for each API service
- **Elsevier Access**: Ensure that your network has permission to access Elsevier content.

### Data Sources and Copyright

- **Literature Data**: Ensure compliance with usage terms and copyright regulations of various data
- **Citation Standards**: Please cite original literature appropriately when using extracted data

### Result Verification

- **Auto-generated Content**: Contents in `retrieval_results/` and `analysis results/` are automatically generated by the system
- **Manual Review**: Recommend manual verification of critical data, especially data for scientific publication

### Troubleshooting Common Issues

1. **API Key Errors**

   ```bash
   Error: Gemini API key not found!
   # Solution: Check API key configuration in config/settings.py
   ```

2. **Network Connection Issues**

   ```bash
   ConnectionError: Failed to connect to API endpoint
   # Solution: Check network connection, consider using proxy or VPN
   ```

3. **File Path Issues**

   ```bash
   FileNotFoundError: XML file not found
   # Solution: Ensure there are processable files in article_xmls/ directory
   ```

## Contributing

Community contributions are welcomed! If you want to contribute code or improve the system:

1. Fork this repository
2. Create a feature branch (`git checkout -b Feature/feature`)
3. Commit your changes (`git commit -m 'Add some Feature'`)
4. Push to the branch (`git push origin Feature/feature`)
5. Open a Pull Request

### Contribution Areas

- New molecular type prompt templates
- Additional literature database interfaces
- Data quality assessment algorithm improvements
- User interface optimization

## Contact

- **Project Maintainer**: Songzx07
- **GitHub**: [LLM_MARVEL_Mining](https://github.com/Songzx07/LLM_MARVEL)
- **Issue Reports**: [GitHub Issues](https://github.com/Songzx07/LLM_MARVEL/issues)

---

_Last updated: August 20, 2025_
