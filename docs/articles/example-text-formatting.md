# Advanced Text Formatting


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

!!! tip

    To run the code from this article as a Python script:

    ```bash
    python3 examples/example-text-formatting.py
    ```

This article demonstrates advanced text formatting capabilities in
rtflite, including fonts, colors, alignment, indentation, and special
formatting for clinical documentation.

## Overview

Advanced text formatting is essential for creating professional-quality
clinical documents that meet regulatory standards. Key formatting
features include:

- Multiple font families, sizes, and styles
- Text colors and background colors
- Justification and alignment options
- Indentation and spacing control
- Special symbols and characters
- Mathematical expressions and subscripts/superscripts

## Imports

``` python
import pandas as pd
import numpy as np
import rtflite as rtf
```

## Create Sample Clinical Data

Generate data to demonstrate various formatting scenarios:

``` python
# Laboratory data with special formatting needs
lab_data = [
    ["Hemoglobin", "12.5", "11.0-15.0", "g/dL", "Normal"],
    ["Platelet Count", "150", "150-400", "×10³/μL", "Low Normal"],
    ["ALT", "45", "≤40", "U/L", "Elevated"],
    ["Creatinine", "1.2", "0.6-1.2", "mg/dL", "High Normal"],
    ["eGFR", "≥60", "≥60", "mL/min/1.73m²", "Normal"],
    ["HbA₁c", "7.2", "<7.0", "%", "Above Target"],
    ["Glucose", "140", "70-100", "mg/dL", "Elevated"],
    ["Total Cholesterol", "220", "<200", "mg/dL", "Elevated"]
]

df_labs = pd.DataFrame(lab_data, 
    columns=["Parameter", "Value", "Reference Range", "Unit", "Interpretation"])

print("Laboratory data created:")
print(df_labs)
```

    Laboratory data created:
                Parameter Value Reference Range         Unit  Interpretation
    0          Hemoglobin  12.5        11.0-15.0        g/dL          Normal
    1      Platelet Count   150         150-400     ×10³/μL     Low Normal
    2                 ALT    45            ≤40         U/L        Elevated
    3          Creatinine   1.2         0.6-1.2       mg/dL     High Normal
    4                eGFR   ≥60             ≥60  mL/min/1.73m²          Normal
    5               HbA₁c   7.2            <7.0           %   Above Target
    6             Glucose   140          70-100       mg/dL        Elevated
    7   Total Cholesterol   220            <200       mg/dL        Elevated

## Basic Text Formatting Table

Demonstrate font families, sizes, and styles:

``` python
# Create formatting demonstration data
format_demo = [
    ["Times New Roman", "Default font", "Standard body text"],
    ["Arial", "Sans-serif font", "Headers and emphasis"],
    ["Courier New", "Monospace font", "Code and data"],
    ["Calibri", "Modern font", "Contemporary documents"],
    ["Symbol", "Mathematical symbols", "α β γ δ ε ζ η θ"]
]

df_fonts = pd.DataFrame(format_demo, 
    columns=["Font Family", "Description", "Usage Example"])

# Create RTF with multiple font formatting
doc_fonts = rtf.RTFDocument(
    df=df_fonts,
    rtf_page=rtf.RTFPage(
        orientation="landscape",
        nrow=40
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Font Family Demonstration",
            "Various Typefaces and Applications"
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.5, 2.5, 3.0],
        text_justification=["l", "l", "l"],
        # Different fonts for each column
        text_font=[
            ["Times New Roman", "Times New Roman", "Times New Roman"],
            ["Arial", "Arial", "Arial"],
            ["Courier New", "Courier New", "Courier New"],
            ["Calibri", "Calibri", "Calibri"],
            ["Symbol", "Symbol", "Symbol"]
        ],
        # Different sizes
        text_font_size=[
            [12, 12, 12],
            [11, 11, 11],
            [10, 10, 10],
            [12, 12, 12],
            [14, 14, 14]
        ],
        # Different styles
        text_format=[
            ["", "", ""],
            ["b", "", ""],  # Bold
            ["", "i", ""],  # Italic
            ["", "", "u"],  # Underline
            ["b", "b", "b"]  # Bold for symbols
        ],
        border_left=["single"] + [""] * 2,
        border_right=[""] * 2 + ["single"]
    )
)

doc_fonts.write_rtf("text_formatting_fonts.rtf")
print("Created text_formatting_fonts.rtf")
```

    Created text_formatting_fonts.rtf

## Color and Background Formatting

