# Row Format


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

This article demonstrates row-level formatting capabilities in rtflite.
It covers borders, cell alignment, column widths, and text formatting
for creating professional tables.

## Overview

Row-level formatting provides granular control over table appearance:

- Border styles (single, double, thick)
- Column width control with relative sizing

## Imports

``` python
import polars as pl
import rtflite as rtf
```

## Border Styles

> please refer `rtf` output. PDF version has known issue for some border
> type.

Demonstrate different border types:

``` python
# Create border demonstration data from BORDER_CODES
border_data = [
    [border_type, f"Example of {border_type or 'no'} border"] 
    for border_type in rtf.attributes.BORDER_CODES.keys()
]

df_borders = pl.DataFrame(border_data, schema=["border_type", "description"])

# Apply different border styles to each row
doc_borders = rtf.RTFDocument(
    df=df_borders,
    rtf_body=rtf.RTFBody(
        border_bottom=tuple(rtf.attributes.BORDER_CODES.keys()),
    )
)

doc_borders.write_rtf("../rtf/row_border_styles.rtf")
```

<embed src="../pdf/row_border_styles.pdf" style="width:100%; height:400px" type="application/pdf">

## Column Widths

Control relative column widths:

``` python
# Create width demonstration data
width_demo = [
    ["Narrow", "Standard Width", "Wide Column"],
    ["1.0", "2.0", "3.0"],
    ["Small", "Medium text content", "Much wider column for longer text"]
]

df_widths = pl.DataFrame(width_demo, schema=["narrow", "standard", "wide"])

# Apply different column width ratios
doc_widths = rtf.RTFDocument(
    df=df_widths,
    rtf_body=rtf.RTFBody(
        col_rel_width=[1.0, 2.0, 3.0],  # Relative width ratios
    )
)

doc_widths.write_rtf("../rtf/row_column_widths.rtf")
```

<embed src="../pdf/row_column_widths.pdf" style="width:100%; height:400px" type="application/pdf">
