from collections.abc import MutableSequence, Sequence
from typing import Any, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

from rtflite.row import (
    BORDER_CODES,
    FORMAT_CODES,
    TEXT_JUSTIFICATION_CODES,
    Border,
    Cell,
    Row,
    TextContent,
    Utils,
)
from rtflite.strwidth import get_string_width


class TextAttributes(BaseModel):
    """Base class for text-related attributes in RTF components"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text_font: Sequence[int] | None = Field(
        default=None, description="Font number for text"
    )

    @field_validator("text_font", mode="after")
    def validate_text_font(cls, v):
        if v is not None:
            for font in v:
                if font not in Utils._font_type()["type"]:
                    raise ValueError(f"Invalid font number: {font}")
        return v

    text_format: Sequence[str] | None = Field(
        default=None,
        description="Text formatting (e.g. 'b' for 'bold', 'i' for'italic')",
    )

    @field_validator("text_format", mode="after")
    def validate_text_format(cls, v):
        if v is not None:
            for format in v:
                for fmt in format:
                    if fmt not in FORMAT_CODES:
                        raise ValueError(f"Invalid text format: {fmt}")
        return v

    text_font_size: Sequence[float] | None = Field(
        default=None, description="Font size in points"
    )

    @field_validator("text_font_size", mode="after")
    def validate_text_font_size(cls, v):
        if v is not None:
            for size in v:
                if size <= 0:
                    raise ValueError(f"Invalid font size: {size}")
        return v

    text_color: Sequence[str] | None = Field(
        default=None, description="Text color name or RGB value"
    )
    text_background_color: Sequence[str] | None = Field(
        default=None, description="Background color name or RGB value"
    )
    text_justification: Sequence[str] | None = Field(
        default=None,
        description="Text alignment ('l'=left, 'c'=center, 'r'=right, 'j'=justify)",
    )

    @field_validator("text_justification", mode="after")
    def validate_text_justification(cls, v):
        if v is not None:
            for justification in v:
                if justification not in TEXT_JUSTIFICATION_CODES:
                    raise ValueError(f"Invalid text justification: {justification}")
        return v

    text_indent_first: Sequence[int] | None = Field(
        default=None, description="First line indent in twips"
    )
    text_indent_left: Sequence[int] | None = Field(
        default=None, description="Left indent in twips"
    )
    text_indent_right: Sequence[int] | None = Field(
        default=None, description="Right indent in twips"
    )
    text_space: Sequence[int] | None = Field(
        default=None, description="Line spacing multiplier"
    )
    text_space_before: Sequence[int] | None = Field(
        default=None, description="Space before paragraph in twips"
    )
    text_space_after: Sequence[int] | None = Field(
        default=None, description="Space after paragraph in twips"
    )
    text_hyphenation: Sequence[bool] | None = Field(
        default=None, description="Enable automatic hyphenation"
    )
    text_convert: Sequence[bool] | None = Field(
        default=None, description="Convert special characters to RTF"
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

    def _encode(self, text: Sequence[str], method: str) -> str:
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


class TableAttributes(TextAttributes):
    """Base class for table-related attributes in RTF components"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    col_rel_width: list[float] | None = Field(
        default=None, description="Relative widths of table columns"
    )

    @field_validator("col_rel_width", mode="after")
    def validate_col_rel_width(cls, v):
        if v is not None:
            for width in v:
                if width <= 0:
                    raise ValueError(f"Invalid column width: {width}")
        return v

    border_left: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Left border style"
    )
    border_right: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Right border style"
    )
    border_top: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Top border style"
    )
    border_bottom: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Bottom border style"
    )
    border_first: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="First row border style"
    )
    border_last: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Last row border style"
    )
    border_color_left: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Left border color"
    )
    border_color_right: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Right border color"
    )
    border_color_top: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Top border color"
    )
    border_color_bottom: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Bottom border color"
    )
    border_color_first: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="First row border color"
    )
    border_color_last: Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Last row border color"
    )
    border_width: Sequence[int] | pd.DataFrame | None = Field(
        default=None, description="Border width in twips"
    )
    cell_height: Sequence[float] | pd.DataFrame | None = Field(
        default=None, description="Cell height in inches"
    )
    cell_justification: Sequence[str] | pd.DataFrame | None = Field(
        default=None,
        description="Cell horizontal alignment ('l'=left, 'c'=center, 'r'=right, 'j'=justify)",
    )

    @field_validator("cell_justification", mode="after")
    def validate_cell_justification(cls, v):
        if v is not None:
            for justification in v:
                if justification not in TEXT_JUSTIFICATION_CODES:
                    raise ValueError(f"Invalid cell justification: {justification}")
        return v

    cell_vertical_justification: Sequence[str] | pd.DataFrame | None = Field(
        default=None,
        description="Cell vertical alignment ('top', 'center', 'bottom')",
    )

    # @field_validator("cell_vertical_justification", mode="after")
    # def validate_cell_vertical_justification(cls, v):
    #     if v is not None:
    #         for justification in v:
    #             if justification not in VERTICAL_ALIGNMENT_CODES:
    #                 raise ValueError(
    #                     f"Invalid cell vertical justification: {justification}"
    #                 )

    cell_nrow: Sequence[int] | pd.DataFrame | None = Field(
        default=None, description="Number of rows per cell"
    )

    @field_validator(
        "col_rel_width",
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
        mode="before",
    )
    def convert_to_list(cls, v):
        """Convert single values to data frame."""
        if v is not None and isinstance(v, (int, str, float, bool)):
            v = [v]

        return v

    @field_validator("border_width", "cell_height", "cell_nrow", mode="after")
    def validate_positive_value(cls, v):
        if v is not None:
            for value in v:
                if value <= 0:
                    raise ValueError(
                        f"{cls.__field_name__.capitalize()} with invalid number of rows per cell: {value}"
                    )
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
        if v is not None:
            for border in v:
                if border not in BORDER_CODES:
                    raise ValueError(
                        f"{cls.__field_name__.capitalize()} with invalid border style: {border}"
                    )
        return v

    def _get_section_attributes(self, indices) -> dict:
        """Helper method to collect all attributes for a section"""
        text_attrs = {
            "text_font": self.text_font,
            "text_format": self.text_format,
            "text_font_size": self.text_font_size,
            "text_color": self.text_color,
            "text_background_color": self.text_background_color,
            "text_justification": self.text_justification,
            "text_indent_first": self.text_indent_first,
            "text_indent_left": self.text_indent_left,
            "text_indent_right": self.text_indent_right,
            "text_space": self.text_space,
            "text_space_before": self.text_space_before,
            "text_space_after": self.text_space_after,
            "text_hyphenation": self.text_hyphenation,
            "text_convert": self.text_convert,
            "col_rel_width": self.col_rel_width,
            "border_left": self.border_left,
            "border_right": self.border_right,
            "border_top": self.border_top,
            "border_bottom": self.border_bottom,
            "border_first": self.border_first,
            "border_last": self.border_last,
            "border_color_left": self.border_color_left,
            "border_color_right": self.border_color_right,
            "border_color_top": self.border_color_top,
            "border_color_bottom": self.border_color_bottom,
            "border_color_first": self.border_color_first,
            "border_color_last": self.border_color_last,
            "border_width": self.border_width,
            "cell_height": self.cell_height,
            "cell_justification": self.cell_justification,
            "cell_vertical_justification": self.cell_vertical_justification,
            "cell_nrow": self.cell_nrow,
        }

        # Broadcast attributes to section indices
        return {
            attr: [BroadcastValue(value=val).iloc(row, col) for row, col in indices]
            for attr, val in text_attrs.items()
        }

    def _encode(
        self, df: pd.DataFrame, col_widths: Sequence[float]
    ) -> MutableSequence[str]:
        dim = df.shape

        def get_broadcast_value(attr_name, row_idx, col_idx=0):
            """Helper function to get broadcast value for a given attribute at specified indices."""
            attr_value = getattr(self, attr_name)
            return BroadcastValue(value=attr_value, dimension=dim).iloc(
                row_idx, col_idx
            )

        if self.cell_nrow is None:
            self.cell_nrow = np.zeros(dim)

            for i in range(dim[0]):
                for j in range(dim[1]):
                    text = str(BroadcastValue(value=df, dimension=dim).iloc(i, j))
                    font_size = BroadcastValue(
                        value=self.text_font_size, dimension=dim
                    ).iloc(i, j)
                    col_width = BroadcastValue(value=col_widths, dimension=dim).iloc(
                        i, j
                    )
                    cell_text_width = get_string_width(text=text, font_size=font_size)
                    self.cell_nrow[i, j] = np.ceil(cell_text_width / col_width)

        rows: MutableSequence[str] = []
        for i in range(dim[0]):
            row = df.iloc[i]
            cells = []

            for j in range(dim[1]):
                col = df.columns[j]

                if j == dim[1] - 1:
                    border_right = Border(
                        style=BroadcastValue(
                            value=self.border_right, dimension=dim
                        ).iloc(i, j)
                    )
                else:
                    border_right = None

                cell = Cell(
                    text=TextContent(
                        text=str(row[col]),
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

    value: Sequence[Any] | pd.DataFrame | None = Field(
        ...,
        description="The value of the table, can be various types including DataFrame.",
    )

    dimension: Tuple[int, int] | None = Field(
        None, description="Dimensions of the table (rows, columns)"
    )

    @field_validator("value", mode="before")
    def convert_value(cls, v):
        if isinstance(v, (str, int, float, bool)):
            v = [v]
        return v

    @field_validator("dimension")
    def validate_dimension(cls, v):
        if v is None:
            return v

        if not isinstance(v, tuple) or len(v) != 2:
            raise TypeError("dimension must be a tuple of (rows, columns)")

        rows, cols = v
        if not isinstance(rows, int) or not isinstance(cols, int):
            raise TypeError("dimension values must be integers")

        if rows <= 0 or cols <= 0:
            raise ValueError("dimension values must be positive")

        return v

    def iloc(self, row_index: int | slice, column_index: int | slice) -> Any:
        """
        Access a value using row and column indices, based on the data type.

        Parameters:
        - row_index: The row index or slice (for lists and DataFrames).
        - column_index: The column index or slice (for DataFrames and dictionaries). Optional for lists.

        Returns:
        - The accessed value or an appropriate error message.
        """
        if self.value is None:
            return None

        if isinstance(self.value, pd.DataFrame):
            # Handle DataFrame as is
            try:
                return self.value.iloc[
                    row_index % self.value.shape[0], column_index % self.value.shape[1]
                ]
            except IndexError as e:
                raise ValueError(f"Invalid DataFrame index or slice: {e}")

        if isinstance(self.value, list):
            # Handle list as column based broadcast data frame
            return self.value[column_index % len(self.value)]

        if isinstance(self.value, tuple):
            # Handle Tuple as row based broadcast data frame
            values = list(self.value)
            return values[row_index % len(values)]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the value to a pandas DataFrame based on the dimension variable if it is not None.

        Returns:
        - A pandas DataFrame representation of the value.

        Raises:
        - ValueError: If the dimension is None or if the value cannot be converted to a DataFrame.
        """
        if self.dimension is None:
            if isinstance(self.value, pd.DataFrame):
                self.dimension = self.value.shape
            elif isinstance(self.value, list):
                self.dimension = (1, len(self.value))
            elif isinstance(self.value, tuple):
                self.dimension = (len(self.value), 1)
            else:
                raise ValueError("Dimension must be specified to convert to DataFrame.")

        if isinstance(self.value, pd.DataFrame):
            # Ensure the DataFrame can be recycled to match the specified dimensions
            row_count, col_count = self.value.shape
            row_repeats = max(1, (self.dimension[0] + row_count - 1) // row_count)
            recycled_rows = pd.concat(
                [self.value] * row_repeats, ignore_index=True
            ).head(self.dimension[0])

            col_repeats = max(1, (self.dimension[1] + col_count - 1) // col_count)
            recycled_df = pd.concat([recycled_rows] * col_repeats, axis=1).iloc[
                :, : self.dimension[1]
            ]

            return recycled_df.reset_index(drop=True)

        if isinstance(self.value, (list, MutableSequence)):
            recycled_values = self.value * (self.dimension[1] // len(self.value) + 1)
            return pd.DataFrame(
                [
                    [
                        recycled_values[i % len(recycled_values)]
                        for i in range(self.dimension[1])
                    ]
                ]
                * self.dimension[0]
            )

        if isinstance(self.value, tuple):
            values = list(self.value)
            return pd.DataFrame(
                [
                    [values[i % len(values)]] * self.dimension[1]
                    for i in range(self.dimension[0])
                ]
            )

        raise ValueError("Unsupported value type for DataFrame conversion.")

    def update_row(self, row_index: int, row_value: list):
        value = self.to_dataframe()
        value.iloc[row_index] = row_value
        return value

    def update_column(self, column_index: int, column_value: list):
        value = self.to_dataframe()
        value.iloc[:, column_index] = column_value
        return value

    def update_cell(self, row_index: int, column_index: int, cell_value: Any):
        value = self.to_dataframe()
        value.iloc[row_index, column_index] = cell_value
        return value