Demonstrate text and background colors:

``` python
# Create color demonstration data
color_demo = [
    ["Normal", "Within reference range", "Continue monitoring"],
    ["Caution", "Borderline values", "Recheck in 3 months"],
    ["Alert", "Outside normal range", "Clinical follow-up needed"],
    ["Critical", "Immediate attention", "Contact physician STAT"],
    ["Info", "Additional context", "See notes below"]
]

df_colors = pd.DataFrame(color_demo, 
    columns=["Status", "Clinical Meaning", "Action Required"])

# Create RTF with color formatting
doc_colors = rtf.RTFDocument(
    df=df_colors,
    rtf_page=rtf.RTFPage(
        orientation="portrait",
        nrow=40
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Clinical Status Color Coding",
            "Visual Indicators for Laboratory Results"
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 3.0, 3.0],
        text_justification=["c", "l", "l"],
        # Text colors by row
        text_color=[
            ["black", "black", "black"],        # Normal - black
            ["orange", "orange", "orange"],     # Caution - orange  
            ["red", "red", "red"],              # Alert - red
            ["darkred", "darkred", "darkred"],  # Critical - dark red
            ["blue", "blue", "blue"]            # Info - blue
        ],
        # Background colors by row
        text_background_color=[
            ["lightgreen", "lightgreen", "lightgreen"],  # Normal - light green
            ["lightyellow", "lightyellow", "lightyellow"], # Caution - light yellow
            ["lightpink", "lightpink", "lightpink"],     # Alert - light pink
            ["pink", "pink", "pink"],                    # Critical - pink
            ["lightblue", "lightblue", "lightblue"]     # Info - light blue
        ],
        # Bold status column
        text_format=[
            ["b", "", ""],
            ["b", "", ""],
            ["b", "", ""],
            ["b", "", ""],
            ["b", "", ""]
        ],
        border_left=["single"] + [""] * 2,
        border_right=[""] * 2 + ["single"]
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Color coding should be used consistently across all laboratory reports. " +
             "Ensure accessibility by not relying solely on color for critical information."
    )
)

doc_colors.write_rtf("text_formatting_colors.rtf")
print("Created text_formatting_colors.rtf")
```

    Created text_formatting_colors.rtf

## Alignment and Indentation

Demonstrate text alignment and indentation options:

``` python
# Create alignment demonstration data
align_demo = [
    ["Primary Endpoint:", "", "Change from baseline at Week 24"],
    ["  • Primary Analysis", "ANCOVA", "Significant improvement (p<0.001)"],
    ["  • Sensitivity Analysis", "MMRM", "Consistent results"],
    ["Secondary Endpoints:", "", ""],
    ["  1. Response Rate", "Binary", "67.3% vs 45.2% (Drug vs Placebo)"],
    ["  2. Time to Response", "Survival", "Hazard Ratio: 1.85 (95% CI: 1.2-2.8)"],
    ["  3. Quality of Life", "ANCOVA", "Clinically meaningful improvement"],
    ["Safety Endpoints:", "", ""],
    ["  → Overall TEAE Rate", "Descriptive", "Similar across groups"],
    ["  → Serious AEs", "Descriptive", "No drug-related SAEs"],
    ["  → Discontinuations", "Descriptive", "Low rate (<5%)"]
]

df_align = pd.DataFrame(align_demo, 
    columns=["Endpoint", "Analysis Method", "Result Summary"])

# Create RTF with alignment and indentation
doc_align = rtf.RTFDocument(
    df=df_align,
    rtf_page=rtf.RTFPage(
        orientation="landscape",
        nrow=40
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Clinical Trial Endpoints Summary",
            "Hierarchical Display with Indentation"
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3.5, 2.0, 4.0],
        text_justification=["l", "c", "l"],
        # Different indentation levels
        text_indent_first=[
            [0, 0, 0],      # Primary header - no indent
            [200, 0, 0],    # Bullet - 200 twips indent
            [200, 0, 0],    # Bullet - 200 twips indent  
            [0, 0, 0],      # Secondary header - no indent
            [200, 0, 0],    # Numbered - 200 twips indent
            [200, 0, 0],    # Numbered - 200 twips indent
            [200, 0, 0],    # Numbered - 200 twips indent
            [0, 0, 0],      # Safety header - no indent
            [200, 0, 0],    # Arrow - 200 twips indent
            [200, 0, 0],    # Arrow - 200 twips indent
            [200, 0, 0]     # Arrow - 200 twips indent
        ],
        # Bold headers, normal sub-items
        text_format=[
            ["b", "b", "b"],  # Primary header
            ["", "", ""],     # Sub-item
            ["", "", ""],     # Sub-item
            ["b", "b", "b"],  # Secondary header
            ["", "", ""],     # Sub-item
            ["", "", ""],     # Sub-item
            ["", "", ""],     # Sub-item
            ["b", "b", "b"],  # Safety header
            ["", "", ""],     # Sub-item
            ["", "", ""],     # Sub-item
            ["", "", ""]      # Sub-item
        ],
        # Different colors for sections
        text_color=[
            ["darkblue", "darkblue", "darkblue"],  # Primary
            ["black", "black", "black"],
            ["black", "black", "black"],
            ["darkgreen", "darkgreen", "darkgreen"], # Secondary
            ["black", "black", "black"],
            ["black", "black", "black"],
            ["black", "black", "black"],
            ["darkred", "darkred", "darkred"],     # Safety
            ["black", "black", "black"],
            ["black", "black", "black"],
            ["black", "black", "black"]
        ],
        border_left=["single"] + [""] * 2,
        border_right=[""] * 2 + ["single"]
    )
)

doc_align.write_rtf("text_formatting_alignment.rtf")
print("Created text_formatting_alignment.rtf")
```

    Created text_formatting_alignment.rtf

