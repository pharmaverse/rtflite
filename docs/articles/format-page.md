# Page format

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

This article demonstrates how to control component placement in multi-page
documents using rtflite.

When generating multi-page RTF documents, you may want to control where titles,
footnotes, and sources appear. The `RTFPage` class provides three parameters
to control this behavior:

- `page_title`: Controls where titles appear ("first", "last", "all")
- `page_footnote`: Controls where footnotes appear ("first", "last", "all")
- `page_source`: Controls where sources appear ("first", "last", "all")

## Default behavior

By default:

- Titles appear on **all pages** (`page_title="all"`)
- Footnotes appear on the **last page only** (`page_footnote="last"`)
- Sources appear on the **last page only** (`page_source="last"`)

## Examples

### Basic setup

```python exec="on" source="above" session="default"
from importlib.resources import files

import polars as pl

from rtflite import RTFDocument, RTFFootnote, RTFPage, RTFSource, RTFTitle
```

```python exec="on" source="above" session="default"
# Load the adverse events dataset
data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path).head(30)
```

### Example 1: default behavior

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Default: title on all pages, footnote and source on last page
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

# Generate RTF and save to file
doc_default.write_rtf("format-page-default.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("format-page-default.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/format-page-default.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 2: title on first page only

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Title on first page only, footnote and source on last page
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

# Save to RTF file
doc_title_first.write_rtf("format-page-title-first.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("format-page-title-first.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/format-page-title-first.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 3: footnote on first page

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Title on first page (default), footnote on first page, source on last page
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

# Save to RTF file
doc_footnote_first.write_rtf("format-page-footnote-first.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("format-page-footnote-first.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/format-page-footnote-first.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 4: all components on all pages

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# All components on all pages
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

# Save to RTF file
doc_all_pages.write_rtf("format-page-all-pages.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("format-page-all-pages.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/format-page-all-pages.pdf" style="width:100%; height:400px" type="application/pdf">

### Example 5: custom combination

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Custom combination: title everywhere, footnote on first page, source on last page
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

# Save to RTF file
doc_custom.write_rtf("format-page-custom.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("format-page-custom.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/format-page-custom.pdf" style="width:100%; height:400px" type="application/pdf">
