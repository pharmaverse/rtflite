# Text & formatting

Base attribute models and utilities for styling text and table cells.

## Text attributes

Shared text styling options consumed by headers, footers, titles, and table cells.

::: rtflite.attributes.TextAttributes

## Table attributes

Table-specific attributes layered on top of text styling (borders, column widths, pagination flags).

::: rtflite.attributes.TableAttributes

## Broadcast value

Utility for broadcasting scalar or vector values across table dimensions.

::: rtflite.attributes.BroadcastValue

## Text content

Low-level text container used inside custom rows and cells.

::: rtflite.row.TextContent

## Rich text

Inline formatting within a single table cell, using `{tag ...}` markers
(inspired by `r2rtf::rtf_rich_text()`).

```python
import polars as pl
import rtflite as rtf

theme = {".warn": {"format": "b", "color": "red", "font_size": 10.5}}
df = pl.DataFrame({
    "Response": pl.Series(
        ["plain", rtf.rich_text("n=50 {.warn (75%)}", theme=theme)],
        dtype=pl.Object,
    )
})
document = rtf.RTFDocument(df=df)
```

Theme keys include the leading dot, such as `".warn"`. Font identifiers are
1–10, using the document's font table. Font sizes must be finite positive
multiples of 0.5 points, matching RTF's half-point units.

Use raw Python strings for literal escapes: `rtf.rich_text(r"{b \{value\}}")`
displays **{value}**, and `rtf.rich_text(r"\\alpha")` displays a literal
backslash followed by `alpha`. Unescaped LaTeX commands still follow the
cell's `text_convert` setting. Superscript and subscript tags can nest; the
inner script overrides the outer one, which resumes after the inner tag closes.

Mixed plain/rich columns require `pl.Object`. `group_by` compares rich values
by their plain text and retains the original formatting when repeating labels
at page boundaries. `page_by` and `subline_by` headings also retain rich spans.

Pagination estimates account for explicit newlines, inherited cell fonts,
and inline font/size overrides. Tall spans reserve extra base-font row units.
Wrapping remains an estimate based on text width; final line breaks depend on
the RTF reader. `str(value)` returns the text without formatting markers.

::: rtflite.rich_text.rich_text

::: rtflite.rich_text.RichText
