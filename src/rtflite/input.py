from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rtflite.attributes import TextAttributes, TableAttributes
from rtflite.core.constants import RTFConstants
from rtflite.row import BORDER_CODES


class AttributeDefaultsMixin:
    """Mixin class for common attribute default setting patterns."""
    
    def _set_attribute_defaults(self, exclude_attrs: set = None) -> None:
        """Set default values for text attributes by converting scalars to lists/tuples."""
        exclude_attrs = exclude_attrs or set()
        for attr, value in self.__dict__.items():
            if attr not in exclude_attrs:
                if isinstance(value, (str, int, float, bool)):
                    setattr(self, attr, [value])
                elif isinstance(value, list):
                    setattr(self, attr, tuple(value))


class ValidationHelpers:
    """Helper class for common validation patterns."""
    
    @staticmethod
    def convert_string_to_sequence(v: Any) -> Any:
        """Convert string to single-item sequence for text fields."""
        if v is not None:
            if isinstance(v, str):
                return [v]
            return v
        return v
    
    @staticmethod
    def validate_boolean_field(v: Any, field_name: str) -> bool:
        """Validate that a field is a boolean value."""
        if not isinstance(v, bool):
            raise ValueError(f"{field_name} must be a boolean, got {type(v).__name__}: {v}")
        return v


class DefaultsFactory:
    """Factory class for creating common default configurations."""
    
    @staticmethod
    def get_text_defaults() -> dict:
        """Get common text attribute defaults."""
        return {
            "text_font": [1],
            "text_font_size": [9],
            "text_indent_first": [0],
            "text_indent_left": [0], 
            "text_indent_right": [0],
            "text_space": [1.0],
            "text_space_before": [RTFConstants.DEFAULT_SPACE_BEFORE],
            "text_space_after": [RTFConstants.DEFAULT_SPACE_AFTER],
            "text_hyphenation": [True],
        }
    
    @staticmethod
    def get_table_defaults() -> dict:
        """Get common table attribute defaults."""
        return {
            "col_rel_width": [1.0],
            "border_width": [[15]],
            "cell_height": [[0.15]],
            "cell_justification": [["c"]],
            "cell_vertical_justification": [["top"]],
            "text_font": [[1]],
            "text_format": [[""]],
            "text_font_size": [[9]],
            "text_justification": [["l"]],
            "text_indent_first": [[0]],
            "text_indent_left": [[0]],
            "text_indent_right": [[0]],
            "text_space": [[1]],
            "text_space_before": [[15]],
            "text_space_after": [[15]],
            "text_hyphenation": [[True]],
        }
    
    @staticmethod
    def get_border_defaults(as_table: bool) -> dict:
        """Get conditional border defaults based on table rendering mode."""
        if as_table:
            # Table rendering: has borders (R2RTF as_table=TRUE behavior)
            return {
                "border_left": [["single"]],
                "border_right": [["single"]],
                "border_top": [["single"]],
                "border_bottom": [[""]],
            }
        else:
            # Plain text rendering: no borders (R2RTF as_table=FALSE behavior)
            return {
                "border_left": [[""]],
                "border_right": [[""]],
                "border_top": [[""]],
                "border_bottom": [[""]],
            }


