from collections.abc import MutableSequence, Sequence
from typing import Any, Text, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from .row import Border, Cell, Row, TextContent
from .strwidth import get_string_width


class TextAttributes(BaseModel):
    """Base class for text-related attributes in RTF components"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    text_font: int | Sequence[int] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Font number for text"
    )
    text_format: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Text formatting (e.g. 'bold', 'italic')"
    )
    text_font_size: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Font size in points"
    )
    text_color: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Text color name or RGB value"
    )
    text_background_color: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Background color name or RGB value"
    )
    text_justification: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None,
        description="Text alignment ('l'=left, 'c'=center, 'r'=right, 'j'=justify)",
    )
    text_indent_first: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="First line indent in inches/twips"
    )
    text_indent_left: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Left indent in inches/twips"
    )
    text_indent_right: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Right indent in inches/twips"
    )
    text_space: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Line spacing multiplier"
    )
    text_space_before: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Space before paragraph in twips"
    )
    text_space_after: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Space after paragraph in twips"
    )
    text_hyphenation: bool | Sequence[bool] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Enable automatic hyphenation"
    )
    text_convert: bool | Sequence[bool] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Convert special characters to RTF"
    )

    def _encode(self, text: Sequence[str], method: str) -> str:
        """Convert the RTF title into RTF syntax using the Text class."""

        dim = [len(text), 1]

        text_components = []
        for i in range(dim[0]):
            text_components.append(
                TextContent(
                    text=str(text[i]),
                    font=BroadcastValue(value=self.text_font, dimension=dim).iloc(i, 0),
                    size=BroadcastValue(value=self.text_font_size, dimension=dim).iloc(
                        i, 0
                    ),
                    format=BroadcastValue(value=self.text_format, dimension=dim).iloc(
                        i, 0
                    ),
                    color=BroadcastValue(value=self.text_color, dimension=dim).iloc(
                        i, 0
                    ),
                    background_color=BroadcastValue(
                        value=self.text_background_color, dimension=dim
                    ).iloc(i, 0),
                    justification=BroadcastValue(
                        value=self.text_justification, dimension=dim
                    ).iloc(i, 0),
                    indent_first=BroadcastValue(
                        value=self.text_indent_first, dimension=dim
                    ).iloc(i, 0),
                    indent_left=BroadcastValue(
                        value=self.text_indent_left, dimension=dim
                    ).iloc(i, 0),
                    indent_right=BroadcastValue(
                        value=self.text_indent_right, dimension=dim
                    ).iloc(i, 0),
                    space=BroadcastValue(value=self.text_space, dimension=dim).iloc(
                        i, 0
                    ),
                    space_before=BroadcastValue(
                        value=self.text_space_before, dimension=dim
                    ).iloc(i, 0),
                    space_after=BroadcastValue(
                        value=self.text_space_after, dimension=dim
                    ).iloc(i, 0),
                    convert=BroadcastValue(value=self.text_convert, dimension=dim).iloc(
                        i, 0
                    ),
                    hyphenation=BroadcastValue(
                        value=self.text_hyphenation, dimension=dim
                    ).iloc(i, 0),
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
                font=BroadcastValue(value=self.text_font, dimension=dim).iloc(i, 0),
                size=BroadcastValue(value=self.text_font_size, dimension=dim).iloc(
                    i, 0
                ),
                format=BroadcastValue(value=self.text_format, dimension=dim).iloc(i, 0),
                color=BroadcastValue(value=self.text_color, dimension=dim).iloc(i, 0),
                background_color=BroadcastValue(
                    value=self.text_background_color, dimension=dim
                ).iloc(i, 0),
                justification=BroadcastValue(
                    value=self.text_justification, dimension=dim
                ).iloc(i, 0),
                indent_first=BroadcastValue(
                    value=self.text_indent_first, dimension=dim
                ).iloc(i, 0),
                indent_left=BroadcastValue(
                    value=self.text_indent_left, dimension=dim
                ).iloc(i, 0),
                indent_right=BroadcastValue(
                    value=self.text_indent_right, dimension=dim
                ).iloc(i, 0),
                space=BroadcastValue(value=self.text_space, dimension=dim).iloc(i, 0),
                space_before=BroadcastValue(
                    value=self.text_space_before, dimension=dim
                ).iloc(i, 0),
                space_after=BroadcastValue(
                    value=self.text_space_after, dimension=dim
                ).iloc(i, 0),
                convert=BroadcastValue(value=self.text_convert, dimension=dim).iloc(
                    i, 0
                ),
                hyphenation=BroadcastValue(
                    value=self.text_hyphenation, dimension=dim
                ).iloc(i, 0),
            )._as_rtf(method="paragraph_format")

        raise ValueError(f"Invalid method: {method}")


class TableAttributes(TextAttributes):
    """Base class for table-related attributes in RTF components"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    col_rel_width: float | Sequence[float] | None = Field(
        default=None, description="Relative widths of table columns"
    )
    border_left: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Left border style"
    )
    border_right: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Right border style"
    )
    border_top: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Top border style"
    )
    border_bottom: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Bottom border style"
    )
    border_first: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="First row border style"
    )
    border_last: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Last row border style"
    )
    border_color_left: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Left border color"
    )
    border_color_right: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Right border color"
    )
    border_color_top: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Top border color"
    )
    border_color_bottom: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Bottom border color"
    )
    border_color_first: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="First row border color"
    )
    border_color_last: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Last row border color"
    )
    border_width: int | Sequence[int] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Border width in twips"
    )
    cell_height: float | Sequence[float] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Cell height in inches"
    )
    cell_justification: str | Sequence[str] | pd.DataFrame | Tuple | None = Field(
        default=None,
        description="Cell horizontal alignment ('l'=left, 'c'=center, 'r'=right, 'j'=justify)",
    )
    cell_vertical_justification: str | Sequence[str] | pd.DataFrame | Tuple | None = (
        Field(
            default=None,
            description="Cell vertical alignment ('top', 'center', 'bottom')",
        )
    )
    cell_nrow: int | Sequence[int] | pd.DataFrame | Tuple | None = Field(
        default=None, description="Number of rows per cell"
    )

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
                        font=BroadcastValue(value=self.text_font, dimension=dim).iloc(
                            i, j
                        ),
                        size=BroadcastValue(
                            value=self.text_font_size, dimension=dim
                        ).iloc(i, j),
                        format=BroadcastValue(
                            value=self.text_format, dimension=dim
                        ).iloc(i, j),
                        color=BroadcastValue(value=self.text_color, dimension=dim).iloc(
                            i, j
                        ),
                        background_color=BroadcastValue(
                            value=self.text_background_color, dimension=dim
                        ).iloc(i, j),
                        justification=BroadcastValue(
                            value=self.text_justification, dimension=dim
                        ).iloc(i, j),
                        indent_first=BroadcastValue(
                            value=self.text_indent_first, dimension=dim
                        ).iloc(i, j),
                        indent_left=BroadcastValue(
                            value=self.text_indent_left, dimension=dim
                        ).iloc(i, j),
                        indent_right=BroadcastValue(
                            value=self.text_indent_right, dimension=dim
                        ).iloc(i, j),
                        space=BroadcastValue(value=self.text_space, dimension=dim).iloc(
                            i, j
                        ),
                        space_before=BroadcastValue(
                            value=self.text_space_before, dimension=dim
                        ).iloc(i, j),
                        space_after=BroadcastValue(
                            value=self.text_space_after, dimension=dim
                        ).iloc(i, j),
                        convert=BroadcastValue(
                            value=self.text_convert, dimension=dim
                        ).iloc(i, j),
                        hyphenation=BroadcastValue(
                            value=self.text_hyphenation, dimension=dim
                        ).iloc(i, j),
                    ),
                    width=col_widths[j],
                    border_left=Border(
                        style=BroadcastValue(
                            value=self.border_left, dimension=dim
                        ).iloc(i, j)
                    ),
                    border_right=border_right,
                    border_top=Border(
                        style=BroadcastValue(value=self.border_top, dimension=dim).iloc(
                            i, j
                        )
                    ),
                    border_bottom=Border(
                        style=BroadcastValue(
                            value=self.border_bottom, dimension=dim
                        ).iloc(i, j)
                    ),
                    vertical_justification=BroadcastValue(
                        value=self.cell_vertical_justification, dimension=dim
                    ).iloc(i, j),
                )
                cells.append(cell)
            rtf_row = Row(
                row_cells=cells,
                justification=BroadcastValue(
                    value=self.cell_justification, dimension=dim
                ).iloc(i, 0),
                height=BroadcastValue(value=self.cell_height, dimension=dim).iloc(i, 0),
            )
            rows.extend(rtf_row._as_rtf())

        return rows


