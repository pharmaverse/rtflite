from collections.abc import Mapping, Sequence

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from ..attributes import TableAttributes
from ..fonts_mapping import FontName, FontNumber
from ..strwidth import get_string_width


class RTFPagination(BaseModel):
    """Core pagination logic and calculations for RTF documents"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    page_width: float = Field(..., description="Page width in inches")
    page_height: float = Field(..., description="Page height in inches")
    margin: Sequence[float] = Field(
        ..., description="Page margins [left, right, top, bottom, header, footer]"
    )
    nrow: int = Field(..., description="Maximum rows per page")
    orientation: str = Field(..., description="Page orientation")

    def calculate_available_space(self) -> Mapping[str, float]:
        """Calculate available space for content on each page"""
        content_width = (
            self.page_width - self.margin[0] - self.margin[1]
        )  # left + right margins
        content_height = (
            self.page_height - self.margin[2] - self.margin[3]
        )  # top + bottom margins
        header_space = self.margin[4]  # header margin
        footer_space = self.margin[5]  # footer margin

        return {
            "content_width": content_width,
            "content_height": content_height,
            "header_space": header_space,
            "footer_space": footer_space,
        }


class RowMetadata(BaseModel):
    """Metadata for a single row's pagination information."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    row_index: int = Field(..., description="Original data row index (0-based)")
    data_rows: int = Field(..., description="Number of rows the data content occupies")
    pageby_header_rows: int = Field(
        default=0, description="Number of rows the page_by header occupies"
    )
    subline_header_rows: int = Field(
        default=0, description="Number of rows the subline_by header occupies"
    )
    column_header_rows: int = Field(
        default=0, description="Number of rows for column headers"
    )
    total_rows: int = Field(..., description="Sum of all row counts")
    page: int = Field(default=0, description="Assigned page number")
    is_group_start: bool = Field(
        default=False, description="True if this row starts a new page_by group"
    )
    is_subline_start: bool = Field(
        default=False, description="True if this row starts a new subline_by group"
    )


