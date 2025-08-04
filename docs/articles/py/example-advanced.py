from importlib.resources import files
import polars as pl
import rtflite as rtf

data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)

ae_subset = df.slice(200, 60)

print("Raw adverse events data:")
print(ae_subset.select(["USUBJID", "TRTA", "AEDECOD", "AESEV", "ASTDY"]).head(10))

ae_t1 = ae_subset.with_columns(
    [
        # Create subline header with study and site information
        (
            pl.lit("Trial Number: ")
            + pl.col("STUDYID")
            + pl.lit(", Site Number: ")
            + pl.col("SITEID").cast(pl.String)
        ).alias("SUBLINEBY"),
        # Create subject line with demographic information
        (
            pl.lit("Subject ID = ")
            + pl.col("USUBJID")
            + pl.lit(", Gender = ")
            + pl.col("SEX")
            + pl.lit(", Race = ")
            + pl.col("RACE")
            + pl.lit(", AGE = ")
            + pl.col("AGE").cast(pl.String)
            + pl.lit(" Years")
            + pl.lit(", TRT = ")
            + pl.col("TRTA")
        ).alias("SUBJLINE"),
        # Format adverse event term (title case)
        pl.col("AEDECOD").str.to_titlecase().alias("AEDECD1"),
        # Create duration string
        (pl.col("ADURN").cast(pl.String) + pl.lit(" ") + pl.col("ADURU")).alias("DUR"),
    ]
).select(
    [
        "SUBLINEBY",
        "TRTA",
        "SUBJLINE",
        "USUBJID",
        "ASTDY",
        "AEDECD1",
        "DUR",
        "AESEV",
        "AESER",
        "AEREL",
        "AEACN",
        "AEOUT",
    ]
)

ae_t1 = ae_t1.sort(["SUBLINEBY", "TRTA", "SUBJLINE", "USUBJID", "ASTDY"])

print("Processed adverse events data:")
print(ae_t1.select(["USUBJID", "ASTDY", "AEDECD1", "AESEV"]).head(10))

doc_single = rtf.RTFDocument(
    df=ae_t1.select(["USUBJID", "AEDECD1", "AESEV", "AESER"]).head(15),
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 1: Single Column group_by"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        group_by=["USUBJID", "AEDECD1"],  # Group by subject ID only
        col_rel_width=[3, 4, 2, 2],
        text_justification=["l", "l", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Subject ID values are shown only once per subject for better readability",
        text_convert=False,
    ),
)

doc_single.write_rtf("../rtf/example_advance_single.rtf")

doc_group = rtf.RTFDocument(
    df=ae_t1.select(["USUBJID", "ASTDY", "AEDECD1", "AESEV", "AESER"]),
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 2: Hierarchical group_by Usage"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Study Day", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        group_by=["USUBJID", "ASTDY"],  # Hierarchical grouping
        col_rel_width=[3, 1, 4, 2, 2],
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Note: group_by feature provides hierarchical value suppression:",
            "• Subject ID: shown once per subject",
            "• Study Day: shown once per subject-day combination",
            "• Blank cells indicate values suppressed for readability",
        ],
        text_convert=False,
    ),
)

doc_group.write_rtf("../rtf/example_advance_group.rtf")

ae_large = ae_t1.head(100)  # Use more rows to trigger pagination

doc_multipage = rtf.RTFDocument(
    df=ae_large.select(["USUBJID", "ASTDY", "AEDECD1", "AESEV", "AESER"]),
    rtf_page=rtf.RTFPage(nrow=25),  # Force pagination
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 3: Multi-page with group_by"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Study Day", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        group_by=["USUBJID", "ASTDY"],
        col_rel_width=[3, 1, 4, 2, 2],
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Note: In multi-page listings, group context is automatically restored",
            "at the beginning of each new page for better readability.",
        ],
        text_convert=False,
    ),
)

doc_multipage.write_rtf("../rtf/example_advance_multipage.rtf")

doc_no_group = rtf.RTFDocument(
    df=ae_t1.select(["USUBJID", "ASTDY", "AEDECD1", "AESEV", "AESER"]).head(20),
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 4: Without group_by (for comparison)"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Study Day", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        # No group_by specified - all values will be displayed
        col_rel_width=[3, 1, 4, 2, 2],
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Without group_by, all values are displayed in every row",
        text_convert=False,
    ),
)

doc_no_group.write_rtf("../rtf/example_advance_no_group.rtf")
