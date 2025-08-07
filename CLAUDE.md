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

The project follows a **modern service-oriented architecture** with clean separation of concerns, designed for maintainability and extensibility:

### Core Architecture Layers

1. **Document Orchestration Layer** (`src/rtflite/encode.py`):
   - `RTFDocument`: Lightweight orchestrator (reduced from 1217 to 735 lines)
   - Delegates complex operations to service and strategy layers
   - Maintains simple, readable public interface

2. **Service Layer** (`src/rtflite/services/`):
   - **`RTFEncodingService`**: Centralized encoding operations
   - **`TextConversionService`**: LaTeX-to-Unicode conversion with validation
   - Clean interfaces, comprehensive error handling, debugging tools

3. **Strategy Pattern** (`src/rtflite/encoding/`):
   - **`SinglePageStrategy`**: Optimized single-page document encoding
   - **`PaginatedStrategy`**: Complex multi-page document handling
   - **`RTFEncodingEngine`**: Strategy selection and orchestration
   - Extensible for future features (lists, figures)

4. **Component System** (`src/rtflite/input.py`):
   - **DefaultsFactory**: Centralized default configuration management
   - **Pydantic models**: Type-safe component definitions
   - **Validation**: Comprehensive input validation

5. **Text Conversion System** (`src/rtflite/text_conversion/`):
   - **`LaTeXSymbolMapper`**: 682 symbols organized by category
   - **`TextConverter`**: Readable conversion engine with statistics
   - **Public interface**: `convert_text()` function for easy use

### Additional Core Components

6. **Attribute Broadcasting** (`src/rtflite/attributes.py`): Pattern for row/column attribute application
7. **String Width Calculation** (`src/rtflite/strwidth.py`): Precise layout calculations
8. **Format Conversion** (`src/rtflite/convert.py`): LibreOffice integration
9. **Dictionary System** (`src/rtflite/dictionary/`): Color and symbol mappings

## Key Development Patterns

### Service-Oriented Development

**Always use the service layer for complex operations**:

```python
# CORRECT: Use service layer
from rtflite.services import RTFEncodingService, TextConversionService

encoding_service = RTFEncodingService()
text_service = TextConversionService()

# Convert text with validation
result = text_service.convert_with_validation("\\alpha test", True)
converted = encoding_service.convert_text_for_encoding("\\beta", True)
```

### Component Creation

**Create components directly using Pydantic models**:

```python
# CORRECT: Direct component creation
from rtflite import RTFTitle, RTFFootnote, RTFBody

title = RTFTitle(text="Clinical Study Report", text_font_size=[14])
footnote = RTFFootnote(text="CI = Confidence Interval", as_table=True)
body = RTFBody(col_rel_width=[2, 1, 1], text_justification=[["l", "c", "c"]])
```

### Text Conversion Best Practices

**Use the new text conversion interface**:

```python
# CORRECT: Use new interface
from rtflite.text_conversion import convert_text

result = convert_text("\\alpha + \\beta", enable_conversion=True)

# For debugging and validation
from rtflite.text_conversion import TextConverter
converter = TextConverter()
stats = converter.get_conversion_statistics("\\alpha \\unknown")
```

### Strategy Pattern Usage

**The encoding engine automatically selects the optimal strategy**:

```python
# CORRECT: The RTFDocument automatically uses the right strategy
doc = RTFDocument(df=data)
rtf_output = doc.rtf_encode()  # Uses SinglePageStrategy or PaginatedStrategy
```

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

**IMPORTANT Font Mapping Rules**:
- **DO NOT MODIFY `fonts_mapping.py`** - The charset values are intentionally different for each font
- The charset mapping in `fonts_mapping.py` is correct as-is and matches R2RTF behavior
- Font table generation in `rtf/syntax.py` handles the formatting and includes `\fprq2` parameter
- The test suite ensures compatibility with R2RTF through semantic RTF comparison

### Testing Patterns

**Test Architecture Components Independently**:

```python
# CORRECT: Test services independently
from rtflite.services import TextConversionService

def test_text_conversion():
    service = TextConversionService()
    result = service.convert_text_content("\\alpha", True)
    assert result == "\u03b1"

# CORRECT: Test with comprehensive validation
def test_conversion_validation():
    service = TextConversionService()
    validation = service.validate_latex_commands("\\alpha \\unknown")
    assert len(validation["valid_commands"]) == 1
    assert len(validation["invalid_commands"]) == 1
```

**Test Integration with Full Documents**:

```python
# CORRECT: Test full RTF pipeline with text conversion
def test_rtf_integration():
    doc = RTFDocument(df=data, rtf_title=RTFTitle(text="Study: \\alpha"))
    # Enable conversion for footnotes/sources (disabled by default)
    doc.rtf_footnote = RTFFootnote(text="Level: \\alpha = 0.05", text_convert=[[True]])
    rtf_output = doc.rtf_encode()
    assert "\u03b1" in rtf_output
```

**Legacy Testing Patterns** (still supported):

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
- `normalize_rtf_borders()`: Handles semantic border equivalence (e.g., `\brdrw15` == `\brdrs\brdrw15`)
- `normalize_rtf_structure()`: Handles page break ordering and whitespace
- `assert_rtf_equals_semantic()`: Complete semantic RTF comparison

#### R2RTF Compatibility Notes

- **Font Charset**: R2RTF uses `\fcharset161` (Greek) for ALL fonts, rtflite matches this in `src/rtflite/fonts_mapping.py`
- **Pagination**: `nrow` parameter includes ALL rows (headers + data + footnotes + sources), not just data rows
- **Border Styles**: Empty border style (`""`) produces `\brdrw15`, explicit `"single"` produces `\brdrs\brdrw15` - both are semantically equivalent

## Project-Specific Considerations

1. **Clinical Reporting Context**: This tool targets pharmaceutical/clinical research reporting with specific formatting requirements for regulatory submissions.

2. **LibreOffice Dependency**: PDF conversion requires LibreOffice installation. The converter automatically finds LibreOffice across different platforms.

3. **Enhanced LaTeX Support**: 
   - **682 LaTeX symbols** organized into categories (Greek, Math Operators, Blackboard Bold, etc.)
   - **Validation tools** for debugging conversion issues
   - **Text conversion service** with comprehensive error handling
   - **Default behavior**: Conversion enabled for data/titles, disabled for footnotes/sources to preserve RTF field codes

4. **Color Management**: Supports clinical trial standard colors through the color dictionary system.

5. **Precision Requirements**: String width calculations and table layouts must be precise for regulatory compliance.

6. **Service-Oriented Architecture**: Complex operations use dedicated services for better maintainability and testing.

## Development Environment

### VSCode Configuration

The project includes VSCode workspace settings in `.vscode/`:

- **RTF File Handling**: RTF files are configured to open with Microsoft Word for proper preview
- **File Associations**: `.rtf` files use system default application (Microsoft Word)
- **Custom Tasks**: `Cmd+Shift+W` keybinding to open RTF files in Word
- **Recommended Extensions**: Python development tools, formatters, and spell checker

**RTF File Preview**: Click any `.rtf` file in VSCode Explorer -> Opens in Microsoft Word for formatted preview

.vscode/                           # VSCode workspace settings
|-- settings.json                  # RTF file associations
|-- tasks.json                     # Microsoft Word integration
+-- keybindings.json              # Custom shortcuts
```

### Troubleshooting

**RTF Comparison Failures**: Use semantic comparison instead of exact string matching:
```python
# WRONG: This may fail due to whitespace/font differences
assert rtf_output == expected

