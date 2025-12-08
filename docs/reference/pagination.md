# Pagination

Metadata-driven pagination utilities and strategies used by the unified encoder.

## RTFPagination

Core pagination settings used to calculate available space on each page.

::: rtflite.pagination.RTFPagination
    options:
      show_root_heading: false
      show_source: false

## PageBreakCalculator

Calculates row metadata, page assignments, and optimal break points.

::: rtflite.pagination.PageBreakCalculator
    options:
      show_root_heading: false
      show_source: false

## Pagination contexts and registry

::: rtflite.pagination.PaginationContext
    options:
      show_root_heading: false
      show_source: false

::: rtflite.pagination.PageContext
    options:
      show_root_heading: false
      show_source: false

::: rtflite.pagination.StrategyRegistry
    options:
      show_root_heading: false
      show_source: false

::: rtflite.pagination.PaginationStrategy
    options:
      show_root_heading: false
      show_source: false

## Built-in strategies

::: rtflite.pagination.strategies.defaults.DefaultPaginationStrategy
    options:
      show_root_heading: false
      show_source: false

::: rtflite.pagination.strategies.grouping.PageByStrategy
    options:
      show_root_heading: false
      show_source: false

::: rtflite.pagination.strategies.grouping.SublineStrategy
    options:
      show_root_heading: false
      show_source: false

## Page feature processing

::: rtflite.pagination.processor.PageFeatureProcessor
    options:
      show_root_heading: false
      show_source: false