## Special Characters and Symbols

Demonstrate mathematical and clinical symbols:

``` python
# Create special characters demonstration
symbols_demo = [
    ["Mathematical", "±2.5", "Plus/minus for confidence intervals"],
    ["Inequality", "≤5% or ≥95%", "Less than or equal, greater than or equal"],
    ["Greek Letters", "α=0.05, β-blocker", "Statistical significance, medication types"],
    ["Subscripts", "HbA₁c, CO₂", "Chemical formulas and medical abbreviations"],
    ["Superscripts", "10³ cells/μL", "Scientific notation and units"],
    ["Arrows", "↑ increased, ↓ decreased", "Direction of change"],
    ["Bullets", "• Primary endpoint", "List formatting"],
    ["Clinical", "♂ male, ♀ female", "Gender symbols"],
    ["Statistics", "χ² test, p-value", "Statistical test notation"],
    ["Units", "m², mg/dL, μg/mL", "Medical and scientific units"]
]

df_symbols = pd.DataFrame(symbols_demo, 
    columns=["Category", "Examples", "Clinical Usage"])

# Create RTF with special characters
doc_symbols = rtf.RTFDocument(
    df=df_symbols,
    rtf_page=rtf.RTFPage(
        orientation="landscape",
        nrow=40
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Special Characters and Symbols Reference",
            "Mathematical and Clinical Notation in RTF Documents"
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 2.5, 4.0],
        text_justification=["l", "c", "l"],
        # Make examples column larger font
        text_font_size=[
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11],
            [11, 12, 11]
        ],
        # Bold category and examples
        text_format=[
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""],
            ["b", "b", ""]
        ],
        # Alternate row colors
        text_background_color=[
            ["white", "white", "white"],
            ["lightgray", "lightgray", "lightgray"],
            ["white", "white", "white"],
            ["lightgray", "lightgray", "lightgray"],
            ["white", "white", "white"],
            ["lightgray", "lightgray", "lightgray"],
            ["white", "white", "white"],
            ["lightgray", "lightgray", "lightgray"],
            ["white", "white", "white"],
            ["lightgray", "lightgray", "lightgray"]
        ],
        border_left=["single"] + [""] * 2,
        border_right=[""] * 2 + ["single"],
        border_top=["single"] * 3,
        border_bottom=["single"] * 3
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Special characters should render consistently across RTF viewers.",
            "For complex mathematical expressions, consider using equation editors.",
            "Greek letters: Use Symbol font or Unicode for proper display."
        ]
    )
)

doc_symbols.write_rtf("text_formatting_symbols.rtf")
print("Created text_formatting_symbols.rtf")
```

    Created text_formatting_symbols.rtf

## Complex Laboratory Report

Create a comprehensive example combining all formatting features:

