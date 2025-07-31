# Advanced Page Element Control


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

!!! tip

    To run the code from this article as a Python script:

    ```bash
    python3 examples/example-pagination-advanced.py
    ```

This article demonstrates rtflite’s advanced page element control
features, allowing precise control over where titles, footnotes, and
other elements appear across multi-page documents. This functionality is
essential for regulatory compliance and professional clinical document
formatting.

## Overview

Advanced page element control enables:

- **Selective element positioning**: Show titles only on first page,
  footnotes only on last page
- **Page-specific content**: Different headers for first
  vs. continuation pages
- **Regulatory compliance**: “Continued” indicators, confidentiality
  footers, page numbering
- **Professional formatting**: Optimize space usage while maintaining
  readability

This is particularly important for: - Regulatory submission documents
with specific formatting requirements - Long tables that need
continuation indicators - Clinical study reports with confidentiality
requirements - Multi-page efficacy and safety summaries

## Imports

``` python
import pandas as pd
import numpy as np
from datetime import datetime
import rtflite as rtf
```

## Create Complex Clinical Dataset

Generate comprehensive clinical data to demonstrate advanced pagination:

``` python
# Create sample efficacy data across multiple timepoints
np.random.seed(456)

# Define study parameters
timepoints = ['Baseline', 'Week 4', 'Week 8', 'Week 12', 'Week 16', 'Week 20', 'Week 24']
treatments = ['Placebo', 'Drug 2.5mg', 'Drug 5mg', 'Drug 10mg']
efficacy_measures = [
    'Primary Efficacy Score',
    'Secondary Score A', 
    'Secondary Score B',
    'Quality of Life Index',
    'Global Assessment'
]

# Generate efficacy data
efficacy_data = []
for measure in efficacy_measures:
    for timepoint in timepoints:
        for treatment in treatments:
            # Generate realistic efficacy data
            if treatment == 'Placebo':
                mean_change = np.random.normal(0, 5)  # Minimal improvement
                n_subjects = np.random.randint(95, 105)
            else:
                # Dose-response relationship
                dose_effect = {'Drug 2.5mg': 5, 'Drug 5mg': 10, 'Drug 10mg': 15}[treatment]
                mean_change = np.random.normal(dose_effect, 6)
                n_subjects = np.random.randint(92, 108)
            
            std_dev = np.random.uniform(8, 15)
            se = std_dev / np.sqrt(n_subjects)
            
            efficacy_data.append({
                'Efficacy_Measure': measure,
                'Timepoint': timepoint,
                'Treatment': treatment,
                'N': n_subjects,
                'Mean_Change': round(mean_change, 2),
                'Std_Dev': round(std_dev, 2),
                'SE': round(se, 2),
                'CI_Lower': round(mean_change - 1.96*se, 2),
                'CI_Upper': round(mean_change + 1.96*se, 2)
            })

df_efficacy = pd.DataFrame(efficacy_data)
print(f"Generated {len(df_efficacy)} efficacy records")
print("\nSample data:")
print(df_efficacy.head())
```

    Generated 140 efficacy records

    Sample data:
          Efficacy_Measure Timepoint   Treatment    N  Mean_Change  Std_Dev    SE  CI_Lower  CI_Upper
    0  Primary Efficacy Score  Baseline     Placebo  102        -1.90    10.75  1.06     -3.98      0.18
    1  Primary Efficacy Score  Baseline  Drug 2.5mg  105         9.74     8.84  0.86      8.05     11.43
    2  Primary Efficacy Score  Baseline   Drug 5mg   95        15.45    11.28  1.16     13.18     17.72
    3  Primary Efficacy Score  Baseline  Drug 10mg  104        19.32    14.51  1.42     16.54     22.10
    4  Primary Efficacy Score    Week 4     Placebo   98         4.28     9.22  0.93      2.46      6.10

## Basic Page Element Control

Demonstrate basic element positioning:

