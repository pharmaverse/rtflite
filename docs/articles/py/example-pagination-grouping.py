import pandas as pd
import numpy as np
import rtflite as rtf

np.random.seed(123)

soc_categories = [
    "Gastrointestinal disorders",
    "Nervous system disorders",
    "Skin and subcutaneous tissue disorders",
    "General disorders and administration site conditions",
    "Infections and infestations",
]

preferred_terms = {
    "Gastrointestinal disorders": [
        "Nausea",
        "Vomiting",
        "Diarrhea",
        "Constipation",
        "Abdominal pain",
    ],
    "Nervous system disorders": ["Headache", "Dizziness", "Somnolence", "Tremor"],
    "Skin and subcutaneous tissue disorders": [
        "Rash",
        "Pruritus",
        "Erythema",
        "Dry skin",
    ],
    "General disorders and administration site conditions": [
        "Fatigue",
        "Pyrexia",
        "Asthenia",
        "Injection site reaction",
    ],
    "Infections and infestations": [
        "Upper respiratory tract infection",
        "Urinary tract infection",
        "Nasopharyngitis",
    ],
}

treatments = ["Placebo", "Drug 5mg", "Drug 10mg"]

ae_data = []
for soc in soc_categories:
    for pt in preferred_terms[soc]:
        for trt in treatments:
            # Generate counts with some randomness
            n_subjects = np.random.poisson(3) + 1  # 1-10 subjects typically
            n_events = n_subjects + np.random.poisson(
                2
            )  # Usually more events than subjects

            ae_data.append(
                {
                    "SOC": soc,
                    "Preferred_Term": pt,
                    "Treatment": trt,
                    "N_Subjects": n_subjects,
                    "N_Events": n_events,
                    "Percentage": round(
                        (n_subjects / 100) * 100, 1
                    ),  # Assuming 100 subjects per arm
                }
            )

df_ae = pd.DataFrame(ae_data)
print(f"Generated {len(df_ae)} adverse event records")
print("\nSample data:")
print(df_ae.head(10))

ae_headers1 = pd.DataFrame([["", "Placebo", "Drug 5mg", "Drug 10mg"]])
ae_headers2 = pd.DataFrame([["Preferred Term", "n (%)", "n (%)", "n (%)"]])

doc_grouped = rtf.RTFDocument(
    df=df_ae,
    rtf_page=rtf.RTFPage(
        nrow=30,  # Allow more rows per page
        orientation="portrait",
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Treatment-Emergent Adverse Events",
            "By System Organ Class",
            "Safety Population",
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=ae_headers1,
            col_rel_width=[3, 2, 2, 2],
            text_justification=["l", "c", "c", "c"],
            text_format=["b"] * 4,
            border_bottom=["single"] * 4,
        ),
        rtf.RTFColumnHeader(
            df=ae_headers2,
            col_rel_width=[3, 2, 2, 2],
            text_justification=["l", "c", "c", "c"],
            text_format=["b"] * 4,
            border_top=["single"] * 4,
            border_bottom=["single"] * 4,
        ),
    ],
    rtf_body=rtf.RTFBody(
        page_by=["SOC"],  # Group by System Organ Class
        new_page=True,  # Force new page for each SOC
        pageby_header=True,  # Show SOC as page header
        col_rel_width=[3, 2, 2, 2],
        text_justification=["l", "c", "c", "c"],
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Treatment-emergent adverse events occurring in ≥2% of subjects in any treatment group. "
        + "Subjects counted once per preferred term per treatment."
    ),
    rtf_source=rtf.RTFSource(text="Source: ADAE dataset, Data cutoff: 15-JAN-2024"),
)

doc_grouped.write_rtf("ae_by_soc_grouped.rtf")
print("Created ae_by_soc_grouped.rtf with page-by grouping")

summary_data = []
for trt in treatments:
    trt_data = df_ae[df_ae["Treatment"] == trt]

    for soc in soc_categories:
        soc_data = trt_data[trt_data["SOC"] == soc]

        total_subjects = soc_data["N_Subjects"].sum()
        total_events = soc_data["N_Events"].sum()
        unique_pts = len(soc_data["Preferred_Term"].unique())

        summary_data.append(
            {
                "Treatment_Group": trt,
                "SOC": soc,
                "Total_Subjects": total_subjects,
                "Total_Events": total_events,
                "Unique_PTs": unique_pts,
                "Avg_Events_Per_Subject": round(
                    total_events / max(total_subjects, 1), 2
                ),
            }
        )

df_summary = pd.DataFrame(summary_data)