class PageBreakCalculator(BaseModel):
    """Calculates where page breaks should occur based on content and constraints"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pagination: RTFPagination = Field(..., description="Pagination configuration")

    def calculate_content_rows(
        self,
        df: pl.DataFrame,
        col_widths: Sequence[float],
        table_attrs: TableAttributes | None = None,
        font_size: float = 9,
        spanning_columns: Sequence[str] | None = None,
    ) -> Sequence[int]:
        """Calculate how many rows each content row will occupy when rendered

        Args:
            df: DataFrame containing the content
            col_widths: Width of each column in inches
            table_attrs: Table attributes containing cell height and font size info
            font_size: Default font size in points
            spanning_columns: Columns that should be treated as spanning the full width

        Returns:
            List of row counts for each data row
        """
        row_counts = []
        dim = df.shape
        spanning_columns = spanning_columns or []
        total_width = sum(col_widths)

        for row_idx in range(df.height):
            max_lines_in_row = 1

            for col_idx, col_width in enumerate(col_widths):
                if col_idx < len(df.columns):
                    # Use proper polars column access - df[column_name][row_idx]
                    col_name = df.columns[col_idx]
                    cell_value = str(df[col_name][row_idx])

                    # Get actual font size from table attributes if available
                    actual_font_size = font_size
                    if table_attrs and hasattr(table_attrs, "text_font_size"):
                        from ..attributes import BroadcastValue

                        actual_font_size = BroadcastValue(
                            value=table_attrs.text_font_size, dimension=dim
                        ).iloc(row_idx, col_idx)

                    # Get actual font from table attributes if available
                    actual_font: FontName | FontNumber = (
                        1  # Default to font number 1 (Times New Roman)
                    )
                    if table_attrs and hasattr(table_attrs, "text_font"):
                        from ..attributes import BroadcastValue

                        font_value = BroadcastValue(
                            value=table_attrs.text_font, dimension=dim
                        ).iloc(row_idx, col_idx)
                        # Handle both FontNumber (int) and FontName (str)
                        if isinstance(font_value, int) and 1 <= font_value <= 10:
                            actual_font = font_value  # type: ignore[assignment]
                        elif isinstance(font_value, str):
                            # If it's a string, use it directly
                            actual_font = font_value  # type: ignore[assignment]

                    # Calculate how many lines this text will need
                    # Use the actual font from table attributes with actual font size
                    text_width = get_string_width(
                        cell_value,
                        font=actual_font,
                        font_size=actual_font_size,  # type: ignore[arg-type]
                    )

                    # Determine effective width for wrapping
                    # If column is a spanning column, use total table width
                    effective_width = (
                        total_width if col_name in spanning_columns else col_width
                    )

                    lines_needed = max(1, int(text_width / effective_width) + 1)
                    max_lines_in_row = max(max_lines_in_row, lines_needed)

            # Account for cell height if specified in table attributes
            cell_height_lines = 1
            if table_attrs and hasattr(table_attrs, "cell_height"):
                from ..attributes import BroadcastValue

                cell_height = BroadcastValue(
                    value=table_attrs.cell_height, dimension=dim
                ).iloc(row_idx, 0)
                # Convert cell height from inches to approximate line count
                # Assuming default line height of ~0.15 inches
                cell_height_lines = max(1, int(cell_height / 0.15))

            row_counts.append(max(max_lines_in_row, cell_height_lines))

        return row_counts

    def find_page_breaks(
        self,
        df: pl.DataFrame,
        col_widths: Sequence[float],
        page_by: Sequence[str] | None = None,
        new_page: bool = False,
        table_attrs: TableAttributes | None = None,
        additional_rows_per_page: int = 0,
    ) -> Sequence[tuple[int, int]]:
        """Find optimal page break positions (r2rtf compatible)

        Args:
            df: DataFrame to paginate
            col_widths: Column widths in inches
            page_by: Columns to group by for page breaks
            new_page: Whether to force new pages between groups
            table_attrs: Table attributes for accurate row calculation
            additional_rows_per_page: Additional rows per page (headers,
                footnotes, sources)

        Returns:
            List of (start_row, end_row) tuples for each page
        """
        if df.height == 0:
            return []

        row_counts = self.calculate_content_rows(
            df, col_widths, table_attrs, spanning_columns=page_by
        )
        page_breaks = []
        current_page_start = 0
        current_page_rows = 0

        # Calculate available rows for data (r2rtf compatible)
        # In r2rtf, nrow includes ALL rows (headers, data, footnotes, sources)
        available_data_rows_per_page = max(
            1, self.pagination.nrow - additional_rows_per_page
        )

        for row_idx, row_height in enumerate(row_counts):
            # Check if adding this row would exceed the page limit (including
            # additional rows)
            if current_page_rows + row_height > available_data_rows_per_page:
                # Create page break before this row
                if current_page_start < row_idx:
                    page_breaks.append((current_page_start, row_idx - 1))
                current_page_start = row_idx
                current_page_rows = row_height
            else:
                current_page_rows += row_height

            # Handle group-based page breaks
            # When page_by + new_page=True, force breaks at group boundaries
            # When page_by alone, allow natural pagination with spanning rows mid-page
            if page_by and new_page and row_idx < df.height - 1:
                current_group = {col: df[col][row_idx] for col in page_by}
                next_group = {col: df[col][row_idx + 1] for col in page_by}

                if current_group != next_group:
                    # Force page break between groups
                    page_breaks.append((current_page_start, row_idx))
                    current_page_start = row_idx + 1
                    current_page_rows = 0

        # Add final page
        if current_page_start < df.height:
            page_breaks.append((current_page_start, df.height - 1))

        return page_breaks

    def calculate_row_metadata(
        self,
        df: pl.DataFrame,
        col_widths: Sequence[float],
        page_by: Sequence[str] | None = None,
        subline_by: Sequence[str] | None = None,
        table_attrs: TableAttributes | None = None,
        removed_column_indices: Sequence[int] | None = None,
        font_size: float = 9,
        additional_rows_per_page: int = 0,
        new_page: bool = False,
    ) -> pl.DataFrame:
        """Generate complete row metadata for pagination."""

        # 1. Calculate data rows
        # Use existing calculation logic but handle removed columns manually
        row_metadata_list = []
        total_width = sum(col_widths)

        # Pre-calculate group changes
        page_by_changes = [True] * df.height
        subline_by_changes = [True] * df.height

        if page_by:
            # Calculate changes for page_by
            # We can use polars shift/diff logic or simple iteration
            # Simple iteration is safer for now
            for i in range(1, df.height):
                prev_row = df.row(i - 1, named=True)
                curr_row = df.row(i, named=True)

                # Check page_by
                is_diff = False
                for col in page_by:
                    if str(prev_row[col]) != str(curr_row[col]):
                        is_diff = True
                        break
                page_by_changes[i] = is_diff

        if subline_by:
            for i in range(1, df.height):
                prev_row = df.row(i - 1, named=True)
                curr_row = df.row(i, named=True)

                # Check subline_by
                is_diff = False
                for col in subline_by:
                    if str(prev_row[col]) != str(curr_row[col]):
                        is_diff = True
                        break
                subline_by_changes[i] = is_diff

        # Iterate rows
        removed_indices = set(removed_column_indices or [])

        for row_idx in range(df.height):
            # 1. Calculate data_rows
            max_lines_in_row = 1
            width_idx = 0

            for col_idx in range(df.width):
                if col_idx in removed_indices:
                    continue

                if width_idx >= len(col_widths):
                    break

                # Calculate individual column width from cumulative widths
                # col_widths contains cumulative widths (right boundaries)
                current_cumulative = col_widths[width_idx]
                prev_cumulative = col_widths[width_idx - 1] if width_idx > 0 else 0
                col_width = current_cumulative - prev_cumulative
                col_name = df.columns[col_idx]
                cell_value = str(df[col_name][row_idx])

                # Font logic
                actual_font_size = font_size
                actual_font = 1

                if table_attrs:
                    pass

                text_width = get_string_width(
                    cell_value,
                    font=actual_font,  # type: ignore
                    font_size=actual_font_size,  # type: ignore
                )

                effective_width = col_width
                lines_needed = max(1, int(text_width / effective_width) + 1)
                max_lines_in_row = max(max_lines_in_row, lines_needed)
                width_idx += 1

            # 2. Calculate header rows
            pageby_rows = 0
            if page_by and page_by_changes[row_idx]:
                # Construct header text
                header_parts = []
                for col in page_by:
                    val = df[col][row_idx]
                    if str(val) != "-----":
                        header_parts.append(f"{col}: {val}")
                header_text = " | ".join(header_parts)
                if header_text:
                    pageby_rows = self._calculate_header_rows(
                        header_text, total_width, font_size=int(font_size)
                    )  # type: ignore

            subline_rows = 0
            if subline_by and subline_by_changes[row_idx]:
                # Construct header text
                header_parts = []
                for col in subline_by:
                    val = df[col][row_idx]
                    if str(val) != "-----":
                        header_parts.append(f"{col}: {val}")
                header_text = " | ".join(header_parts)
                if header_text:
                    subline_rows = self._calculate_header_rows(
                        header_text, total_width, font_size=int(font_size)
                    )  # type: ignore

            total_rows = max_lines_in_row + pageby_rows + subline_rows

            row_metadata_list.append(
                {
                    "row_index": row_idx,
                    "data_rows": max_lines_in_row,
                    "pageby_header_rows": pageby_rows,
                    "subline_header_rows": subline_rows,
                    "column_header_rows": 0,  # To be filled later or passed in
                    "total_rows": total_rows,
                    "page": 0,  # To be assigned
                    "is_group_start": page_by_changes[row_idx] if page_by else False,
                    "is_subline_start": subline_by_changes[row_idx]
                    if subline_by
                    else False,
                }
            )

        # Create DataFrame with explicit schema to handle empty case
        schema = {
            "row_index": pl.Int64,
            "data_rows": pl.Int64,
            "pageby_header_rows": pl.Int64,
            "subline_header_rows": pl.Int64,
            "column_header_rows": pl.Int64,
            "total_rows": pl.Int64,
            "page": pl.Int64,
            "is_group_start": pl.Boolean,
            "is_subline_start": pl.Boolean,
        }
        meta_df = pl.DataFrame(row_metadata_list, schema=schema, orient="row")

        # Assign pages
        return self._assign_pages(meta_df, additional_rows_per_page, new_page)

    def _calculate_header_rows(
        self,
        header_text: str,
        total_width: float,
        font: FontName | FontNumber = 1,
        font_size: int = 18,
    ) -> int:
        """Calculate how many rows a header will occupy."""
        text_width = get_string_width(header_text, font=font, font_size=font_size)
        return max(1, int(text_width / total_width) + 1)

    def _assign_pages(
        self,
        meta_df: pl.DataFrame,
        additional_rows_per_page: int = 0,
        new_page: bool = False,
    ) -> pl.DataFrame:
        """Assign page numbers to the metadata DataFrame."""
        if meta_df.height == 0:
            return meta_df

        available_rows = max(1, self.pagination.nrow - additional_rows_per_page)
        current_page = 1
        current_rows = 0

        # We need to iterate and update 'page' column
        # Convert to list of dicts for mutable iteration
        rows = meta_df.to_dicts()

        for i, row in enumerate(rows):
            row_height = row["total_rows"]

            # Check if we need a new page
            force_break = False

            # Force break on subline start (except first row)
            if row["is_subline_start"] and i > 0:
                force_break = True

            # Force break on group start if requested
            if new_page and row["is_group_start"] and i > 0:
                force_break = True

            if (
                force_break or (current_rows + row_height > available_rows)
            ) and current_rows > 0:
                current_page += 1
                current_rows = 0

            row["page"] = current_page
            current_rows += row_height

        return pl.DataFrame(rows)
