# Changelog

## rtflite 2.5.1

### Testing

- Migrated the RTF snapshot tests implementation to a proper solution
  `pytest-r-snapshot` to reduce boilerplate code and improve maintainability.
  The legacy fixture generation workflow is removed and the snapshots are
  stored under the standard location `tests/__r_snapshots__/` (#181).

## rtflite 2.5.0

### New features

- Added `RTFDocument.write_html` and `RTFDocument.write_pdf` for exporting RTF
  documents to HTML and PDF via LibreOffice, matching the `write_docx`
  conversion workflow (#176).

### Testing

- Added parameterized tests covering DOCX, HTML, and PDF exports, with a
  new `pdf` extra (`pypdf`) for PDF text extraction.
  Improved LibreOffice availability checks to skip integration tests
  when conversion is not working (#176).

## rtflite 2.4.0

### Breaking changes

- Removed the `executable_path` argument from `RTFDocument.write_docx`; pass
  `converter=LibreOfficeConverter(executable_path=...)` instead (#172).

### Improvements

- `RTFDocument.write_docx` now accepts a `converter=` instance to configure
  LibreOffice invocation (including custom executable paths) and to enable
  reusing a converter across multiple conversions (#172).

### Converters

- `LibreOfficeConverter(executable_path=...)` now accepts `Path` objects
  and resolves executable names via `PATH` when given
  (for example, `"soffice"`) (#172).

## rtflite 2.3.1

### Improvements

- Added `executable_path` parameter to `write_docx()` method (#170).
- Added `/tmp/soffice` and `/tmp/libreoffice` paths for Linux (#170).

## rtflite 2.3.0

### New features

- Added `concatenate_docx` function to merge DOCX outputs without manual
  field refreshes, preserving per-section orientation (#160).

### Testing

- Added DOCX concatenation coverage and centralized optional dependency
  skip markers for `python-docx` and LibreOffice to keep tests gated
  appropriately (#160).

### Documentation

- Updated the assembly article to use `concatenate_docx` in code examples and
  added a reference page for assemble function to the mkdocs site (#160).

## rtflite 2.2.0

### New features

- Added `RTFDocument.write_docx` to export tables as DOCX via LibreOffice,
  with `str`/`Path` input support and automatic parent directory creation (#156).
- Improved `write_rtf` to accept `Path` inputs and create missing output
  directories (#156).

### Documentation

- Expanded DOCX assembly guidance with toggle field caveats and `python-docx`
  concatenation examples (#157).
- Documented installing the `docx` extra in the README and assemble article,
  including `uv sync --extra docx` for developers (#155).

## rtflite 2.1.1

### Bug fixes

- Reduced packaging files size by excluding unnecessary files and directories (#152).
- Fixed an issue when paginating tables with `page_by` and `subline_by` (#152).

## rtflite 2.1.0

### New features

- Added `assemble_rtf` and `assemble_docx` functions for RTF and DOCX assembly (#142).

### Bug fixes

- Fixed an issue where `RTFPage` orientation was not correctly respected during assembly in certain edge cases (#141).

## rtflite 2.0.0

### Breaking changes

- Removed legacy pagination/encoding APIs, including `ContentDistributor`,
  `PageDict`/`AdvancedPaginationService`, and the `SinglePageStrategy`/
  `PaginatedStrategy` classes; dropped backwards-compatibility helpers
  such as `text_convert` and `get_color_index` (#138).

### Refactors

- Introduced a unified rendering pipeline (`UnifiedRTFEncoder`) with a strategy
  registry, page feature processor, and renderer that handle pagination,
  borders, and page headers consistently, including combined `page_by` and
  `subline_by` grouping (#138).
- Simplified public exports by re-exporting `RTFEncodingEngine`,
  `TableAttributes`, `RTFSubline`, and `get_string_width` from the top-level
  package while reorganizing core config/constants imports (#138).

### Testing and documentation

- Added regression tests for combined grouping and `page_by` column alignment,
  and removed obsolete advanced pagination tests; cleaned up RTF doc fixtures
  and trimmed pagination reference docs to match the new architecture (#138).

## rtflite 1.2.0

### Bug fixes

- Fixed `page_by` pagination when using `RTFPage(orientation="landscape")`,
  covering single- and multi-page tables and aligning documentation examples
  (#128, #131, #134).

### Maintenance

- Added GitHub Actions workflow to run `ruff check` for code linting,
  updated GitHub Actions workflows to use `actions/checkout@v6`,
  and updated badges in `README.md` (#133).

## rtflite 1.1.1

### New features

- Enhanced group-by divider filtering functionality to support the
  `-----` syntax (#118).

### Bug fixes

- Fixed text conversion issue for greater than or equal (>=) and less than or
  equal (<=) symbols (#119).

## rtflite 1.1.0

### Python version support

- Added Python 3.14 support by conditionally requiring pyarrow >= 22.0.0
  under Python 3.14 (#114).

### Linting and typing

- Added ruff linter configuration to `pyproject.toml` with popular rule sets
  and fixed all linting issues (#115).
- Refactored type annotations to use built-in generics and abstract base classes
  following modern typing best practices (#107).

### Documentation

- Added pharmaverse badge to the README (#108).
- Added `AGENTS.md` with guidelines for AI coding agents (#109).

### Maintenance

- Updated GitHub Actions workflows to use the latest `checkout` and
  `setup-python` versions (#114).
- Refactored the logo generation script to use ImageMagick, removing the
  R and hexSticker dependency (#111).

## rtflite 1.0.2

### Typing

- Adopted modern typing best practices: use `|` unions instead of
  `Union`/`Optional`, and built-in generics instead of `typing` aliases (#95).
- Resolved all mypy issues; type checks now pass cleanly (#97, #99, #101).
- Added a mypy GitHub Actions workflow for continuous type checking (#100).

### Testing

- Added a developer script to compare current RTF outputs with snapshots
  generated from mkdocs site articles (#102).

### Documentation

- Updated `CLAUDE.md` to replace outdated `.qmd`-based rendering instructions
  with the markdown-exec approach (#93).

## rtflite 1.0.1

### Bug fixes

- Fixed hard-coded font in pagination calculations to properly use
  user-selected fonts (#91).

### Dependencies

- Lowered minimum Pillow version to 8.0.0 with automatic font size type
  coercion to `int` for Pillow < 10.0.0 compatibility (#89).

### Documentation

- Improved readability and technical accuracy of documentation (#85, #86, #87).

## rtflite 1.0.0

This major release marks rtflite as production-ready for table, listing,
and figure generation in RTF format.
It introduces advanced pagination features, enhanced group handling,
complete color support, and significant architectural improvements
for better maintainability and performance.

### New features

- **Advanced pagination features**
    - Added the `subline_by` parameter for creating paragraph headers before each page group.
    - Enhanced `group_by` functionality with hierarchical value suppression within groups.
    - Implemented page context restoration for multi-page tables with `group_by`.

- **Enhanced color system**
    - Complete 657-color support with full r2rtf R package compatibility.

- **Text conversion improvements**
    - Text conversion (LaTeX to Unicode) enabled by default for all components.
    - Better handling of special characters and symbols.
    - Enhanced validation for text conversion operations.

- **Table formatting**
    - Added the `as_table` parameter for `RTFFootnote` and `RTFSource` components.
    - Auto-inheritance of `col_rel_width` from `rtf_body` to `rtf_column_header`.
    - Improved handling of table borders and footnote placement.

### Architecture improvements

- **Service-oriented architecture**
    - Introduced dedicated service layer for complex operations.
    - Implemented strategy pattern for encoding (`SinglePageStrategy`, `PaginatedStrategy`).
    - Created `RTFEncodingEngine` for strategy orchestration.

- **Code organization**
    - Consolidated constants and eliminated magic numbers throughout the codebase.
    - Method decomposition and improved input validation.
    - Cleaner public interfaces with thorough error handling.

### Dependency changes

- Removed numpy and pandas as hard dependencies.
- Moved pyarrow to development dependencies.
- Now uses narwhals for DataFrame abstraction.
- Prefer polars as the primary DataFrame interface.

### Documentation

- Added vignette-style articles to document the new features.
- Reorganized API reference for better user experience.
- Renamed documentation files to use hyphens consistently.
- Updated all examples to use modern best practices.
- Fixed Polars `DataOrientationWarning` in documentation examples.

### Testing

- Added single-page RTF tests with fixtures generated by r2rtf.
- Added extensive multi-page tests for the `as_table` feature.

## rtflite 0.1.3

### Documentation

- Add contributing guidelines to make it easy for onboarding new developers
  to the recommended development workflow (#25).
- Update `README.md` to add hyperlink to the R package r2rtf (#24).

### Maintenance

- Remove the strict version requirement for the development dependency
  mkdocs-autorefs (#21).

## rtflite 0.1.2

### Maintenance

- Manage project with uv (#19).
- Update the logo image generation workflow to use web fonts (#18).

## rtflite 0.1.1

### Documentation

- Use absolute URL to replace relative path for logo image in `README.md`,
  for proper rendering on PyPI (#16).

## rtflite 0.1.0

### New features

- Introduced core RTF document components, such as `RTFDocument`, `RTFPage`,
  `RTFTitle`, `RTFColumnHeader`, and `RTFBody`. These classes establish the
  foundation for composing structured RTF documents with a text encoding
  pipeline. Use Pydantic for data validation.
- Implemented string width calculation using Pillow with metric-compatible fonts.
  This will be incorporated in the pagination and layout algorithms in
  future releases.
- Implemented a LibreOffice-based document converter for RTF to PDF conversion
  with automatic LibreOffice detection mechanisms under Linux, macOS, and Windows.

### Documentation

- Added an article on creating baseline characteristics tables.
- Integrated code coverage reports via pytest-cov into the documentation site.