doc_advanced = rtf.RTFDocument(
    df=df_summary,
    rtf_page=rtf.RTFPage(
        nrow=15,  # Smaller pages for better grouping demonstration
        orientation="landscape",
        page_title_location="first",  # Title only on first page
        page_footnote_location="last",  # Footnote only on last page
    ),
    rtf_page_header=rtf.RTFPageHeader(
        text="CONFIDENTIAL - Study XYZ-789 - Adverse Event Summary"
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Adverse Event Summary by Treatment Group",
            "System Organ Class Analysis",
            "Integrated Safety Analysis Set",
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=pd.DataFrame(
                [
                    [
                        "System Organ Class",
                        "Total Subjects",
                        "Total Events",
                        "Unique Terms",
                        "Avg Events/Subject",
                    ]
                ]
            ),
            col_rel_width=[3, 1.5, 1.5, 1.5, 1.5],
            text_justification=["l", "c", "c", "c", "c"],
            text_format=["b"] * 5,
            text_background_color=["lightblue"] * 5,
            border_top=["single"] * 5,
            border_bottom=["single"] * 5,
        )
    ],
    rtf_body=rtf.RTFBody(
        page_by=["Treatment_Group"],  # Group by treatment
        new_page=True,  # New page for each treatment
        pageby_header=True,  # Show treatment as header
        col_rel_width=[3, 1.5, 1.5, 1.5, 1.5],
        text_justification=["l", "c", "c", "c", "c"],
        # Alternate row colors within each group
        text_background_color=["white", "lightgray"] * 3,
        border_left=["single", "", "", "", ""],
        border_right=["", "", "", "", "single"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Summary includes all treatment-emergent adverse events reported during the study period. "
        + "Subjects may contribute to multiple system organ classes."
    ),
    rtf_source=rtf.RTFSource(
        text="Generated: {DATETIME} | Source: Integrated ADAE Analysis Dataset v2.1"
    ),
)

doc_advanced.write_rtf("ae_summary_by_treatment.rtf")
print("Created ae_summary_by_treatment.rtf with treatment grouping")

doc_mixed = rtf.RTFDocument(
    df=df_ae.head(40),  # Use subset for cleaner example
    rtf_page=rtf.RTFPage(
        nrow=50,  # Large page to accommodate multiple groups
        orientation="portrait",
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Adverse Events - Grouped Display",
            "Multiple System Organ Classes per Page",
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=pd.DataFrame(
                [
                    [
                        "System Organ Class / Preferred Term",
                        "Placebo n(%)",
                        "Drug 5mg n(%)",
                        "Drug 10mg n(%)",
                    ]
                ]
            ),
            col_rel_width=[4, 2, 2, 2],
            text_justification=["l", "c", "c", "c"],
            text_format=["b"] * 4,
            border_bottom=["single"] * 4,
        )
    ],
    rtf_body=rtf.RTFBody(
        page_by=["SOC"],  # Group by SOC
        new_page=False,  # DON'T force new pages - allow multiple groups per page
        pageby_header=True,  # Still show group headers
        col_rel_width=[4, 2, 2, 2],
        text_justification=["l", "c", "c", "c"],
        # Highlight group headers with different formatting
        text_format=["b", "", "", ""],  # Bold first column (will be group headers)
        text_background_color=["lightblue", "white", "white", "white"],
        border_left=["single", "", "", ""],
        border_right=["", "", "", "single"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="System Organ Classes are grouped together but may appear on the same page to optimize space usage."
    ),
)

doc_mixed.write_rtf("ae_mixed_grouping.rtf")
print("Created ae_mixed_grouping.rtf with mixed grouping (no forced page breaks)")

try:
    converter = rtf.LibreOfficeConverter()

    files_to_convert = [
        "ae_by_soc_grouped.rtf",
        "ae_summary_by_treatment.rtf",
        "ae_mixed_grouping.rtf",
    ]

    for file in files_to_convert:
        converter.convert(
            input_files=file, output_dir=".", format="pdf", overwrite=True
        )
        print(f"✓ Converted {file} to PDF")

    print("\nAll PDF conversions completed successfully!")

except FileNotFoundError as e:
    print(f"Note: {e}")
    print("\nTo enable PDF conversion, install LibreOffice:")
    print("- macOS: brew install --cask libreoffice")
    print("- Ubuntu/Debian: sudo apt-get install libreoffice")
    print("- Windows: Download from https://www.libreoffice.org/")
    print("\nRTF files have been successfully created:")
    print("- ae_by_soc_grouped.rtf")
    print("- ae_summary_by_treatment.rtf")
    print("- ae_mixed_grouping.rtf")
    print("\nThese files can be opened in any RTF-compatible application.")
