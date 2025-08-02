# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

rtflite is a lightweight RTF (Rich Text Format) composer for Python that specializes in creating production-quality tables and figures for pharmaceutical and clinical research reporting. It is inspired by the R package r2rtf.

## Python Package Management with uv

Use uv exclusively for Python package management in this project.

### Package Management Commands

- All Python dependencies **must be installed, synchronized, and locked** using uv
- Never use pip, pip-tools, poetry, or conda directly for dependency management

Use these commands:

- Install dependencies: `uv add <package>`
- Remove dependencies: `uv remove <package>`
- Sync dependencies: `uv sync`

### Running Python Code

- Run a Python script with `uv run <script-name>.py`
- Run Python tools like Pytest or Ruff with `uv run pytest` or `uv run ruff`
- Launch a Python repl with `uv run python`

### Managing Scripts with PEP 723 Inline Metadata

- Run a Python script with inline metadata (dependencies defined at the top of the file) with: `uv run script.py`
- You can add or remove dependencies manually from the `dependencies =` section at the top of the script, or
- Or using uv CLI:
    - `uv add package-name --script script.py`
    - `uv remove package-name --script script.py`

## Development Commands

### Testing

We use pytest for unit testing with virtual environment activation required.

```bash
# Activate virtual environment (required for all commands)
source .venv/bin/activate

# Run tests with coverage
pytest --cov=rtflite --cov-report=xml

# Run specific test file
pytest tests/test_encode.py

# Run tests with verbose output
pytest -v

# Skip LibreOffice converter tests (they are marked with @pytest.mark.skip)
pytest -v -k "not TestLibreOfficeConverter"
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

### RTF Test Fixture Management

The project uses R2RTF as the reference implementation for generating test fixtures:

```bash
# Regenerate all RTF fixture files from R code comments in test files
python3 tests/fixtures/run_r_tests.py

# This script:
# 1. Cleans the r_outputs directory completely
# 2. Extracts R code from ```{r, label} blocks in Python test files
# 3. Generates .rtf files (not .txt) in tests/fixtures/r_outputs/
# 4. Requires R with r2rtf and dplyr packages installed
```

**Important**: R code in test comments must use the correct pattern:
```r
# R code must use this pattern for rtf_encode():
test_data |>
  rtf_page(...) |>
  rtf_colheader(...) |>
  rtf_body(...) |>
  rtf_encode() |>
  write_rtf(tempfile()) |>
  readLines() |>
  cat(sep = "\n")

