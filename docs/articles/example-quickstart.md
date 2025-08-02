# Introduction to rtflite


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

## Overview

`rtflite` is a Python package to create production ready tables and
figures in RTF format. The Python package is designed to

- provide simple “verb” functions that correspond to each component of a
  table, to help you translate data frame to table in RTF file.
- enable method chaining.
- only focus on **table format**. Data manipulation and analysis should
  be handled by other Python packages. (e.g., `polars`, `pandas`)
- `rtflite` minimizes package dependency

Before creating an RTF table we need to:

- Figure out table layout.
- Split the layout into small tasks in the form of a computer program.
- Execute the program.

This document introduces `rtflite` basic set of tools, and show how to
transfer data frames into Table, Listing, and Figure (TLFs).

## Data: Adverse Events

To explore the basic RTF generation verbs in `rtflite`, we will use the
dataset `adae.parquet`. This dataset contain adverse events (AE)
information from a clinical trial.

Below is the meaning of relevant variables.

- USUBJID: Unique Subject Identifier
- TRTA: Actual Treatment
- AEDECOD: Dictionary-Derived Term

``` python
from importlib.resources import files
import polars as pl
import rtflite as rtf
```

``` python
# Load adverse events data
data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)

df.select(['USUBJID', 'TRTA', 'AEDECOD']).head(4)
```

## Table ready data

`polars` package is used for data manipulation to create a data frame
that contains all the information we want to add in an RTF table.

> Please note other packages can also be used for the same purpose.

In this AE example, we provide number of subjects with each type of AE
by treatment group.

``` python
tbl = (
    df.
    group_by(['TRTA', 'AEDECOD'])
    .agg(pl.len().alias('n'))
    .sort("TRTA")
    .pivot(values='n', index='AEDECOD', on='TRTA')
    .fill_null(0)
    .sort('AEDECOD')  # Sort by adverse event name to match R output
)
print(tbl.head(4))
```

## Single table verbs

`rtflite` aims to provide one function for each type of table layout.
Commonly used verbs includes:

- `RTFPage`: RTF page information
- `RTFTitle`: RTF title information
- `RTFColumnHeader`: RTF column header information
- `RTFBody`: RTF table body information
- `RTFFootnote`: RTF footnote information
- `RTFSource`: RTF data source information