class BroadcastValue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    value: int | float | str | Tuple | Sequence[Any] | pd.DataFrame | None = Field(
        ...,
        description="The value of the table, can be various types including DataFrame.",
    )

    dimension: Tuple[int, int] | None = Field(
        None, description="Dimensions of the table (rows, columns)"
    )

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

        if isinstance(self.value, (int, float, str)):
            return self.value

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
            elif isinstance(self.value, (int, float, str)):
                self.dimension = (1, 1)
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

        if isinstance(self.value, (int, float, str)):
            return pd.DataFrame([[self.value] * self.dimension[1]] * self.dimension[0])

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


class RTFPage(BaseModel):
    """RTF page configuration"""

    width: float | None = Field(default=None, description="Page width in inches")
    height: float | None = Field(default=None, description="Page height in inches")
    margin: Sequence[float] | None = Field(
        default=None,
        description="Page margins [left, right, top, bottom, header, footer] in inches",
    )
    orientation: str | None = Field(
        default="portrait", description="Page orientation ('portrait' or 'landscape')"
    )
    col_width: float | None = Field(
        default=None, description="Total width of table columns in inches"
    )
    nrow: int | None = Field(default=None, description="Number of rows per page")
    use_color: bool | None = Field(
        default=False, description="Whether to use color in the document"
    )
    page_title: str | None = Field(default="all", description="Title display location")
    page_footnote: str | None = Field(
        default="last", description="Footnote display location"
    )
    page_source: str | None = Field(
        default="last", description="Source display location"
    )
    border_first: str | None = Field(
        default="double", description="First row border style"
    )
    border_last: str | None = Field(
        default="double", description="Last row border style"
    )

    def _set_default(self):
        if self.orientation == "portrait":
            self.width = self.width or 8.5
            self.height = self.height or 11
            self.margin = self.margin or [1.25, 1, 1.75, 1.25, 1.75, 1.00625]
            self.col_width = self.col_width or self.width - 2.25
            self.nrow = self.nrow or 40

        if self.orientation == "landscape":
            self.width = self.width or 11
            self.height = self.height or 8.5
            self.margin = self.margin or [1.0, 1.0, 2, 1.25, 1.25, 1.25]
            self.col_width = self.col_width or self.width - 2.5
            self.nrow = self.nrow or 24

        if len(self.margin) != 6:
            raise ValueError("Margin length must be 6.")

        return self


