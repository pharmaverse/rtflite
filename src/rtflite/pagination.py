from collections.abc import Sequence
from typing import Any, Dict, List, Tuple

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from .strwidth import get_string_width


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

    def calculate_available_space(self) -> Dict[str, float]:
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


class PageBreakCalculator(BaseModel):
    """Calculates where page breaks should occur based on content and constraints"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pagination: RTFPagination = Field(..., description="Pagination configuration")

    def calculate_content_rows(
        self,
        df: pl.DataFrame,
        col_widths: List[float],
        cell_height: float = 0.15,
        font_size: int = 9,
    ) -> List[int]:
        """Calculate how many rows each content row will occupy when rendered

        Args:
            df: DataFrame containing the content
            col_widths: Width of each column in inches
            cell_height: Height of each cell in inches
            font_size: Font size in points

        Returns:
            List of row counts for each data row
        """
        row_counts = []

        for row_idx in range(df.height):
            max_lines_in_row = 1

            for col_idx, col_width in enumerate(col_widths):
                if col_idx < len(df.columns):
                    cell_value = str(df[col_idx][row_idx])
                    # Calculate how many lines this text will need
                    text_width = get_string_width(cell_value, font_size)
                    lines_needed = max(1, int(text_width / col_width) + 1)
                    max_lines_in_row = max(max_lines_in_row, lines_needed)

            row_counts.append(max_lines_in_row)

        return row_counts

    def find_page_breaks(
        self,
        df: pl.DataFrame,
        col_widths: List[float],
        page_by: List[str] = None,
        new_page: bool = False,
    ) -> List[Tuple[int, int]]:
        """Find optimal page break positions

        Args:
            df: DataFrame to paginate
            col_widths: Column widths in inches
            page_by: Columns to group by for page breaks
            new_page: Whether to force new pages between groups

        Returns:
            List of (start_row, end_row) tuples for each page
        """
        if df.height == 0:
            return []

        row_counts = self.calculate_content_rows(df, col_widths)
        page_breaks = []
        current_page_start = 0
        current_page_rows = 0

        for row_idx, row_height in enumerate(row_counts):
            # Check if adding this row would exceed page limit
            if current_page_rows + row_height > self.pagination.nrow:
                # Create page break before this row
                if current_page_start < row_idx:
                    page_breaks.append((current_page_start, row_idx - 1))
                current_page_start = row_idx
                current_page_rows = row_height
            else:
                current_page_rows += row_height

            # Handle group-based page breaks
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


class ContentDistributor(BaseModel):
    """Manages content distribution across multiple pages"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pagination: RTFPagination = Field(..., description="Pagination configuration")
    calculator: PageBreakCalculator = Field(..., description="Page break calculator")

    def distribute_content(
        self,
        df: pl.DataFrame,
        col_widths: List[float],
        page_by: List[str] = None,
        new_page: bool = False,
        pageby_header: bool = True,
    ) -> List[Dict[str, Any]]:
        """Distribute content across multiple pages

        Args:
            df: DataFrame to distribute
            col_widths: Column widths in inches
            page_by: Columns to group by
            new_page: Force new pages between groups
            pageby_header: Repeat headers on new pages

        Returns:
            List of page information dictionaries
        """
        page_breaks = self.calculator.find_page_breaks(
            df, col_widths, page_by, new_page
        )
        pages = []

        for page_num, (start_row, end_row) in enumerate(page_breaks):
            page_df = df[start_row : end_row + 1]

            page_info = {
                "page_number": page_num + 1,
                "total_pages": len(page_breaks),
                "data": page_df,
                "start_row": start_row,
                "end_row": end_row,
                "is_first_page": page_num == 0,
                "is_last_page": page_num == len(page_breaks) - 1,
                "needs_header": pageby_header or page_num == 0,
                "col_widths": col_widths,
            }

            pages.append(page_info)

        return pages

    def get_group_headers(
        self, df: pl.DataFrame, page_by: List[str], start_row: int
    ) -> Dict[str, Any]:
        """Get group header information for a page

        Args:
            df: Original DataFrame
            page_by: Grouping columns
            start_row: Starting row for this page

        Returns:
            Dictionary with group header information
        """
        if not page_by or start_row >= df.height:
            return {}

        group_values = {}
        for col in page_by:
            group_values[col] = df[col][start_row]

        return {
            "group_by_columns": page_by,
            "group_values": group_values,
            "header_text": " | ".join(
                f"{col}: {val}" for col, val in group_values.items()
            ),
        }
