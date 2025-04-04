# Changelog

## rtflite 0.1.3

### Documentation

- Add contributing guidelines to make it easy for onboarding new developers
  to the recommended development workflow (#25).
- Update `README.md` to add hyperlink to the R package r2rtf (#24).

### Maintenance

- Remove the strict version requirement for the devlopment dependency
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
