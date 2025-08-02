from importlib.resources import files
import polars as pl
import rtflite as rtf

data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)

df.select(["USUBJID", "TRTA", "AEDECOD"]).head(4)

tbl = (
    df.group_by(["TRTA", "AEDECOD"])
    .agg(pl.len().alias("n"))
    .sort("TRTA")
    .pivot(values="n", index="AEDECOD", on="TRTA")
    .fill_null(0)
    .sort("AEDECOD")  # Sort by adverse event name to match R output
)
print(tbl.head(4))

doc = rtf.RTFDocument(
    df=tbl.head(6),
    rtf_body=rtf.RTFBody(),  # Step 1: Add table attributes
)

doc.write_rtf("../rtf/intro-ae1.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(6),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 2, 2, 2]  # define relative width
    ),
)

doc.write_rtf("../rtf/intro-ae2.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(6),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo",
            "Xanomeline High Dose",
            "Xanomeline Low Dose",
        ],
    ),
    rtf_body=rtf.RTFBody(col_rel_width=[3, 2, 2, 2]),
)

doc.write_rtf("../rtf/intro-ae3.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(50),
    rtf_page=rtf.RTFPage(nrow=15),
    rtf_column_header=[
        rtf.RTFColumnHeader(text=[" ", "Treatment"], col_rel_width=[3, 3]),
        rtf.RTFColumnHeader(
            text=[
                "Adverse Events",
                "Placebo",
                "Xanomeline High Dose",
                "Xanomeline Low Dose",
            ],
            col_rel_width=[3, 1, 1, 1],
        ),
    ],
    rtf_body=rtf.RTFBody(col_rel_width=[3, 1, 1, 1]),
)

doc.write_rtf("../rtf/intro-ae4.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(15),
    rtf_title=rtf.RTFTitle(
        text=["Summary of Adverse Events by Treatment Group", "Safety Analysis Set"]
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo\\line (N=86)",
            "Xanomeline High Dose\\line (N=84)",
            "Xanomeline Low Dose\\line (N=84)",
        ],
    ),
    rtf_body=rtf.RTFBody(col_rel_width=[3, 2, 2, 2]),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Adverse events are coded using MedDRA version 25.0.",
            "Events are sorted alphabetically by preferred term.",
        ]
    ),
    rtf_source=rtf.RTFSource(text="Source: ADAE dataset, Data cutoff: 01JAN2023"),
)

doc.write_rtf("../rtf/intro-ae5.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(10),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo",
            "Xanomeline High Dose",
            "Xanomeline Low Dose",
        ],
        text_format="b",  # Bold headers
        text_justification=["l", "c", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 1, 1, 1],
        text_justification=["l", "c", "c", "c"],
    ),
)

doc.write_rtf("../rtf/intro-ae6.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(8),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo",
            "Xanomeline High Dose",
            "Xanomeline Low Dose",
        ],
        border_bottom=["single", "double", "single", "single"],
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 2, 2, 2],
        border_left=["single", "", "", ""],
    ),
)

doc.write_rtf("../rtf/intro-ae7.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(20),
    rtf_page=rtf.RTFPage(
        orientation="landscape",  # Landscape for wider tables
        nrow=10,
        border_first="dashed",  # Dash border for first/last pages
        border_last="dashed",
    ),
    rtf_title=rtf.RTFTitle(text="Adverse Events Summary - Landscape Layout"),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo (N=86)",
            "Xanomeline High Dose (N=84)",
            "Xanomeline Low Dose (N=84)",
        ],
    ),
    rtf_body=rtf.RTFBody(col_rel_width=[4, 2, 2, 2]),
)

doc.write_rtf("../rtf/intro-ae8.rtf")


border_pattern = [
    ["single", "", "single", ""],  # Row 1: borders on columns 1 and 3
    ["", "double", "", "double"],  # Row 2: borders on columns 2 and 4
    ["single", "single", "single", "single"],  # Row 3: borders on all columns
]

doc = rtf.RTFDocument(
    df=tbl.head(3),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo",
            "Xanomeline High Dose",
            "Xanomeline Low Dose",
        ],
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 2, 2, 2],
        border_top=border_pattern,  # Apply custom border pattern
    ),
)

doc.write_rtf("../rtf/intro-ae9.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(50),
    rtf_page=rtf.RTFPage(
        nrow=15,
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Complete Adverse Events Summary",
            "All Treatment Groups - Multi-page Table",
        ]
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Adverse Events",
            "Placebo\\line (N=86)",
            "Xanomeline High Dose\\line (N=84)",
            "Xanomeline Low Dose\\line (N=84)",
        ],
        text_format="b",
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 1, 1, 1],
        text_justification=["l", "c", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "MedDRA version 25.0 coding applied.",
            "Table includes all reported adverse events regardless of relationship to study drug.",
            "Events sorted alphabetically by preferred term.",
        ]
    ),
    rtf_source=rtf.RTFSource(text="Dataset: ADAE | Cutoff: 01JAN2023"),
)

doc.write_rtf("../rtf/intro-ae10.rtf")
