import polars as pl
from rtflite import RTFDocument, RTFTitle, RTFFootnote, RTFSource, RTFPage
from importlib.resources import files

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
print("RTF document created: ../rtf/formatting_page_default.rtf")

rtf_default = doc_default.rtf_encode()
title_count = rtf_default.count("Adverse Events Summary by Treatment")
footnote_count = rtf_default.count("Abbreviations:")
source_count = rtf_default.count("ADAE Dataset")

print(f"Default behavior:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")

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
print("RTF document created: ../rtf/formatting_page_title_first.rtf")

title_count = doc_title_first.rtf_encode().count("Adverse Events Summary by Treatment")
footnote_count = doc_title_first.rtf_encode().count("Abbreviations:")
source_count = doc_title_first.rtf_encode().count("ADAE Dataset")

print(f"Title on first page only:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")

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
print("RTF document created: ../rtf/formatting_page_footnote_first.rtf")

title_count = doc_footnote_first.rtf_encode().count(
    "Adverse Events Summary by Treatment"
)
footnote_count = doc_footnote_first.rtf_encode().count("Abbreviations:")
source_count = doc_footnote_first.rtf_encode().count("ADAE Dataset")

print(f"Footnote on first page:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")

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
print("RTF document created: ../rtf/formatting_page_all_pages.rtf")

title_count = doc_all_pages.rtf_encode().count("Adverse Events Summary by Treatment")
footnote_count = doc_all_pages.rtf_encode().count("Abbreviations:")
source_count = doc_all_pages.rtf_encode().count("ADAE Dataset")

print(f"All components on all pages:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")

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
print("RTF document created: ../rtf/formatting_page_custom.rtf")

title_count = doc_custom.rtf_encode().count("Adverse Events Summary by Treatment")
footnote_count = doc_custom.rtf_encode().count("Abbreviations:")
source_count = doc_custom.rtf_encode().count("ADAE Dataset")

print(f"Custom combination:")
print(f"  Title appears {title_count} time(s) (all pages)")
print(f"  Footnote appears {footnote_count} time(s) (first page only)")
print(f"  Source appears {source_count} time(s) (last page only)")

small_df = df.head(10)

doc_single_page = RTFDocument(
    df=small_df.select(["USUBJID", "TRTA", "AEDECOD", "AESEV", "AESER", "AEREL"]),
    rtf_page=RTFPage(
        nrow=50,  # Large enough to fit all data on one page
        page_title="last",  # This setting is ignored for single-page docs
        page_footnote="first",  # This setting is ignored for single-page docs
        page_source="all",  # This setting is ignored for single-page docs
    ),
    rtf_title=RTFTitle(text="Adverse Events Summary by Treatment"),
    rtf_footnote=RTFFootnote(
        text="Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related"
    ),
    rtf_source=RTFSource(text="Source: ADAE Dataset from Clinical Trial Database"),
)

rtf_single = doc_single_page.rtf_encode()

title_count = rtf_single.count("Adverse Events Summary by Treatment")
footnote_count = rtf_single.count("Abbreviations:")
source_count = rtf_single.count("ADAE Dataset")

print(f"Single-page document:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")
print("  All components appear once regardless of page placement settings")

valid_options = ["first", "last", "all"]

print("Valid options for page_title, page_footnote, and page_source:")
for option in valid_options:
    print(f"  - '{option}'")

try:
    invalid_page = RTFPage(page_title="invalid")
except ValueError as e:
    print(f"\nValidation error: {e}")
