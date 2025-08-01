import polars as pl
import rtflite as rtf

border_demo = [
    ["Border Type", "Description", "Usage", "Example"],
    ["Single", "Standard single line", "Table structure", "Default borders"],
    ["Double", "Double line border", "Headers, emphasis", "Section separators"],
    ["Thick", "Thick single line", "Outer boundaries", "Document frames"],
    ["None", "No border", "Clean appearance", "Seamless sections"],
    ["Mixed", "Combination styles", "Complex layouts", "Professional tables"],
]

df_borders = pl.DataFrame(
    border_demo, schema=["type", "description", "usage", "example"]
)

doc_borders = rtf.RTFDocument(
    df=df_borders,
    rtf_title=rtf.RTFTitle(
        text=["Border Formatting Examples", "RTF Border Style Demonstration"]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 2.5, 2.5, 2.5],
        text_justification=["l", "l", "l", "l"],
        text_format=["b", "", "", ""],  # Bold border type column
        # Different border combinations
        border_top=["double", "single", "single", "single"],
        border_bottom=["double", "single", "single", "single"],
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
)

doc_borders.write_rtf("../rtf/border_formatting.rtf")
print("Created border_formatting.rtf")

align_demo = [
    ["Alignment", "Sample Text", "Numbers", "Decimals"],
    ["Left", "Left aligned text", "123", "45.67"],
    ["Center", "Centered text", "456", "89.01"],
    ["Right", "Right aligned text", "789", "23.45"],
    ["Mixed", "Combined alignments", "999", "78.90"],
]

df_align = pl.DataFrame(align_demo, schema=["alignment", "text", "numbers", "decimals"])

doc_align = rtf.RTFDocument(
    df=df_align,
    rtf_title=rtf.RTFTitle(
        text=["Cell Justification Examples", "Column-Specific Alignment Patterns"]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 3.0, 2.0, 2.0],
        # Different alignment for each column
        text_justification=["l", "l", "c", "r"],  # Left, Left, Center, Right
        text_format=["b", "", "", ""],  # Bold alignment column
        text_color=["darkblue", "black", "green", "red"],
        border_top=["single"] * 4,
        border_bottom=["single"] * 4,
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
)

doc_align.write_rtf("../rtf/alignment_formatting.rtf")
print("Created alignment_formatting.rtf")

width_demo = [
    ["Column", "Width Ratio", "Appearance", "Best Use"],
    ["Narrow", "1.0", "Compact", "IDs, codes, flags"],
    ["Standard", "2.0", "Balanced", "Text, descriptions"],
    ["Wide", "3.0", "Spacious", "Long text, comments"],
    ["Extra Wide", "4.0", "Maximum", "Detailed explanations"],
]

df_widths = pl.DataFrame(width_demo, schema=["column", "ratio", "appearance", "use"])

