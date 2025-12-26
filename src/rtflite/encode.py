"""RTF Document class - main entry point for RTF generation.

This module provides the RTFDocument class with a clean, service-oriented architecture.
All complex logic has been delegated to specialized services and strategies.
"""

import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .convert import LibreOfficeConverter
from .input import (
    RTFBody,
    RTFColumnHeader,
    RTFFigure,
    RTFFootnote,
    RTFPage,
    RTFPageFooter,
    RTFPageHeader,
    RTFSource,
    RTFSubline,
    RTFTitle,
)
from .row import Utils


class RTFDocument(BaseModel):
    """Main class for creating RTF documents with tables, text, and figures.

    RTFDocument is the central class for generating Rich Text Format (RTF) files
    containing formatted tables, titles, footnotes, and other document elements.
    It provides a comprehensive API for creating professional documents commonly
    used in clinical trials, scientific research, and data reporting.

    Examples:
        Simple table with title:
        ```python
        import rtflite as rtf
        import polars as pl

        df = pl.DataFrame({
            "Subject": ["001", "002", "003"],
            "Age": [45, 52, 38],
            "Treatment": ["Drug A", "Drug B", "Placebo"]
        })

        doc = rtf.RTFDocument(
            df=df,
            rtf_title=rtf.RTFTitle(text="Patient Demographics"),
            rtf_body=rtf.RTFBody(col_rel_width=[2, 1, 2])
        )
        doc.write_rtf("demographics.rtf")
        ```

        Multi-page document with headers and footers:
        ```python
        doc = rtf.RTFDocument(
            df=large_df,
            rtf_page=rtf.RTFPage(nrow=40, orientation="landscape"),
            rtf_page_header=rtf.RTFPageHeader(),  # Default page numbering
            rtf_page_footer=rtf.RTFPageFooter(text="Confidential"),
            rtf_title=rtf.RTFTitle(text="Clinical Study Results"),
            rtf_column_header=rtf.RTFColumnHeader(
                text=["Subject ID", "Visit", "Result", "Units"]
            ),
            rtf_body=rtf.RTFBody(
                col_rel_width=[2, 1, 1, 1],
                text_justification=[["l", "c", "r", "c"]]
            ),
            rtf_footnote=rtf.RTFFootnote(
                text="Results are mean +/- SD"
            )
        )
        doc.write_rtf("results.rtf")
        ```

        Document with grouped data and sublines:
        ```python
        doc = rtf.RTFDocument(
            df=grouped_df,
            rtf_body=rtf.RTFBody(
                group_by=["SITE", "TREATMENT"],  # Suppress duplicate values
                subline_by=["STUDY_PHASE"],      # Create section headers
                col_rel_width=[2, 2, 1, 1]
            )
        )
        ```

    Attributes:
        df: Data to display in the table. Can be a single DataFrame or list of
            DataFrames for multi-section documents. Accepts pandas or polars
            DataFrames (automatically converted to polars internally).

        rtf_page: Page configuration including size, orientation, margins, and
            pagination settings.

        rtf_page_header: Optional header appearing at the top of every page.

        rtf_page_footer: Optional footer appearing at the bottom of every page.

        rtf_title: Document title(s) displayed at the top.

        rtf_column_header: Column headers for the table. Can be a single header
            or list of headers for multi-row headers.

        rtf_body: Table body configuration including column widths, formatting,
            borders, and special features like group_by and subline_by.

        rtf_footnote: Optional footnote text displayed after the table.

        rtf_source: Optional source citation displayed at the very bottom.

        rtf_figure: Optional figure/image to embed in the document.

    Methods:
        rtf_encode(): Generate the complete RTF document as a string.
        write_rtf(file_path): Write the RTF document to a file.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core data
    df: pl.DataFrame | list[pl.DataFrame] | None = Field(
        default=None,
        description=(
            "The DataFrame(s) containing the data for the RTF document. "
            "Accepts single DataFrame or list of DataFrames for "
            "multi-section documents. Accepts pandas or polars DataFrame, "
            "internally converted to polars. Optional when using figure-only "
            "documents."
        ),
    )

    # Document structure
    rtf_page: RTFPage = Field(
        default_factory=lambda: RTFPage(),
        description="Page settings including size, orientation and margins",
    )
    rtf_page_header: RTFPageHeader | None = Field(
        default=None, description="Text to appear in the header of each page"
    )
    rtf_title: RTFTitle | None = Field(
        default_factory=lambda: RTFTitle(),
        description="Title section settings including text and formatting",
    )
    rtf_subline: RTFSubline | None = Field(
        default=None, description="Subject line text to appear below the title"
    )
    rtf_column_header: (
        Sequence[RTFColumnHeader] | Sequence[Sequence[RTFColumnHeader | None]]
    ) = Field(
        default_factory=lambda: [RTFColumnHeader()],
        description=(
            "Column header settings. For multi-section documents, use nested "
            "list format: [[header1], [header2], [None]] where None means no "
            "header for that section."
        ),
    )
    rtf_body: RTFBody | Sequence[RTFBody] | None = Field(
        default_factory=lambda: RTFBody(),
        description=(
            "Table body section settings including column widths and "
            "formatting. For multi-section documents, provide a list of "
            "RTFBody objects."
        ),
    )
    rtf_footnote: RTFFootnote | None = Field(
        default=None, description="Footnote text to appear at bottom of document"
    )
    rtf_source: RTFSource | None = Field(
        default=None, description="Data source citation text"
    )
    rtf_page_footer: RTFPageFooter | None = Field(
        default=None, description="Text to appear in the footer of each page"
    )
    rtf_figure: RTFFigure | None = Field(
        default=None, description="Figure/image content to embed in the document"
    )

    @field_validator("rtf_column_header", mode="before")
    def convert_column_header_to_list(cls, v):
        """Convert single RTFColumnHeader to list or handle nested list format"""
        if v is not None and isinstance(v, RTFColumnHeader):
            return [v]
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_dataframe(cls, values):
        """Convert DataFrame(s) to polars for internal processing."""
        if "df" in values and values["df"] is not None:
            df = values["df"]
            import narwhals as nw
            import polars as pl

            # Handle single DataFrame
            if not isinstance(df, list):
                if isinstance(df, pl.DataFrame):
                    pass  # Already polars
                else:
                    # Use narwhals to handle any DataFrame type
                    try:
                        nw_df = nw.from_native(df)
                        values["df"] = nw_df.to_native(pl.DataFrame)
                    except Exception as e:
                        raise ValueError(
                            f"DataFrame must be a valid DataFrame: {str(e)}"
                        ) from e
            # Handle list of DataFrames
            else:
                converted_dfs = []
                for i, single_df in enumerate(df):
                    if isinstance(single_df, pl.DataFrame):
                        converted_dfs.append(single_df)
                    else:
                        try:
                            # Use narwhals to handle any DataFrame type
                            nw_df = nw.from_native(single_df)
                            converted_dfs.append(nw_df.to_native(pl.DataFrame))
                        except Exception as e:
                            raise ValueError(
                                f"DataFrame at index {i} must be a valid "
                                f"DataFrame: {str(e)}"
                            ) from e
                values["df"] = converted_dfs
        return values

    @model_validator(mode="after")
    def validate_column_names(self):
        """Validate column references and multi-section consistency."""
        # Validate df and rtf_figure usage
        if self.df is None and self.rtf_figure is None:
            raise ValueError("Either 'df' or 'rtf_figure' must be provided")

        if self.df is not None and self.rtf_figure is not None:
            raise ValueError(
                "Cannot use both 'df' and 'rtf_figure' together. Use either "
                "tables or figures in a single document."
            )

        # When RTFFigure is used, enforce as_table=False for footnotes and sources
        if self.rtf_figure is not None:
            if self.rtf_footnote is not None and getattr(
                self.rtf_footnote, "as_table", True
            ):
                raise ValueError(
                    "When using RTFFigure, RTFFootnote must have as_table=False"
                )
            if self.rtf_source is not None and getattr(
                self.rtf_source, "as_table", False
            ):
                raise ValueError(
                    "When using RTFFigure, RTFSource must have as_table=False"
                )

        # Skip column validation if no DataFrame provided (figure-only documents)
        if self.df is None:
            return self

        # Multi-section validation
        is_multi_section = isinstance(self.df, list)
        if is_multi_section:
            # Validate rtf_body is also a list with matching length
            if not isinstance(self.rtf_body, list):
                raise ValueError("When df is a list, rtf_body must also be a list")
            if len(self.df) != len(self.rtf_body):
                raise ValueError(
                    "df list length "
                    f"({len(self.df)}) must match rtf_body list length "
                    f"({len(self.rtf_body)})"
                )

            # Validate rtf_column_header if it's nested list format
            if (
                isinstance(self.rtf_column_header, list)
                and self.rtf_column_header
                and isinstance(self.rtf_column_header[0], list)
                and len(self.rtf_column_header) != len(self.df)
            ):
                raise ValueError(
                    "rtf_column_header nested list length "
                    f"({len(self.rtf_column_header)}) must match df list "
                    f"length ({len(self.df)})"
                )

            # Per-section column validation
            for i, (section_df, section_body) in enumerate(
                zip(self.df, self.rtf_body, strict=True)
            ):
                self._validate_section_columns(section_df, section_body, i)
        else:
            # Single section validation (existing logic)
            self._validate_section_columns(self.df, self.rtf_body, 0)

        return self

    def _validate_section_columns(self, df, body, section_index):
        """Validate column references for a single section."""
        columns = df.columns
        section_label = f"section {section_index}" if section_index > 0 else "df"

        if body.group_by is not None:
            for column in body.group_by:
                if column not in columns:
                    raise ValueError(
                        f"`group_by` column {column} not found in {section_label}"
                    )

        if body.page_by is not None:
            for column in body.page_by:
                if column not in columns:
                    raise ValueError(
                        f"`page_by` column {column} not found in {section_label}"
                    )

        if body.subline_by is not None:
            for column in body.subline_by:
                if column not in columns:
                    raise ValueError(
                        f"`subline_by` column {column} not found in {section_label}"
                    )

    def __init__(self, **data):
        super().__init__(**data)

        # Set default column widths based on DataFrame dimensions when a
        # DataFrame is provided.
        if self.df is not None:
            is_multi_section = isinstance(self.df, list)

            if is_multi_section:
                # Handle multi-section documents
                for section_df, section_body in zip(
                    self.df, self.rtf_body, strict=True
                ):
                    dim = section_df.shape
                    if section_body.col_rel_width is None:
                        section_body.col_rel_width = [1] * dim[1]
                    elif len(section_body.col_rel_width) == 1 and dim[1] > 1:
                        section_body.col_rel_width = section_body.col_rel_width * dim[1]

                # Handle column headers for multi-section
                if self.rtf_column_header and isinstance(
                    self.rtf_column_header[0], list
                ):
                    # Nested list format: [[header1], [header2], [None]]
                    for section_headers, section_body in zip(
                        self.rtf_column_header, self.rtf_body, strict=True
                    ):
                        if section_headers:  # Skip if [None]
                            for header in section_headers:
                                if header and header.col_rel_width is None:
                                    header.col_rel_width = (
                                        section_body.col_rel_width.copy()
                                    )
                elif self.rtf_column_header:
                    # Flat list format - apply to first section only
                    for header in self.rtf_column_header:
                        if header.col_rel_width is None:
                            header.col_rel_width = self.rtf_body[0].col_rel_width.copy()
            else:
                # Handle single section documents (existing logic)
                dim = self.df.shape
                if self.rtf_body.col_rel_width is None:
                    self.rtf_body.col_rel_width = [1] * dim[1]
                elif len(self.rtf_body.col_rel_width) == 1 and dim[1] > 1:
                    self.rtf_body.col_rel_width = self.rtf_body.col_rel_width * dim[1]

                # Inherit col_rel_width from rtf_body to rtf_column_header if
                # not specified
                if self.rtf_column_header:
                    for header in self.rtf_column_header:
                        if header.col_rel_width is None:
                            header.col_rel_width = self.rtf_body.col_rel_width.copy()

        # Calculate table spacing for text components
        self._table_space = int(
            Utils._inch_to_twip(self.rtf_page.width - self.rtf_page.col_width) / 2
        )

        # Apply table spacing to text components if needed
        self._apply_table_spacing()

    def _apply_table_spacing(self):
        """Apply table-based spacing to text components that reference the table."""
        for component in [self.rtf_subline, self.rtf_page_header, self.rtf_page_footer]:
            if component is not None and component.text_indent_reference == "table":
                component.text_space_before = (
                    self._table_space + component.text_space_before
                )
                component.text_space_after = (
                    self._table_space + component.text_space_after
                )

    def rtf_encode(self) -> str:
        """Generate the complete RTF document as a string.

        This method processes all document components and generates the final
        RTF code including headers, formatting, tables, and all other elements.
        The resulting string can be written to a file or processed further.

        Returns:
            str: Complete RTF document string ready to be saved as an .rtf file.

        Examples:
            ```python
            doc = RTFDocument(df=data, rtf_title=RTFTitle(text="Report"))
            rtf_string = doc.rtf_encode()
            # Can write manually or process further
            with open("output.rtf", "w") as f:
                f.write(rtf_string)
            ```
        """
        from .encoding import RTFEncodingEngine

        engine = RTFEncodingEngine()
        return engine.encode_document(self)

    def write_rtf(self, file_path: str | Path) -> None:
        """Write the RTF document to a file.

        Generates the complete RTF document and writes it to the specified file path.
        The file is written in UTF-8 encoding and will have the `.rtf` extension.

        Args:
            file_path: Path where the RTF file should be saved.
                Accepts string or Path input. Can be absolute or relative.
                Directories are created if they do not already exist.

        Examples:
            ```python
            doc = RTFDocument(df=data, rtf_title=RTFTitle(text="Report"))
            doc.write_rtf("output/report.rtf")
            ```

        Note:
            The method prints the file path to stdout for confirmation.
        """
        target_path = Path(file_path).expanduser()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        print(target_path)
        rtf_code = self.rtf_encode()
        target_path.write_text(rtf_code, encoding="utf-8")

    def write_docx(
        self,
        file_path: str | Path,
        *,
        converter: LibreOfficeConverter | None = None,
    ) -> None:
        """Write the document as a DOCX file.

        Writes the document to a temporary RTF file first, and then converts
        it to DOCX with LibreOffice. Temporary directories are used for
        all intermediate files to avoid placing artifacts alongside the
        requested output path.

        Args:
            file_path: Destination path for the DOCX file.
                Accepts string or Path input. Can be absolute or relative.
                Directories are created if they do not already exist.
            converter: Optional LibreOffice converter instance.
                Pass a configured instance (for example with a custom
                `executable_path`) to control how LibreOffice is invoked and to
                avoid re-initializing and re-verifying the executable path across
                multiple conversions. Note that each call to ``convert()`` still
                starts a new LibreOffice process in headless mode; the process is
                not kept alive between conversions.

        Examples:
            ```python
            doc = RTFDocument(df=data, rtf_title=RTFTitle(text="Report"))
            doc.write_docx("output/report.docx")
            ```

            Custom LibreOffice executable:
            ```python
            converter = LibreOfficeConverter(executable_path="/custom/path/to/soffice")
            doc.write_docx("output/report.docx", converter=converter)
            ```

        Note:
            The method prints the file path to stdout for confirmation.
        """
        target_path = Path(file_path).expanduser()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if converter is None:
            converter = LibreOfficeConverter()
        with tempfile.TemporaryDirectory() as tmpdir:
            rtf_path = Path(tmpdir) / f"{target_path.stem}.rtf"
            rtf_code = self.rtf_encode()
            rtf_path.write_text(rtf_code, encoding="utf-8")

            with tempfile.TemporaryDirectory() as convert_tmpdir:
                converted = converter.convert(
                    input_files=rtf_path,
                    output_dir=Path(convert_tmpdir),
                    format="docx",
                    overwrite=True,
                )
                if not isinstance(converted, Path):
                    raise TypeError(
                        "LibreOffice conversion returned an unexpected output for a "
                        "single input file; expected `Path`, got object of type "
                        f"{type(converted)!r} with value {converted!r}."
                    )
                docx_path = converted
                shutil.move(str(docx_path), target_path)

        print(target_path)

    def write_html(
        self,
        file_path: str | Path,
        *,
        converter: LibreOfficeConverter | None = None,
    ) -> None:
        """Write the document as an HTML file.

        Writes the document to a temporary RTF file first, and then converts
        it to HTML with LibreOffice. Temporary directories are used for
        all intermediate files to avoid placing artifacts alongside the
        requested output path.

        Args:
            file_path: Destination path for the HTML file.
                Accepts string or Path input. Can be absolute or relative.
                Directories are created if they do not already exist.
            converter: Optional LibreOffice converter instance.
                Pass a configured instance (for example with a custom
                `executable_path`) to control how LibreOffice is invoked and to
                avoid re-initializing and re-verifying the executable path across
                multiple conversions. Note that each call to ``convert()`` still
                starts a new LibreOffice process in headless mode; the process is
                not kept alive between conversions.

        Examples:
            ```python
            doc = RTFDocument(df=data, rtf_title=RTFTitle(text="Report"))
            doc.write_html("output/report.html")
            ```

        Note:
            LibreOffice may create a companion directory (for example
            `report.html_files`) for embedded resources. When present, it is moved
            alongside the requested output path.
        """
        target_path = Path(file_path).expanduser()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if converter is None:
            converter = LibreOfficeConverter()
        with tempfile.TemporaryDirectory() as tmpdir:
            rtf_path = Path(tmpdir) / f"{target_path.stem}.rtf"
            rtf_code = self.rtf_encode()
            rtf_path.write_text(rtf_code, encoding="utf-8")

            with tempfile.TemporaryDirectory() as convert_tmpdir:
                converted = converter.convert(
                    input_files=rtf_path,
                    output_dir=Path(convert_tmpdir),
                    format="html",
                    overwrite=True,
                )
                if not isinstance(converted, Path):
                    raise TypeError(
                        "LibreOffice conversion returned an unexpected output for a "
                        "single input file; expected `Path`, got object of type "
                        f"{type(converted)!r} with value {converted!r}."
                    )
                html_path = converted
                resources_dir = html_path.with_name(f"{html_path.name}_files")
                shutil.move(str(html_path), target_path)
                if resources_dir.is_dir():
                    shutil.move(
                        str(resources_dir), target_path.parent / resources_dir.name
                    )

        print(target_path)

    def write_pdf(
        self,
        file_path: str | Path,
        *,
        converter: LibreOfficeConverter | None = None,
    ) -> None:
        """Write the document as a PDF file.

        Writes the document to a temporary RTF file first, and then converts
        it to PDF with LibreOffice. Temporary directories are used for
        all intermediate files to avoid placing artifacts alongside the
        requested output path.

        Args:
            file_path: Destination path for the PDF file.
                Accepts string or Path input. Can be absolute or relative.
                Directories are created if they do not already exist.
            converter: Optional LibreOffice converter instance.
                Pass a configured instance (for example with a custom
                `executable_path`) to control how LibreOffice is invoked and to
                avoid re-initializing and re-verifying the executable path across
                multiple conversions. Note that each call to ``convert()`` still
                starts a new LibreOffice process in headless mode; the process is
                not kept alive between conversions.

        Examples:
            ```python
            doc = RTFDocument(df=data, rtf_title=RTFTitle(text="Report"))
            doc.write_pdf("output/report.pdf")
            ```
        """
        target_path = Path(file_path).expanduser()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if converter is None:
            converter = LibreOfficeConverter()
        with tempfile.TemporaryDirectory() as tmpdir:
            rtf_path = Path(tmpdir) / f"{target_path.stem}.rtf"
            rtf_code = self.rtf_encode()
            rtf_path.write_text(rtf_code, encoding="utf-8")

            with tempfile.TemporaryDirectory() as convert_tmpdir:
                converted = converter.convert(
                    input_files=rtf_path,
                    output_dir=Path(convert_tmpdir),
                    format="pdf",
                    overwrite=True,
                )
                if not isinstance(converted, Path):
                    raise TypeError(
                        "LibreOffice conversion returned an unexpected output for a "
                        "single input file; expected `Path`, got object of type "
                        f"{type(converted)!r} with value {converted!r}."
                    )
                pdf_path = converted
                shutil.move(str(pdf_path), target_path)

        print(target_path)