``` python
# Create column headers for efficacy table
efficacy_headers = pd.DataFrame([
    ['Timepoint', 'Treatment', 'N', 'Mean Change', 'Std Dev', 'SE', '95% CI Lower', '95% CI Upper']
])

# Create document with basic page element control
doc_basic = rtf.RTFDocument(
    df=df_efficacy,
    rtf_page=rtf.RTFPage(
        nrow=25,  # Moderate page size
        orientation="landscape",
        # Page element location controls
        page_title_location="first",     # Title only on first page
        page_footnote_location="last",   # Footnote only on last page  
        page_source_location="last"      # Source only on last page
    ),
    rtf_page_header=rtf.RTFPageHeader(
        text="CONFIDENTIAL - Protocol ABC-123 - Efficacy Analysis"
    ),
    rtf_page_footer=rtf.RTFPageFooter(
        text="Page {PAGE} of {NUMPAGES} | Generated: " + datetime.now().strftime("%d-%b-%Y %H:%M")
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Primary and Secondary Efficacy Endpoints",
            "Mean Change from Baseline by Treatment Group",
            "Full Analysis Set - Study ABC-123"
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=efficacy_headers,
            col_rel_width=[1.5, 1.5, 0.8, 1.2, 1.0, 0.8, 1.2, 1.2],
            text_justification=["c"] * 8,
            text_format=["b"] * 8,
            text_background_color=["lightblue"] * 8,
            border_top=["single"] * 8,
            border_bottom=["single"] * 8
        )
    ],
    rtf_body=rtf.RTFBody(
        page_by=["Efficacy_Measure"],  # Group by efficacy measure
        new_page=False,  # Allow multiple measures per page
        pageby_header=True,
        col_rel_width=[1.5, 1.5, 0.8, 1.2, 1.0, 0.8, 1.2, 1.2],
        text_justification=["l", "l", "c", "c", "c", "c", "c", "c"],
        # Highlight measure headers
        text_format=["b", "", "", "", "", "", "", ""],
        text_background_color=["lightyellow", "white", "white", "white", "white", "white", "white", "white"],
        border_left=["single"] + [""] * 7,
        border_right=[""] * 7 + ["single"]
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="CI = Confidence Interval; SE = Standard Error. " +
             "Mean change calculated as endpoint value minus baseline value. " +
             "Positive values indicate improvement from baseline."
    ),
    rtf_source=rtf.RTFSource(
        text="Source: ADEFF Analysis Dataset v3.2 | Database Lock: 15-MAR-2024 09:00 UTC | " +
             "Analysis Plan: SAP-ABC-123 v2.1"
    )
)

doc_basic.write_rtf("efficacy_basic_pagination.rtf")
print("Created efficacy_basic_pagination.rtf with basic page element control")
```

    Created efficacy_basic_pagination.rtf with basic page element control

## Advanced Multi-Page Document with Continuation Indicators

Create a sophisticated document with continuation indicators:

``` python
# Create a comprehensive efficacy summary with different page elements
doc_advanced = rtf.RTFDocument(
    df=df_efficacy,
    rtf_page=rtf.RTFPage(
        nrow=20,  # Smaller pages to force more page breaks
        orientation="landscape",
        page_title_location="first",    # Full title only on first page
        page_footnote_location="all",   # Footnotes on all pages for important info
        page_source_location="last"     # Source only on last page
    ),
    rtf_page_header=rtf.RTFPageHeader(
        text="CONFIDENTIAL - Study ABC-123 - Primary Analysis | " + 
             "Continuation pages show abbreviated headers"
    ),
    rtf_page_footer=rtf.RTFPageFooter(
        text="Page {PAGE} of {NUMPAGES} | Protocol ABC-123 | CONFIDENTIAL"
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "COMPREHENSIVE EFFICACY ANALYSIS",
            "Primary and Secondary Endpoints - Mean Change from Baseline",
            "Full Analysis Set (N=400) - Intent-to-Treat Population",
            "Study ABC-123: Phase III Randomized Controlled Trial",
            "Data Cutoff: 15-MAR-2024"
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=pd.DataFrame([['Efficacy Measure', 'Timepoint', 'Treatment Group', 'N', 'Mean Δ', 'SD', 'SE', '95% CI']]),
            col_rel_width=[2.0, 1.2, 1.5, 0.8, 1.0, 0.8, 0.8, 1.4],
            text_justification=["c"] * 8,
            text_format=["b"] * 8,
            text_font_size=[9] * 8,  # Smaller font for headers
            text_background_color=["darkblue"] * 8,
            text_color=["white"] * 8,
            border_top=["single"] * 8,
            border_bottom=["single"] * 8,
            border_left=["single"] + [""] * 7,
            border_right=[""] * 7 + ["single"]
        )
    ],
    rtf_body=rtf.RTFBody(
        page_by=["Efficacy_Measure"],
        new_page=True,  # Force new page for each efficacy measure
        pageby_header=True,
        col_rel_width=[2.0, 1.2, 1.5, 0.8, 1.0, 0.8, 0.8, 1.4],
        text_justification=["l", "c", "l", "c", "c", "c", "c", "c"],
        text_font_size=[9] * 8,  # Consistent smaller font
        # Different formatting for measure headers vs data
        text_format=["b", "", "", "", "", "", "", ""],
        text_background_color=["lightcyan", "white"] * 4,
        border_left=["single"] + [""] * 7,
        border_right=[""] * 7 + ["single"],
        border_top=[""] * 8,
        border_bottom=["dotted"] * 8  # Subtle row separators
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Δ = Change from baseline; CI = Confidence Interval; SE = Standard Error; SD = Standard Deviation. " +
             "Analysis performed using ANCOVA with baseline value as covariate. " +
             "Missing data handled using Last Observation Carried Forward (LOCF). " +
             "Statistical significance tested at α=0.05 level."
    ),
    rtf_source=rtf.RTFSource(
        text="Data Source: Electronic Data Capture System | " +
             "Analysis Dataset: ADEFF v3.2 (15-MAR-2024) | " +
             "Analysis Software: SAS v9.4 | " +
             "Statistical Analysis Plan: SAP-ABC-123-v2.1 | " +
             "Quality Control: Double-programmed and verified"
    )
)

doc_advanced.write_rtf("efficacy_advanced_pagination.rtf")
print("Created efficacy_advanced_pagination.rtf with advanced page control")
```

    Created efficacy_advanced_pagination.rtf with advanced page control