doc_widths = rtf.RTFDocument(
    df=df_widths,
    rtf_title=rtf.RTFTitle(
        text=["Column Width Control", "Relative Width Ratio Examples"]
    ),
    rtf_body=rtf.RTFBody(
        # Demonstrate different width ratios
        col_rel_width=[1.5, 1.0, 2.0, 3.5],  # Narrow to wide progression
        text_justification=["l", "c", "c", "l"],
        text_format=["b", "b", "", ""],  # Bold first two columns
        text_color=["darkblue", "red", "black", "gray"],
        text_background_color=["lightblue", "lightyellow", "white", "lightgray"],
        border_top=["single"] * 4,
        border_bottom=["single"] * 4,
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
)

doc_widths.write_rtf("../rtf/width_formatting.rtf")
print("Created width_formatting.rtf")

format_combo_demo = [
    ["Format", "Code", "Example", "Clinical Use"],
    ["Bold", "b", "Bold text", "Headers, emphasis"],
    ["Italic", "i", "Italic text", "Notes, references"],
    ["Underline", "u", "Underlined text", "Important items"],
    ["Strikethrough", "s", "Crossed out", "Deprecated values"],
    ["Bold+Italic", "bi", "Bold italic", "Maximum emphasis"],
    ["Bold+Underline", "bu", "Bold underlined", "Critical alerts"],
    ["Mixed Styles", "varies", "Multiple formats", "Complex documents"],
]

df_format_combos = pl.DataFrame(
    format_combo_demo, schema=["format", "code", "example", "use"]
)

doc_format_combos = rtf.RTFDocument(
    df=df_format_combos,
    rtf_title=rtf.RTFTitle(
        text=["Text Format Combinations", "Multiple Formatting Options"]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 1.5, 2.5, 3.0],
        text_justification=["l", "c", "c", "l"],
        text_format=["b", "b", "", "i"],  # Bold, Bold, Normal, Italic
        text_color=["darkblue", "red", "black", "green"],
        text_font_size=[18, 16, 16, 14],  # Variable font sizes
        border_top=["single"] * 4,
        border_bottom=["single"] * 4,
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
)

doc_format_combos.write_rtf("../rtf/format_combinations.rtf")
print("Created format_combinations.rtf")

style_demo = [
    ["Element", "Style", "Color Scheme", "Purpose"],
    ["Headers", "Bold + Background", "Blue on Light Blue", "Section identification"],
    ["Normal Data", "Standard", "Black on White", "Regular content"],
    ["Warnings", "Bold + Color", "Red on Light Pink", "Alert conditions"],
    ["Highlights", "Background Only", "Yellow Background", "Important data"],
    ["Footnotes", "Italic + Small", "Gray Text", "Additional info"],
    ["Critical", "Bold + Underline", "Dark Red on Pink", "Urgent attention"],
]

df_styles = pl.DataFrame(style_demo, schema=["element", "style", "colors", "purpose"])

doc_styles = rtf.RTFDocument(
    df=df_styles,
    rtf_title=rtf.RTFTitle(
        text=["Advanced Styling Examples", "Colors, Backgrounds, and Typography"]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 2.5, 2.5, 3.0],
        text_justification=["l", "l", "l", "l"],
        text_format=["b", "", "", ""],  # Bold element column
        text_color=["darkblue", "black", "purple", "gray"],
        text_background_color=["lightblue", "white", "lightyellow", "lightgray"],
        text_font_size=[18, 16, 16, 14],
        border_top=["double"] + ["single"] * 3,
        border_bottom=["double"] + ["single"] * 3,
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
)

doc_styles.write_rtf("../rtf/advanced_styling.rtf")
print("Created advanced_styling.rtf")

clinical_data = [
    ["Endpoint", "Treatment", "N", "Result", "P-value", "Significance"],
    ["Primary Efficacy", "Placebo", "150", "12.3 (2.1)", "—", "Reference"],
    ["", "Drug 25mg", "148", "15.7 (2.3)", "0.023", "Significant"],
    ["", "Drug 50mg", "152", "18.9 (2.2)", "<0.001", "Highly Significant"],
    ["Secondary Endpoint 1", "Placebo", "150", "45.2%", "—", "Reference"],
    ["", "Drug 25mg", "148", "62.8%", "0.012", "Significant"],
    ["", "Drug 50mg", "152", "71.4%", "0.003", "Significant"],
    ["Secondary Endpoint 2", "Placebo", "150", "8.2 (1.5)", "—", "Reference"],
    ["", "Drug 25mg", "148", "6.1 (1.3)", "0.087", "Non-significant"],
    ["", "Drug 50mg", "152", "5.4 (1.2)", "0.041", "Significant"],
    ["Safety Endpoint", "Placebo", "150", "12.0%", "—", "Reference"],
    ["", "Drug 25mg", "148", "15.5%", "0.456", "Non-significant"],
    ["", "Drug 50mg", "152", "18.2%", "0.234", "Non-significant"],
]

df_clinical = pl.DataFrame(
    clinical_data,
    schema=["endpoint", "treatment", "n", "result", "pvalue", "significance"],
)

doc_clinical = rtf.RTFDocument(
    df=df_clinical,
    rtf_page=rtf.RTFPage(orientation="landscape", nrow=30),
    rtf_title=rtf.RTFTitle(
        text=[
            "Clinical Trial Results Summary",
            "Efficacy and Safety Endpoints by Treatment Group",
            "Study ABC-2024-001 | Final Analysis",
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3.0, 2.0, 1.0, 2.0, 1.5, 2.5],
        text_justification=["l", "l", "c", "c", "c", "l"],
        text_format=[
            "b",
            "",
            "",
            "",
            "b",
            "b",
        ],  # Bold endpoints, p-values, significance
        text_color=["darkblue", "black", "black", "black", "red", "darkgreen"],
        text_background_color=[
            "lightblue",
            "white",
            "white",
            "white",
            "white",
            "white",
        ],
        text_font_size=[16, 14, 14, 14, 14, 14],
        text_indent_first=[0, 300, 0, 0, 0, 0],  # Indent treatments under endpoints
        # Complex border pattern
        border_top=["double"] + [""] * 5,
        border_bottom=[""] * 5 + ["single"],
        border_left=["single", "", "", "", "", ""],
        border_right=["", "", "", "", "", "single"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Values presented as mean (standard deviation) or percentage as appropriate",
            "P-values calculated using ANCOVA for continuous endpoints, Chi-square for categorical",
            "Significance: p<0.05 = Significant, p<0.01 = Highly Significant",
            "— = Reference group for statistical comparisons",
        ]
    ),
    rtf_source=rtf.RTFSource(
        text="Clinical Study Database | Statistical Analysis Plan v2.1 | Generated: 15-Dec-2024"
    ),
)

doc_clinical.write_rtf("../rtf/clinical_conditional.rtf")
print("Created clinical_conditional.rtf")

lab_data = [
    ["Parameter", "Value", "Reference", "Status", "Action"],
    ["Hemoglobin", "11.2", "12.0-15.0", "Low", "Monitor"],
    ["Platelet Count", "180", "150-400", "Normal", "Continue"],
    ["ALT", "65", "≤40", "Elevated", "Investigate"],
    ["Creatinine", "2.1", "0.6-1.2", "High", "Alert Physician"],
    ["Glucose", "95", "70-100", "Normal", "Continue"],
    ["Total Cholesterol", "245", "<200", "Elevated", "Lifestyle Counseling"],
    ["HbA1c", "8.2", "<7.0", "Poor Control", "Adjust Therapy"],
    ["Blood Pressure", "165/95", "<140/90", "Hypertensive", "Medication Review"],
]

df_lab = pl.DataFrame(
    lab_data, schema=["parameter", "value", "reference", "status", "action"]
)

doc_lab = rtf.RTFDocument(
    df=df_lab,
    rtf_title=rtf.RTFTitle(
        text=[
            "Laboratory Values Report",
            "Patient: Wilson, Mary (MRN: 789123)",
            "Collection Date: 15-Dec-2024",
        ]
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.5, 1.5, 2.0, 2.0, 2.5],
        text_justification=["l", "c", "c", "l", "l"],
        text_format=["b", "", "", "b", ""],  # Bold parameters and status
        text_color=["darkblue", "black", "gray", "red", "black"],
        text_background_color=["lightblue", "white", "lightgray", "white", "white"],
        text_font_size=[16, 14, 14, 16, 14],
        # Sophisticated border pattern
        border_top=["single"] * 5,
        border_bottom=["single"] * 5,
        border_left=["single", "", "", "", ""],
        border_right=["", "", "", "", "single"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Status: Normal = Within reference range, Low/High = Outside normal limits",
            "Elevated values require clinical correlation and follow-up",
            "Reference ranges may vary by laboratory and patient population",
        ]
    ),
)

doc_lab.write_rtf("../rtf/lab_status_formatting.rtf")
print("Created lab_status_formatting.rtf")
