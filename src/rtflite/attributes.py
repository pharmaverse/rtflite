import math
from collections.abc import MutableSequence, Sequence
from typing import Any, Tuple

import narwhals as nw
import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator

from rtflite.row import (
    BORDER_CODES,
    FORMAT_CODES,
    TEXT_JUSTIFICATION_CODES,
    VERTICAL_ALIGNMENT_CODES,
    Border,
    Cell,
    Row,
    TextContent,
    Utils,
)
from rtflite.services.color_service import color_service
from rtflite.strwidth import get_string_width


def _to_nested_list(v):
    if v is None:
        return None

    if isinstance(v, (int, str, float, bool)):
        v = [[v]]

    if isinstance(v, Sequence):
        if isinstance(v, list) and any(
            isinstance(item, (str, int, float, bool)) for item in v
        ):
            v = [v]
        elif isinstance(v, list) and all(isinstance(item, list) for item in v):
            v = v
        elif isinstance(v, tuple):
            v = [[item] for item in v]
        else:
            raise TypeError("Invalid value type. Must be a list or tuple.")

    # Use narwhals to handle any DataFrame type
    if hasattr(v, "__dataframe__") or hasattr(
        v, "columns"
    ):  # Check if it's DataFrame-like
        if isinstance(v, pl.DataFrame):
            v = v.rows()
        else:
            try:
                nw_df = nw.from_native(v)
                v = nw_df.to_native(pl.DataFrame).rows()
            except Exception:
                # If narwhals can't handle it, try direct conversion
                if isinstance(v, pl.DataFrame):
                    v = v.rows()

    # Convert numpy arrays or array-like objects to lists
    if hasattr(v, "__array__") and hasattr(v, "tolist"):
        v = v.tolist()

    return v


