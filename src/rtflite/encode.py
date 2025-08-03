"""RTF Document class - main entry point for RTF generation.

This module provides the RTFDocument class with a clean, service-oriented architecture.
All complex logic has been delegated to specialized services and strategies.
"""

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .input import (
    RTFBody,
    RTFColumnHeader,
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
    df: pl.DataFrame = Field(
        ...,
        description="The DataFrame containing the data for the RTF document. Accepts pandas or polars DataFrame, internally converted to polars.",
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
    rtf_column_header: list[RTFColumnHeader] = Field(
        default_factory=lambda: [RTFColumnHeader()],
        description="Column header settings",
    )
    rtf_body: RTFBody | None = Field(
        default_factory=lambda: RTFBody(),
        description="Table body section settings including column widths and formatting",
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

    @field_validator("rtf_column_header", mode="before")
    def convert_column_header_to_list(cls, v):
        """Convert single RTFColumnHeader to list"""
        if v is not None and isinstance(v, RTFColumnHeader):
            return [v]
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_dataframe(cls, values):
        """Convert DataFrame to polars for internal processing."""
        if "df" in values:
            df = values["df"]
            import polars as pl

            try:
                import pandas as pd

                if isinstance(df, pd.DataFrame):
                    # Convert pandas to polars
                    values["df"] = pl.from_pandas(df)

            except ImportError:
                # pandas not available, ensure it's polars
                if not isinstance(df, pl.DataFrame):
                    raise ValueError("DataFrame must be a polars DataFrame")
        return values

    @model_validator(mode="after")
    def validate_column_names(self):
        """Validate that column references exist in DataFrame."""
        columns = self.df.columns

        if self.rtf_body.group_by is not None:
            for column in self.rtf_body.group_by:
                if column not in columns:
                    raise ValueError(f"`group_by` column {column} not found in `df`")

        if self.rtf_body.page_by is not None:
            for column in self.rtf_body.page_by:
                if column not in columns:
                    raise ValueError(f"`page_by` column {column} not found in `df`")

        if self.rtf_body.subline_by is not None:
            for column in self.rtf_body.subline_by:
                if column not in columns:
                    raise ValueError(f"`subline_by` column {column} not found in `df`")

        return self

    def __init__(self, **data):
        super().__init__(**data)
        # Set default column widths based on DataFrame dimensions
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

