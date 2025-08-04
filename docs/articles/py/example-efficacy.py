from importlib.resources import files
import polars as pl
import rtflite as rtf

data_path1 = files("rtflite.data").joinpath("tbl1.parquet")
tbl1 = pl.read_parquet(data_path1)

data_path2 = files("rtflite.data").joinpath("tbl2.parquet")
tbl2 = pl.read_parquet(data_path2)

data_path3 = files("rtflite.data").joinpath("tbl3.parquet")
tbl3 = pl.read_parquet(data_path3)

header_11 = rtf.RTFColumnHeader(
    text=["", "Baseline", "Week 20", "Change from Baseline"],
    col_rel_width=[1.2, 2, 2, 4],
    text_justification=["l", "c", "c", "c"],
)

header_12 = rtf.RTFColumnHeader(
    text=[
        "Treatment",
        "N",
        "Mean (SD)",
        "N",
        "Mean (SD)",
        "N",
        "Mean (SD)",
        "LS Mean (95% CI){^a}",
    ],
    col_rel_width=[1.2, 0.5, 1.5, 0.5, 1.5, 0.5, 1.5, 2],
    text_justification=["l"] + ["c"] * 7,
    border_bottom="single",
)

header_2 = rtf.RTFColumnHeader(
    text=["Pairwise Comparison", "Difference in LS Mean (95% CI){^a}", "p-Value"],
    col_rel_width=[3.7, 3.5, 2],
    text_justification=["l", "c", "c"],
)

tbl1_body = rtf.RTFBody(
    col_rel_width=[1.2, 0.5, 1.5, 0.5, 1.5, 0.5, 1.5, 2],
    text_justification=["l"] + ["c"] * 7,
)

tbl2_body = rtf.RTFBody(
    col_rel_width=[3.7, 3.5, 2],
    text_justification=["l"] + ["c"] * 2,
    border_top="single",
)

tbl3_body = rtf.RTFBody(text_justification="l", border_top="single")

doc = rtf.RTFDocument(
    df=[tbl1, tbl2, tbl3],
    rtf_title=rtf.RTFTitle(
        text=[
            "ANCOVA of Change from Baseline at Week 20",
            "Missing Data Approach",
            "Analysis Population",
        ]
    ),
    rtf_column_header=[
        [header_11, header_12],  # Headers for section 1 (2 header rows)
        [header_2],  # Headers for section 2 (1 header row)
        [None],  # Headers for section 3 (no headers)
    ],
    rtf_body=[tbl1_body, tbl2_body, tbl3_body],
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "{^a} Based on an ANCOVA model.",
            "ANCOVA = Analysis of Covariance, CI = Confidence Interval, LS = Least Squares, SD = Standard Deviation",
        ]
    ),
    rtf_source=rtf.RTFSource(text=["Source: [study999: adam-adeff]"]),
)

doc.write_rtf("../rtf/example_efficacy.rtf")
