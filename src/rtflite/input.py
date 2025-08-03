from collections.abc import Sequence
from typing import Any
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class RTFTextComponent(TextAttributes, AttributeDefaultsMixin):
    """Consolidated base class for text-based RTF components.

    This class unifies RTFPageHeader, RTFPageFooter, RTFSubline, and RTFTitle
    components which share nearly identical structure with only different defaults.
    """

    text: Sequence[str] | None = Field(default=None, description="Text content")
    text_indent_reference: str | None = Field(
        default="table",
        description="Reference point for indentation ('page' or 'table')",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    def __init__(self, **data):
        # Get defaults from the component-specific config
        defaults = self._get_component_defaults()

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)
        self._set_default()

    def _set_default(self):
        self._set_attribute_defaults()
        return self

    def _get_component_defaults(self) -> dict:
        """Override in subclasses to provide component-specific defaults."""
        return DefaultsFactory.get_text_defaults()


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
            raise ValueError(
                f"{field_name} must be a boolean, got {type(v).__name__}: {v}"
            )
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
    def get_page_header_defaults() -> dict:
        """Get page header specific defaults."""
        defaults = DefaultsFactory.get_text_defaults()
        defaults.update(
            {
                "text_font_size": [12],
                "text_justification": ["r"],
                "text_convert": [False],  # Preserve RTF field codes
                "text_indent_reference": "page",
            }
        )
        return defaults

    @staticmethod
    def get_page_footer_defaults() -> dict:
        """Get page footer specific defaults."""
        defaults = DefaultsFactory.get_text_defaults()
        defaults.update(
            {
                "text_font_size": [12],
                "text_justification": ["c"],
                "text_convert": [False],  # Preserve RTF field codes
                "text_indent_reference": "page",
            }
        )
        return defaults

    @staticmethod
    def get_title_defaults() -> dict:
        """Get title specific defaults."""
        defaults = DefaultsFactory.get_text_defaults()
        defaults.update(
            {
                "text_font_size": [12],
                "text_justification": ["c"],
                "text_space_before": [180.0],
                "text_space_after": [180.0],
                "text_convert": [True],  # Enable LaTeX conversion for titles
                "text_indent_reference": "table",
            }
        )
        return defaults

    @staticmethod
    def get_subline_defaults() -> dict:
        """Get subline specific defaults."""
        defaults = DefaultsFactory.get_text_defaults()
        defaults.update(
            {
                "text_font_size": [9],
                "text_justification": ["l"],
                "text_convert": [False],
                "text_indent_reference": "table",
            }
        )
        return defaults

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

    page_title: str = Field(
        default="all",
        description="Where to display titles in multi-page documents ('first', 'last', 'all')",
    )
    page_footnote: str = Field(
        default="last",
        description="Where to display footnotes in multi-page documents ('first', 'last', 'all')",
    )
    page_source: str = Field(
        default="last",
        description="Where to display source in multi-page documents ('first', 'last', 'all')",
    )

    @field_validator("border_first", "border_last")
    def validate_border(cls, v):
        if v not in BORDER_CODES:
            raise ValueError(
                f"{cls.__field_name__.capitalize()} with invalid border style: {v}"
            )
        return v

    @field_validator("page_title", "page_footnote", "page_source")
    def validate_page_placement(cls, v):
        valid_options = {"first", "last", "all"}
        if v not in valid_options:
            raise ValueError(
                f"Invalid page placement option '{v}'. Must be one of {valid_options}"
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


class RTFPageHeader(RTFTextComponent):
    """RTF page header component with right-aligned default text."""

    def __init__(self, **data):
        # Set the default header text if not provided
        if "text" not in data:
            data["text"] = "Page \\chpgn of {\\field{\\*\\fldinst NUMPAGES }}"
        super().__init__(**data)

    def _get_component_defaults(self) -> dict:
        return DefaultsFactory.get_page_header_defaults()


class RTFPageFooter(RTFTextComponent):
    """RTF page footer component with center-aligned text."""

    def _get_component_defaults(self) -> dict:
        return DefaultsFactory.get_page_footer_defaults()


class RTFSubline(RTFTextComponent):
    """RTF subline component with left-aligned text."""

    def _get_component_defaults(self) -> dict:
        return DefaultsFactory.get_subline_defaults()


class RTFTableTextComponent(TableAttributes):
    """Consolidated base class for table-based text components (footnotes and sources).

    This class unifies RTFFootnote and RTFSource which share nearly identical structure
    with only different default values for as_table and text justification.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: Sequence[str] | None = Field(default=None, description="Text content")
    as_table: bool = Field(
        description="Whether to render as table (True) or plain text (False)",
    )

    @field_validator("text", mode="before")
    def convert_text(cls, v):
        return ValidationHelpers.convert_string_to_sequence(v)

    @field_validator("as_table", mode="before")
    def validate_as_table(cls, v):
        return ValidationHelpers.validate_boolean_field(v, "as_table")

    def __init__(self, **data):
        # Set as_table default if not provided
        if "as_table" not in data:
            data["as_table"] = self._get_default_as_table()

        as_table = data["as_table"]
        defaults = self._get_component_table_defaults(as_table)
        defaults.update(data)
        super().__init__(**defaults)
        self._process_text_conversion()

    def _get_default_as_table(self) -> bool:
        """Override in subclasses to provide component-specific as_table default."""
        return True

    def _get_component_table_defaults(self, as_table: bool) -> dict:
        """Get defaults with component-specific overrides."""
        defaults = DefaultsFactory.get_table_defaults()
        border_defaults = DefaultsFactory.get_border_defaults(as_table)
        component_overrides = self._get_component_overrides()

        defaults.update(border_defaults)
        defaults.update(component_overrides)
        return defaults

    def _get_component_overrides(self) -> dict:
        """Override in subclasses to provide component-specific overrides."""
        return {"text_convert": [[False]]}  # Default: disable text conversion

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
            if isinstance(value, (str, int, float, bool)):
                setattr(self, attr, [value])
        return self


class RTFFootnote(RTFTableTextComponent):
    """RTF footnote component with table rendering enabled by default."""

    def _get_default_as_table(self) -> bool:
        return True  # Footnotes default to table rendering


class RTFSource(RTFTableTextComponent):
    """RTF source component with plain text rendering by default and center justification."""

    def _get_default_as_table(self) -> bool:
        return False  # Sources default to plain text rendering

    def _get_component_overrides(self) -> dict:
        base_overrides = super()._get_component_overrides()
        base_overrides.update(
            {
                "text_justification": [["c"]],  # Center justification for sources
            }
        )
        return base_overrides


class RTFTitle(RTFTextComponent):
    """RTF title component with center-aligned text and LaTeX conversion enabled."""

    def _get_component_defaults(self) -> dict:
        return DefaultsFactory.get_title_defaults()


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
            "as_colheader",
            "page_by",
            "new_page",
            "pageby_header",
            "pageby_row",
            "subline_by",
            "last_row",
        }

        for attr, value in self.__dict__.items():
            if (
                isinstance(value, (str, int, float, bool))
                and attr not in excluded_attrs
            ):
                setattr(self, attr, [value])

    def _set_border_defaults(self) -> None:
        """Set default values for border and justification attributes."""
        self.border_top = self.border_top or [""]
        self.border_bottom = self.border_bottom or [""]
        self.border_left = self.border_left or ["single"]
        self.border_right = self.border_right or ["single"]
        self.border_first = self.border_first or ["single"]
        self.border_last = self.border_last or ["single"]
        self.cell_vertical_justification = self.cell_vertical_justification or [
            "center"
        ]
        self.text_justification = self.text_justification or ["c"]

    def _validate_page_by_logic(self) -> None:
        """Validate that page_by and new_page settings are consistent."""
        if self.page_by is None and self.new_page:
            raise ValueError("`new_page` must be `False` if `page_by` is not specified")


class RTFFigure(BaseModel):
    """RTF Figure component for embedding images in RTF documents.

    This class handles figure embedding with support for multiple images,
    custom sizing, and proper RTF encoding.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Figure data
    figures: str | Path | list[str | Path] | None = Field(
        default=None,
        description="Image file path(s) - single path or list of paths to PNG, JPEG, or EMF files",
    )

    # Figure dimensions
    fig_height: float | list[float] = Field(
        default=5.0, description="Height of figures in inches (single value or list)"
    )
    fig_width: float | list[float] = Field(
        default=5.0, description="Width of figures in inches (single value or list)"
    )

    # Figure positioning
    fig_align: str = Field(
        default="center",
        description="Horizontal alignment of figures ('left', 'center', 'right')",
    )
    fig_pos: str = Field(
        default="after",
        description="Position relative to table content ('before' or 'after')",
    )

    @field_validator("fig_height", "fig_width", mode="before")
    def convert_dimensions(cls, v):
        """Convert single value to list if needed."""
        if isinstance(v, (int, float)):
            return [v]
        return v

    @field_validator("fig_align")
    def validate_alignment(cls, v):
        """Validate figure alignment value."""
        valid_alignments = ["left", "center", "right"]
        if v not in valid_alignments:
            raise ValueError(
                f"Invalid fig_align. Must be one of {valid_alignments}. Given: {v}"
            )
        return v

    @field_validator("fig_pos")
    def validate_position(cls, v):
        """Validate figure position value."""
        valid_positions = ["before", "after"]
        if v not in valid_positions:
            raise ValueError(
                f"Invalid fig_pos. Must be one of {valid_positions}. Given: {v}"
            )
        return v

    @model_validator(mode="after")
    def validate_figure_data(self):
        """Validate figure paths and convert to list format."""
        if self.figures is not None:
            # Convert single path to list
            if isinstance(self.figures, (str, Path)):
                self.figures = [self.figures]
            
            # Validate that all files exist
            for fig_path in self.figures:
                path_obj = Path(fig_path)
                if not path_obj.exists():
                    raise FileNotFoundError(f"Figure file not found: {fig_path}")
        
        return self
