# Text format

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

This article demonstrates advanced text formatting capabilities in rtflite.
It covers fonts, colors, alignment, indentation, special characters,
and comprehensive formatting for clinical documentation.

## Overview

Advanced text formatting is essential for creating production-ready
clinical documents that meet regulatory standards.

Key formatting features include:

- Text format styles (bold, italic, underline, superscript, subscript)
- Font sizes and alignment options (left, center, right, justified)
- Text colors and background colors
- Indentation and spacing control
- Special symbols and mathematical notation
- Inline formatting combinations

## Imports

```python exec="on" source="above" session="default"
import polars as pl

import rtflite as rtf
```

## Text style

Demonstrate core text formatting options:

```python exec="on" source="above" session="default" result="text"
# Create formatting demonstration data
format_demo = [
    ["Normal", "", "Regular text", "Default body text"],
    ["Bold", "b", "Bold text", "Emphasis and headers"],
    ["Italic", "i", "Italic text", "Special terms, notes"],
    ["Bold Italic", "bi", "Bold italic text", "Maximum emphasis"],
    ["Underline", "u", "Underlined text", "Highlight important items"],
    ["Strikethrough", "s", "Crossed out", "Deprecated content"],
]

df_formats = pl.DataFrame(
    format_demo, schema=["format_type", "code", "example", "usage"], orient="row"
)
print(df_formats)
```

Apply text formatting using column-based approach:

> Using tuples `()` allows user to define parameters by row.

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Apply text formatting by row
doc_formats = rtf.RTFDocument(
    df=df_formats,
    rtf_body=rtf.RTFBody(
        text_format=("", "b", "i", "bi", "u", "s"),
    ),
)

doc_formats.write_rtf("text-format-styles.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("text-format-styles.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/text-format-styles.pdf" style="width:100%; height:400px" type="application/pdf">

## Font size and alignment

Demonstrate font size variations and text alignment:

```python exec="on" source="above" session="default" result="text"
# Create font size and alignment data
font_align_demo = [
    ["Left", "12pt", "l"],
    ["Center", "14pt", "c"],
    ["Right", "10pt", "r"],
    ["Justified", "11pt", "j"],
]

df_font_align = pl.DataFrame(
    font_align_demo, schema=["alignment", "size", "text_justification"], orient="row"
)
print(df_font_align)
```

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Apply font sizes and alignment
doc_font_align = rtf.RTFDocument(
    df=df_font_align,
    rtf_body=rtf.RTFBody(
        text_justification=("l", "c", "r", "j"),
        text_font_size=(12, 14, 10, 11),
    ),
)

doc_font_align.write_rtf("text-font-size-alignment.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("text-font-size-alignment.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/text-font-size-alignment.pdf" style="width:100%; height:400px" type="application/pdf">

## Text color

Demonstrate text and background color applications:

```python exec="on" source="above" session="default" result="text"
# Create color demonstration data
color_demo = [
    ["Normal", "Black text on white"],
    ["Warning", "Orange text for caution"],
    ["Error", "Red text for alerts"],
    ["Info", "Blue text for information"],
]

df_colors = pl.DataFrame(color_demo, schema=["status", "description"], orient="row")
print(df_colors)
```

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Apply text colors
doc_colors = rtf.RTFDocument(
    df=df_colors,
    rtf_body=rtf.RTFBody(
        text_color=("black", "orange", "red", "blue"),
    ),
)

doc_colors.write_rtf("text-color.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("text-color.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/text-color.pdf" style="width:100%; height:400px" type="application/pdf">

## Indentation

Show indentation options for hierarchical content:

```python exec="on" source="above" session="default" result="text"
# Create indentation demonstration data
indent_demo = [
    ["Main section", "No indent"],
    ["First level subsection", "300 twips indent"],
    ["Second level detail", "600 twips indent"],
    ["Third level item", "900 twips indent"],
]

df_indent = pl.DataFrame(indent_demo, schema=["level", "description"], orient="row")
print(df_indent)
```

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Apply indentation levels
doc_indent = rtf.RTFDocument(
    df=df_indent,
    rtf_body=rtf.RTFBody(
        text_justification="l",
        text_indent_first=(0, 300, 600, 900),
    ),
)

doc_indent.write_rtf("text-indentation.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("text-indentation.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/text-indentation.pdf" style="width:100%; height:400px" type="application/pdf">
