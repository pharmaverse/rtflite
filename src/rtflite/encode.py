"""RTF Document class - main entry point for RTF generation.

This module provides the RTFDocument class with a clean, service-oriented architecture.
All complex logic has been delegated to specialized services and strategies.
"""

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    """RTF Document - clean data model with service-based encoding."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core data
    df: pl.DataFrame | list[pl.DataFrame] | None = Field(
        default=None,
        description="The DataFrame(s) containing the data for the RTF document. Accepts single DataFrame or list of DataFrames for multi-section documents. Accepts pandas or polars DataFrame, internally converted to polars. Optional when using figure-only documents.",
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
    rtf_column_header: list[RTFColumnHeader] | list[list[RTFColumnHeader | None]] = Field(
        default_factory=lambda: [RTFColumnHeader()],
        description="Column header settings. For multi-section documents, use nested list format: [[header1], [header2], [None]] where None means no header for that section.",
    )
    rtf_body: RTFBody | list[RTFBody] | None = Field(
        default_factory=lambda: RTFBody(),
        description="Table body section settings including column widths and formatting. For multi-section documents, provide a list of RTFBody objects.",
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
            import polars as pl

            try:
                import pandas as pd

                # Handle single DataFrame
                if isinstance(df, pd.DataFrame):
                    values["df"] = pl.from_pandas(df)
                elif isinstance(df, pl.DataFrame):
                    pass  # Already polars
                # Handle list of DataFrames
                elif isinstance(df, list):
                    converted_dfs = []
                    for i, single_df in enumerate(df):
                        if isinstance(single_df, pd.DataFrame):
                            converted_dfs.append(pl.from_pandas(single_df))
                        elif isinstance(single_df, pl.DataFrame):
                            converted_dfs.append(single_df)
                        else:
                            raise ValueError(f"DataFrame at index {i} must be a pandas or polars DataFrame")
                    values["df"] = converted_dfs

            except ImportError:
                # pandas not available, ensure it's polars
                if isinstance(df, list):
                    for i, single_df in enumerate(df):
                        if not isinstance(single_df, pl.DataFrame):
                            raise ValueError(f"DataFrame at index {i} must be a polars DataFrame")
                elif not isinstance(df, pl.DataFrame):
                    raise ValueError("DataFrame must be a polars DataFrame")
        return values

    @model_validator(mode="after")
    def validate_column_names(self):
        """Validate that column references exist in DataFrame and multi-section consistency."""
        # Validate df and rtf_figure usage
        if self.df is None and self.rtf_figure is None:
            raise ValueError("Either 'df' or 'rtf_figure' must be provided")
        
        if self.df is not None and self.rtf_figure is not None:
            raise ValueError("Cannot use both 'df' and 'rtf_figure' together. Use either tables or figures in a single document.")
        
        # When RTFFigure is used, enforce as_table=False for footnotes and sources
        if self.rtf_figure is not None:
            if self.rtf_footnote is not None and getattr(self.rtf_footnote, 'as_table', True):
                raise ValueError("When using RTFFigure, RTFFootnote must have as_table=False")
            if self.rtf_source is not None and getattr(self.rtf_source, 'as_table', False):
                raise ValueError("When using RTFFigure, RTFSource must have as_table=False")
        
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
                raise ValueError(f"df list length ({len(self.df)}) must match rtf_body list length ({len(self.rtf_body)})")
            
            # Validate rtf_column_header if it's nested list format
            if isinstance(self.rtf_column_header[0], list):
                if len(self.rtf_column_header) != len(self.df):
                    raise ValueError(f"rtf_column_header nested list length ({len(self.rtf_column_header)}) must match df list length ({len(self.df)})")
            
            # Per-section column validation
            for i, (section_df, section_body) in enumerate(zip(self.df, self.rtf_body)):
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
                    raise ValueError(f"`group_by` column {column} not found in {section_label}")

        if body.page_by is not None:
            for column in body.page_by:
                if column not in columns:
                    raise ValueError(f"`page_by` column {column} not found in {section_label}")

        if body.subline_by is not None:
            for column in body.subline_by:
                if column not in columns:
                    raise ValueError(f"`subline_by` column {column} not found in {section_label}")

    def __init__(self, **data):
        super().__init__(**data)
        
        # Set default column widths based on DataFrame dimensions (if DataFrame provided)
        if self.df is not None:
            is_multi_section = isinstance(self.df, list)
            
            if is_multi_section:
                # Handle multi-section documents  
                for section_df, section_body in zip(self.df, self.rtf_body):
                    dim = section_df.shape
                    section_body.col_rel_width = section_body.col_rel_width or [1] * dim[1]

                # Handle column headers for multi-section
                if self.rtf_column_header and isinstance(self.rtf_column_header[0], list):
                    # Nested list format: [[header1], [header2], [None]]
                    for section_headers, section_body in zip(self.rtf_column_header, self.rtf_body):
                        if section_headers:  # Skip if [None]
                            for header in section_headers:
                                if header and header.col_rel_width is None:
                                    header.col_rel_width = section_body.col_rel_width.copy()
                elif self.rtf_column_header:
                    # Flat list format - apply to first section only
                    for header in self.rtf_column_header:
                        if header.col_rel_width is None:
                            header.col_rel_width = self.rtf_body[0].col_rel_width.copy()
            else:
                # Handle single section documents (existing logic)
                dim = self.df.shape
                self.rtf_body.col_rel_width = self.rtf_body.col_rel_width or [1] * dim[1]

                # Inherit col_rel_width from rtf_body to rtf_column_header if not specified
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
        """Generate RTF code using the encoding engine.
        
        Returns:
            Complete RTF document string
        """
        from .encoding import RTFEncodingEngine
        engine = RTFEncodingEngine()
        return engine.encode_document(self)

    def write_rtf(self, file_path: str) -> None:
        """Write the RTF code into a `.rtf` file."""
        print(file_path)
        rtf_code = self.rtf_encode()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rtf_code)