# NOT this (will cause "list cannot be handled by cat" error):
rtf_encode() |> cat()
```

### Render Documentation

mkdocs is used for building the documentation website (via a GitHub Actions workflow).

To improve documentation automation, we embedded Python code chunks in Markdown. This is similar to the principles used by R package vignettes (single source of truth and literate programming).

Specifically, we write articles in Quarto (`.qmd`) format, which are then converted to `.md` files (for mkdocs) and `.py` files (for generating the RTF outputs). Note that the Quarto toolchain and its code chunk evaluation feature is **not** used directly to render outputs.

- The articles are written as `.qmd` files in: `docs/scripts/quarto/*.qmd`
- The outputs are in: `docs/scripts/*.md`; `docs/scripts/py/*.py`

To render the documentation and asset outputs, run this custom shell script: `sh docs/scripts/sync.sh`. This script will convert the `.qmd` files to `.md` and `.py` files, and then run the `.py` files to generate the RTF outputs and convert them to PDF files.

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

The project includes Liberation and CrOS fonts for consistent string width calculations. Always use the strwidth module for text measurements rather than estimations.

### Testing Patterns

- Tests include R output fixtures for cross-language compatibility
- Use pytest fixtures for common test data
- Test files mirror source structure in `tests/` directory

#### RTF Snapshot Testing

The project uses sophisticated RTF comparison for exact snapshot testing:

```python
# Use semantic RTF comparison for exact assertion testing
from tests.utils_snapshot import assert_rtf_equals_semantic

def test_example():
    rtf_output = doc.rtf_encode()
    expected = r_output.read("fixture_name")
    
    # This handles font tables, borders, whitespace, and structural differences
    assert_rtf_equals_semantic(rtf_output, expected, "test_name")
```

**Key utilities in `tests/utils_snapshot.py`**:
- `remove_font_table()`: Removes font table sections for comparison
- `normalize_rtf_borders()`: Handles semantic border equivalence (e.g., `\brdrw15` ≡ `\brdrs\brdrw15`)
- `normalize_rtf_structure()`: Handles page break ordering and whitespace
- `assert_rtf_equals_semantic()`: Complete semantic RTF comparison

#### R2RTF Compatibility Notes

- **Font Charset**: R2RTF uses `\fcharset161` (Greek) for ALL fonts, rtflite matches this in `src/rtflite/fonts_mapping.py`
- **Pagination**: `nrow` parameter includes ALL rows (headers + data + footnotes + sources), not just data rows
- **Border Styles**: Empty border style (`""`) produces `\brdrw15`, explicit `"single"` produces `\brdrs\brdrw15` - both are semantically equivalent

## Project-Specific Considerations

1. **Clinical Reporting Context**: This tool targets pharmaceutical/clinical research reporting with specific formatting requirements for regulatory submissions.

2. **LibreOffice Dependency**: PDF conversion requires LibreOffice installation. The converter automatically finds LibreOffice across different platforms.

3. **Unicode and LaTeX Support**: The project includes mappings for Unicode and LaTeX symbols commonly used in scientific notation.

4. **Color Management**: Supports clinical trial standard colors through the color dictionary system.

5. **Precision Requirements**: String width calculations and table layouts must be precise for regulatory compliance.

## Development Environment

### VSCode Configuration

The project includes VSCode workspace settings in `.vscode/`:

- **RTF File Handling**: RTF files are configured to open with Microsoft Word for proper preview
- **File Associations**: `.rtf` files use system default application (Microsoft Word)
- **Custom Tasks**: `Cmd+Shift+W` keybinding to open RTF files in Word
- **Recommended Extensions**: Python development tools, formatters, and spell checker

**RTF File Preview**: Click any `.rtf` file in VSCode Explorer → Opens in Microsoft Word for formatted preview

### File Structure

```
tests/fixtures/r_outputs/          # RTF fixture files (.rtf format)
├── test_pagination_*.rtf          # Pagination test fixtures  
├── test_input_*.rtf               # Input validation fixtures
└── test_row_*.rtf                 # Row formatting fixtures

tests/utils_snapshot.py            # RTF comparison utilities
tests/fixtures/run_r_tests.py      # RTF fixture generator
.vscode/                           # VSCode workspace settings
├── settings.json                  # RTF file associations
├── tasks.json                     # Microsoft Word integration
└── keybindings.json              # Custom shortcuts
```

### Troubleshooting

**RTF Comparison Failures**: Use semantic comparison instead of exact string matching:
```python
# ❌ This may fail due to whitespace/font differences
assert rtf_output == expected

# ✅ Use this for robust RTF comparison
assert_rtf_equals_semantic(rtf_output, expected, "test_name")
```

**R Script Errors**: Ensure R code uses proper `write_rtf()` → `readLines()` → `cat()` chain in test comments

**LibreOffice Tests**: Skip with `@pytest.mark.skip` decorator if LibreOffice not available

## Common Development Workflows

### Adding New RTF Features

1. **Write tests first** with R2RTF reference code in comments
2. **Generate fixtures**: `python3 tests/fixtures/run_r_tests.py`
3. **Implement feature** in rtflite
4. **Use semantic comparison**: `assert_rtf_equals_semantic()` for tests
5. **Verify output**: Click `.rtf` files to preview in Microsoft Word

### Updating Pagination Logic

- Remember: `nrow` includes ALL rows (headers + data + footnotes)
- Test with different combinations of headers, footers, and data
- Check that page breaks occur at correct positions
- Verify header repetition across pages

### Font and Border Changes

- Font changes: Update `src/rtflite/fonts_mapping.py` 
- Border changes: May require updates to semantic comparison utilities
- Always test against R2RTF fixtures for compatibility

### Quick Testing Commands

```bash
# Test specific functionality
source .venv/bin/activate
pytest tests/test_pagination.py -v
pytest tests/test_input.py::test_rtf_encode_minimal -v

# Regenerate all fixtures after R code changes
python3 tests/fixtures/run_r_tests.py

# Check RTF output quality
# (Click .rtf files in VSCode to open in Microsoft Word)
```
