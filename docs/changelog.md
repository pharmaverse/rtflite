# Changelog

## rtflite 0.1.0

## New features

- Introduced core RTF document components, such as `RTFDocument`, `RTFPage`,
  `RTFTitle`, `RTFColumnHeader`, and `RTFBody`. These classes establish the
  foundation for composing structured RTF documents with a text encoding
  pipeline. Use Pydantic for data validation.
- Implemented string width calculation using Pillow with metric-compatible fonts.
  This will be incorporated in the pagination and layout algorithms in
  future releases.
- Implemented a LibreOffice-based document converter for RTF to PDF conversion
  with automatic LibreOffice detection mechanisms under Linux, macOS, and Windows.

## Documentation

- Added an article on creating baseline characteristics tables.
- Integrated code coverage reports via pytest-cov into the documentation site.
