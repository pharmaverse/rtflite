import polars as pl

import rtflite as rtf

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

doc_formats = rtf.RTFDocument(
    df=df_formats,
    rtf_body=rtf.RTFBody(
        text_format=("", "b", "i", "bi", "u", "s"),
    ),
)

doc_formats.write_rtf("../rtf/text_format_styles.rtf")

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

doc_font_align = rtf.RTFDocument(
    df=df_font_align,
    rtf_body=rtf.RTFBody(
        text_justification=("l", "c", "r", "j"),
        text_font_size=(12, 14, 10, 11),
    ),
)

doc_font_align.write_rtf("../rtf/text_font_size_alignment.rtf")

color_demo = [
    ["Normal", "Black text on white"],
    ["Warning", "Orange text for caution"],
    ["Error", "Red text for alerts"],
    ["Info", "Blue text for information"],
]

df_colors = pl.DataFrame(color_demo, schema=["status", "description"], orient="row")
print(df_colors)

doc_colors = rtf.RTFDocument(
    df=df_colors,
    rtf_body=rtf.RTFBody(
        text_color=("black", "orange", "red", "blue"),
    ),
)

doc_colors.write_rtf("../rtf/text_color.rtf")

indent_demo = [
    ["Main section", "No indent"],
    ["First level subsection", "300 twips indent"],
    ["Second level detail", "600 twips indent"],
    ["Third level item", "900 twips indent"],
]

df_indent = pl.DataFrame(indent_demo, schema=["level", "description"], orient="row")
print(df_indent)

doc_indent = rtf.RTFDocument(
    df=df_indent,
    rtf_body=rtf.RTFBody(
        text_justification="l",
        text_indent_first=(0, 300, 600, 900),
    ),
)

doc_indent.write_rtf("../rtf/text_indentation.rtf")
