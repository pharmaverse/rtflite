# Assemble

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

This article demonstrates how to assemble multiple RTF files into a single RTF or DOCX file using rtflite.

## Prerequisites

To enable DOCX support, install rtflite with the `docx` extra:

```bash
pip install rtflite[docx]
```

## Define input files

```python exec="on" source="above" session="default"
from pathlib import Path
from rtflite import assemble_docx, assemble_rtf, concatenate_docx
```

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
input_files = [
    "example-ae-summary.rtf",
    "example-efficacy.rtf",
]
```

## Assemble into RTF

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
assemble_rtf(input_files, "combined-rtf.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined-rtf.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined-rtf.pdf" style="width:100%; height:400px" type="application/pdf">

## Assemble into DOCX with toggle fields

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
assemble_docx(input_files, "combined-docx.docx")
```

Open `combined-docx.docx` in Word and refresh fields to resolve the
`INCLUDETEXT` placeholders. Without opening in Word, the placeholders
appear as `Error! Reference source not found.`
because `python-docx` does not evaluate those fields.

!!! note
    The `assemble_docx` workflow intentionally mirrors how medical writers
    paste hyperlinks into CSR sections. After the link is in place,
    toggling fields or running **Update Field** in Word reconnects the
    assembled file to the original TLFs without additional copy-paste work.
    This hybrid approach, which relies on Word's field codes, is documented
    in the [r4csr book](https://r4csr.org/tlf-assemble.html).

Another example to assemble into DOCX with mixed orientation pages (portrait, landscape):

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
assemble_docx(
    input_files,
    "combined-mixed.docx",
    landscape=[False, True]
)
```

Open `combined-mixed.docx` in Word and update fields to pull in the portrait
and landscape tables. Until the fields are refreshed, you will see the same
`Error! Reference source not found.` placeholders.

## Assemble into DOCX without toggle fields

`RTFDocument.write_docx` (added in rtflite 2.2.0) creates DOCX files for
individual rtflite tables directly.
Use `concatenate_docx` (added in rtflite 2.3.0, powered by `python-docx`)
to concatenate the DOCX outputs when you need final files without manual
field refreshes, similar to `assemble_rtf`.

Generate example DOCX tables:

```python exec="on" source="above" session="default"
from importlib.resources import files

import polars as pl
import rtflite as rtf

ae_path = files("rtflite.data").joinpath("adae.parquet")
ae = pl.read_parquet(ae_path)
ae_summary = (
    ae.group_by(["TRTA", "AEDECOD"])
    .agg(pl.len().alias("n"))
    .pivot(values="n", index="AEDECOD", on="TRTA")
    .fill_null(0)
    .sort("AEDECOD")
)
```

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Two portrait tables
portrait_doc1 = rtf.RTFDocument(
    df=ae_summary.head(12),
    rtf_title=rtf.RTFTitle(text="Adverse Events (Portrait)"),
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
portrait_doc1.write_docx("portrait-ae-1.docx")

portrait_doc2 = rtf.RTFDocument(
    df=ae_summary.slice(12, 12),
    rtf_title=rtf.RTFTitle(text="Adverse Events (Portrait, Part 2)"),
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
portrait_doc2.write_docx("portrait-ae-2.docx")

# One landscape table
landscape_doc = rtf.RTFDocument(
    df=ae_summary.head(20),
    rtf_page=rtf.RTFPage(
        orientation="landscape",
        nrow=10,
        border_first="dashed",
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
landscape_doc.write_docx("landscape-ae.docx")
```

### Concatenate two portrait DOCX files

Use `concatenate_docx` to start from the first DOCX (avoids a blank leading
page) and add a new section per file so each starts on its own page with the
correct orientation.

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
portrait_files = [
    "portrait-ae-1.docx",
    "portrait-ae-2.docx",
]

concatenate_docx(
    portrait_files,
    "combined-python-docx.docx",
)
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined-python-docx.docx", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined-python-docx.pdf" style="width:100%; height:400px" type="application/pdf">

### Concatenate portrait + landscape DOCX files

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
files_with_orientation = [
    ("portrait-ae-1.docx", False),
    ("landscape-ae.docx", True),
]

concatenate_docx(
    [path for path, _ in files_with_orientation],
    "combined-python-docx-mixed.docx",
    landscape=[is_landscape for _, is_landscape in files_with_orientation],
)
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined-python-docx-mixed.docx", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined-python-docx-mixed.pdf" style="width:100%; height:400px" type="application/pdf">
