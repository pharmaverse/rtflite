from collections.abc import MutableSequence
from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .attributes import BroadcastValue
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
    TableAttributes,
)
from .pagination import RTFPagination, PageBreakCalculator, ContentDistributor
from .row import Utils


class RTFDocument(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pl.DataFrame = Field(
        ...,
        description="The DataFrame containing the data for the RTF document. Accepts pandas or polars DataFrame, internally converted to polars.",
    )
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
    
    @field_validator("rtf_column_header", mode="before")
    def convert_column_header_to_list(cls, v):
        """Convert single RTFColumnHeader to list"""
        if v is not None and isinstance(v, RTFColumnHeader):
            return [v]
        return v
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
        dim = self.df.shape
        # Set default values
        self.rtf_body.col_rel_width = self.rtf_body.col_rel_width or [1] * dim[1]
        
        # Inherit col_rel_width from rtf_body to rtf_column_header if not specified
        if self.rtf_column_header:
            for header in self.rtf_column_header:
                if header.col_rel_width is None:
                    header.col_rel_width = self.rtf_body.col_rel_width.copy()
        
        self._table_space = int(
            Utils._inch_to_twip(self.rtf_page.width - self.rtf_page.col_width) / 2
        )

        if self.rtf_subline is not None:
            if self.rtf_subline.text_indent_reference == "table":
                self.rtf_subline.text_space_before = (
                    self._table_space + self.rtf_subline.text_space_before
                )
                self.rtf_subline.text_space_after = (
                    self._table_space + self.rtf_subline.text_space_after
                )

        if self.rtf_page_header is not None:
            if self.rtf_page_header.text_indent_reference == "table":
                self.rtf_page_header.text_space_before = (
                    self._table_space + self.rtf_page_header.text_space_before
                )
                self.rtf_page_header.text_space_after = (
                    self._table_space + self.rtf_page_header.text_space_after
                )

        if self.rtf_page_footer is not None:
            if self.rtf_page_footer.text_indent_reference == "table":
                self.rtf_page_footer.text_space_before = (
                    self._table_space + self.rtf_page_footer.text_space_before
                )
                self.rtf_page_footer.text_space_after = (
                    self._table_space + self.rtf_page_footer.text_space_after
                )

    def _needs_pagination(self) -> bool:
        """Check if document needs pagination based on content size and page limits"""
        if self.rtf_body.page_by and self.rtf_body.new_page:
            return True

        # Create pagination instance to calculate rows needed
        pagination = RTFPagination(
            page_width=self.rtf_page.width,
            page_height=self.rtf_page.height,
            margin=self.rtf_page.margin,
            nrow=self.rtf_page.nrow,
            orientation=self.rtf_page.orientation,
        )

        calculator = PageBreakCalculator(pagination=pagination)
        col_total_width = self.rtf_page.col_width
        col_widths = Utils._col_widths(self.rtf_body.col_rel_width, col_total_width)

        # Calculate rows needed for content
        content_rows = calculator.calculate_content_rows(
            self.df, col_widths, self.rtf_body
        )

        total_rows = sum(content_rows)
        return total_rows > self.rtf_page.nrow

    def _create_pagination_instance(self) -> tuple[RTFPagination, ContentDistributor]:
        """Create pagination and content distributor instances"""
        pagination = RTFPagination(
            page_width=self.rtf_page.width,
            page_height=self.rtf_page.height,
            margin=self.rtf_page.margin,
            nrow=self.rtf_page.nrow,
            orientation=self.rtf_page.orientation,
        )

        calculator = PageBreakCalculator(pagination=pagination)
        distributor = ContentDistributor(pagination=pagination, calculator=calculator)

        return pagination, distributor

    def _rtf_page_break_encode(self) -> str:
        """Generate proper RTF page break sequence matching r2rtf format"""
        page_setup = (
            f"\\paperw{int(self.rtf_page.width * 1440)}"
            f"\\paperh{int(self.rtf_page.height * 1440)}\n\n"
            f"{self._rtf_page_margin_encode()}\n"
        )
        
        return f"{{\\pard\\fs2\\par}}\\page{{\\pard\\fs2\\par}}\n{page_setup}"

    def _apply_pagination_borders(
        self, rtf_attrs: TableAttributes, page_info: dict, total_pages: int
    ) -> TableAttributes:
        """Apply proper borders for paginated context following r2rtf design:
        
        rtf_page.border_first/last: Controls borders for the entire table
        rtf_body.border_first/last: Controls borders for each page  
        rtf_body.border_top/bottom: Controls borders for individual cells
        
        Logic:
        - First page, first row: Apply rtf_page.border_first (overrides rtf_body.border_first)
        - Last page, last row: Apply rtf_page.border_last (overrides rtf_body.border_last)
        - Non-first pages, first row: Apply rtf_body.border_first
        - Non-last pages, last row: Apply rtf_body.border_last
        - All other rows: Use existing border_top/bottom from rtf_body
        """
        from copy import deepcopy
        
        # Create a deep copy of the attributes to avoid modifying the original  
        page_attrs = deepcopy(rtf_attrs)
        page_df_height = page_info["data"].height
        
        if page_df_height == 0:
            return page_attrs
        
        # Apply borders based on page position
        # Only apply double borders to the very first and very last rows of the entire table
        
        # For first page: only apply rtf_page.border_first to table body if NO column headers
        # (Column headers get the page-level border when they exist)
        has_column_headers = self.rtf_column_header and len(self.rtf_column_header) > 0
        if page_info["is_first_page"] and not has_column_headers:
            if self.rtf_page.border_first:
                page_attrs = self._apply_border_to_row(
                    page_attrs, 0, "top", self.rtf_page.border_first, page_info["data"].width
                )
                
        if page_info["is_last_page"]:
            # Last page: Apply rtf_page.border_last to last row only
            if self.rtf_page.border_last:
                last_row_idx = page_df_height - 1
                page_attrs = self._apply_border_to_row(
                    page_attrs, last_row_idx, "bottom", self.rtf_page.border_last, page_info["data"].width
                )
                
        # Note: When column headers are present, they get the rtf_page.border_first
        # The table body only gets rtf_page.border_first when there are no column headers
            
        return page_attrs
    
    def _apply_border_to_row(
        self, page_attrs: TableAttributes, row_idx: int, border_side: str, border_style: str, num_cols: int
    ) -> TableAttributes:
        """Apply specified border style to a specific row"""
        border_attr = f"border_{border_side}"
        
        if not hasattr(page_attrs, border_attr):
            return page_attrs
            
        # Get current border values
        current_borders = getattr(page_attrs, border_attr)
        
        # Ensure borders list is large enough
        while len(current_borders) <= row_idx:
            current_borders.append(current_borders[-1] if current_borders else [""])
            
        # Ensure the row has enough columns
        while len(current_borders[row_idx]) < num_cols:
            current_borders[row_idx].append(
                current_borders[row_idx][-1] if current_borders[row_idx] else ""
            )
        
        # Apply specified border to all cells in this row
        for col_idx in range(num_cols):
            current_borders[row_idx][col_idx] = border_style
            
        # Update the attribute
        setattr(page_attrs, border_attr, current_borders)
        return page_attrs

    def _rtf_page_encode(self) -> str:
        """Define RTF page settings"""
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

    def _rtf_page_header_encode(self, method: str) -> str:
        """Convert the RTF page header into RTF syntax using the Text class."""
        if not self.rtf_page_header:
            return None

        return self.rtf_page_header._encode(
            text=self.rtf_page_header.text, method=method
        )

    def _rtf_page_header_encode(self, method: str) -> str:
        """Convert the RTF page header into RTF syntax using the Text class."""
        if self.rtf_page_header is None:
            return None

        encode = self.rtf_page_header._encode(
            text=self.rtf_page_header.text, method=method
        )
        return f"{{\\header{encode}}}"

    def _rtf_page_footer_encode(self, method: str) -> str:
        """Convert the RTF page footer into RTF syntax using the Text class."""
        if self.rtf_page_footer is None:
            return None

        encode = self.rtf_page_footer._encode(
            text=self.rtf_page_footer.text, method=method
        )
        return f"{{\\footer{encode}}}"

    def _rtf_title_encode(self, method: str) -> str:
        """Convert the RTF title into RTF syntax using the Text class."""
        if not self.rtf_title or not self.rtf_title.text:
            return None

        return self.rtf_title._encode(text=self.rtf_title.text, method=method)

    def _rtf_subline_encode(self, method: str) -> str:
        """Convert the RTF subline into RTF syntax using the Text class."""
        if self.rtf_subline is None or not self.rtf_subline.text:
            return None

        encode = self.rtf_subline._encode(text=self.rtf_subline.text, method=method)
        return encode

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
        data = self.df.to_dicts()
        var = self.rtf_body.page_by

        # Handle empty DataFrame
        if len(data) == 0:
            return None

        # obtain column names and dimensions
        columns = list(data[0].keys())

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

                need_header = False
                if level == len(var) - 1:
                    need_header = True
                else:
                    for lvl in range(level + 1):
                        if group[var[lvl]] != prev_values[var[lvl]]:
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

    def _rtf_footnote_encode(self) -> str:
        """Convert the RTF footnote into RTF syntax using the Text class."""
        rtf_attrs = self.rtf_footnote

        if rtf_attrs is None:
            return None

        col_total_width = self.rtf_page.col_width
        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

        # Create DataFrame from text string
        df = pl.DataFrame([[rtf_attrs.text]])
        return rtf_attrs._encode(df, col_widths)

    def _rtf_source_encode(self) -> str:
        """Convert the RTF source into RTF syntax using the Text class."""
        rtf_attrs = self.rtf_source

        if rtf_attrs is None:
            return None

        col_total_width = self.rtf_page.col_width
        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

        # Create DataFrame from text string
        df = pl.DataFrame([[rtf_attrs.text]])
        return rtf_attrs._encode(df, col_widths)

    def _rtf_body_encode(
        self, df: pl.DataFrame, rtf_attrs: TableAttributes | None
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
        col_total_width = self.rtf_page.col_width
        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

        # Check if pagination is needed
        if self._needs_pagination():
            return self._rtf_body_encode_paginated(df, rtf_attrs, col_widths)

        # Handle existing page_by grouping (non-paginated)
        page_by = self._page_by()
        if page_by is None:
            return rtf_attrs._encode(df, col_widths)

        rows = []
        for section in page_by:
            # Skip empty sections
            indices = [(row, col) for row, col, level in section]
            if not indices:
                continue

            # Create DataFrame for current section
            section_df = pl.DataFrame(
                {
                    str(i): [BroadcastValue(value=df).iloc(row, col)]
                    for i, (row, col) in enumerate(indices)
                }
            )

            # Collect all text and table attributes
            section_attrs_dict = rtf_attrs._get_section_attributes(indices)
            section_attrs = TableAttributes(**section_attrs_dict)

            # Calculate column widths and encode section
            section_col_widths = Utils._col_widths(
                section_attrs.col_rel_width, col_total_width
            )
            rows.extend(section_attrs._encode(section_df, section_col_widths))

        return rows

    def _rtf_body_encode_paginated(
        self, df: pl.DataFrame, rtf_attrs: TableAttributes, col_widths: list[float]
    ) -> MutableSequence[str]:
        """Encode body content with pagination support"""
        _, distributor = self._create_pagination_instance()

        # Distribute content across pages
        pages = distributor.distribute_content(
            df=df,
            col_widths=col_widths,
            page_by=self.rtf_body.page_by,
            new_page=self.rtf_body.new_page,
            pageby_header=self.rtf_body.pageby_header,
            table_attrs=rtf_attrs,
        )

        all_rows = []
        for page_info in pages:
            page_df = page_info["data"]

            # Add page break before each page (except first)
            if not page_info["is_first_page"]:
                all_rows.append(self._rtf_page_break_encode())

            # Create modified table attributes for pagination context
            page_attrs = self._apply_pagination_borders(
                rtf_attrs, page_info, len(pages)
            )

            # Encode page content with modified borders
            page_rows = page_attrs._encode(page_df, col_widths)
            all_rows.extend(page_rows)

        return all_rows

    def _should_show_element_on_page(
        self, element_location: str, page_info: dict
    ) -> bool:
        """Determine if an element should be shown on a specific page"""
        if element_location == "all":
            return True
        elif element_location == "first":
            return page_info["is_first_page"]
        elif element_location == "last":
            return page_info["is_last_page"]
        else:
            return False

    def _rtf_encode_paginated(self) -> str:
        """Generate RTF code for paginated documents"""
        dim = self.df.shape

        # Get pagination instance and distribute content
        _, distributor = self._create_pagination_instance()
        col_total_width = self.rtf_page.col_width
        col_widths = Utils._col_widths(self.rtf_body.col_rel_width, col_total_width)

        pages = distributor.distribute_content(
            df=self.df,
            col_widths=col_widths,
            page_by=self.rtf_body.page_by,
            new_page=self.rtf_body.new_page,
            pageby_header=self.rtf_body.pageby_header,
            table_attrs=self.rtf_body,
        )

        # Prepare border settings
        doc_border_top = BroadcastValue(
            value=self.rtf_page.border_first, dimension=(1, dim[1])
        ).to_list()[0]
        doc_border_bottom = BroadcastValue(
            value=self.rtf_page.border_last, dimension=(1, dim[1])
        ).to_list()[0]

        # Generate RTF for each page
        page_contents = []

        for page_info in pages:
            page_elements = []

            # Add page break before each page (except first)
            if not page_info["is_first_page"]:
                page_elements.append(self._rtf_page_break_encode())

            # Add title if it should appear on this page
            if (
                self.rtf_title
                and self.rtf_title.text
                and self._should_show_element_on_page(
                    self.rtf_page.page_title_location, page_info
                )
            ):
                title_content = self._rtf_title_encode(method="line")
                if title_content:
                    page_elements.append(title_content)
                    page_elements.append("\n")

            # Add subline if it should appear on this page
            if (
                self.rtf_subline
                and self.rtf_subline.text
                and self._should_show_element_on_page(
                    self.rtf_page.page_title_location, page_info
                )
            ):
                subline_content = self._rtf_subline_encode(method="line")
                if subline_content:
                    page_elements.append(subline_content)
                    page_elements.append("\n")

            # Add column headers if needed
            if page_info["needs_header"] and self.rtf_column_header:
                if (
                    self.rtf_column_header[0].text is None
                    and self.rtf_body.as_colheader
                ):
                    columns = [
                        col
                        for col in self.df.columns
                        if col not in (self.rtf_body.page_by or [])
                    ]
                    self.rtf_column_header[0].text = pl.DataFrame(
                        [columns],
                        schema=[f"col_{i}" for i in range(len(columns))],
                        orient="row",
                    )

                # Apply pagination borders to column headers
                from copy import deepcopy
                
                # Process each column header with proper borders
                header_elements = []
                for i, header in enumerate(self.rtf_column_header):
                    header_copy = deepcopy(header)
                    
                    # Apply page-level borders to column headers (matching non-paginated behavior)
                    if page_info["is_first_page"] and i == 0:  # First header on first page
                        if self.rtf_page.border_first and header_copy.text is not None:
                            header_dims = header_copy.text.shape
                            # Apply page border_first to top of first column header
                            header_copy.border_top = BroadcastValue(
                                value=header_copy.border_top, dimension=header_dims
                            ).update_row(0, [self.rtf_page.border_first] * header_dims[1])
                    
                    # Encode the header with modified borders
                    header_rtf = self._rtf_column_header_encode(df=header_copy.text, rtf_attrs=header_copy)
                    header_elements.extend(header_rtf)

                page_elements.extend(header_elements)

            # Add page content (table body) with proper border handling
            page_df = page_info["data"]
            
            # Apply pagination borders to the body attributes
            page_attrs = self._apply_pagination_borders(
                self.rtf_body, page_info, len(pages)
            )
            
            # Encode page content with modified borders
            page_body = page_attrs._encode(page_df, col_widths)
            page_elements.extend(page_body)

            # Add footnote if it should appear on this page
            if (
                self.rtf_footnote
                and self.rtf_footnote.text
                and self._should_show_element_on_page(
                    self.rtf_page.page_footnote_location, page_info
                )
            ):
                footnote_content = self._rtf_footnote_encode()
                if footnote_content:
                    page_elements.extend(footnote_content)

            # Add source if it should appear on this page
            if (
                self.rtf_source
                and self.rtf_source.text
                and self._should_show_element_on_page(
                    self.rtf_page.page_source_location, page_info
                )
            ):
                source_content = self._rtf_source_encode()
                if source_content:
                    page_elements.extend(source_content)

            page_contents.extend(page_elements)

        # Build complete RTF document
        return "\n".join(
            [
                item
                for item in [
                    self._rtf_start_encode(),
                    self._rtf_font_table_encode(),
                    "\n",
                    self._rtf_page_encode(),
                    self._rtf_page_margin_encode(),
                    self._rtf_page_header_encode(method="line"),
                    self._rtf_page_footer_encode(method="line"),
                    "\n".join(page_contents),
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

    def _rtf_column_header_encode(
        self, df: pl.DataFrame, rtf_attrs: TableAttributes | None
    ) -> MutableSequence[str]:
        dim = df.shape
        col_total_width = self.rtf_page.col_width

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
        font_charset = font_types["charset"]

        font_table = "{\\fonttbl"
        for rtf, style, name, charset in zip(
            font_rtf, font_style, font_name, font_charset
        ):
            font_table += f"{{{rtf}{style}{charset}\\fprq2 {name};}}\n"
        font_table += "}"

        return font_table

    def rtf_encode(self) -> str:
        """Generate RTF code"""
        # Use paginated encoding if pagination is needed
        if self._needs_pagination():
            return self._rtf_encode_paginated()
        # Otherwise use standard encoding
        dim = self.df.shape

        # Title
        rtf_title = self._rtf_title_encode(method="line")

        # Page Border
        doc_border_top = BroadcastValue(
            value=self.rtf_page.border_first, dimension=(1, dim[1])
        ).to_list()[0]
        doc_border_bottom = BroadcastValue(
            value=self.rtf_page.border_last, dimension=(1, dim[1])
        ).to_list()[0]
        page_border_top = BroadcastValue(
            value=self.rtf_body.border_first, dimension=(1, dim[1])
        ).to_list()[0]
        page_border_bottom = BroadcastValue(
            value=self.rtf_body.border_last, dimension=(1, dim[1])
        ).to_list()[0]

        # Column header
        if self.rtf_column_header is None:
            rtf_column_header = ""
            # Only update borders if DataFrame has rows
            if dim[0] > 0:
                self.rtf_body.border_top = BroadcastValue(
                    value=self.rtf_body.border_top, dimension=dim
                ).update_row(0, doc_border_top)
        else:
            if self.rtf_column_header[0].text is None and self.rtf_body.as_colheader:
                columns = [
                    col
                    for col in self.df.columns
                    if col not in (self.rtf_body.page_by or [])
                ]
                # Create DataFrame with explicit column names to ensure single row
                self.rtf_column_header[0].text = pl.DataFrame(
                    [columns],
                    schema=[f"col_{i}" for i in range(len(columns))],
                    orient="row",
                )
                self.rtf_column_header = self.rtf_column_header[:1]

            # Only update borders if DataFrame has rows
            if dim[0] > 0:
                self.rtf_column_header[0].border_top = BroadcastValue(
                    value=self.rtf_column_header[0].border_top, dimension=dim
                ).update_row(0, doc_border_top)

            rtf_column_header = [
                self._rtf_column_header_encode(df=header.text, rtf_attrs=header)
                for header in self.rtf_column_header
            ]

        # Only update borders if DataFrame has rows
        if dim[0] > 0:
            self.rtf_body.border_top = BroadcastValue(
                value=self.rtf_body.border_top, dimension=dim
            ).update_row(0, page_border_top)

        # Bottom border last line update
        if self.rtf_footnote is not None:
            self.rtf_footnote.border_bottom = BroadcastValue(
                value=self.rtf_footnote.border_bottom, dimension=(1, 1)
            ).update_row(0, page_border_bottom[0])

            self.rtf_footnote.border_bottom = BroadcastValue(
                value=self.rtf_footnote.border_bottom, dimension=(1, 1)
            ).update_row(0, doc_border_bottom[0])
        else:
            # Only update borders if DataFrame has rows
            if dim[0] > 0:
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
                item
                for item in [
                    self._rtf_start_encode(),
                    self._rtf_font_table_encode(),
                    "\n",
                    self._rtf_page_encode(),
                    self._rtf_page_margin_encode(),
                    self._rtf_page_header_encode(method="line"),
                    self._rtf_page_footer_encode(method="line"),
                    rtf_title,
                    "\n",
                    self._rtf_subline_encode(method="line"),
                    "\n".join(
                        header for sublist in rtf_column_header for header in sublist
                    )
                    if rtf_column_header
                    else None,
                    "\n".join(rtf_body),
                    "\n".join(self._rtf_footnote_encode())
                    if self.rtf_footnote is not None
                    else None,
                    "\n".join(self._rtf_source_encode())
                    if self.rtf_source is not None
                    else None,
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

    def write_rtf(self, file_path: str) -> None:
        """Write the RTF code into a `.rtf` file."""
        print(file_path)
        rtf_code = self.rtf_encode()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rtf_code)