class TextAttributes(BaseModel):
    """Base class for text-related attributes in RTF components"""

    text_font: list[int] | list[list[int]] | None = Field(
        default=None, description="Font number for text"
    )

    @field_validator("text_font", mode="after")
    def validate_text_font(cls, v):
        if v is None:
            return v

        # Check if it's a nested list
        if v and isinstance(v[0], list):
            for row in v:
                for font in row:
                    if font not in Utils._font_type()["type"]:
                        raise ValueError(f"Invalid font number: {font}")
        else:
            # Flat list
            for font in v:
                if font not in Utils._font_type()["type"]:
                    raise ValueError(f"Invalid font number: {font}")
        return v

    text_format: list[str] | list[list[str]] | None = Field(
        default=None,
        description="Text formatting (e.g. 'b' for 'bold', 'i' for'italic')",
    )

    @field_validator("text_format", mode="after")
    def validate_text_format(cls, v):
        if v is None:
            return v

        # Check if it's a nested list
        if v and isinstance(v[0], list):
            for row in v:
                for format in row:
                    for fmt in format:
                        if fmt not in FORMAT_CODES:
                            raise ValueError(f"Invalid text format: {fmt}")
        else:
            # Flat list
            for format in v:
                for fmt in format:
                    if fmt not in FORMAT_CODES:
                        raise ValueError(f"Invalid text format: {fmt}")
        return v

    text_font_size: list[float] | list[list[float]] | None = Field(
        default=None, description="Font size in points"
    )

    @field_validator("text_font_size", mode="after")
    def validate_text_font_size(cls, v):
        if v is None:
            return v

        # Check if it's a nested list
        if v and isinstance(v[0], list):
            for row in v:
                for size in row:
                    if size <= 0:
                        raise ValueError(f"Invalid font size: {size}")
        else:
            # Flat list
            for size in v:
                if size <= 0:
                    raise ValueError(f"Invalid font size: {size}")
        return v

    text_color: list[str] | list[list[str]] | None = Field(
        default=None, description="Text color name or RGB value"
    )

    @field_validator("text_color", mode="after")
    def validate_text_color(cls, v):
        if v is None:
            return v

        # Check if it's a nested list
        if v and isinstance(v[0], list):
            for row in v:
                for color in row:
                    # Allow empty string for "no color"
                    if color and not color_service.validate_color(color):
                        suggestions = color_service.get_color_suggestions(color, 3)
                        suggestion_text = (
                            f" Did you mean: {', '.join(suggestions)}?"
                            if suggestions
                            else ""
                        )
                        raise ValueError(
                            f"Invalid text color: '{color}'.{suggestion_text}"
                        )
        else:
            # Flat list
            for color in v:
                # Allow empty string for "no color"
                if color and not color_service.validate_color(color):
                    suggestions = color_service.get_color_suggestions(color, 3)
                    suggestion_text = (
                        f" Did you mean: {', '.join(suggestions)}?"
                        if suggestions
                        else ""
                    )
                    raise ValueError(f"Invalid text color: '{color}'.{suggestion_text}")
        return v

    text_background_color: list[str] | list[list[str]] | None = Field(
        default=None, description="Background color name or RGB value"
    )

    @field_validator("text_background_color", mode="after")
    def validate_text_background_color(cls, v):
        if v is None:
            return v

        # Check if it's a nested list
        if v and isinstance(v[0], list):
            for row in v:
                for color in row:
                    # Allow empty string for "no color"
                    if color and not color_service.validate_color(color):
                        suggestions = color_service.get_color_suggestions(color, 3)
                        suggestion_text = (
                            f" Did you mean: {', '.join(suggestions)}?"
                            if suggestions
                            else ""
                        )
                        raise ValueError(
                            f"Invalid text background color: '{color}'.{suggestion_text}"
                        )
        else:
            # Flat list
            for color in v:
                # Allow empty string for "no color"
                if color and not color_service.validate_color(color):
                    suggestions = color_service.get_color_suggestions(color, 3)
                    suggestion_text = (
                        f" Did you mean: {', '.join(suggestions)}?"
                        if suggestions
                        else ""
                    )
                    raise ValueError(
                        f"Invalid text background color: '{color}'.{suggestion_text}"
                    )
        return v

    text_justification: list[str] | list[list[str]] | None = Field(
        default=None,
        description="Text alignment ('l'=left, 'c'=center, 'r'=right, 'j'=justify)",
    )

    @field_validator("text_justification", mode="after")
    def validate_text_justification(cls, v):
        if v is None:
            return v

        # Check if it's a nested list
        if v and isinstance(v[0], list):
            for row in v:
                for justification in row:
                    if justification not in TEXT_JUSTIFICATION_CODES:
                        raise ValueError(f"Invalid text justification: {justification}")
        else:
            # Flat list
            for justification in v:
                if justification not in TEXT_JUSTIFICATION_CODES:
                    raise ValueError(f"Invalid text justification: {justification}")
        return v

    text_indent_first: list[int] | list[list[int]] | None = Field(
        default=None, description="First line indent in twips"
    )
    text_indent_left: list[int] | list[list[int]] | None = Field(
        default=None, description="Left indent in twips"
    )
    text_indent_right: list[int] | list[list[int]] | None = Field(
        default=None, description="Right indent in twips"
    )
    text_space: list[int] | list[list[int]] | None = Field(
        default=None, description="Line spacing multiplier"
    )
    text_space_before: list[int] | list[list[int]] | None = Field(
        default=None, description="Space before paragraph in twips"
    )
    text_space_after: list[int] | list[list[int]] | None = Field(
        default=None, description="Space after paragraph in twips"
    )
    text_hyphenation: list[bool] | list[list[bool]] | None = Field(
        default=None, description="Enable automatic hyphenation"
    )
    text_convert: list[bool] | list[list[bool]] | None = Field(
        default=[True], description="Convert LaTeX commands to Unicode characters"
    )

    @field_validator(
        "text_font",
        "text_format",
        "text_font_size",
        "text_color",
        "text_background_color",
        "text_justification",
        "text_indent_first",
        "text_indent_left",
        "text_indent_right",
        "text_space",
        "text_space_before",
        "text_space_after",
        "text_hyphenation",
        "text_convert",
        mode="before",
    )
    def convert_to_list(cls, v):
        """Convert single values to lists before validation."""
        if v is not None and isinstance(v, (int, str, float, bool)):
            return [v]
        return v

    def _encode_text(self, text: Sequence[str], method: str) -> str:
        """Convert the RTF title into RTF syntax using the Text class."""

        dim = [len(text), 1]

        def get_broadcast_value(attr_name, row_idx, col_idx=0):
            """Helper function to get broadcast value for a given attribute at specified indices."""
            attr_value = getattr(self, attr_name)
            return BroadcastValue(value=attr_value, dimension=dim).iloc(
                row_idx, col_idx
            )

        text_components = []
        for i in range(dim[0]):
            text_components.append(
                TextContent(
                    text=str(text[i]),
                    font=get_broadcast_value("text_font", i),
                    size=get_broadcast_value("text_font_size", i),
                    format=get_broadcast_value("text_format", i),
                    color=get_broadcast_value("text_color", i),
                    background_color=get_broadcast_value("text_background_color", i),
                    justification=get_broadcast_value("text_justification", i),
                    indent_first=get_broadcast_value("text_indent_first", i),
                    indent_left=get_broadcast_value("text_indent_left", i),
                    indent_right=get_broadcast_value("text_indent_right", i),
                    space=get_broadcast_value("text_space", i),
                    space_before=get_broadcast_value("text_space_before", i),
                    space_after=get_broadcast_value("text_space_after", i),
                    convert=get_broadcast_value("text_convert", i),
                    hyphenation=get_broadcast_value("text_hyphenation", i),
                )
            )

        if method == "paragraph":
            return [
                text_component._as_rtf(method="paragraph")
                for text_component in text_components
            ]

        if method == "line":
            line = "\\line".join(
                [
                    text_component._as_rtf(method="plain")
                    for text_component in text_components
                ]
            )
            return TextContent(
                text=str(line),
                font=get_broadcast_value("text_font", i),
                size=get_broadcast_value("text_font_size", i),
                format=get_broadcast_value("text_format", i),
                color=get_broadcast_value("text_color", i),
                background_color=get_broadcast_value("text_background_color", i),
                justification=get_broadcast_value("text_justification", i),
                indent_first=get_broadcast_value("text_indent_first", i),
                indent_left=get_broadcast_value("text_indent_left", i),
                indent_right=get_broadcast_value("text_indent_right", i),
                space=get_broadcast_value("text_space", i),
                space_before=get_broadcast_value("text_space_before", i),
                space_after=get_broadcast_value("text_space_after", i),
                convert=get_broadcast_value("text_convert", i),
                hyphenation=get_broadcast_value("text_hyphenation", i),
            )._as_rtf(method="paragraph_format")

        raise ValueError(f"Invalid method: {method}")

    def calculate_lines(
        self, text: str, available_width: float, row_idx: int = 0, col_idx: int = 0
    ) -> int:
        """
        Calculate number of lines needed for text given available width.

        Args:
            text: Text content to measure
            available_width: Available width in inches
            row_idx: Row index for attribute lookup (default: 0)
            col_idx: Column index for attribute lookup (default: 0)

        Returns:
            Number of lines needed (minimum 1)
        """
        if not text or available_width <= 0:
            return 1

        # Create a dummy dimension for broadcast lookup
        dim = (max(1, row_idx + 1), max(1, col_idx + 1))

        # Get font attributes using broadcast logic - raise error if None
        if self.text_font is None:
            raise ValueError("text_font must be set to calculate lines")
        font_broadcast = BroadcastValue(value=self.text_font, dimension=dim)
        font_number = font_broadcast.iloc(row_idx, col_idx)

        if self.text_font_size is None:
            raise ValueError("text_font_size must be set to calculate lines")
        size_broadcast = BroadcastValue(value=self.text_font_size, dimension=dim)
        font_size = size_broadcast.iloc(row_idx, col_idx)

        # Calculate total text width
        total_width = get_string_width(
            text=text, font=font_number, font_size=font_size, unit="in"
        )

        # Simple approximation: divide total width by available width and round up
        return max(1, int(math.ceil(total_width / available_width)))