class RTFPage(BaseModel):
    """RTF page configuration"""

    orientation: str | None = Field(
        default="portrait", description="Page orientation ('portrait' or 'landscape')"
    )

    @field_validator("orientation")
    def validate_orientation(cls, v):
        if v not in ["portrait", "landscape"]:
            raise ValueError(
                f"Invalid orientation. Must be 'portrait' or 'landscape'. Given: {v}"
            )
        return v

    width: float | None = Field(default=None, description="Page width in inches")
    height: float | None = Field(default=None, description="Page height in inches")
    margin: Sequence[float] | None = Field(
        default=None,
        description="Page margins [left, right, top, bottom, header, footer] in inches",
    )

    @field_validator("margin")
    def validate_margin(cls, v):
        if v is not None and len(v) != 6:
            raise ValueError("Margin must be a sequence of 6 values.")
        return v

    nrow: int | None = Field(default=None, description="Number of rows per page")

    border_first: str | None = Field(
        default="double", description="First row border style"
    )
    border_last: str | None = Field(
        default="double", description="Last row border style"
    )
    col_width: float | None = Field(
        default=None, description="Total width of table columns in inches"
    )
    use_color: bool | None = Field(
        default=False, description="Whether to use color in the document"
    )

    page_title_location: str | None = Field(
        default="all", description="Where to display titles ('all', 'first', 'last')"
    )
    page_footnote_location: str | None = Field(
        default="all", description="Where to display footnotes ('all', 'first', 'last')"
    )
    page_source_location: str | None = Field(
        default="all", description="Where to display source ('all', 'first', 'last')"
    )

    @field_validator("border_first", "border_last")
    def validate_border(cls, v):
        if v not in BORDER_CODES:
            raise ValueError(
                f"{cls.__field_name__.capitalize()} with invalid border style: {v}"
            )
        return v

    @field_validator(
        "page_title_location", "page_footnote_location", "page_source_location"
    )
    def validate_location(cls, v):
        if v not in ["all", "first", "last"]:
            raise ValueError(
                f"Invalid location. Must be 'all', 'first', or 'last'. Given: {v}"
            )
        return v

    @field_validator("width", "height", "nrow", "col_width")
    def validate_width_height(cls, v):
        if v is not None and v <= 0:
            raise ValueError(
                f"{cls.__field_name__.capitalize()} must be greater than 0."
            )
        return v

    def __init__(self, **data):
        super().__init__(**data)
        self._set_default()

    def _set_default(self):
        """Set default values based on page orientation."""
        if self.orientation == "portrait":
            self._set_portrait_defaults()
        elif self.orientation == "landscape":
            self._set_landscape_defaults()
        
        self._validate_margin_length()
        return self
    
    def _set_portrait_defaults(self) -> None:
        """Set default values for portrait orientation."""
        self.width = self.width or 8.5
        self.height = self.height or 11
        self.margin = self.margin or [1.25, 1, 1.75, 1.25, 1.75, 1.00625]
        self.col_width = self.col_width or self.width - 2.25
        self.nrow = self.nrow or 40
    
    def _set_landscape_defaults(self) -> None:
        """Set default values for landscape orientation."""
        self.width = self.width or 11
        self.height = self.height or 8.5
        self.margin = self.margin or [1.0, 1.0, 2, 1.25, 1.25, 1.25]
        self.col_width = self.col_width or self.width - 2.5
        self.nrow = self.nrow or 24
    
    def _validate_margin_length(self) -> None:
        """Validate that margin has exactly 6 values."""
        if len(self.margin) != 6:
            raise ValueError("Margin length must be 6.")


