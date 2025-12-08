# Text & formatting

Base attribute models and utilities for styling text and table cells.

## Text attributes

Shared text styling options consumed by headers, footers, titles, and table cells.

::: rtflite.attributes.TextAttributes
    options:
      show_root_heading: false
      show_source: false

## Table attributes

Table-specific attributes layered on top of text styling (borders, column widths, pagination flags).

::: rtflite.attributes.TableAttributes
    options:
      show_root_heading: false
      show_source: false

## Broadcast value

Utility for broadcasting scalar or vector values across table dimensions.

::: rtflite.attributes.BroadcastValue
    options:
      show_root_heading: false
      show_source: false

## Text content

Low-level text container used inside custom rows and cells.

::: rtflite.row.TextContent
    options:
      show_root_heading: false
      show_source: false