class TableAttributes(TextAttributes):
    """Base class for table-related attributes in RTF components"""

    col_rel_width: list[float] | None = Field(
        default=None, description="Relative widths of table columns"
    )

    border_left: list[list[str]] = Field(
        default=[[""]], description="Left border style"
    )
    border_right: list[list[str]] = Field(
        default=[[""]], description="Right border style"
    )
    border_top: list[list[str]] = Field(default=[[""]], description="Top border style")
    border_bottom: list[list[str]] = Field(
        default=[[""]], description="Bottom border style"
    )
    border_first: list[list[str]] = Field(
        default=[[""]], description="First row border style"
    )
    border_last: list[list[str]] = Field(
        default=[[""]], description="Last row border style"
    )
    border_color_left: list[list[str]] = Field(
        default=[[""]], description="Left border color"
    )
    border_color_right: list[list[str]] = Field(
        default=[[""]], description="Right border color"
    )
    border_color_top: list[list[str]] = Field(
        default=[[""]], description="Top border color"
    )
    border_color_bottom: list[list[str]] = Field(
        default=[[""]], description="Bottom border color"
    )
    border_color_first: list[list[str]] = Field(
        default=[[""]], description="First row border color"
    )
    border_color_last: list[list[str]] = Field(
        default=[[""]], description="Last row border color"
    )

    @field_validator(
        "border_color_left",
        "border_color_right",
        "border_color_top",
        "border_color_bottom",
        "border_color_first",
        "border_color_last",
        mode="after",
    )
    def validate_border_colors(cls, v):
        if v is None:
            return v

        for row in v:
            for color in row:
                # Allow empty string for no color
                if color and not color_service.validate_color(color):
                    suggestions = color_service.get_color_suggestions(color, 3)
                    suggestion_text = (
                        f" Did you mean: {', '.join(suggestions)}?"
                        if suggestions
                        else ""
                    )
                    raise ValueError(
                        f"Invalid border color: '{color}'.{suggestion_text}"
                    )
        return v

    border_width: list[list[int]] = Field(
        default=[[15]], description="Border width in twips"
    )
    cell_height: list[list[float]] = Field(
        default=[[0.15]], description="Cell height in inches"
    )
    cell_justification: list[list[str]] = Field(
        default=[["l"]],
        description="Cell horizontal alignment ('l'=left, 'c'=center, 'r'=right, 'j'=justify)",
    )

    cell_vertical_justification: list[list[str]] = Field(
        default=[["center"]],
        description="Cell vertical alignment ('top', 'center', 'bottom')",
    )

    @field_validator("cell_vertical_justification", mode="after")
    def validate_cell_vertical_justification(cls, v):
        if v is None:
            return v

        for row in v:
            for justification in row:
                if justification not in VERTICAL_ALIGNMENT_CODES:
                    raise ValueError(
                        f"Invalid cell vertical justification: {justification}"
                    )
        return v

    cell_nrow: list[list[int]] = Field(
        default=[[1]], description="Number of rows per cell"
    )

    @field_validator("col_rel_width", mode="before")
    def convert_col_rel_width_to_list(cls, v):
        if v is not None and isinstance(v, (int, str, float, bool)):
            return [v]
        return v

    @field_validator(
        "border_left",
        "border_right",
        "border_top",
        "border_bottom",
        "border_first",
        "border_last",
        "border_color_left",
        "border_color_right",
        "border_color_top",
        "border_color_bottom",
        "border_color_first",
        "border_color_last",
        "border_width",
        "cell_height",
        "cell_justification",
        "cell_vertical_justification",
        "cell_nrow",
        "text_font",
        "text_format",
        "text_font_size",
        "text_color",
        "text_background_color",
        "text_justification",
        "text_indent_first",
        "text_indent_left",
        "text_indent_right",
        "text_space",
        "text_space_before",
        "text_space_after",
        "text_hyphenation",
        "text_convert",
        mode="before",
    )
    def convert_to_nested_list(cls, v):
        return _to_nested_list(v)

    @field_validator(
        "col_rel_width", "border_width", "cell_height", "cell_nrow", mode="after"
    )
    def validate_positive_value(cls, v):
        if v is not None:
            # Check if any value is <= 0
            if isinstance(v[0], (list, tuple)):
                # 2D array
                if any(val <= 0 for row in v for val in row):
                    raise ValueError(
                        f"{cls.__field_name__.capitalize()} must be positive"
                    )
            else:
                # 1D array
                if any(val <= 0 for val in v):
                    raise ValueError(
                        f"{cls.__field_name__.capitalize()} must be positive"
                    )
        return v

    @field_validator("cell_justification", mode="after")
    def validate_cell_justification(cls, v):
        if v is None:
            return v

        for row in v:
            for justification in row:
                if justification not in TEXT_JUSTIFICATION_CODES:
                    raise ValueError(f"Invalid cell justification: {justification}")
        return v

    @field_validator(
        "border_left",
        "border_right",
        "border_top",
        "border_bottom",
        "border_first",
        "border_last",
        mode="after",
    )
    def validate_border(cls, v):
        """Validate that all border styles are valid."""
        if v is None:
            return v

        for row in v:
            for border in row:
                if border not in BORDER_CODES:
                    field_name = cls.__field_name__.capitalize()
                    raise ValueError(
                        f"{field_name} with invalid border style: {border}"
                    )

        return v

    def _get_section_attributes(self, indices) -> dict:
        """Helper method to collect all attributes for a section"""
        # Get all attributes that start with text_, col_, border_, or cell_
        attrs = {}
        for attr in dir(self):
            if (
                attr.startswith("text_")
                or attr.startswith("col_")
                or attr.startswith("border_")
                or attr.startswith("cell_")
            ):
                if not callable(getattr(self, attr)):
                    attrs[attr] = getattr(self, attr)

        # Broadcast attributes to section indices, excluding None values
        return {
            attr: [BroadcastValue(value=val).iloc(row, col) for row, col in indices]
            for attr, val in attrs.items()
            if val is not None
        }

    def _encode(
        self, df: pl.DataFrame, col_widths: Sequence[float]
    ) -> MutableSequence[str]:
        dim = df.shape

        def get_broadcast_value(attr_name, row_idx, col_idx=0):
            """Helper function to get broadcast value for a given attribute at specified indices."""
            attr_value = getattr(self, attr_name)
            return BroadcastValue(value=attr_value, dimension=dim).iloc(
                row_idx, col_idx
            )

        if self.cell_nrow is None:
            self.cell_nrow = [[0.0 for _ in range(dim[1])] for _ in range(dim[0])]

            for i in range(dim[0]):
                for j in range(dim[1]):
                    text = str(BroadcastValue(value=df, dimension=dim).iloc(i, j))
                    col_width = BroadcastValue(value=col_widths, dimension=dim).iloc(
                        i, j
                    )

                    # Enhanced: Use calculate_lines method for better text wrapping
                    self.cell_nrow[i, j] = self.calculate_lines(
                        text=text, available_width=col_width, row_idx=i, col_idx=j
                    )

        rows: MutableSequence[str] = []
        for i in range(dim[0]):
            row = df.row(i)
            cells = []

            for j in range(dim[1]):
                if j == dim[1] - 1:
                    border_right = Border(
                        style=BroadcastValue(
                            value=self.border_right, dimension=dim
                        ).iloc(i, j)
                    )
                else:
                    border_right = None

                # Handle null values - display as empty string instead of "None"
                raw_value = row[j]
                if raw_value is None:
                    cell_value = ""
                else:
                    cell_value = str(raw_value)

                cell = Cell(
                    text=TextContent(
                        text=cell_value,
                        font=get_broadcast_value("text_font", i, j),
                        size=get_broadcast_value("text_font_size", i, j),
                        format=get_broadcast_value("text_format", i, j),
                        color=get_broadcast_value("text_color", i, j),
                        background_color=get_broadcast_value(
                            "text_background_color", i, j
                        ),
                        justification=get_broadcast_value("text_justification", i, j),
                        indent_first=get_broadcast_value("text_indent_first", i, j),
                        indent_left=get_broadcast_value("text_indent_left", i, j),
                        indent_right=get_broadcast_value("text_indent_right", i, j),
                        space=get_broadcast_value("text_space", i, j),
                        space_before=get_broadcast_value("text_space_before", i, j),
                        space_after=get_broadcast_value("text_space_after", i, j),
                        convert=get_broadcast_value("text_convert", i, j),
                        hyphenation=get_broadcast_value("text_hyphenation", i, j),
                    ),
                    width=col_widths[j],
                    border_left=Border(style=get_broadcast_value("border_left", i, j)),
                    border_right=border_right,
                    border_top=Border(style=get_broadcast_value("border_top", i, j)),
                    border_bottom=Border(
                        style=get_broadcast_value("border_bottom", i, j)
                    ),
                    vertical_justification=get_broadcast_value(
                        "cell_vertical_justification", i, j
                    ),
                )
                cells.append(cell)
            rtf_row = Row(
                row_cells=cells,
                justification=get_broadcast_value("cell_justification", i, 0),
                height=get_broadcast_value("cell_height", i, 0),
            )
            rows.extend(rtf_row._as_rtf())

        return rows


