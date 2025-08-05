from importlib.resources import files
import polars as pl
import rtflite as rtf

data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)

ae_subset = df.slice(200, 60)

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

doc_single = rtf.RTFDocument(
    df=ae_t1.select(["USUBJID", "AEDECD1", "AESEV", "AESER"])
    .head(15)
    .sort(["USUBJID", "AEDECD1"]),
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
        group_by=["USUBJID", "AEDECD1"],  # Group by subject ID and adverse event
        col_rel_width=[3, 4, 2, 2],
        text_justification=["l", "l", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Subject ID and Adverse Event values are shown only once per group for better readability",
        text_convert=False,
    ),
)

doc_single.write_rtf("../rtf/example_advance_single.rtf")

ae_large = ae_t1.head(100)  # Use more rows to trigger pagination

doc_multipage = rtf.RTFDocument(
    df=ae_large.select(["USUBJID", "ASTDY", "AEDECD1", "AESEV", "AESER"]).sort(
        ["USUBJID", "ASTDY"]
    ),
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

ae_with_treatments = (
    ae_t1.filter(pl.col("TRTA").is_in(["Placebo", "Xanomeline High Dose"]))
    .select(["TRTA", "USUBJID", "ASTDY", "AEDECD1", "AESEV"])
    .head(40)
    .sort(["TRTA", "USUBJID", "ASTDY"])
)

doc_treatment_separated = rtf.RTFDocument(
    df=ae_with_treatments,
    rtf_title=rtf.RTFTitle(
        text=[
            "Adverse Events Listing",
            "Example 5: group_by + new_page (Treatment Separation)",
        ],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Treatment", "Subject ID", "Study Day", "Adverse Event", "Severity"],
        text_format="b",
        text_justification=["l", "l", "c", "l", "c"],
    ),
    rtf_body=rtf.RTFBody(
        page_by=["TRTA"],  # Separate pages by treatment
        new_page=True,  # Force new page for each treatment
        group_by=[
            "TRTA",
            "USUBJID",
            "ASTDY",
        ],  # Suppress duplicates within each treatment page
        col_rel_width=[2, 3, 1, 4, 2],
        text_justification=["l", "l", "c", "l", "c"],
        pageby_header=True,  # Repeat headers on each treatment page
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Example of group_by + new_page combination:",
            "- Each treatment group gets its own page(s) (new_page=True)",
            "- Within each treatment, USUBJID and ASTDY are suppressed when duplicate (group_by)",
            "- Headers are repeated on each treatment page (pageby_header=True)",
        ],
        text_convert=False,
    ),
)

doc_treatment_separated.write_rtf("../rtf/example_advance_group_newpage.rtf")

ae_subline_data = (
    ae_t1.filter(pl.col("TRTA").is_in(["Placebo", "Xanomeline High Dose"]))
    .head(30)
    .sort(["SUBLINEBY", "TRTA", "USUBJID"])
)

doc_subline = rtf.RTFDocument(
    df=ae_subline_data.select(["SUBLINEBY", "USUBJID", "AEDECD1", "AESEV", "AESER"]),
    rtf_title=rtf.RTFTitle(
        text=[
            "Adverse Events Listing",
            "Example 6: subline_by with Subheader Generation",
        ],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Subject ID",
            "Adverse Event",
            "Severity",
            "Serious",
        ],  # Headers for remaining columns after SUBLINEBY removal
        text_format="b",
        text_justification=["l", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        subline_by=["SUBLINEBY"],  # Creates subheader rows from SUBLINEBY values
        col_rel_width=[
            3,
            4,
            2,
            2,
        ],  # Widths for remaining 4 columns after SUBLINEBY removal
        text_justification=["l", "l", "c", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Note: subline_by creates subheader rows that span all columns",
            "- SUBLINEBY column values become bold subheader text",
            "- Original SUBLINEBY column is removed from table data",
            "- Subheaders provide clear visual grouping of related records",
        ],
        text_convert=False,
    ),
)

doc_subline.write_rtf("../rtf/example_advance_subline.rtf")

ae_comprehensive = (
    ae_t1.head(40)
    .with_columns(
        [
            # Add visit information to create multiple rows per subject
            pl.when(pl.int_range(pl.len()) % 3 == 0)
            .then(pl.lit("Visit 1"))
            .when(pl.int_range(pl.len()) % 3 == 1)
            .then(pl.lit("Visit 2"))
            .otherwise(pl.lit("Visit 3"))
            .alias("VISIT")
        ]
    )
    .sort(["SUBLINEBY", "USUBJID", "VISIT"])
)

doc_comprehensive = rtf.RTFDocument(
    df=ae_comprehensive.select(["SUBLINEBY", "USUBJID", "VISIT", "AEDECD1", "AESEV"]),
    rtf_title=rtf.RTFTitle(
        text=[
            "Adverse Events Listing",
            "Example 7: subline_by + group_by Comprehensive",
        ],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=[
            "Subject ID",
            "Visit",
            "Adverse Event",
            "Severity",
        ],  # Headers for remaining columns after SUBLINEBY removal
        text_format="b",
        text_justification=["l", "c", "l", "c"],
    ),
    rtf_body=rtf.RTFBody(
        subline_by=["SUBLINEBY"],  # Creates trial/site subheaders
        group_by=["USUBJID"],  # Suppresses duplicate subject IDs
        col_rel_width=[
            3,
            2,
            4,
            2,
        ],  # Widths for remaining 4 columns after SUBLINEBY removal
        text_justification=["l", "c", "l", "c"],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Advanced example combining subline_by and group_by:",
            "- SUBLINEBY creates bold subheader rows for trial/site information",
            "- group_by suppresses duplicate USUBJID values within each group",
            "- Result: Clear visual hierarchy with minimal redundancy",
        ],
        text_convert=False,
    ),
)

doc_comprehensive.write_rtf("../rtf/example_advance_comprehensive.rtf")
