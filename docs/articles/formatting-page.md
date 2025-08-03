# Page Format


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

# Controlling Component Placement in Multi-page Documents

When generating multi-page RTF documents, you may want to control where
titles, footnotes, and sources appear. The `RTFPage` class provides
three parameters to control this behavior:

- `page_title`: Controls where titles appear (“first”, “last”, “all”)
- `page_footnote`: Controls where footnotes appear (“first”, “last”,
  “all”)
- `page_source`: Controls where sources appear (“first”, “last”, “all”)

## Default Behavior

By default: - Titles appear on **all pages** (`page_title="all"`) -
Footnotes appear on the **last page only** (`page_footnote="last"`) -
Sources appear on the **last page only** (`page_source="last"`)

## Examples

### Basic Setup

``` python
import polars as pl
from rtflite import RTFDocument, RTFTitle, RTFFootnote, RTFSource, RTFPage
from importlib.resources import files

# Load the adverse events dataset
data_path = files('rtflite.data').joinpath('adae.parquet')
df = pl.read_parquet(data_path).head(30)
```

### Example 1: Default Behavior

``` python
# Default: title on all pages, footnote and source on last page
doc_default = RTFDocument(
    df=df.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'AESER', 'AEREL']),  # Select key columns
    rtf_page=RTFPage(nrow=15),  # Force pagination with 15 rows per page
    rtf_title=RTFTitle(text='Adverse Events Summary by Treatment'),
    rtf_footnote=RTFFootnote(text='Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related'),
    rtf_source=RTFSource(text='Source: ADAE Dataset from Clinical Trial Database')
)

# Generate RTF and save to file
doc_default.write_rtf("../rtf/formatting_page_default.rtf")
print("RTF document created: ../rtf/formatting_page_default.rtf")

# Count occurrences
rtf_default = doc_default.rtf_encode()
title_count = rtf_default.count('Adverse Events Summary by Treatment')
footnote_count = rtf_default.count('Abbreviations:')
source_count = rtf_default.count('ADAE Dataset')

print(f"Default behavior:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")
```

<embed src="../pdf/formatting_page_default.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 2: Title on First Page Only

``` python
# Title on first page only, footnote and source on last page
doc_title_first = RTFDocument(
    df=df.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'AESER', 'AEREL']),
    rtf_page=RTFPage(
        nrow=15,
        page_title="first",      # Title on first page only
        page_footnote="last",    # Footnote on last page (default)
        page_source="last"       # Source on last page (default)
    ),
    rtf_title=RTFTitle(text='Adverse Events Summary by Treatment'),
    rtf_footnote=RTFFootnote(text='Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related'),
    rtf_source=RTFSource(text='Source: ADAE Dataset from Clinical Trial Database')
)

# Generate RTF and save to file
doc_title_first.write_rtf("../rtf/formatting_page_title_first.rtf")
print("RTF document created: ../rtf/formatting_page_title_first.rtf")

title_count = doc_title_first.rtf_encode().count('Adverse Events Summary by Treatment')
footnote_count = doc_title_first.rtf_encode().count('Abbreviations:')
source_count = doc_title_first.rtf_encode().count('ADAE Dataset')

print(f"Title on first page only:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")
```

<embed src="../pdf/formatting_page_title_first.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 3: Footnote on First Page

``` python
# Title on first page (default), footnote on first page, source on last page
doc_footnote_first = RTFDocument(
    df=df.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'AESER', 'AEREL']),
    rtf_page=RTFPage(
        nrow=15,
        page_title="first",      # Title on first page
        page_footnote="first",   # Footnote on first page
        page_source="last"       # Source on last page (default)
    ),
    rtf_title=RTFTitle(text='Adverse Events Summary by Treatment'),
    rtf_footnote=RTFFootnote(text='Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related'),
    rtf_source=RTFSource(text='Source: ADAE Dataset from Clinical Trial Database')
)

# Generate RTF and save to file
doc_footnote_first.write_rtf("../rtf/formatting_page_footnote_first.rtf")
print("RTF document created: ../rtf/formatting_page_footnote_first.rtf")

title_count = doc_footnote_first.rtf_encode().count('Adverse Events Summary by Treatment')
footnote_count = doc_footnote_first.rtf_encode().count('Abbreviations:')
source_count = doc_footnote_first.rtf_encode().count('ADAE Dataset')

print(f"Footnote on first page:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")
```

<embed src="../pdf/formatting_page_footnote_first.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 4: All Components on All Pages