All these verbs are designed to enables usage of method chaining. A full
list of all functions can be found in the [package
reference](https://merck.github.io/rtflite/reference/).

## Simple Example

A minimal example below illustrates how to combine verbs to create an
RTF table.

- `RTFBody()` defines table body layout.
- `RTFDocument()` transfers table layout information into RTF syntax.
- `write_rtf()` saves RTF encoding into a file with file extension
  `.rtf`.

``` python
# Create simple RTF document
doc = rtf.RTFDocument(
    df=tbl.head(6),
    rtf_body=rtf.RTFBody()  # Step 1: Add table attributes
)

# Step 2 & 3: Convert to RTF and write to file
doc.write_rtf("../rtf/intro-ae1.rtf")
```

## Column Width

If we want to adjust the width of each column to provide more space to
the first column, this can be achieved by updating `col_rel_width` in
`RTFBody`.

The input of `col_rel_width` is a list with same length for number of
columns. This argument defines the relative length of each column within
a pre-defined total column width.

In this example, the defined relative width is 3:2:2:2. Only the ratio
of `col_rel_width` is used. Therefore it is equivalent to use
`col_rel_width = [6,4,4,4]` or `col_rel_width = [1.5,1,1,1]`.

``` python
# Create RTF document with custom column widths
doc = rtf.RTFDocument(
    df=tbl.head(6),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 2, 2, 2]  # define relative width
    )
)

doc.write_rtf("../rtf/intro-ae2.rtf")
```

## Column Headers

In `RTFColumnHeader`, `text` argument is used to provide content of
column header. We used a list to separate the columns.

``` python
# Create RTF document with column headers
doc = rtf.RTFDocument(
    df=tbl.head(6),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Adverse Events", "Placebo", "Xanomeline High Dose", "Xanomeline Low Dose"],
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 2, 2, 2]
    )
)

doc.write_rtf("../rtf/intro-ae3.rtf")
```

We also allow column headers be displayed in multiple lines. If an empty
column name is needed for a column, you can insert an empty string;
e.g., `["name 1", "", "name 3"]`.

In `RTFColumnHeader`, the `col_rel_width` can be used to align column
header with different number of columns.

By using `RTFColumnHeader` with `col_rel_width`, one can customize
complicated column headers. If there are multiple pages, column header
will repeat at each page by default.

``` python
# Create RTF document with multi-line column headers
doc = rtf.RTFDocument(
    df=tbl.head(50),
    rtf_page=rtf.RTFPage(nrow = 15),
    rtf_column_header=[
        rtf.RTFColumnHeader(
            text=[" ", "Treatment"],
            col_rel_width=[3, 3]
        ),
        rtf.RTFColumnHeader(
            text=["Adverse Events", "Placebo", "Xanomeline High Dose", "Xanomeline Low Dose"],
            col_rel_width=[3, 1, 1, 1]
        )
    ],
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 1, 1, 1]
    )
)

doc.write_rtf("../rtf/intro-ae4.rtf")
```

## Titles, Footnotes, and Data Source

RTF documents can include additional components to provide context and
documentation:

- `RTFTitle`: Add document titles and subtitles
- `RTFFootnote`: Add explanatory footnotes
- `RTFSource`: Add data source attribution

``` python
# Create RTF document with titles, footnotes, and source
doc = rtf.RTFDocument(
    df=tbl.head(15),
    rtf_title=rtf.RTFTitle(
        text=[
            "Summary of Adverse Events by Treatment Group",
            "Safety Analysis Set"
        ]
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
            "Events are sorted alphabetically by preferred term."
        ]
    ),
    rtf_source=rtf.RTFSource(
        text="Source: ADAE dataset, Data cutoff: 01JAN2023"
    ),
)

doc.write_rtf("../rtf/intro-ae5.rtf")
```

Note the use of `\\line` in column headers to create line breaks within
cells.

## Text Formatting and Alignment

`rtflite` supports various text formatting options:

- **Text formatting**: Bold (`b`), italic (`i`), underline (`u`),
  strikethrough (`s`)
- **Text alignment**: Left (`l`), center (`c`), right (`r`), justify
  (`j`)
- **Font properties**: Font size, font family

``` python
# Create RTF document with text formatting and alignment
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
```

## Border Customization

Table borders can be customized extensively:

- **Border styles**: `single`, `double`, `thick`, `dotted`, `dashed`
- **Border sides**: `border_top`, `border_bottom`, `border_left`,
  `border_right`
- **Page borders**: `border_first`, `border_last` for first/last rows
  across pages

``` python
# Create RTF document with custom borders
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
```

## Page Layout and Orientation

`RTFPage` provides control over page layout:

- **Orientation**: `portrait` or `landscape`
- **Page size**: Custom width and height
- **Margins**: Left, right, top, bottom, header, footer margins
- **Rows per page**: Control pagination with `nrow`

``` python
# Create RTF document with landscape layout
doc = rtf.RTFDocument(
    df=tbl.head(20),
    rtf_page=rtf.RTFPage(
        orientation="landscape",  # Landscape for wider tables
        nrow=10,
        border_first="dashed",   # Dash border for first/last pages
        border_last="dashed"
    ),
    rtf_title=rtf.RTFTitle(
        text="Adverse Events Summary - Landscape Layout"
    ),
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
```

## Cell-level Formatting

Using the BroadcastValue pattern, you can apply formatting to individual
cells:

``` python
# Example of cell-level border control for specific cells
from rtflite.attributes import BroadcastValue

# Create custom border patterns
border_pattern = [
    ["single", "", "single", ""],     # Row 1: borders on columns 1 and 3
    ["", "double", "", "double"],     # Row 2: borders on columns 2 and 4
    ["single", "single", "single", "single"]  # Row 3: borders on all columns
]

doc = rtf.RTFDocument(
    df=tbl.head(3),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Adverse Events", "Placebo", "Xanomeline High Dose", "Xanomeline Low Dose"],
    ),
    rtf_body=rtf.RTFBody(
        col_rel_width=[3, 2, 2, 2],
        border_top=border_pattern  # Apply custom border pattern
    ),
)

doc.write_rtf("../rtf/intro-ae9.rtf")
```

### Multi-page Considerations

For large tables spanning multiple pages, `rtflite` handles:

- Automatic page breaks based on `nrow` setting
- Column header repetition on each page
- Consistent border styling across page boundaries
- Proper footnote and source placement

``` python
# Large table with consistent formatting across pages
doc = rtf.RTFDocument(
    df=tbl.head(50),  
    rtf_page=rtf.RTFPage(
        nrow=15, 
    ),
    rtf_title=rtf.RTFTitle(
        text=[
            "Complete Adverse Events Summary",
            "All Treatment Groups - Multi-page Table"
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
            "Events sorted alphabetically by preferred term."
        ]
    ),
    rtf_source=rtf.RTFSource(
        text="Dataset: ADAE | Cutoff: 01JAN2023" 
    ),
)

doc.write_rtf("../rtf/intro-ae10.rtf")
```
