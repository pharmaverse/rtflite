# Agent Instructions for rtflite

## Project overview
- `rtflite` is a lightweight Python library for composing rich-text-format (RTF) documents used for production-quality tables and figures.
- Runtime code lives under `src/rtflite/` and is packaged via `pyproject.toml` with Python 3.10+ support.
- Automated tests live in `tests/` and cover pagination, encoding, services, and snapshot comparisons of generated RTF strings.

## Code organization highlights
- **Core models & configuration**: `src/rtflite/core/` exposes reusable constants and configuration structures consumed across services.
- **Input schemas**: `src/rtflite/input.py` and related modules define Pydantic models (`RTFBody`, `RTFFigure`, `RTFPage`, etc.) that describe incoming table/figure data.
- **Composition logic**: Modules such as `encode.py`, `pagination/`, `row.py`, `attributes.py`, and `services/` transform structured data into final RTF output. They make heavy use of Pydantic validators, typed helper classes, and string-building utilities.
- **Font and color utilities**: `fonts/`, `fonts_mapping.py`, `text_convert.py`, `text_conversion/`, and `services/color_service.py` manage font metrics, color lookup, and text normalization.
- **Conversion helpers**: `convert.py` provides integration with LibreOffice for PDF conversion, while shell/python scripts in `scripts/` (e.g., `check_rtf.sh`, `verify_ascii.py`) support validation workflows.
- **Documentation**: `docs/` hosts the Zensical site. Markdown articles may execute Python snippets via `markdown-exec` during site builds.

## Development workflow expectations
- Use [uv](https://docs.astral.sh/uv/) for environment management. Run `uv sync` to create/refresh the local virtual environment before developing.
- Keep imports sorted with `isort .` and format code with `ruff format`. Follow existing typing conventions---prefer explicit type hints and Pydantic field validators over dynamic typing.
- Maintain consistency with existing error handling (primarily `ValueError`/`TypeError` for validation issues) and adhere to the RTF command patterns already present in helper modules.
- When touching Markdown files in the repository root, run `sh docs/scripts/sync.sh` to propagate changes into the documentation site.
- Do not automatically commit changes. Always leave changes unstaged for the user to review and commit manually, unless explicitly instructed to commit.

## Testing & quality gates
- Execute `pytest` (or targeted subsets) before committing. Snapshot-style tests compare normalized RTF output; update fixtures thoughtfully and document rationale when expectations change.
- If functionality affects documentation examples, rebuild the docs locally with `zensical build --clean` (or preview via `zensical serve`) to confirm rendered outputs.
- Keep dependency metadata (`uv.lock`) in sync when upgrading libraries; use `uv lock --upgrade` followed by `uv sync` if dependency changes are intentional.

## Additional tips
- Reuse utility functions in `tests/utils.py` and `tests/utils_snapshot.py` when authoring new tests to ensure consistent normalization of RTF strings.
- Consult `scripts/update_color_table.R` and `scripts/update_unicode_latex.py` when modifying color tables or Unicode handling to avoid drifting from validated data sources.
- Public API exports are centralized in `src/rtflite/__init__.py`; update `__all__` when adding new user-facing classes or helpers.

## System Architecture: Pagination & Rendering

The project uses a modular, strategy-based architecture for pagination and rendering.

### 1. Strategy Registry & Index
- **Pagination Logic**: Decoupled from the core distributor.
- **Strategies**:
    - `DefaultPaginationStrategy`: Standard row-limit based pagination.
    - `PageByStrategy`: Handles `page_by` grouping logic.
    - `SublineStrategy`: Handles `subline_by` logic.
- **Registry**: `StrategyRegistry` resolves strategies based on configuration.

### 2. Unified Rendering Pipeline
- **`UnifiedRTFEncoder`**: Handles all document encoding (replacing legacy split strategies).
- **Flow**:
    1.  **Paginate**: Select strategy -> Split DataFrame into `List[PageContext]`.
    2.  **Process**: Apply per-page features (borders, headers, dynamic attributes) via `PageFeatureProcessor`.
    3.  **Render**: Use `PageRenderer` to convert each `PageContext` to RTF.
    4.  **Assemble**: Concatenate page RTF chunks.

### 3. Feature Isolation
- Page-specific features (top/bottom borders, spanning rows, footnotes) are calculated and finalized on the `PageContext` object before rendering.

## Recent Updates (Dec 2025): Metadata-Driven Pagination

### Overview
Pagination logic has been refactored to be **metadata-driven**, centralizing row height and page break calculations into `PageBreakCalculator`.

### Key Components
- **`RowMetadata`**: A Pydantic model (in `core.py`) defining the structure of each row's pagination data (row index, data rows, header rows, page assignment, group start flags).
- **`PageBreakCalculator.calculate_row_metadata`**: The core method that generates a Polars DataFrame of `RowMetadata`. It handles:
    - Content row height calculation (respecting fonts and column widths).
    - Header row estimation.
    - Page assignment logic (respecting `nrow`, `additional_rows_per_page`, `new_page`).
    - Group start detection for `page_by` and `subline_by`.

### Strategy Updates
- **`DefaultPaginationStrategy`**: Uses `calculate_row_metadata` to determine page breaks based on content height.
- **`PageByStrategy`**: Uses `calculate_row_metadata` with `page_by` columns to handle grouping and potential page breaks.
- **`SublineStrategy`**: Uses `calculate_row_metadata` with `subline_by` (passed as `subline_by` arg) and `new_page=True` to enforce page breaks on subline changes.

### Validation Status
- **Tests**: All 394 tests passed, including regression tests for pagination and grouping.
- **Linting**: Codebase is clean (`ruff check` passed).
- **Types**: Type checking passed (`mypy .` passed), with explicit casting used for Polars aggregation results.
