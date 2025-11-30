from typing import Any, Sequence

import polars as pl

from ..core import PageBreakCalculator, RTFPagination
from .base import PageContext, PaginationContext, PaginationStrategy


class PageByStrategy(PaginationStrategy):
    """Pagination strategy that respects grouping columns (page_by)."""

    def paginate(self, context: PaginationContext) -> list[PageContext]:
        # Initialize calculator
        pagination_config = RTFPagination(
            page_width=context.rtf_page.width,
            page_height=context.rtf_page.height,
            margin=context.rtf_page.margin,
            nrow=context.rtf_page.nrow,
            orientation=context.rtf_page.orientation,
        )
        calculator = PageBreakCalculator(pagination=pagination_config)

        page_by = context.rtf_body.page_by
        new_page = context.rtf_body.new_page

        # Calculate breaks
        page_breaks = calculator.find_page_breaks(
            df=context.df,
            col_widths=context.col_widths,
            page_by=page_by,
            new_page=new_page,
            table_attrs=context.table_attrs,
            additional_rows_per_page=context.additional_rows_per_page,
        )

        pages = []
        for page_num, (start_row, end_row) in enumerate(page_breaks):
            page_df = context.df.slice(start_row, end_row - start_row + 1)

            is_first = page_num == 0
            # Logic for repeating headers: if pageby_header is True, or if it's the first page
            needs_header = context.rtf_body.pageby_header or is_first

            page_ctx = PageContext(
                page_number=page_num + 1,
                total_pages=len(page_breaks),
                data=page_df,
                is_first_page=is_first,
                is_last_page=(page_num == len(page_breaks) - 1),
                col_widths=context.col_widths,
                needs_header=needs_header,
                table_attrs=context.table_attrs,
            )

            # Add page_by header info
            if page_by:
                page_ctx.pageby_header_info = self._get_group_headers(
                    context.df, page_by, start_row
                )

                # Detect group boundaries for spanning rows mid-page
                group_boundaries = self._detect_group_boundaries(
                    context.df, page_by, start_row, end_row
                )
                if group_boundaries:
                    page_ctx.group_boundaries = group_boundaries

            pages.append(page_ctx)

        return pages

    def _get_group_headers(
        self, df: pl.DataFrame, page_by: Sequence[str], start_row: int
    ) -> dict[str, Any]:
        """Get group header information for a page."""
        if not page_by or start_row >= df.height:
            return {}

        group_values = {}
        for col in page_by:
            val = df[col][start_row]
            if str(val) != "-----":
                group_values[col] = val

        return {
            "group_by_columns": page_by,
            "group_values": group_values,
            "header_text": " | ".join(
                f"{col}: {val}" for col, val in group_values.items()
            ),
        }

    def _detect_group_boundaries(
        self, df: pl.DataFrame, page_by: Sequence[str], start_row: int, end_row: int
    ) -> list[dict[str, Any]]:
        """Detect group boundaries within a page range."""
        group_boundaries = []
        for row_idx in range(start_row, end_row):
            if row_idx + 1 <= end_row:
                current_group = {col: df[col][row_idx] for col in page_by}
                next_group = {col: df[col][row_idx + 1] for col in page_by}

                if current_group != next_group:
                    next_group_filtered = {
                        k: v for k, v in next_group.items() if str(v) != "-----"
                    }
                    group_boundaries.append(
                        {
                            "absolute_row": row_idx + 1,
                            "page_relative_row": row_idx + 1 - start_row,
                            "group_values": next_group_filtered,
                        }
                    )
        return group_boundaries


class SublineStrategy(PageByStrategy):
    """Pagination strategy for subline_by (forces new pages and special headers)."""

    def paginate(self, context: PaginationContext) -> list[PageContext]:
        # Subline strategy acts like page_by but uses subline_by columns and forces new_page=True
        subline_by = context.rtf_body.subline_by

        # Initialize calculator
        pagination_config = RTFPagination(
            page_width=context.rtf_page.width,
            page_height=context.rtf_page.height,
            margin=context.rtf_page.margin,
            nrow=context.rtf_page.nrow,
            orientation=context.rtf_page.orientation,
        )
        calculator = PageBreakCalculator(pagination=pagination_config)

        # Force new_page=True for subline strategy
        page_breaks = calculator.find_page_breaks(
            df=context.df,
            col_widths=context.col_widths,
            page_by=subline_by,
            new_page=True,
            table_attrs=context.table_attrs,
            additional_rows_per_page=context.additional_rows_per_page,
        )

        pages = []
        for page_num, (start_row, end_row) in enumerate(page_breaks):
            page_df = context.df.slice(start_row, end_row - start_row + 1)

            is_first = page_num == 0

            page_ctx = PageContext(
                page_number=page_num + 1,
                total_pages=len(page_breaks),
                data=page_df,
                is_first_page=is_first,
                is_last_page=(page_num == len(page_breaks) - 1),
                col_widths=context.col_widths,
                needs_header=is_first or context.rtf_body.pageby_header,
                table_attrs=context.table_attrs,
            )

            if subline_by:
                page_ctx.subline_header = self._get_group_headers(
                    context.df, subline_by, start_row
                )

            pages.append(page_ctx)

        return pages
