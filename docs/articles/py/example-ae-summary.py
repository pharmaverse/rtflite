import pandas as pd
import numpy as np
import rtflite as rtf

np.random.seed(789)

treatments = {"Placebo": 100, "Drug 50mg": 101, "Drug 100mg": 99}

ae_structure = {
    "Gastrointestinal disorders": {
        "Nausea": [0.15, 0.22, 0.28],  # Incidence rates by treatment
        "Diarrhea": [0.12, 0.18, 0.20],
        "Vomiting": [0.08, 0.12, 0.15],
        "Constipation": [0.10, 0.08, 0.06],
    },
    "Nervous system disorders": {
        "Headache": [0.18, 0.20, 0.25],
        "Dizziness": [0.10, 0.15, 0.18],
        "Somnolence": [0.05, 0.10, 0.12],
    },
    "General disorders": {
        "Fatigue": [0.14, 0.16, 0.20],
        "Pyrexia": [0.08, 0.10, 0.10],
        "Asthenia": [0.06, 0.08, 0.10],
    },
}

ae_data = []
for trt_idx, (trt, n_subjects) in enumerate(treatments.items()):
    subject_ids = [f"{trt[:4].upper()}-{i:03d}" for i in range(1, n_subjects + 1)]

    for soc, pts in ae_structure.items():
        for pt, rates in pts.items():
            # Number of subjects experiencing this AE
            n_ae = int(n_subjects * rates[trt_idx])

            # Create records for subjects with this AE
            for i in range(n_ae):
                ae_data.append(
                    {
                        "USUBJID": subject_ids[i],
                        "TREATMENT": trt,
                        "SOC": soc,
                        "PT": pt,
                        "AESER": "N"
                        if np.random.random() > 0.05
                        else "Y",  # 5% serious
                        "AEREL": np.random.choice(
                            ["Not Related", "Possibly Related", "Related"],
                            p=[0.3, 0.5, 0.2],
                        ),
                    }
                )

df_ae = pd.DataFrame(ae_data)
print(f"Generated {len(df_ae)} AE records")
print(f"Unique subjects with AEs: {df_ae['USUBJID'].nunique()}")

ae_summary = []

for soc in ae_structure.keys():
    for pt in ae_structure[soc].keys():
        row_data = {"SOC": soc, "PT": pt}

        for trt in treatments.keys():
            # Count subjects with this AE
            n_subjects_total = treatments[trt]
            subjects_with_ae = df_ae[
                (df_ae["TREATMENT"] == trt)
                & (df_ae["SOC"] == soc)
                & (df_ae["PT"] == pt)
            ]["USUBJID"].nunique()

            pct = (subjects_with_ae / n_subjects_total) * 100

            row_data[f"{trt}_n"] = subjects_with_ae
            row_data[f"{trt}_pct"] = f"{pct:.1f}"
            row_data[f"{trt}_display"] = f"{subjects_with_ae} ({pct:.1f})"

        ae_summary.append(row_data)

df_summary = pd.DataFrame(ae_summary)

df_summary = df_summary.sort_values(["SOC", "PT"])


def max_incidence(row):
    return max(
        float(row["Placebo_pct"]),
        float(row["Drug 50mg_pct"]),
        float(row["Drug 100mg_pct"]),
    )


df_summary["max_pct"] = df_summary.apply(max_incidence, axis=1)
df_filtered = df_summary[df_summary["max_pct"] >= 5.0].copy()
df_filtered = df_filtered.drop("max_pct", axis=1)

print(f"\nAE Summary (≥5% incidence):")
print(
    df_filtered[
        ["SOC", "PT", "Placebo_display", "Drug 50mg_display", "Drug 100mg_display"]
    ]
)

rtf_data = df_filtered[
    ["SOC", "PT", "Placebo_display", "Drug 50mg_display", "Drug 100mg_display"]
].copy()
rtf_data.columns = [
    "System Organ Class",
    "Preferred Term",
    "Placebo",
    "Drug 50mg",
    "Drug 100mg",
]

header1 = pd.DataFrame([["", "", "Number (%) of Subjects", "", ""]])
header2 = pd.DataFrame(
    [
        [
            "System Organ Class",
            "Preferred Term",
            f"Placebo\n(N={treatments['Placebo']})",
            f"Drug 50mg\n(N={treatments['Drug 50mg']})",
            f"Drug 100mg\n(N={treatments['Drug 100mg']})",
        ]
    ]
)

doc = rtf.RTFDocument(
    df=rtf_data,
    rtf_page=rtf.RTFPage(orientation="portrait", nrow=40),
    rtf_title=rtf.RTFTitle(
        text=[
            "Table 14.3.1.1: Treatment-Emergent Adverse Events",
            "Occurring in ≥5% of Subjects in Any Treatment Group",
            "Safety Population",
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=header1,
            col_rel_width=[2.5, 2.5, 1.5, 1.5, 1.5],
            text_justification=["l", "l", "c", "c", "c"],
            text_format=["b"] * 5,
            border_bottom=[""] * 5,
        ),
        rtf.RTFColumnHeader(
            df=header2,
            col_rel_width=[2.5, 2.5, 1.5, 1.5, 1.5],
            text_justification=["l", "l", "c", "c", "c"],
            text_format=["b"] * 5,
            border_top=["single"] * 5,
            border_bottom=["single"] * 5,
        ),
    ],
    rtf_body=rtf.RTFBody(
        page_by=["System Organ Class"],  # Group by SOC
        new_page=False,  # Keep SOCs together when possible
        col_rel_width=[2.5, 2.5, 1.5, 1.5, 1.5],
        text_justification=["l", "l", "c", "c", "c"],
        text_indent_first=[0, 100, 0, 0, 0],  # Indent PT under SOC
        border_left=["single"] + [""] * 4,
        border_right=[""] * 4 + ["single"],
        border_bottom=[""] * 5,
        # Format SOC headers differently
        text_format=["b", "", "", "", ""],
        text_background_color=["", "", "", "", ""],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Subjects with multiple occurrences of an AE are counted only once per preferred term. "
        + "Percentages are based on the number of subjects in each treatment group. "
        + "MedDRA Version 24.1 was used for coding."
    ),
    rtf_source=rtf.RTFSource(
        text="Source: ADAE SDTM Dataset, Data Cutoff: 31-DEC-2023"
    ),
)

