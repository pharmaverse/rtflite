# Table components

Components for creating table structures, spanning rows, and embedded figures.

## RTFBody

Configures table bodies, including grouping, spanning rows, and metadata-driven pagination.

::: rtflite.input.RTFBody
    options:
      show_root_heading: false
      show_source: false

## RTFColumnHeader

Column header definitions. Supports multi-row headers via nested sequences.

::: rtflite.input.RTFColumnHeader
    options:
      show_root_heading: false
      show_source: false

## RTFFigure

Embeds figures and images alongside or in place of tabular content.

::: rtflite.input.RTFFigure
    options:
      show_root_heading: false
      show_source: false

## Row components

Lower-level components for constructing rows and cells manually when needed.

### Row

::: rtflite.row.Row
    options:
      show_root_heading: false
      show_source: false

### Cell

::: rtflite.row.Cell
    options:
      show_root_heading: false
      show_source: false

### Border

::: rtflite.row.Border
    options:
      show_root_heading: false
      show_source: false
