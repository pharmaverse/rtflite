# Pagination

This document summarizes the pagination feature implementation in rtflite, designed to match r2rtf behavior for automatic table splitting across multiple pages.

## Overview

The pagination feature automatically splits large tables across multiple RTF pages when the content exceeds the specified number of rows per page (`nrow`). This ensures tables are properly formatted for regulatory submissions and professional documents.

## Key features

### Automatic pagination

- **Automatic triggering**: Pagination activates when table content exceeds `nrow` limit
- **Default `nrow` values**:
  - Portrait orientation: 40 rows per page
  - Landscape orientation: 24 rows per page
- **No manual configuration required**: Users don't need to specify `nrow` explicitly

### Page break handling

- **Proper RTF encoding**: Uses `{\pard\fs2\par}\page{\pard\fs2\par}` format
- **Page setup inclusion**: Each new page includes paper size and margin settings
- **Correct positioning**: Page breaks occur right before column headers of next page

### Border management

The pagination system implements a three-tier border hierarchy matching r2rtf design:

1. **`rtf_page.border_first/border_last`**: Controls borders for the entire table
   - `border_first`: Applied to first row of first page (default: "double")
   - `border_last`: Applied to last row of last page (default: "double")

2. **`rtf_body.border_first/border_last`**: Controls borders for each page
   - `border_first`: Applied to first row of each non-first page (default: "single")
   - `border_last`: Applied to last row of each non-last page (default: "single")

3. **`rtf_body.border_top/bottom/left/right`**: Controls borders for individual cells
   - Standard cell borders maintained throughout the table

### Column header repetition

- **Automatic repetition**: Column headers repeat on each page by default
- **Proper border application**: Column headers receive appropriate page-level borders
- **Multi-level headers**: Supports complex multi-row column header structures

## Implementation details

### Core components

#### 1. Pagination detection

```python
def _needs_pagination(self) -> bool:
    """Check if document needs pagination based on content size and page limits"""
    # Creates pagination instance to calculate rows needed
    # Returns True if total_rows > nrow
```

#### 2. Page break generation

```python
def _rtf_page_break_encode(self) -> str:
    """Generate proper RTF page break sequence matching r2rtf format"""
    # Returns: {\pard\fs2\par}\page{\pard\fs2\par} + page setup
```

#### 3. Border logic application

```python
def _apply_pagination_borders(self, rtf_attrs, page_info, total_pages) -> TableAttributes:
    """Apply proper borders for paginated context following r2rtf design"""
    # Implements the three-tier border hierarchy
```

#### 4. Content distribution

- Uses `RTFPagination`, `PageBreakCalculator`, and `ContentDistributor` classes
- Handles page-by grouping and content splitting
- Maintains data integrity across page boundaries

### RTF structure

Each paginated document follows this structure:

```rtf
[Page 1]
{\rtf1\ansi...}           # RTF header
{\fonttbl...}             # Font table
\paperw...\paperh...      # Page setup
\margl...\margr...        # Margins
[Title content]           # Optional title
[Column headers]          # With page-level borders
[Table rows 1-nrow]       # Data content

[Page 2+]
{\pard\fs2\par}\page{\pard\fs2\par}  # Page break
\paperw...\paperh...      # Page setup (repeated)
\margl...\margr...        # Margins (repeated)
[Title content]           # Optional (based on page_title_location)
[Column headers]          # Repeated with appropriate borders
[Table rows nrow+1-2*nrow] # Continued data content
...
```

## Usage examples

### Basic automatic pagination

```python
import rtflite as rtf
import polars as pl

# Large dataset (>40 rows for portrait)
df = pl.DataFrame({"col1": range(100), "col2": range(100, 200)})

doc = rtf.RTFDocument(
    df=df,
    # rtf_page uses defaults: portrait, nrow=40
    rtf_column_header=[
        rtf.RTFColumnHeader(text=["Column 1", "Column 2"])
    ],
    rtf_body=rtf.RTFBody()
)

doc.write_rtf("paginated_table.rtf")  # Automatically creates ~3 pages
```

### Custom page settings

```python
doc = rtf.RTFDocument(
    df=df,
    rtf_page=rtf.RTFPage(
        orientation="landscape",  # nrow=24 by default
        border_first="double",    # Entire table start border
        border_last="double"      # Entire table end border
    ),
    rtf_body=rtf.RTFBody(
        border_first=[["single"]],  # Each page start border
        border_last=[["single"]],   # Each page end border
    )
)
```

### Forced pagination

```python
doc = rtf.RTFDocument(
    df=small_df,  # Even small datasets can be paginated
    rtf_page=rtf.RTFPage(nrow=10),  # Force 10 rows per page
    rtf_body=rtf.RTFBody()
)
```

## Technical architecture

### Class relationships

```
RTFDocument
|-- _needs_pagination() -> bool
|-- _create_pagination_instance() -> (RTFPagination, ContentDistributor)
|-- _rtf_page_break_encode() -> str
|-- _apply_pagination_borders() -> TableAttributes
|-- _rtf_encode_paginated() -> str  # Main paginated encoding
+-- _rtf_body_encode_paginated() -> List[str]  # Body-only paginated encoding
```

### Border application flow

1. **Page content distribution**: Content split across pages
2. **Border calculation**: Determine appropriate borders for each page position
3. **Column header processing**: Apply page-level borders to headers
4. **Body content processing**: Apply pagination borders to table body
5. **RTF generation**: Encode with proper border codes

## RTF border codes

| Border Type | RTF Code | Usage |
|-------------|----------|-------|
| Single | `\brdrs` | Page boundaries, regular cells |
| Double | `\brdrdb` | Table start/end boundaries |
| None | `""` | No border |

## Configuration options

### RTFPage settings

- `orientation`: "portrait" or "landscape"
- `nrow`: Rows per page (auto-calculated if not specified)
- `border_first`: Border style for entire table start
- `border_last`: Border style for entire table end
- `page_title_location`: "all", "first", or "last"
- `page_footnote_location`: "all", "first", or "last"
- `page_source_location`: "all", "first", or "last"

### RTFBody settings

- `border_first`: Border style for each page start
- `border_last`: Border style for each page end
- `border_top/bottom/left/right`: Individual cell borders
- `pageby_header`: Whether to repeat column headers (default: True)

## Known limitations and future enhancements

### Current limitations

1. **Fixed row calculation**: Pagination based on row count, not actual content height
2. **Simple page breaks**: No widow/orphan control
3. **Limited page-by support**: Basic grouping functionality

### Potential enhancements

1. **Content-aware pagination**: Calculate page breaks based on actual content height
2. **Advanced page-by features**: More sophisticated grouping and page break controls
3. **Widow/orphan control**: Prevent isolated rows at page boundaries
4. **Custom page break locations**: Allow manual page break insertion
5. **Page numbering**: Add automatic page number generation
6. **Conditional formatting**: Page-specific formatting rules