``` python
# Enhanced laboratory data with formatting indicators
lab_enhanced = [
    ["Complete Blood Count", "", "", "", ""],
    ["  Hemoglobin", "12.5", "11.0-15.0", "g/dL", "Normal"],
    ["  Hematocrit", "37.8", "33.0-45.0", "%", "Normal"],
    ["  Platelet Count", "145", "150-400", "×10³/μL", "Low↓"],
    ["  White Blood Cell Count", "6.8", "4.0-10.0", "×10³/μL", "Normal"],
    ["", "", "", "", ""],
    ["Comprehensive Metabolic Panel", "", "", "", ""],
    ["  Glucose (Fasting)", "140", "70-100", "mg/dL", "Elevated↑"],
    ["  Creatinine", "1.2", "0.6-1.2", "mg/dL", "High Normal"],
    ["  eGFR", "≥60", "≥60", "mL/min/1.73m²", "Normal"],
    ["  ALT", "45", "≤40", "U/L", "Elevated↑"],
    ["  Total Bilirubin", "0.8", "0.2-1.2", "mg/dL", "Normal"],
    ["", "", "", "", ""],
    ["Lipid Panel", "", "", "", ""],
    ["  Total Cholesterol", "220", "<200", "mg/dL", "Elevated↑"],
    ["  LDL Cholesterol", "140", "<100", "mg/dL", "Elevated↑"],
    ["  HDL Cholesterol", "35", "≥40", "mg/dL", "Low↓"],
    ["  Triglycerides", "180", "<150", "mg/dL", "Elevated↑"],
    ["", "", "", "", ""],
    ["Diabetes Monitoring", "", "", "", ""],
    ["  HbA₁c", "7.2", "<7.0", "%", "Above Target↑"],
    ["  Microalbumin", "45", "<30", "mg/g creatinine", "Elevated↑"]
]

df_lab_enhanced = pd.DataFrame(lab_enhanced,
    columns=["Test", "Result", "Reference Range", "Units", "Status"])

# Create comprehensive laboratory report
doc_lab = rtf.RTFDocument(
    df=df_lab_enhanced,
    rtf_page=rtf.RTFPage(
        orientation="portrait",
        nrow=50
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Comprehensive Laboratory Report",
            "Patient: Smith, John (DOB: 15-Jan-1970, MRN: 123456)",
            "Date Collected: " + pd.Timestamp.now().strftime("%d-%b-%Y") + " | Lab Report #: LAB-2024-001"
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3.5, 1.5, 2.0, 2.0, 2.0],
        text_justification=["l", "c", "c", "l", "l"],
        # Conditional formatting based on content
        text_format=[
            ["b", "b", "b", "b", "b"],  # Section headers
            ["", "", "", "", ""],       # Normal values
            ["", "", "", "", ""],
            ["", "", "", "", "b"],      # Low value - bold status
            ["", "", "", "", ""],
            ["", "", "", "", ""],       # Blank row
            ["b", "b", "b", "b", "b"],  # Section header
            ["", "", "", "", "b"],      # Elevated - bold status
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", "b"],      # Elevated - bold status
            ["", "", "", "", ""],
            ["", "", "", "", ""],       # Blank row
            ["b", "b", "b", "b", "b"],  # Section header
            ["", "", "", "", "b"],      # Elevated - bold status
            ["", "", "", "", "b"],      # Elevated - bold status
            ["", "", "", "", "b"],      # Low - bold status
            ["", "", "", "", "b"],      # Elevated - bold status
            ["", "", "", "", ""],       # Blank row
            ["b", "b", "b", "b", "b"],  # Section header
            ["", "", "", "", "b"],      # Above target - bold status
            ["", "", "", "", "b"]       # Elevated - bold status
        ],
        # Color coding for abnormal values
        text_color=[
            ["darkblue"] * 5,    # Section header
            ["black"] * 5,       # Normal
            ["black"] * 5,       # Normal
            ["red"] * 5,         # Low (red)
            ["black"] * 5,       # Normal
            ["black"] * 5,       # Blank
            ["darkblue"] * 5,    # Section header
            ["red"] * 5,         # Elevated (red)
            ["black"] * 5,       # Normal
            ["black"] * 5,       # Normal
            ["red"] * 5,         # Elevated (red)
            ["black"] * 5,       # Normal
            ["black"] * 5,       # Blank
            ["darkblue"] * 5,    # Section header
            ["red"] * 5,         # Elevated (red)
            ["red"] * 5,         # Elevated (red)
            ["red"] * 5,         # Low (red)
            ["red"] * 5,         # Elevated (red)
            ["black"] * 5,       # Blank
            ["darkblue"] * 5,    # Section header
            ["red"] * 5,         # Above target (red)
            ["red"] * 5          # Elevated (red)
        ],
        # Indentation for test names under sections
        text_indent_first=[
            [0] + [0] * 4,       # Section header
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [0] * 5,             # Blank
            [0] + [0] * 4,       # Section header
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [0] * 5,             # Blank
            [0] + [0] * 4,       # Section header
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4,     # Indented test
            [0] * 5,             # Blank
            [0] + [0] * 4,       # Section header
            [300] + [0] * 4,     # Indented test
            [300] + [0] * 4      # Indented test
        ],
        border_left=["single"] + [""] * 4,
        border_right=[""] * 4 + ["single"]
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Reference ranges are for adult populations and may vary by laboratory.",
            "↑ = Above normal range, ↓ = Below normal range",
            "Critical values requiring immediate attention are highlighted in red.",
            "This report should be interpreted by a qualified healthcare provider."
        ]
    ),
    rtf_source=rtf.RTFSource(
        text="Generated by: Clinical Laboratory Information System v2.1 | " +
             "Reviewed by: Dr. Jane Wilson, MD | Report Date: " + 
             pd.Timestamp.now().strftime("%d-%b-%Y %H:%M")
    )
)

doc_lab.write_rtf("text_formatting_clinical.rtf")
print("Created text_formatting_clinical.rtf")
```

    Created text_formatting_clinical.rtf