doc.write_rtf("ae_summary_table.rtf")
print("\nCreated ae_summary_table.rtf")

ae_rel_summary = []

for soc in ae_structure.keys():
    # Add SOC header row
    soc_row = {
        "category": soc,
        "subcategory": "",
        "Placebo_all": "",
        "Drug 50mg_all": "",
        "Drug 100mg_all": "",
        "Placebo_related": "",
        "Drug 50mg_related": "",
        "Drug 100mg_related": "",
    }
    ae_rel_summary.append(soc_row)

    for pt in ae_structure[soc].keys():
        row_data = {"category": "", "subcategory": f"  {pt}"}  # Indent PT

        for trt in treatments.keys():
            n_total = treatments[trt]

            # All AEs
            all_ae = df_ae[
                (df_ae["TREATMENT"] == trt)
                & (df_ae["SOC"] == soc)
                & (df_ae["PT"] == pt)
            ]["USUBJID"].nunique()

            # Related AEs
            related_ae = df_ae[
                (df_ae["TREATMENT"] == trt)
                & (df_ae["SOC"] == soc)
                & (df_ae["PT"] == pt)
                & (df_ae["AEREL"].isin(["Possibly Related", "Related"]))
            ]["USUBJID"].nunique()

            all_pct = (all_ae / n_total) * 100
            rel_pct = (related_ae / n_total) * 100

            row_data[f"{trt}_all"] = f"{all_ae} ({all_pct:.1f})" if all_ae > 0 else "0"
            row_data[f"{trt}_related"] = (
                f"{related_ae} ({rel_pct:.1f})" if related_ae > 0 else "0"
            )

        ae_rel_summary.append(row_data)

df_rel_summary = pd.DataFrame(ae_rel_summary)

header_rel1 = pd.DataFrame(
    [["", "", "All TEAEs", "", "", "Drug-Related TEAEs", "", ""]]
)
header_rel2 = pd.DataFrame(
    [
        [
            "System Organ Class",
            "Preferred Term",
            "Placebo",
            "Drug 50mg",
            "Drug 100mg",
            "Placebo",
            "Drug 50mg",
            "Drug 100mg",
        ]
    ]
)

doc_rel = rtf.RTFDocument(
    df=df_rel_summary,
    rtf_page=rtf.RTFPage(
        orientation="landscape",  # Wider table needs landscape
        nrow=40,
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Table 14.3.2.1: Treatment-Emergent Adverse Events by Relationship to Study Drug",
            "All Incidences - Safety Population",
        ]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            df=header_rel1,
            col_rel_width=[2.0, 2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2],
            text_justification=["l", "l", "c", "c", "c", "c", "c", "c"],
            text_format=["b"] * 8,
            border_bottom=[""] * 8,
            text_background_color=[
                "white",
                "white",
                "lightblue",
                "lightblue",
                "lightblue",
                "lightyellow",
                "lightyellow",
                "lightyellow",
            ],
        ),
        rtf.RTFColumnHeader(
            df=header_rel2,
            col_rel_width=[2.0, 2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2],
            text_justification=["l", "l", "c", "c", "c", "c", "c", "c"],
            text_format=["b"] * 8,
            border_top=["single"] * 8,
            border_bottom=["single"] * 8,
        ),
    ],
    rtf_body=rtf.RTFBody(
        col_rel_width=[2.0, 2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2],
        text_justification=["l", "l", "c", "c", "c", "c", "c", "c"],
        text_format=[
            ["b", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
        ],  # Bold SOC rows
        border_left=["single"] + [""] * 7,
        border_right=[""] * 7 + ["single"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="TEAEs = Treatment-Emergent Adverse Events. "
        + "Drug-Related includes events assessed as 'Possibly Related' or 'Related' by the investigator. "
        + "N = Number of subjects in treatment group; n (%) = Number (percentage) of subjects with event."
    ),
    rtf_source=rtf.RTFSource(
        text="Program: t-ae-rel.py | Output: "
        + pd.Timestamp.now().strftime("%d%b%Y:%H:%M")
    ),
)

doc_rel.write_rtf("ae_summary_relationship.rtf")
print("Created ae_summary_relationship.rtf")

try:
    converter = rtf.LibreOfficeConverter()

    files_to_convert = ["ae_summary_table.rtf", "ae_summary_relationship.rtf"]

    for file in files_to_convert:
        converter.convert(
            input_files=file, output_dir=".", format="pdf", overwrite=True
        )
        print(f"✓ Converted {file} to PDF")

    print("\nPDF conversion completed successfully!")

except FileNotFoundError as e:
    print(f"Note: {e}")
    print("\nTo enable PDF conversion, install LibreOffice:")
    print("- macOS: brew install --cask libreoffice")
    print("- Ubuntu/Debian: sudo apt-get install libreoffice")
    print("- Windows: Download from https://www.libreoffice.org/")
    print(
        "\nRTF files have been successfully created and can be opened in any RTF-compatible application."
    )
