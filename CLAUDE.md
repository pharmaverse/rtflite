# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
rtflite is a lightweight RTF (Rich Text Format) composer for Python that specializes in creating production-quality tables and figures for pharmaceutical and clinical research reporting. It is inspired by the R package r2rtf.

## Development Commands

### Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Testing
```bash
# Run tests with coverage
pytest --cov=rtflite --cov-report=xml

# Run specific test file
pytest tests/test_encode.py

# Run tests with verbose output
pytest -v
```

### Code Quality
```bash
# Sort imports
isort .

# Format code
ruff format

# Check linting issues
ruff check

# Auto-fix linting issues
ruff check --fix
```

### Installation
```bash
# Install with all dependencies for development
pip install -e '.[all]'

# Install minimal dependencies
pip install -e .
```

### Documentation

```bash
# Sync source document
# source: docs/scripts/quarto/example-*.qmd
# output: docs/scripts/*.md; docs/scripts/py/*.py
bash docs/scripts/sync.sh
```

## Architecture Overview

The project follows a modular architecture centered around RTF document generation:

1. **Core Document Model** (`src/rtflite/encode.py`): The `RTFDocument` class orchestrates document generation, managing pages, encoding, and output.

2. **Component System** (`src/rtflite/input.py`): Pydantic-based models for RTF components:
   - `RTFPage`: Page-level settings and content
   - `RTFPageHeader/Footer`: Repeated page elements
   - `RTFTable`: Table data and formatting
   - `RTFText`: Styled text content

3. **Attribute Broadcasting** (`src/rtflite/attributes.py`): Implements a broadcasting pattern for applying text and table attributes across rows/columns, similar to numpy broadcasting.

4. **String Width Calculation** (`src/rtflite/strwidth.py`): Uses Pillow and embedded fonts to calculate precise string widths for table layout. Critical for proper column sizing.

5. **Format Conversion** (`src/rtflite/convert.py`): Integrates with LibreOffice for RTF-to-PDF conversion. Automatically detects LibreOffice installation paths across platforms.

## Key Development Patterns

### Data Structure Preferences
- Use nested lists instead of pandas DataFrames (project is removing pandas dependency)
- Convert numpy arrays to nested lists when needed
- Prefer narwhals for DataFrame abstraction when dataframe operations are necessary

### Pydantic Validation
All RTF components use Pydantic BaseModel with validators:
```python
class RTFComponent(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
```

### Font Handling
The project includes Liberation and Cros fonts for consistent string width calculations. Always use the strwidth module for text measurements rather than estimations.

### Testing Patterns
- Tests include R output fixtures for cross-language compatibility
- Use pytest fixtures for common test data
- Test files mirror source structure in `tests/` directory

## Project-Specific Considerations

1. **Clinical Reporting Context**: This tool targets pharmaceutical/clinical research reporting with specific formatting requirements for regulatory submissions.

2. **LibreOffice Dependency**: PDF conversion requires LibreOffice installation. The converter automatically finds LibreOffice across different platforms.

3. **Unicode and LaTeX Support**: The project includes mappings for Unicode and LaTeX symbols commonly used in scientific notation.

4. **Color Management**: Supports clinical trial standard colors through the color dictionary system.

5. **Precision Requirements**: String width calculations and table layouts must be precise for regulatory compliance.