## Convert to PDF

``` python
# Convert all RTF files to PDF
try:
    converter = rtf.LibreOfficeConverter()
    
    files_to_convert = [
        "text_formatting_fonts.rtf",
        "text_formatting_colors.rtf", 
        "text_formatting_alignment.rtf",
        "text_formatting_symbols.rtf",
        "text_formatting_clinical.rtf"
    ]
    
    for file in files_to_convert:
        converter.convert(
            input_files=file,
            output_dir=".",
            format="pdf",
            overwrite=True
        )
        print(f"✓ Converted {file} to PDF")
    
    print("\nPDF conversion completed successfully!")
    
except FileNotFoundError as e:
    print(f"Note: {e}")
    print("\nTo enable PDF conversion, install LibreOffice:")
    print("- macOS: brew install --cask libreoffice")
    print("- Ubuntu/Debian: sudo apt-get install libreoffice")
    print("- Windows: Download from https://www.libreoffice.org/")
    print("\nRTF files have been successfully created and can be opened in any RTF-compatible application.")
```

    ✓ Converted text_formatting_fonts.rtf to PDF
    ✓ Converted text_formatting_colors.rtf to PDF
    ✓ Converted text_formatting_alignment.rtf to PDF
    ✓ Converted text_formatting_symbols.rtf to PDF
    ✓ Converted text_formatting_clinical.rtf to PDF

    PDF conversion completed successfully!

## Key Features Demonstrated

### 1. Font Control

- Multiple font families (Times New Roman, Arial, Courier New, Calibri,
  Symbol)
- Variable font sizes within tables
- Font style combinations (bold, italic, underline)
- Monospace fonts for code and data alignment

### 2. Color Management

- Text color specification by cell or row
- Background color highlighting
- Color-coded status indicators
- Professional color schemes for clinical documentation

### 3. Text Alignment and Spacing

- Left, center, and right justification
- First-line indentation for hierarchical display
- Custom spacing for structured documents
- Multi-level indentation patterns

### 4. Special Characters

- Mathematical symbols (±, ≤, ≥, α, β, χ²)
- Clinical notation (♂, ♀, ↑, ↓)
- Scientific units (m², μL, subscripts, superscripts)
- Unicode character support

### 5. Clinical Document Standards

- Hierarchical section organization
- Color-coded abnormal values
- Professional header and footer information
- Consistent formatting throughout document

## Best Practices for Text Formatting

1.  **Consistency**:
    - Use the same fonts throughout related documents
    - Maintain consistent color schemes
    - Apply formatting rules uniformly
2.  **Readability**:
    - Choose appropriate font sizes (11-12pt for body text)
    - Use sufficient contrast between text and background
    - Avoid overuse of formatting styles
3.  **Accessibility**:
    - Don’t rely solely on color for critical information
    - Use bold or italics to reinforce color coding
    - Provide clear legends for symbols and colors
4.  **Clinical Standards**:
    - Follow institutional formatting guidelines
    - Use standard medical abbreviations and symbols
    - Include appropriate disclaimers and interpretive notes
5.  **Technical Considerations**:
    - Test formatting across different RTF viewers
    - Use Unicode for special characters when possible
    - Consider font availability on target systems

This example demonstrates the comprehensive text formatting capabilities
of rtflite for creating professional clinical and scientific documents
that meet industry standards for presentation and accessibility.