class BroadcastValue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: list[list[Any]] | None = Field(
        ...,
        description="The value of the table, can be various types including DataFrame.",
    )

    dimension: Tuple[int, int] | None = Field(
        None, description="Dimensions of the table (rows, columns)"
    )

    @field_validator("value", mode="before")
    def convert_value(cls, v):
        return _to_nested_list(v)

    @field_validator("dimension")
    def validate_dimension(cls, v):
        if v is None:
            return v

        if not isinstance(v, tuple) or len(v) != 2:
            raise TypeError("dimension must be a tuple of (rows, columns)")

        rows, cols = v
        if not isinstance(rows, int) or not isinstance(cols, int):
            raise TypeError("dimension values must be integers")

        if rows < 0 or cols <= 0:
            raise ValueError("rows must be non-negative and cols must be positive")

        return v

    def iloc(self, row_index: int, column_index: int) -> Any:
        if self.value is None:
            return None

        try:
            return self.value[row_index % len(self.value)][
                column_index % len(self.value[0])
            ]
        except IndexError as e:
            raise ValueError(f"Invalid DataFrame index or slice: {e}")

    def to_list(self) -> list:
        if self.value is None:
            return None

        row_count, col_count = len(self.value), len(self.value[0])

        row_repeats = max(1, (self.dimension[0] + row_count - 1) // row_count)
        col_repeats = max(1, (self.dimension[1] + col_count - 1) // col_count)

        value = [column * col_repeats for column in self.value] * row_repeats
        return [row[: self.dimension[1]] for row in value[: self.dimension[0]]]

    def update_row(self, row_index: int, row_value: list):
        if self.value is None:
            return None

        self.value = self.to_list()
        self.value[row_index] = row_value
        return self.value

    def update_column(self, column_index: int, column_value: list):
        if self.value is None:
            return None

        self.value = self.to_list()
        for i, row in enumerate(self.value):
            row[column_index] = column_value[i]
        return self.value

    def update_cell(self, row_index: int, column_index: int, cell_value: Any):
        if self.value is None:
            return None

        self.value = self.to_list()
        self.value[row_index][column_index] = cell_value
        return self.value
