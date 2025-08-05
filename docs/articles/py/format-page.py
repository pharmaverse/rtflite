from importlib.resources import files

import polars as pl

from rtflite import RTFDocument, RTFTitle, RTFFootnote, RTFSource, RTFPage

data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path).head(30)

doc_default = RTFDocument(
    df=df.select(
        ["USUBJID", "TRTA", "AEDECOD", "AESEV", "AESER", "AEREL"]
    ),  # Select key columns
    rtf_page=RTFPage(nrow=15),  # Force pagination with 15 rows per page
    rtf_title=RTFTitle(text="Adverse Events Summary by Treatment"),
    rtf_footnote=RTFFootnote(
        text="Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related"
    ),
    rtf_source=RTFSource(text="Source: ADAE Dataset from Clinical Trial Database"),
)

doc_default.write_rtf("../rtf/formatting_page_default.rtf")

doc_title_first = RTFDocument(
    df=df.select(["USUBJID", "TRTA", "AEDECOD", "AESEV", "AESER", "AEREL"]),
    rtf_page=RTFPage(
        nrow=15,
        page_title="first",  # Title on first page only
        page_footnote="last",  # Footnote on last page (default)
        page_source="last",  # Source on last page (default)
    ),
    rtf_title=RTFTitle(text="Adverse Events Summary by Treatment"),
    rtf_footnote=RTFFootnote(
        text="Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related"
    ),
    rtf_source=RTFSource(text="Source: ADAE Dataset from Clinical Trial Database"),
)

doc_title_first.write_rtf("../rtf/formatting_page_title_first.rtf")

doc_footnote_first = RTFDocument(
    df=df.select(["USUBJID", "TRTA", "AEDECOD", "AESEV", "AESER", "AEREL"]),
    rtf_page=RTFPage(
        nrow=15,
        page_title="first",  # Title on first page
        page_footnote="first",  # Footnote on first page
        page_source="last",  # Source on last page (default)
    ),
    rtf_title=RTFTitle(text="Adverse Events Summary by Treatment"),
    rtf_footnote=RTFFootnote(
        text="Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related"
    ),
    rtf_source=RTFSource(text="Source: ADAE Dataset from Clinical Trial Database"),
)

doc_footnote_first.write_rtf("../rtf/formatting_page_footnote_first.rtf")

doc_all_pages = RTFDocument(
    df=df.select(["USUBJID", "TRTA", "AEDECOD", "AESEV", "AESER", "AEREL"]),
    rtf_page=RTFPage(
        nrow=15,
        page_title="all",  # Title on all pages
        page_footnote="all",  # Footnote on all pages
        page_source="all",  # Source on all pages
    ),
    rtf_title=RTFTitle(text="Adverse Events Summary by Treatment"),
    rtf_footnote=RTFFootnote(
        text="Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related"
    ),
    rtf_source=RTFSource(text="Source: ADAE Dataset from Clinical Trial Database"),
)

doc_all_pages.write_rtf("../rtf/formatting_page_all_pages.rtf")

doc_custom = RTFDocument(
    df=df.select(["USUBJID", "TRTA", "AEDECOD", "AESEV", "AESER", "AEREL"]),
    rtf_page=RTFPage(
        nrow=15,
        page_title="all",  # Title on all pages
        page_footnote="first",  # Footnote on first page only
        page_source="last",  # Source on last page only
    ),
    rtf_title=RTFTitle(text="Adverse Events Summary by Treatment"),
    rtf_footnote=RTFFootnote(
        text="Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related"
    ),
    rtf_source=RTFSource(text="Source: ADAE Dataset from Clinical Trial Database"),
)

doc_custom.write_rtf("../rtf/formatting_page_custom.rtf")