## Regulatory Compliance Document

Create a document meeting strict regulatory requirements:

``` python
# Create subset of data for regulatory table
regulatory_data = df_efficacy[
    (df_efficacy['Efficacy_Measure'] == 'Primary Efficacy Score') & 
    (df_efficacy['Timepoint'].isin(['Baseline', 'Week 12', 'Week 24']))
].copy()

doc_regulatory = rtf.RTFDocument(
    df=regulatory_data,
    rtf_page=rtf.RTFPage(
        nrow=15,  # Conservative row limit for regulatory docs
        orientation="portrait",
        page_title_location="all",      # Title on all pages for regulatory
        page_footnote_location="all",   # Footnotes on all pages
        page_source_location="all"      # Source on all pages for traceability
    ),
    rtf_page_header=rtf.RTFPageHeader(
        text="CONFIDENTIAL AND PROPRIETARY | Study ABC-123 | For Regulatory Submission Only"
    ),
    rtf_page_footer=rtf.RTFPageFooter(
        text="Page {PAGE} of {NUMPAGES} | Sponsor: Example Pharma Inc. | " +
             "Submission: CTD Module 5.3.5.1 | Date: " + datetime.now().strftime("%d%b%Y").upper()
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Table 14.2.1.1: Primary Efficacy Endpoint Analysis",
            "Mean Change from Baseline in Primary Efficacy Score",
            "Full Analysis Set - Study ABC-123"
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=pd.DataFrame([['Visit', 'Treatment Group', 'N', 'Baseline Mean (SD)', 'Change from Baseline', '95% Confidence Interval']]),
            col_rel_width=[1.5, 2.0, 0.8, 1.8, 1.5, 2.0],
            text_justification=["c"] * 6,
            text_format=["b"] * 6,
            text_font_size=[10] * 6,
            border_top=["double"] * 6,   # Double border for regulatory
            border_bottom=["single"] * 6,
            border_left=["single"] + [""] * 5,
            border_right=[""] * 5 + ["single"]
        )
    ],
    rtf_body=rtf.RTFBody(
        col_rel_width=[1.5, 2.0, 0.8, 1.8, 1.5, 2.0],
        text_justification=["c", "l", "c", "c", "c", "c"],
        text_font_size=[10] * 6,  # Regulatory standard font size
        border_left=["single"] + [""] * 5,
        border_right=[""] * 5 + ["single"],
        border_bottom=[""] * 6,
        # Final border at end of table
        border_last=[["double"] * 6]
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Analysis performed on Full Analysis Set using ANCOVA with baseline score as covariate " +
             "and treatment as fixed effect. Missing values imputed using Last Observation Carried Forward. " +
             "Two-sided p-values <0.05 considered statistically significant. " +
             "CI calculated using least squares means and standard errors from ANCOVA model."
    ),
    rtf_source=rtf.RTFSource(
        text="Source: Table generated from ADEFF.XPT dataset (created 15MAR2024 09:15 UTC). " +
             "Program: t-14-2-1-1-primary-efficacy.sas (v1.2). " +
             "Output generated: " + datetime.now().strftime("%d%b%Y %H:%M UTC").upper() + ". " +
             "Reviewed by: [Reviewer Name] on [Date]."
    )
)

doc_regulatory.write_rtf("primary_efficacy_regulatory.rtf")
print("Created primary_efficacy_regulatory.rtf with regulatory compliance features")
```

    Created primary_efficacy_regulatory.rtf with regulatory compliance features

