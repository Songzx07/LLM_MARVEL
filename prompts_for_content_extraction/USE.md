# MARVEL-Specific Data Extraction

### Overall Features

- **Flexible quantum number extraction**: Adapts to various molecular while maintaining MARVEL compatibility
- **TSV format compliance**: Generates data tables that can integrate with MARVEL workflow

### Spectroscopy Domain Intelligence

- **Experimental validation**: Excludes purely theoretical calculations and unassigned line lists
- **Multi-molecule support**: General templates work across molecular types
- **Quality control**: Removes duplicate transitions and ensures quantum number completeness
- **Uncertainty handling**: Distinguishes between per-line uncertainties and global instrumental resolution values

## Overview

This project provides specialized prompt templates used in **LLMs** for extracting molecular spectroscopy data from scientific literature used for the **MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm**. These prompts are designed to convert published experimental transition data into MARVEL-compatible TSV format, enabling systematic curation of high-resolution molecular spectroscopy databases.

## Technical Requirements

### Platform Specifications

- **Recommended Platform**: Google AI Studio
- **Model Requirements**: Gemini 2.5-Pro or Gemini 2.5Flash
- **Sampling Parameter Configuration**: Temperature == 0.5, Top-p == 0.95, Think Mode On

### Input Data Preparation

- **Primary Sources**: Scientific papers in PDF format
- **Supplementary Files**: Data in txt, word, csv, etc.
- **File Organization**: Papers should be pre-filtered for MARVEL relevance

### Important Limitations

- **Manual File Handling**: Users must download and upload literature files individually
- **Template Customization Required**: Prompts need modification for specific molecular species and quantum number schemes
- **No Automation**: This system provides prompts only—no automated processing pipeline included
- **Result Accuracy**: For long data tables, the output results may have missing lines or even mistakes. In that case, Manual check is susggested.

## Use Steps

### 1. Fetch Pre-Screened Literature

Before using the prompts, ensure you aim to analyse papers filtered or pre-analysed by the system.

### 2. Choose the Appropriate Prompt Template

#### A. Primary Template: General MARVEL Extraction (General-Prompts)

This is the **main template** designed for broad applicability across different molecular species:

**For Known Relevant Papers** (`General_MARVEL_Extraction_Known_Data.txt`):

- **Purpose**: Extract transition data from papers confirmed to contain MARVEL-relevant data
- **Functionality**: Directly extracts wavenumbers, full quantum numbers, and uncertainties into TSV format
- **Output**: MARVEL-compatible TSV files with flexible quantum number columns

**For Unsure Relevance and Unknown Data Existence Papers** (`General_MARVEL_Extraction_Unknown_Data.txt`):

- **Purpose**: Screen literature for MARVEL relevance and extract data
- **Functionality**: Evaluates papers against MARVEL criteria, then extracts if relevant
- **Output**: Relevance assessment followed by conditional data extraction

#### B. Specialized Template: CH₄-Specific Templates (CH4-Prompts)

**Learning Resource for Molecule-Specific Customization**:

- **Purpose**: Enhanced prompts for CH4-specific analysis and extraction
- **Key Differences from General Templates**:  
  &nbsp;&nbsp;Details of needed quantum numbers:

  - Polyad P'
  - Total Angular momentum J'
  - Total Symmetry C'
  - Counting α'

- **Use as Reference**: Compare with general templates to understand customization approaches for other molecules

### 3. Google AI Studio Workflow

#### Project Setup:

1. **Create New Chat**: Go to Google AI Studio and select a model
2. **Upload Literature**: Attach PDF and any supplementary data files
3. **Insert Prompt**: Copy the appropriate general template (or customized version)
4. **Set Parameters**: Ensure sufficient token allocation for large datasets

#### Execution Strategy:

1. **Start with General Templates**: Begin with either Known or Unknown Data templates
2. **Single Paper Processing**: Upload one paper at a time for thorough analysis
3. **Quality Check**: Review extracted TSV format against original data tables
4. **Export Results**: Save TSV blocks as `.txt` files with MARVEL-compatible naming

#### Template Selection Decision Tree:

- **Literature Relevance Analysis Needed?** → Use `General_MARVEL_Extraction_Unknown_Data.txt`
- **Confirmed MARVEL Data?** → Use `General_MARVEL_Extraction_Known_Data.txt`
- **Need Molecule-Specific Details?** → Customize general template using CH₄ example

## Troubleshooting Guide

### Prompt Performance Issues

#### If Low Extraction Success Rate:

- **More Runs**: Run for more times if the selected LLM delays in giving results
- **Check Paper Quality**: Ensure papers contain tabulated transition data
- **Verify Token Limits**: Large papers may exceed context windows
- **Simplify Instructions**: Remove unnecessary complexity for straightforward extractions

#### If Incorrect Quantum Number Mapping:

- **Review Molecular Notation**: Different papers may use varying quantum number conventions
- **Update Prompt Templates**: Modify for specific molecular symmetry requirements
- **Cross-Validate Results**: Compare extracted assignments with original tables

### Data Format Validation

#### TSV Structure Check:

```bash
# General Template Output Format:
WaveNumber_cm-1    Uncertainty    Upper_State    Lower_State    Source_tag.rownumber
1234.5678          0.002          (1,2,F2,1)     (0,1,A1,1)     21SmJoAn.001

# CH₄-Specific Template Output Format (for comparison):
WaveNumber_cm-1    Uncertainty    Upper_P  Upper_J  Upper_C  Upper_α  Lower_P  Lower_J  Lower_C  Lower_α  Source_tag.rownumber
1234.5678          0.002          1        2        F2       1        0        1        A1       1        21SmJoAn.001
```

---

**Last Updated**: August 2025  
**Technical Support**: Submit issues via GitHub for prompt optimization and troubleshooting
