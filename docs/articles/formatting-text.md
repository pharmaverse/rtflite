# Text formatting


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

This article demonstrates advanced text formatting capabilities in
rtflite. It covers fonts, colors, alignment, indentation, special
characters, and comprehensive formatting for clinical documentation.

## Overview

Advanced text formatting is essential for creating production ready
clinical documents that meet regulatory standards. Key formatting
features include:

- Text format styles (bold, italic, underline, superscript, subscript)
- Font sizes and alignment options (left, center, right, justified)  
- Text colors and background colors
- Indentation and spacing control
- Special symbols and mathematical notation
- Inline formatting combinations

## Imports

``` python
import polars as pl
import rtflite as rtf
```

## Text Style

Demonstrate core text formatting options:

``` python
# Create formatting demonstration data
format_demo = [
    ["Normal", "", "Regular text", "Default body text"],
    ["Bold", "b", "Bold text", "Emphasis and headers"],
    ["Italic", "i", "Italic text", "Special terms, notes"],
    ["Bold Italic", "bi", "Bold italic text", "Maximum emphasis"],
    ["Underline", "u", "Underlined text", "Highlight important items"],
    ["Strikethrough", "s", "Crossed out", "Deprecated content"]
]

df_formats = pl.DataFrame(format_demo, schema=["format_type", "code", "example", "usage"])
print(df_formats)
```

Apply text formatting using column-based approach:

> Using tuples `()` allow user define parameters by row.

``` python
# Apply text formatting by row
doc_formats = rtf.RTFDocument(
    df=df_formats,
    rtf_body=rtf.RTFBody(
        text_format=("", "b", "i", "bi", "u", "s"),  
    )
)

doc_formats.write_rtf("../rtf/text_format_styles.rtf")
```

<embed src="../pdf/text_format_styles.pdf" style="width:100%; height:400px" type="application/pdf">

## Font Size and Alignment

Demonstrate font size variations and text alignment:

``` python
# Create font size and alignment data
font_align_demo = [
    ["Left", "12pt", "l"],
    ["Center", "14pt", "c"],
    ["Right", "10pt", "r"],
    ["Justified", "11pt", "j"],
]

df_font_align = pl.DataFrame(font_align_demo, schema=["alignment", "size", "text_justification"])
print(df_font_align)
```

``` python
# Apply font sizes and alignment
doc_font_align = rtf.RTFDocument(
    df=df_font_align,
    rtf_body=rtf.RTFBody(
        text_justification=("l", "c", "r", "j"), 
        text_font_size=(12, 14, 10, 11), 
    )
)

doc_font_align.write_rtf("../rtf/text_font_size_alignment.rtf")
```

<embed src="../pdf/text_font_size_alignment.pdf" style="width:100%; height:400px" type="application/pdf">

## Text Color

> the feature is under development
> (https://github.com/pharmaverse/rtflite/issues/2)

Demonstrate text and background color applications:

``` python
# Create color demonstration data
color_demo = [
    ["Normal", "Black text on white"],
    ["Warning", "Orange text for caution"],
    ["Error", "Red text for alerts"],
    ["Info", "Blue text for information"]
]

df_colors = pl.DataFrame(color_demo, schema=["status", "description"])
print(df_colors)
```

``` python
# Apply text colors
doc_colors = rtf.RTFDocument(
    df=df_colors,
    rtf_body=rtf.RTFBody(
        text_color=("black", "orange", "red", "blue"),
    )
)

doc_colors.write_rtf("../rtf/text_color.rtf")
```

<embed src="../pdf/text_color.pdf" style="width:100%; height:400px" type="application/pdf">

## Indentation

Show indentation options for hierarchical content:

``` python
# Create indentation demonstration data
indent_demo = [
    ["Main section", "No indent"],
    ["First level subsection", "300 twips indent"],
    ["Second level detail", "600 twips indent"],
    ["Third level item", "900 twips indent"]
]

df_indent = pl.DataFrame(indent_demo, schema=["level", "description"])
print(df_indent)
```

``` python
# Apply indentation levels
doc_indent = rtf.RTFDocument(
    df=df_indent,
    rtf_body=rtf.RTFBody(
        text_justification = "l",
        text_indent_first=(0, 300, 600, 900),
    )
)

doc_indent.write_rtf("../rtf/text_indentation.rtf")
```

<embed src="../pdf/text_indentation.pdf" style="width:100%; height:400px" type="application/pdf">