## Convert All Documents

``` python
# Convert all files to PDF
try:
    converter = rtf.LibreOfficeConverter()
    
    files_to_convert = [
        "efficacy_basic_pagination.rtf",
        "efficacy_advanced_pagination.rtf",
        "primary_efficacy_regulatory.rtf"
    ]
    
    print("Converting files to PDF...")
    for file in files_to_convert:
        converter.convert(
            input_files=file,
            output_dir=".",
            format="pdf",
            overwrite=True
        )
        print(f"✓ Converted {file} to PDF")
    
    print("\nAll PDF conversions completed successfully!")
    print("Documents are ready for regulatory review and submission.")
    
except FileNotFoundError as e:
    print(f"Note: {e}")
    print("\nTo enable PDF conversion, install LibreOffice:")
    print("- macOS: brew install --cask libreoffice")
    print("- Ubuntu/Debian: sudo apt-get install libreoffice")
    print("- Windows: Download from https://www.libreoffice.org/")
    print("\nRTF files have been successfully created:")
    print("- efficacy_basic_pagination.rtf (basic page element control)")
    print("- efficacy_advanced_pagination.rtf (advanced multi-page features)")
    print("- primary_efficacy_regulatory.rtf (regulatory compliance format)")
    print("\nThese files can be opened in any RTF-compatible application.")
```

    Converting files to PDF...
    ✓ Converted efficacy_basic_pagination.rtf to PDF
    ✓ Converted efficacy_advanced_pagination.rtf to PDF
    ✓ Converted primary_efficacy_regulatory.rtf to PDF

    All PDF conversions completed successfully!
    Documents are ready for regulatory review and submission.

## Key Advanced Features

### 1. Precise Element Positioning

- **`page_title_location`**: Control where titles appear (“first”,
  “last”, “all”)
- **`page_footnote_location`**: Control footnote placement
- **`page_source_location`**: Control source attribution placement
- Optimizes space while maintaining necessary information

### 2. Regulatory Compliance Features

- **Double borders** for formal regulatory tables
- **Comprehensive footnotes** with methodology details
- **Source traceability** with timestamps and version control
- **Page numbering** with study identifiers

### 3. Professional Page Headers/Footers

- **Confidentiality notices** on every page
- **Study identifiers** and protocol numbers
- **Generation timestamps** for audit trails
- **Page numbering** with total page counts

### 4. Performance Optimization

- **Efficient pagination** for large datasets
- **Optimized page sizes** based on content density
- **Multi-level grouping** without forced page breaks
- **Consistent formatting** across all pages

## Best Practices for Advanced Pagination

1.  **Regulatory Documents**:
    - Use `page_title_location="all"` for formal submission tables
    - Include comprehensive footnotes on all pages
    - Add source attribution with version control
    - Use double borders and formal formatting
2.  **Clinical Study Reports**:
    - Show titles only on first page to save space
    - Place detailed footnotes only on last page
    - Include confidentiality notices in headers
    - Add generation timestamps for reproducibility
3.  **Large Dataset Documents**:
    - Optimize page size (`nrow`) based on content complexity
    - Use landscape orientation for wide tables
    - Consider multi-level grouping without forced breaks
    - Implement consistent font sizing for readability
4.  **Quality Control**:
    - Test pagination with representative data sizes
    - Verify element positioning across all pages
    - Check formatting consistency after page breaks
    - Validate PDF conversion for final review

This advanced pagination control enables creation of sophisticated
clinical documents that meet the highest standards for regulatory
submission and professional presentation.