# CORRECT: Use this for robust RTF comparison
assert_rtf_equals_semantic(rtf_output, expected, "test_name")
```

**R Script Errors**: Ensure R code uses proper `write_rtf()` -> `readLines()` -> `cat()` chain in test comments

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

- **Font changes**: DO NOT modify `src/rtflite/fonts_mapping.py` - charset values are correct as-is
- **Font table formatting**: Changes should be made in `src/rtflite/rtf/syntax.py` if needed
- **Border changes**: May require updates to semantic comparison utilities
- **Always test against R2RTF fixtures** for compatibility
- **Trust the test suite**: Tests verify R2RTF compatibility through semantic comparison

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

# Test text conversion features
pytest tests/test_text_conversion.py -v

# Test service layer independently  
pytest tests/test_factory.py -v
```

## Architectural Principles for Future Development

### 1. Service-First Design
- **Extract complex logic** into services before implementing in RTFDocument
- **Test services independently** before integration
- **Use dependency injection** for service composition

### 2. Strategy Pattern Usage
- **Add new strategies** for new document types (lists, figures, etc.)
- **Keep strategies focused** on single responsibilities
- **Test strategies independently** of the engine

### 3. Component System Extension
- **Add new Pydantic models** for new component types
- **Centralize default management** in DefaultsFactory
- **Use direct component creation** with type validation

### 4. Text Conversion Enhancement
- **Extend symbol mappings** through the dictionary system
- **Add validation tools** for new symbol categories
- **Use text conversion service** for all text processing

### 5. Maintainability Focus
- **Prioritize readability** over performance optimizations
- **Write comprehensive tests** for all new functionality
- **Document complex algorithms** with clear comments
- **Use type hints** consistently throughout the codebase

### 6. Testing Strategy
- **Test architectural layers independently**:
  - Services: Unit tests with mocked dependencies
  - Strategies: Integration tests with real documents
  - Factories: Component creation and configuration tests
  - Full pipeline: End-to-end RTF generation tests

## Recent Features and Updates

### Subline_by Feature (v0.2.0)
- Creates paragraph headers before each page (not table rows)
- Automatically removes subline_by columns from table display
- Forces pagination (new_page=True) when used
- Values appear as clean section headers above each group

### Enhanced group_by (v0.2.0)
- Hierarchical value suppression within groups
- Page context restoration for multi-page tables
- Proper handling with pagination system
- Compatible with subline_by for complex layouts

### Documentation Maintenance

When updating documentation:
1. **Update docstrings in source code** - Primary documentation source
2. **Use ASCII-only characters** - No Unicode in source files
3. **Focus on rtflite behavior** - Avoid comparing to other tools
4. **Test examples** - Ensure all code examples work
5. **Follow Google style** - For docstring formatting

### ASCII-Only Code Policy

**IMPORTANT**: All source code files must contain only ASCII characters to ensure maximum compatibility and portability.

#### Required Practices:
1. **Use Unicode escape sequences** in strings:
   - CORRECT: `"\u03b1"` for Greek alpha
   - WRONG: `"alpha"` (direct Unicode character)

2. **Use ASCII alternatives** for symbols:
   - CORRECT: `# CORRECT:` or `# [OK]`
   - WRONG: `# [checkmark]` (emoji/symbols)
   
3. **In test assertions**, always use escape sequences:
   ```python
   # CORRECT:
   assert result == "\u03b1 test"
   
   # WRONG:
   assert result == "alpha test"
   ```

4. **In documentation strings**:
   - Use descriptive text: "Greek letter alpha"
   - Or use escape sequences: "\u03b1"
   - Never use literal Unicode characters

5. **Run verification** before committing:
   ```bash
   uv run python scripts/verify_ascii.py
   ```

#### Exceptions:
- Auto-generated files (coverage reports, CSS)
- External data files (if necessary)
- Files explicitly marked for exclusion

See `DOCUMENTATION_GUIDE.md` for detailed documentation practices.

### Key Files for New Contributors

- `src/rtflite/encode.py` - Main RTFDocument class
- `src/rtflite/input.py` - RTF component definitions
- `src/rtflite/services/` - Service layer implementations
- `src/rtflite/encoding/strategies.py` - Encoding strategies
- `tests/fixtures/run_r_tests.py` - Test fixture generation
