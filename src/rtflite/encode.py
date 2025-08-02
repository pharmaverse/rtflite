from collections.abc import MutableSequence

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .attributes import BroadcastValue
from .core.constants import RTFConstants, RTFMeasurements
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
from .encoding import RTFEncodingEngine
from .services import RTFEncodingService


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
        # Initialize encoding service
        self._encoding_service = RTFEncodingService()
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

    def _calculate_additional_rows_per_page(self) -> int:
        """Calculate additional rows needed per page for headers, footnotes, sources (r2rtf compatible)

        Returns:
            Number of additional rows per page beyond data rows
        """
        additional_rows = 0

        # Count column headers (repeat on each page)
        if self.rtf_column_header:
            for header in self.rtf_column_header:
                if header.text is not None:
                    # Each header is typically 1 row, but could be multiline
                    # For now, conservatively count 1 row per header
                    additional_rows += 1

        # Count footnote rows (appears on pages based on page_footnote_location)
        if self.rtf_footnote and self.rtf_footnote.text:
            # Footnote is typically 1 row - for conservative estimate, assume it appears on each page
            additional_rows += 1

        # Count source rows (appears on pages based on page_source_location)
        if self.rtf_source and self.rtf_source.text:
            # Source is typically 1 row - for conservative estimate, assume it appears on each page
            additional_rows += 1

        return additional_rows

    def _needs_pagination(self) -> bool:
        """Check if document needs pagination based on content size and page limits (r2rtf compatible)

        Now counts ALL rows including headers, footnotes, sources like r2rtf does.
        In r2rtf, nrow includes headers, data, footnotes, sources - everything.
        """
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

        # Calculate rows needed for data content only
        content_rows = calculator.calculate_content_rows(
            self.df, col_widths, self.rtf_body
        )

        # Calculate additional rows per page (headers, footnotes, sources)
        additional_rows_per_page = self._calculate_additional_rows_per_page()

        # Calculate how many data rows can fit per page
        data_rows = sum(content_rows)
        available_data_rows_per_page = max(
            1, self.rtf_page.nrow - additional_rows_per_page
        )

        # If we can't fit even the additional components, we definitely need pagination
        if additional_rows_per_page >= self.rtf_page.nrow:
            return True

        # Check if data rows exceed what can fit on a single page
        return data_rows > available_data_rows_per_page

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
        """Generate proper RTF page break sequence - delegated to encoding service."""
        return self._encoding_service.encode_page_break(self.rtf_page, self._rtf_page_margin_encode)

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
        page_df_width = page_info["data"].width
        page_shape = (page_df_height, page_df_width)

        if page_df_height == 0:
            return page_attrs

        # Clear border_first and border_last from being broadcast to all rows
        # These should only apply to specific rows based on pagination logic
        if hasattr(page_attrs, "border_first") and page_attrs.border_first:
            # Don't use border_first in pagination - it's handled separately
            page_attrs.border_first = None

        if hasattr(page_attrs, "border_last") and page_attrs.border_last:
            # Don't use border_last in pagination - it's handled separately
            page_attrs.border_last = None

        # Ensure border_top and border_bottom are properly sized for this page
        if not page_attrs.border_top:
            page_attrs.border_top = [
                [""] * page_df_width for _ in range(page_df_height)
            ]
        if not page_attrs.border_bottom:
            page_attrs.border_bottom = [
                [""] * page_df_width for _ in range(page_df_height)
            ]

        # Apply borders based on page position
        # For first page: only apply rtf_page.border_first to table body if NO column headers
        has_column_headers = self.rtf_column_header and len(self.rtf_column_header) > 0
        if page_info["is_first_page"] and not has_column_headers:
            if self.rtf_page.border_first:
                # Apply border to all cells in the first row
                for col_idx in range(page_df_width):
                    page_attrs = self._apply_border_to_cell(
                        page_attrs,
                        0,
                        col_idx,
                        "top",
                        self.rtf_page.border_first,
                        page_shape,
                    )

        # For first page with column headers: ensure consistent border style
        if page_info["is_first_page"] and has_column_headers:
            # Apply same border style as non-first pages to maintain consistency
            if self.rtf_body.border_first:
                border_style = (
                    self.rtf_body.border_first[0][0]
                    if isinstance(self.rtf_body.border_first, list)
                    else self.rtf_body.border_first
                )
                # Apply single border style to first data row (same as other pages)
                for col_idx in range(page_df_width):
                    page_attrs = self._apply_border_to_cell(
                        page_attrs, 0, col_idx, "top", border_style, page_shape
                    )

        # Apply page-level borders for non-first/last pages
        if not page_info["is_first_page"] and self.rtf_body.border_first:
            # Apply border_first to first row of non-first pages
            border_style = (
                self.rtf_body.border_first[0][0]
                if isinstance(self.rtf_body.border_first, list)
                else self.rtf_body.border_first
            )
            for col_idx in range(page_df_width):
                page_attrs = self._apply_border_to_cell(
                    page_attrs, 0, col_idx, "top", border_style, page_shape
                )

        # Check if footnotes or sources will appear on this page
        has_footnote_on_page = (
            self.rtf_footnote
            and self.rtf_footnote.text
            and self._should_show_element_on_page(
                self.rtf_page.page_footnote_location, page_info
            )
        )
        has_source_on_page = (
            self.rtf_source
            and self.rtf_source.text
            and self._should_show_element_on_page(
                self.rtf_page.page_source_location, page_info
            )
        )

        # Apply border logic based on page position and footnote/source presence
        if not page_info["is_last_page"]:
            # Non-last pages: apply single border after footnote/source, or after data if no footnote/source
            if self.rtf_body.border_last:
                border_style = (
                    self.rtf_body.border_last[0][0]
                    if isinstance(self.rtf_body.border_last, list)
                    else self.rtf_body.border_last
                )

                if not (has_footnote_on_page or has_source_on_page):
                    # No footnote/source: apply border to last data row
                    for col_idx in range(page_df_width):
                        page_attrs = self._apply_border_to_cell(
                            page_attrs,
                            page_df_height - 1,
                            col_idx,
                            "bottom",
                            border_style,
                            page_shape,
                        )
                else:
                    # Has footnote/source: apply border_last from RTFBody
                    self._apply_footnote_source_borders(
                        page_info, border_style, is_last_page=False
                    )

        else:  # is_last_page
            # Last page: apply double border after footnote/source, or after data if no footnote/source
            if self.rtf_page.border_last:
                # Check if this page contains the absolute last row
                total_rows = self.df.height
                is_absolute_last_row = page_info["end_row"] == total_rows - 1

                if is_absolute_last_row:
                    if not (has_footnote_on_page or has_source_on_page):
                        # No footnote/source: apply border to last data row
                        last_row_idx = page_df_height - 1
                        for col_idx in range(page_df_width):
                            page_attrs = self._apply_border_to_cell(
                                page_attrs,
                                last_row_idx,
                                col_idx,
                                "bottom",
                                self.rtf_page.border_last,
                                page_shape,
                            )
                    else:
                        # Has footnote/source: set border for footnote/source (handled in separate method)
                        self._apply_footnote_source_borders(
                            page_info, self.rtf_page.border_last, is_last_page=True
                        )

        return page_attrs

    def _apply_footnote_source_borders(
        self, page_info: dict, border_style: str, is_last_page: bool
    ):
        """Apply borders to footnote and source components based on page position."""

        # Determine which component should get the border
        has_footnote = (
            self.rtf_footnote
            and self.rtf_footnote.text
            and self._should_show_element_on_page(
                self.rtf_page.page_footnote_location, page_info
            )
        )
        has_source = (
            self.rtf_source
            and self.rtf_source.text
            and self._should_show_element_on_page(
                self.rtf_page.page_source_location, page_info
            )
        )

        # Apply border to components based on as_table setting
        # Priority: Source with as_table=True > Footnote with as_table=True > any component
        target_component = None

        # Extract as_table values (now stored as booleans)
        footnote_as_table = None
        if has_footnote:
            footnote_as_table = getattr(self.rtf_footnote, "as_table", True)

        source_as_table = None
        if has_source:
            source_as_table = getattr(self.rtf_source, "as_table", False)

        if has_source and source_as_table:
            # Source is rendered as table: prioritize source for borders
            target_component = ("source", self.rtf_source)
        elif has_footnote and footnote_as_table:
            # Footnote is rendered as table: use footnote for borders
            target_component = ("footnote", self.rtf_footnote)
        elif has_source:
            # Fallback: source even if plain text
            target_component = ("source", self.rtf_source)
        elif has_footnote:
            # Fallback: footnote even if plain text
            target_component = ("footnote", self.rtf_footnote)

        if target_component:
            component_name, component = target_component
            if not hasattr(component, "_page_border_style"):
                component._page_border_style = {}
            component._page_border_style[page_info["page_number"]] = border_style

    def _apply_border_to_cell(
        self,
        page_attrs: TableAttributes,
        row_idx: int,
        col_idx: int,
        border_side: str,
        border_style: str,
        page_shape: tuple[int, int],
    ) -> TableAttributes:
        """Apply specified border style to a specific cell using BroadcastValue"""
        border_attr = f"border_{border_side}"

        if not hasattr(page_attrs, border_attr):
            return page_attrs

        # Get current border values
        current_borders = getattr(page_attrs, border_attr)

        # Create BroadcastValue to expand borders to page shape
        border_broadcast = BroadcastValue(value=current_borders, dimension=page_shape)

        # Update the specific cell
        border_broadcast.update_cell(row_idx, col_idx, border_style)

        # Update the attribute with the expanded value
        setattr(page_attrs, border_attr, border_broadcast.value)
        return page_attrs

    def _apply_border_to_row(
        self,
        page_attrs: TableAttributes,
        row_idx: int,
        border_side: str,
        border_style: str,
        num_cols: int,
    ) -> TableAttributes:
        """Apply specified border style to a specific row"""
        border_attr = f"border_{border_side}"

        if not hasattr(page_attrs, border_attr):
            return page_attrs

        # Get current border values
        current_borders = getattr(page_attrs, border_attr)

        # Ensure borders list is large enough
        while len(current_borders) <= row_idx:
            # Create a copy of the last row's borders, not a reference
            if current_borders:
                current_borders.append(current_borders[-1].copy())
            else:
                current_borders.append([""] * num_cols)

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
        """Define RTF page settings - delegated to encoding service."""
        return self._encoding_service.encode_page_settings(self.rtf_page)

    def _rtf_page_margin_encode(self) -> str:
        """Define RTF margin settings - delegated to encoding service."""
        return self._encoding_service.encode_page_margin(self.rtf_page)

    def _rtf_page_header_encode(self, method: str) -> str:
        """Convert the RTF page header into RTF syntax - delegated to encoding service."""
        result = self._encoding_service.encode_page_header(self.rtf_page_header, method)
        if result:
            return f"{{\\header{result}}}"
        return None

    def _rtf_page_footer_encode(self, method: str) -> str:
        """Convert the RTF page footer into RTF syntax - delegated to encoding service."""
        result = self._encoding_service.encode_page_footer(self.rtf_page_footer, method)
        if result:
            return f"{{\\footer{result}}}"
        return None

    def _rtf_title_encode(self, method: str) -> str:
        """Convert the RTF title into RTF syntax - delegated to encoding service."""
        return self._encoding_service.encode_title(self.rtf_title, method)

    def _rtf_subline_encode(self, method: str) -> str:
        """Convert the RTF subline into RTF syntax - delegated to encoding service."""
        return self._encoding_service.encode_subline(self.rtf_subline, method)

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

    def _rtf_footnote_encode(self, page_number: int = None) -> MutableSequence[str]:
        """Convert the RTF footnote into RTF syntax - delegated to encoding service."""
        result = self._encoding_service.encode_footnote(
            self.rtf_footnote, page_number, self.rtf_page.col_width
        )
        return result if result else None

    def _rtf_source_encode(self, page_number: int = None) -> MutableSequence[str]:
        """Convert the RTF source into RTF syntax - delegated to encoding service."""
        result = self._encoding_service.encode_source(
            self.rtf_source, page_number, self.rtf_page.col_width
        )
        return result if result else None

    def _rtf_body_encode(
        self, df: pl.DataFrame, rtf_attrs: TableAttributes | None
    ) -> MutableSequence[str]:
        """Convert the RTF table into RTF syntax - delegated to encoding service."""
        return self._encoding_service.encode_body(self, df, rtf_attrs)


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
        """Generate RTF code for paginated documents - delegated to PaginatedStrategy."""
        from .encoding.strategies import PaginatedStrategy
        strategy = PaginatedStrategy()
        return strategy.encode(self)

    def _rtf_column_header_encode(
        self, df: pl.DataFrame, rtf_attrs: TableAttributes | None
    ) -> MutableSequence[str]:
        """Convert column header into RTF syntax - delegated to encoding service."""
        return self._encoding_service.encode_column_header(df, rtf_attrs, self.rtf_page.col_width)

    def _rtf_start_encode(self) -> str:
        """Generate RTF document start - delegated to encoding service."""
        return self._encoding_service.encode_document_start()

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
        """Generate RTF code using the encoding engine."""
        # Use the new encoding engine for strategy selection
        engine = RTFEncodingEngine()
        return engine.encode_document(self)
    
    def _rtf_encode_single_page(self) -> str:
        """Generate RTF code for single-page documents - delegated to SinglePageStrategy."""
        from .encoding.strategies import SinglePageStrategy
        strategy = SinglePageStrategy()
        return strategy.encode(self)

    def write_rtf(self, file_path: str) -> None:
        """Write the RTF code into a `.rtf` file."""
        print(file_path)
        rtf_code = self.rtf_encode()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(rtf_code)
