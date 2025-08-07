# Row format

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

This article demonstrates row-level formatting capabilities in rtflite.
It covers borders, cell alignment, column widths, and text formatting
for creating professional tables.

## Overview

Row-level formatting provides granular control over table appearance:

- Border styles (single, double, thick)
- Column width control with relative sizing

## Imports

```python exec="on" source="above" session="default"
import polars as pl

import rtflite as rtf
```

## Border styles

> Please refer to the `rtf` output. The converted PDF version has known issues
> for some border types due to converter (LibreOffice) limitations.

Demonstrate different border types:

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Create border demonstration data from BORDER_CODES
border_data = [
    [border_type, f"Example of {border_type or 'no'} border"]
    for border_type in rtf.attributes.BORDER_CODES.keys()
]

df_borders = pl.DataFrame(
    border_data, schema=["border_type", "description"], orient="row"
)

# Apply different border styles to each row
doc_borders = rtf.RTFDocument(
    df=df_borders,
    rtf_body=rtf.RTFBody(
        border_bottom=tuple(rtf.attributes.BORDER_CODES.keys()),
    ),
)

doc_borders.write_rtf("row-border-styles.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("row-border-styles.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/row-border-styles.pdf" style="width:100%; height:400px" type="application/pdf">

## Column widths

Control relative column widths:

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Create width demonstration data
width_demo = [
    ["Narrow", "Standard Width", "Wide Column"],
    ["1.0", "2.0", "3.0"],
    ["Small", "Medium text content", "Much wider column for longer text"],
]

df_widths = pl.DataFrame(width_demo, schema=["narrow", "standard", "wide"])

# Apply different column width ratios
doc_widths = rtf.RTFDocument(
    df=df_widths,
    rtf_body=rtf.RTFBody(
        col_rel_width=[1.0, 2.0, 3.0],  # Relative width ratios
    ),
)

doc_widths.write_rtf("row-column-widths.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("row-column-widths.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/row-column-widths.pdf" style="width:100%; height:400px" type="application/pdf">
