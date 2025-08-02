from importlib.resources import files
import polars as pl
import rtflite as rtf

data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)

df.select(["USUBJID", "TRTA", "AEDECOD"]).head(4)

tbl = (
    df.group_by(["TRTA", "AEDECOD"])
    .agg(pl.len().alias("n"))
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
        col_rel_width=[3, 2, 2, 2],
    ),
    rtf_body=rtf.RTFBody(col_rel_width=[3, 2, 2, 2]),
)

doc.write_rtf("../rtf/intro-ae3.rtf")

doc = rtf.RTFDocument(
    df=tbl.head(50),
    # rtf_page uses default settings (portrait: nrow=40, landscape: nrow=24)
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