``` python
# All components on all pages
doc_all_pages = RTFDocument(
    df=df.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'AESER', 'AEREL']),
    rtf_page=RTFPage(
        nrow=15,
        page_title="all",        # Title on all pages
        page_footnote="all",     # Footnote on all pages
        page_source="all"        # Source on all pages
    ),
    rtf_title=RTFTitle(text='Adverse Events Summary by Treatment'),
    rtf_footnote=RTFFootnote(text='Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related'),
    rtf_source=RTFSource(text='Source: ADAE Dataset from Clinical Trial Database')
)

# Generate RTF and save to file
doc_all_pages.write_rtf("../rtf/formatting_page_all_pages.rtf")
print("RTF document created: ../rtf/formatting_page_all_pages.rtf")

title_count = doc_all_pages.rtf_encode().count('Adverse Events Summary by Treatment')
footnote_count = doc_all_pages.rtf_encode().count('Abbreviations:')
source_count = doc_all_pages.rtf_encode().count('ADAE Dataset')

print(f"All components on all pages:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")
```

<embed src="../pdf/formatting_page_all_pages.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 5: Custom Combination

``` python
# Custom combination: title everywhere, footnote on first page, source on last page
doc_custom = RTFDocument(
    df=df.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'AESER', 'AEREL']),
    rtf_page=RTFPage(
        nrow=15,
        page_title="all",        # Title on all pages
        page_footnote="first",   # Footnote on first page only
        page_source="last"       # Source on last page only
    ),
    rtf_title=RTFTitle(text='Adverse Events Summary by Treatment'),
    rtf_footnote=RTFFootnote(text='Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related'),
    rtf_source=RTFSource(text='Source: ADAE Dataset from Clinical Trial Database')
)

# Generate RTF and save to file
doc_custom.write_rtf("../rtf/formatting_page_custom.rtf")
print("RTF document created: ../rtf/formatting_page_custom.rtf")

title_count = doc_custom.rtf_encode().count('Adverse Events Summary by Treatment')
footnote_count = doc_custom.rtf_encode().count('Abbreviations:')
source_count = doc_custom.rtf_encode().count('ADAE Dataset')

print(f"Custom combination:")
print(f"  Title appears {title_count} time(s) (all pages)")
print(f"  Footnote appears {footnote_count} time(s) (first page only)")
print(f"  Source appears {source_count} time(s) (last page only)")
```

<embed src="../pdf/formatting_page_custom.pdf" style="width:100%; height:400px" type="application/pdf">

## Single-Page Documents

For single-page documents, all components appear regardless of the
`page_title`, `page_footnote`, and `page_source` settings:

``` python
# Small dataset that fits on one page
small_df = df.head(10)

doc_single_page = RTFDocument(
    df=small_df.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'AESER', 'AEREL']),
    rtf_page=RTFPage(
        nrow=50,                 # Large enough to fit all data on one page
        page_title="last",       # This setting is ignored for single-page docs
        page_footnote="first",   # This setting is ignored for single-page docs
        page_source="all"        # This setting is ignored for single-page docs
    ),
    rtf_title=RTFTitle(text='Adverse Events Summary by Treatment'),
    rtf_footnote=RTFFootnote(text='Abbreviations: USUBJID=Subject ID, TRTA=Treatment, AEDECOD=Adverse Event, AESEV=Severity, AESER=Serious, AEREL=Related'),
    rtf_source=RTFSource(text='Source: ADAE Dataset from Clinical Trial Database')
)

rtf_single = doc_single_page.rtf_encode()

title_count = rtf_single.count('Adverse Events Summary by Treatment')
footnote_count = rtf_single.count('Abbreviations:')
source_count = rtf_single.count('ADAE Dataset')

print(f"Single-page document:")
print(f"  Title appears {title_count} time(s)")
print(f"  Footnote appears {footnote_count} time(s)")
print(f"  Source appears {source_count} time(s)")
print("  All components appear once regardless of page placement settings")
```

## Validation

The `RTFPage` class validates the placement options:

``` python
# Valid options
valid_options = ["first", "last", "all"]

print("Valid options for page_title, page_footnote, and page_source:")
for option in valid_options:
    print(f"  - '{option}'")

# Invalid options will raise ValueError
try:
    invalid_page = RTFPage(page_title="invalid")
except ValueError as e:
    print(f"\nValidation error: {e}")
```

## Summary

| Parameter | Description | Default | Options |
|----|----|----|----|
| `page_title` | Controls where titles appear | `"all"` | `"first"`, `"last"`, `"all"` |
| `page_footnote` | Controls where footnotes appear | `"last"` | `"first"`, `"last"`, `"all"` |
| `page_source` | Controls where sources appear | `"last"` | `"first"`, `"last"`, `"all"` |

These settings provide fine-grained control over component placement in
multi-page documents, allowing you to create professional reports that
meet specific formatting requirements for regulatory submissions and
clinical reporting.