class RTFPageHeader(TextAttributes, AttributeDefaultsMixin):
    text: Sequence[str] | None = Field(
        default="Page \\chpgn of {\\field{\\*\\fldinst NUMPAGES }}",
        description="Page header text content",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    text_indent_reference: str | None = Field(
        default="page",
        description="Reference point for indentation ('page' or 'table')",
    )

    def __init__(self, **data):
        defaults = {
            "text_font": [1],
            "text_font_size": [12],  
            "text_justification": ["r"],
            "text_indent_first": [0],
            "text_indent_left": [0],
            "text_indent_right": [0],
            "text_space": [1.0],
            "text_space_before": [RTFConstants.DEFAULT_SPACE_BEFORE],
            "text_space_after": [RTFConstants.DEFAULT_SPACE_AFTER],
            "text_hyphenation": [True],
            "text_convert": [False],  
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()

    def _set_default(self):
        self._set_attribute_defaults()
        return self


class RTFPageFooter(TextAttributes, AttributeDefaultsMixin):
    text: Sequence[str] | None = Field(
        default=None, description="Page footer text content"
    )
    text_indent_reference: str | None = Field(
        default="page",
        description="Reference point for indentation ('page' or 'table')",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    def __init__(self, **data):
        defaults = {
            "text_font": [1],
            "text_font_size": [12],  # Match r2rtf default of 12pt
            "text_justification": ["c"],
            "text_indent_first": [0],
            "text_indent_left": [0],
            "text_indent_right": [0],
            "text_space": [1.0],
            "text_space_before": [RTFConstants.DEFAULT_SPACE_BEFORE],
            "text_space_after": [RTFConstants.DEFAULT_SPACE_AFTER],
            "text_hyphenation": [True],
            "text_convert": [False],  # Disable to preserve RTF field codes
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()

    def _set_default(self):
        self._set_attribute_defaults()
        return self


class RTFSubline(TextAttributes, AttributeDefaultsMixin):
    text: Sequence[str] | None = Field(
        default=None, description="Page footer text content"
    )
    text_indent_reference: str | None = Field(
        default="table",
        description="Reference point for indentation ('page' or 'table')",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    def __init__(self, **data):
        defaults = {
            "text_font": [1],
            "text_font_size": [9],
            "text_justification": ["l"],
            "text_indent_first": [0],
            "text_indent_left": [0],
            "text_indent_right": [0],
            "text_space": [1.0],
            "text_space_before": [RTFConstants.DEFAULT_SPACE_BEFORE],
            "text_space_after": [RTFConstants.DEFAULT_SPACE_AFTER],
            "text_hyphenation": [True],
            "text_convert": [True],
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()

    def _set_default(self):
        self._set_attribute_defaults()
        return self


class RTFFootnote(TableAttributes):
    """Class for RTF footnote settings"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: Sequence[str] | None = Field(default=None, description="Footnote table")
    as_table: bool = Field(
        default=True,
        description="Whether to render footnote as table (True) or plain text (False)",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    @field_validator("as_table", mode="before")
    def validate_as_table(cls, v):
        return ValidationHelpers.validate_boolean_field(v, "as_table")

    def __init__(self, **data):
        as_table = data.get("as_table", True)  # Default True for footnotes
        defaults = self._get_footnote_defaults(as_table)
        defaults.update(data)
        super().__init__(**defaults)
        self._process_text_conversion()
    
    def _get_footnote_defaults(self, as_table: bool) -> dict:
        """Get default configuration for footnote based on rendering mode."""
        defaults = DefaultsFactory.get_table_defaults()
        border_defaults = DefaultsFactory.get_border_defaults(as_table)
        
        # Footnote-specific overrides
        footnote_overrides = {
            "text_convert": [[False]],  # Disable text conversion for footnotes
        }
        
        defaults.update(border_defaults)
        defaults.update(footnote_overrides)
        return defaults
    
    def _process_text_conversion(self) -> None:
        """Convert text sequence to line-separated string format."""
        if self.text is not None:
            if isinstance(self.text, Sequence):
                if len(self.text) == 0:
                    self.text = []
                else:
                    self.text = "\\line ".join(self.text)

    def _set_default(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)) and attr not in ["as_table"]:
                setattr(self, attr, [value])

        return self


class RTFSource(TableAttributes):
    """Class for RTF data source settings"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: Sequence[str] | None = Field(default=None, description="Data source table")
    as_table: bool = Field(
        default=False,
        description="Whether to render source as table (True) or plain text (False)",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    @field_validator("as_table", mode="before")
    def validate_as_table(cls, v):
        return ValidationHelpers.validate_boolean_field(v, "as_table")

    def __init__(self, **data):
        as_table = data.get("as_table", False)  # Default False for sources
        defaults = self._get_source_defaults(as_table)
        defaults.update(data)
        super().__init__(**defaults)
        self._process_text_conversion()
    
    def _get_source_defaults(self, as_table: bool) -> dict:
        """Get default configuration for source based on rendering mode."""
        defaults = DefaultsFactory.get_table_defaults()
        border_defaults = DefaultsFactory.get_border_defaults(as_table)
        
        # Source-specific overrides
        source_overrides = {
            "text_justification": [["c"]],  # Center justification for sources
            "text_convert": [[False]],  # Disable text conversion for sources
        }
        
        defaults.update(border_defaults)
        defaults.update(source_overrides)
        return defaults
    
    def _process_text_conversion(self) -> None:
        """Convert text sequence to line-separated string format."""
        if self.text is not None:
            if isinstance(self.text, Sequence):
                if len(self.text) == 0:
                    self.text = []
                else:
                    self.text = "\\line ".join(self.text)

    def _set_default(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)) and attr not in ["as_table"]:
                setattr(self, attr, [value])

        return self


class RTFTitle(TextAttributes, AttributeDefaultsMixin):
    text: Sequence[str] | None = Field(default=None, description="Title text content")
    text_indent_reference: str | None = Field(
        default="table",
        description="Reference point for indentation ('page' or 'table')",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    def __init__(self, **data):
        defaults = {
            "text_font": [1],
            "text_font_size": [12],
            "text_justification": ["c"],
            "text_indent_first": [0],
            "text_indent_left": [0],
            "text_indent_right": [0],
            "text_space": [1.0],
            "text_space_before": [180.0],
            "text_space_after": [180.0],
            "text_hyphenation": [True],
            "text_convert": [True],
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()

    def _set_default(self):
        self._set_attribute_defaults()
        return self


class RTFColumnHeader(TableAttributes):
    """Class for RTF column header settings"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: Sequence[str] | None = Field(default=None, description="Column header table")

    @field_validator("text", mode="before")
    def convert_text_before(cls, v):
        if v is not None:
            if isinstance(v, str):
                return [v]
            if isinstance(v, (list, tuple)) and all(
                isinstance(item, str) for item in v
            ):
                return list(v)
        return v

    @field_validator("text", mode="after")
    def convert_text_after(cls, v):
        if v is not None and isinstance(v, (list, tuple)):
            try:
                import polars as pl

                schema = [f"col_{i + 1}" for i in range(len(v))]
                return pl.DataFrame([v], schema=schema, orient="row")
            except ImportError:
                pass
        return v

    def __init__(self, **data):
        data = self._handle_backwards_compatibility(data)
        defaults = self._get_column_header_defaults()
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()
    
    def _handle_backwards_compatibility(self, data: dict) -> dict:
        """Handle backwards compatibility for df parameter."""
        if "df" in data and "text" not in data:
            df = data.pop("df")
            data["text"] = self._convert_dataframe_to_text(df)
        return data
    
    def _convert_dataframe_to_text(self, df) -> list | None:
        """Convert DataFrame to text list based on orientation."""
        try:
            import polars as pl
            
            if isinstance(df, pl.DataFrame):
                return self._handle_dataframe_orientation(df)
        except ImportError:
            pass
        return None
    
    def _handle_dataframe_orientation(self, df) -> list:
        """Handle DataFrame orientation for column headers."""
        # For backwards compatibility, assume single-row DataFrame
        # If DataFrame has multiple rows, transpose it first
        if df.shape[0] > 1 and df.shape[1] == 1:
            # Column-oriented: transpose to row-oriented
            return df.get_column(df.columns[0]).to_list()
        else:
            # Row-oriented: take first row
            return list(df.row(0))
    
    def _get_column_header_defaults(self) -> dict:
        """Get default configuration for column headers."""
        return {
            "border_left": ["single"],
            "border_right": ["single"],
            "border_top": ["single"],
            "border_bottom": [""],
            "border_width": [15],
            "cell_height": [0.15],
            "cell_justification": ["c"],
            "cell_vertical_justification": ["bottom"],
            "text_font": [1],
            "text_format": [""],
            "text_font_size": [9],
            "text_justification": ["c"],
            "text_indent_first": [0],
            "text_indent_left": [0],
            "text_indent_right": [0],
            "text_space": [1],
            "text_space_before": [15],
            "text_space_after": [15],
            "text_hyphenation": [False],
            "text_convert": [True],
        }

    def _set_default(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)):
                setattr(self, attr, [value])

        return self


class RTFBody(TableAttributes):
    """Class for RTF document body settings"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    as_colheader: bool = Field(
        default=True, description="Whether to display column headers"
    )
    group_by: Sequence[str] | None = Field(
        default=None, description="Column name to group rows by"
    )
    page_by: Sequence[str] | None = Field(
        default=None, description="Column name to create page breaks by"
    )
    new_page: bool = Field(default=False, description="Force new page before table")
    pageby_header: bool = Field(default=True, description="Repeat headers on new pages")
    pageby_row: str = Field(
        default="column",
        description="Page break handling for rows ('column' or 'value')",
    )
    subline_by: Sequence[str] | None = Field(
        default=None, description="Column name to create sublines by"
    )
    last_row: bool = Field(
        default=True,
        description="Whether the table contains the last row of the final table",
    )

    @field_validator("group_by", "page_by", "subline_by", mode="before")
    def convert_text(cls, v):
        if v is not None:
            if isinstance(v, str):
                return [v]
            return v

    @field_validator("pageby_row")
    def validate_pageby_row(cls, v):
        if v not in ["column", "first_row"]:
            raise ValueError(
                f"Invalid pageby_row. Must be 'column' or 'first_row'. Given: {v}"
            )
        return v

    def __init__(self, **data):
        defaults = {
            "border_left": [["single"]],
            "border_right": [["single"]],
            "border_first": [["single"]],
            "border_last": [["single"]],
            "border_width": [[15]],
            "cell_height": [[0.15]],
            "cell_justification": [["c"]],
            "cell_vertical_justification": [["top"]],
            "text_font": [[1]],
            "text_font_size": [[9]],
            "text_indent_first": [[0]],
            "text_indent_left": [[0]],
            "text_indent_right": [[0]],
            "text_space": [[1]],
            "text_space_before": [[15]],
            "text_space_after": [[15]],
            "text_hyphenation": [[False]],
            "text_convert": [[True]],
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()

    def _set_default(self):
        self._set_table_attribute_defaults()
        self._set_border_defaults()
        self._validate_page_by_logic()
        return self
    
    def _set_table_attribute_defaults(self) -> None:
        """Set default values for table attributes, excluding special control attributes."""
        excluded_attrs = {
            "as_colheader", "page_by", "new_page", "pageby_header", 
            "pageby_row", "subline_by", "last_row"
        }
        
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)) and attr not in excluded_attrs:
                setattr(self, attr, [value])
    
    def _set_border_defaults(self) -> None:
        """Set default values for border and justification attributes."""
        self.border_top = self.border_top or [""]
        self.border_bottom = self.border_bottom or [""]
        self.border_left = self.border_left or ["single"]
        self.border_right = self.border_right or ["single"]
        self.border_first = self.border_first or ["single"]
        self.border_last = self.border_last or ["single"]
        self.cell_vertical_justification = self.cell_vertical_justification or ["center"]
        self.text_justification = self.text_justification or ["c"]
    
    def _validate_page_by_logic(self) -> None:
        """Validate that page_by and new_page settings are consistent."""
        if self.page_by is None and self.new_page:
            raise ValueError(
                "`new_page` must be `False` if `page_by` is not specified"
            )
