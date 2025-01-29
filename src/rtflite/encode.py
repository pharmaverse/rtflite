from collections.abc import MutableSequence

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from .input import (
    BroadcastValue,
    RTFBody,
    RTFColumnHeader,
    RTFPage,
    RTFTitle,
    TableAttributes,
)
from .row import Border, Cell, Row, TextContent, Utils
from .strwidth import get_string_width


class RTFDocument(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame = Field(
        ..., description="The DataFrame containing the data for the RTF document."
    )
    rtf_page: RTFPage = Field(
        default_factory=lambda: RTFPage(),
        description="Page settings including size, orientation and margins",
    )
    rtf_page_header: str | None = Field(
        default=None, description="Text to appear in the header of each page"
    )
    rtf_title: RTFTitle | None = Field(
        default_factory=lambda: RTFTitle(),
        description="Title section settings including text and formatting",
    )
    rtf_subline: str | None = Field(
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
    rtf_footnote: str | None = Field(
        default=None, description="Footnote text to appear at bottom of document"
    )
    rtf_source: str | None = Field(
        default=None, description="Data source citation text"
    )
    rtf_page_footer: str | None = Field(
        default=None, description="Text to appear in the footer of each page"
    )

    def _rtf_page_encode(self) -> str:
        """Define RTF page settings"""

        self.rtf_page = self.rtf_page._set_default()

        page_size = [
            f"\\paperw{Utils._inch_to_twip(self.rtf_page.width)}",
            f"\\paperh{Utils._inch_to_twip(self.rtf_page.height)}",
        ]
        page_size = "".join(page_size)

        if self.rtf_page.orientation == "landscape":
            page_size += "\\landscape\n"
        else:
            page_size += "\n"

        # Add page footer if exists
        # if self.rtf_page.page_footer:
        #     footer = ["{\\footer", self._rtf_paragraph(self.rtf_page.page_footer), "}"]
        #     page_size = "\n".join(footer + [page_size])

        # Add page header if exists
        # if self.rtf_page.page_header:
        #     header = ["{\\header", self._rtf_paragraph(self.rtf_page.page_header), "}"]
        #     page_size = "\n".join(header + [page_size])

        return page_size

    def _rtf_page_margin_encode(self) -> str:
        """Define RTF margin settings"""

        self.rtf_page = self.rtf_page._set_default()

        margin_codes = [
            "\\margl",
            "\\margr",
            "\\margt",
            "\\margb",
            "\\headery",
            "\\footery",
        ]
        margins = [Utils._inch_to_twip(m) for m in self.rtf_page.margin]
        margin = "".join(
            f"{code}{margin}" for code, margin in zip(margin_codes, margins)
        )
        return margin + "\n"

    def _rtf_title_encode(self, method: str) -> str:
        """Convert the RTF title into RTF syntax using the Text class."""
        if not self.rtf_title:
            return None

        self.rtf_title = self.rtf_title._set_default()

        return self.rtf_title._encode(text=self.rtf_title.text, method=method)

    def _page_by(self) -> list[list[tuple[int, int, int]]]:
        """Create components for page_by format.

        This method organizes data into sections based on the page_by grouping variables.

        Returns:
            A list of sections, where each section is a list of tuples (row_idx, col_idx, level).
            Each tuple represents:
            - row_idx: The row index in the dataframe
            - col_idx: The column index in the dataframe
            - level: The nesting level of the section header.

        """
        # obtain input data
        data = self.df.to_dict("records")
        var = self.rtf_body.page_by

        # obtain column names and dimensions
        columns = list(data[0].keys())
        dim = (len(data), len(columns))

        if var is None:
            return None

        def get_column_index(column_name: str) -> int:
            """Get the index of a column in the column list."""
            return columns.index(column_name)

        def get_matching_rows(group_values: dict) -> list[int]:
            """Get row indices that match the group values."""
            return [
                i
                for i, row in enumerate(data)
                if all(row[k] == v for k, v in group_values.items())
            ]

        def get_unique_combinations(variables: list[str]) -> list[dict]:
            """Get unique combinations of values for the specified variables."""
            seen = set()
            unique = []
            for row in data:
                key = tuple(row[v] for v in variables)
                if key not in seen:
                    seen.add(key)
                    unique.append({v: row[v] for v in variables})
            return unique

        output = []
        prev_values = {v: None for v in var}

        # Process each unique combination of grouping variables
        for group in get_unique_combinations(var):
            indices = get_matching_rows(group)

            # Handle headers for each level
            for level, var_name in enumerate(var):
                current_val = group[var_name]

                # Check if we need to print this level's header
                # We print if either:
                # 1. This is the deepest level (always print)
                # 2. The value at this level has changed
                need_header = False
                if level == len(var) - 1:
                    need_header = True
                else:
                    for l in range(level + 1):
                        if group[var[l]] != prev_values[var[l]]:
                            need_header = True
                            break

                if need_header:
                    col_idx = get_column_index(var_name)
                    # Add level information as third element in tuple
                    output.append([(indices[0], col_idx, level)])

                prev_values[var_name] = current_val

            # Handle data rows
            for index in indices:
                output.append(
                    [
                        (index, j, len(var))
                        for j in range(len(columns))
                        if columns[j] not in var
                    ]
                )

        return output

    def _rtf_body_encode(
        self, df: pd.DataFrame, rtf_attrs: TableAttributes | None
    ) -> MutableSequence[str]:
        """Convert the RTF table into RTF syntax using the Cell class.

        Args:
            df: Input DataFrame to encode
            rtf_attrs: Table attributes for styling

        Returns:
            List of RTF-encoded strings representing table rows
        """
        if rtf_attrs is None:
            return None

        # Initialize dimensions and widths
        dim = df.shape
        col_total_width = self.rtf_page._set_default().col_width
        page_by = self._page_by()

        if page_by is None:
            col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)
            return rtf_attrs._encode(df, col_widths)

        rows = []
        for section in page_by:
            # Skip empty sections
            indices = [(row, col) for row, col, level in section]
            if not indices:
                continue

            # Create DataFrame for current section
            section_df = pd.DataFrame(
                {
                    i: [BroadcastValue(value=df).iloc(row, col)]
                    for i, (row, col) in enumerate(indices)
                }
            )

            # Collect all text and table attributes
            section_attrs_dict = rtf_attrs._get_section_attributes(indices)
            section_attrs = TableAttributes(**section_attrs_dict)

            # Calculate column widths and encode section
            col_widths = Utils._col_widths(section_attrs.col_rel_width, col_total_width)
            rows.extend(section_attrs._encode(section_df, col_widths))

        return rows

    def _rtf_column_header_encode(
        self, df: pd.DataFrame, rtf_attrs: TableAttributes | None
    ) -> MutableSequence[str]:
        dim = df.shape
        col_total_width = self.rtf_page._set_default().col_width

        if rtf_attrs is None:
            return None

        rtf_attrs.col_rel_width = rtf_attrs.col_rel_width or [1] * dim[1]
        rtf_attrs = rtf_attrs._set_default()

        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

        return rtf_attrs._encode(df, col_widths)

    def _rtf_start_encode(self) -> str:
        return "{\\rtf1\\ansi\n\\deff0\\deflang1033"

    def _rtf_font_table_encode(self) -> str:
        """Define RTF fonts"""
        font_types = Utils._font_type()
        font_rtf = [f"\\f{i}" for i in range(10)]
        font_style = font_types["style"]
        font_name = font_types["name"]

        font_table = "{\\fonttbl"
        for rtf, style, name in zip(font_rtf, font_style, font_name):
            font_table += f"{{{rtf}{style}\\fcharset161\\fprq2 {name};}}\n"
        font_table += "}"

        return font_table

    def rtf_encode(self) -> str:
        """Generate RTF code"""
        dim = self.df.shape
        # Set default values
        self.rtf_body.col_rel_width = self.rtf_body.col_rel_width or [1] * dim[1]
        self.rtf_body = self.rtf_body._set_default()

        # Title
        rtf_title = self._rtf_title_encode(method="line")

        # Page Border
        doc_border_top = BroadcastValue(
            value=self.rtf_page.border_first, dimension=(1, dim[1])
        ).to_dataframe()
        doc_border_bottom = BroadcastValue(
            value=self.rtf_page.border_last, dimension=(1, dim[1])
        ).to_dataframe()
        page_border_top = BroadcastValue(
            value=self.rtf_body.border_first, dimension=(1, dim[1])
        ).to_dataframe()
        page_border_bottom = BroadcastValue(
            value=self.rtf_body.border_last, dimension=(1, dim[1])
        ).to_dataframe()

        # Column header
        if self.rtf_column_header is None:
            rtf_column_header = ""
            self.rtf_body.border_top = BroadcastValue(
                value=self.rtf_body.border_top, dimension=dim
            ).update_row(0, doc_border_top)
        else:
            if self.rtf_column_header[0].df is None and self.rtf_body.as_colheader:
                columns = [
                    col
                    for col in self.df.columns
                    if col not in (self.rtf_body.page_by or [])
                ]
                self.rtf_column_header[0].df = pd.DataFrame([columns])
                self.rtf_column_header = self.rtf_column_header[:1]

            self.rtf_column_header[0].border_top = BroadcastValue(
                value=self.rtf_column_header[0], dimension=dim
            ).update_row(0, doc_border_top)

            rtf_column_header = [
                self._rtf_column_header_encode(df=header.df, rtf_attrs=header)
                for header in self.rtf_column_header
            ]

        self.rtf_body.border_top = BroadcastValue(
            value=self.rtf_body.border_top, dimension=dim
        ).update_row(0, page_border_top)
        self.rtf_body.border_bottom = BroadcastValue(
            value=self.rtf_body.border_bottom, dimension=dim
        ).update_row(dim[0] - 1, page_border_bottom)
        self.rtf_body.border_bottom = BroadcastValue(
            value=self.rtf_body.border_bottom, dimension=dim
        ).update_row(dim[0] - 1, doc_border_bottom)

        # Body
        rtf_body = self._rtf_body_encode(df=self.df, rtf_attrs=self.rtf_body)

        return "\n".join(
            [
                self._rtf_start_encode(),
                self._rtf_font_table_encode(),
                "\n",
                self._rtf_page_encode(),
                self._rtf_page_margin_encode(),
                rtf_title,
                "\n",
                "\n".join(
                    header for sublist in rtf_column_header for header in sublist
                ),
                "\n".join(rtf_body),
                "\n\n",
                "}",
            ]
        )

    def write_rtf(self, file_path: str) -> None:
        """Write the RTF code into a `.rtf` file."""
        print(file_path)
        rtf_code = self.rtf_encode()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rtf_code)