class RTFTitle(TextAttributes):
    text: str | Sequence[str] | None = Field(
        default=None, description="Title text content"
    )
    text_indent_reference: str | Sequence[str] | None = Field(
        default="table",
        description="Reference point for indentation ('page' or 'table')",
    )

    def __init__(self, **data):
        defaults = {
            "text_font": 1,
            "text_font_size": 12,
            "text_justification": "c",
            "text_indent_first": 0,
            "text_indent_left": 0,
            "text_indent_right": 0,
            "text_space": 1.0,
            "text_space_before": 180.0,
            "text_space_after": 180.0,
            "text_hyphenation": True,
            "text_convert": True,
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)

    def _set_default(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)):
                setattr(self, attr, [value])
            if isinstance(value, list):
                setattr(self, attr, tuple(value))
        return self


class RTFColumnHeader(TableAttributes):
    """Class for RTF column header settings"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: str | Sequence[str] | pd.DataFrame | None = Field(
        default=None, description="Column header table"
    )

    def __init__(self, **data):
        defaults = {
            "border_left": "single",
            "border_right": "single",
            "border_top": "single",
            "border_bottom": "",
            "border_width": 15,
            "cell_height": 0.15,
            "cell_justification": "c",
            "cell_vertical_justification": "bottom",
            "text_font": 1,
            "text_format": "",
            "text_font_size": 9,
            "text_justification": "c",
            "text_indent_first": 0,
            "text_indent_left": 0,
            "text_indent_right": 0,
            "text_space": 1,
            "text_space_before": 15,
            "text_space_after": 15,
            "text_hyphenation": False,
            "text_convert": True,
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)

        # Convert df to DataFrame during initialization
        if self.df is not None:
            self.df = BroadcastValue(value=self.df).to_dataframe()

    def _set_default(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)):
                setattr(self, attr, [value])

        return self


class RTFBody(TableAttributes):
    """Class for RTF document body settings"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    df: pd.DataFrame | None = Field(default=None, description="Table data")

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

    def __init__(self, **data):
        defaults = {
            "border_left": "single",
            "border_right": "single",
            "border_first": "single",
            "border_last": "single",
            "border_width": 15,
            "cell_height": 0.15,
            "cell_justification": "c",
            "cell_vertical_justification": "top",
            "text_font": 1,
            "text_font_size": 9,
            "text_indent_first": 0,
            "text_indent_left": 0,
            "text_indent_right": 0,
            "text_space": 1,
            "text_space_before": 15,
            "text_space_after": 15,
            "text_hyphenation": False,
            "text_convert": True,
        }

        # Update defaults with any provided values
        defaults.update(data)
        super().__init__(**defaults)

    def _set_default(self):
        for attr, value in self.__dict__.items():
            if isinstance(value, (str, int, float, bool)) and attr not in [
                "as_colheader",
                "page_by",
                "new_page",
                "pageby_header",
                "pageby_row",
                "subline_by",
                "last_row",
            ]:
                setattr(self, attr, [value])

        self.border_top = self.border_top or ""
        self.border_bottom = self.border_bottom or ""
        self.border_left = self.border_left or "single"
        self.border_right = self.border_right or "single"
        self.border_first = self.border_first or "single"
        self.border_last = self.border_last or "single"
        self.cell_vertical_justification = self.cell_vertical_justification or "c"
        self.text_justification = self.text_justification or "c"

        if self.page_by is None:
            if self.new_page:
                raise ValueError(
                    "`new_page` must be `False` if `page_by` is not specified"
                )

        return self
