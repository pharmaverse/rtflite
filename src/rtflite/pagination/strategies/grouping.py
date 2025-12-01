from collections.abc import Sequence
from typing import Any, cast

import polars as pl

from ..core import PageBreakCalculator, RTFPagination
from .base import PageContext, PaginationContext, PaginationStrategy


class PageByStrategy(PaginationStrategy):
    """Pagination strategy that respects grouping columns (page_by)."""

    def paginate(self, context: PaginationContext) -> list[PageContext]:
        # Initialize calculator
        assert context.rtf_page.width is not None
        assert context.rtf_page.height is not None
        assert context.rtf_page.margin is not None
        assert context.rtf_page.nrow is not None
        assert context.rtf_page.orientation is not None

        pagination_config = RTFPagination(
            page_width=context.rtf_page.width,
            page_height=context.rtf_page.height,
            margin=context.rtf_page.margin,
            nrow=context.rtf_page.nrow,
            orientation=context.rtf_page.orientation,
        )
        calculator = PageBreakCalculator(pagination=pagination_config)

        page_by = context.rtf_body.page_by

        # Calculate metadata
        metadata = calculator.calculate_row_metadata(
            df=context.df,
            col_widths=context.col_widths,
            page_by=page_by,
            table_attrs=context.table_attrs,
            removed_column_indices=context.removed_column_indices,
            additional_rows_per_page=context.additional_rows_per_page,
            new_page=context.rtf_body.new_page,
        )

        pages = []
        import polars as pl

        unique_pages = metadata["page"].unique().sort()
        total_pages = len(unique_pages)

        for page_num in unique_pages:
            page_rows = metadata.filter(pl.col("page") == page_num)

            if page_rows.height == 0:
                continue

            start_row = cast(int, page_rows["row_index"].min())
            end_row = cast(int, page_rows["row_index"].max())

            page_df = context.df.slice(start_row, end_row - start_row + 1)
            display_page_num = int(page_num)

            is_first = display_page_num == 1
            # Repeating headers: if pageby_header is True, or if it's the first page.
            needs_header = context.rtf_body.pageby_header or is_first

            page_ctx = PageContext(
                page_number=display_page_num,
                total_pages=total_pages,
                data=page_df,
                is_first_page=is_first,
                is_last_page=(display_page_num == total_pages),
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
        # Subline strategy uses subline_by columns and forces new_page=True.
        subline_by = context.rtf_body.subline_by

        # Initialize calculator
        assert context.rtf_page.width is not None
        assert context.rtf_page.height is not None
        assert context.rtf_page.margin is not None
        assert context.rtf_page.nrow is not None
        assert context.rtf_page.orientation is not None

        pagination_config = RTFPagination(
            page_width=context.rtf_page.width,
            page_height=context.rtf_page.height,
            margin=context.rtf_page.margin,
            nrow=context.rtf_page.nrow,
            orientation=context.rtf_page.orientation,
        )
        calculator = PageBreakCalculator(pagination=pagination_config)

        # Calculate metadata
        # SublineStrategy forces new page on subline change.
        metadata = calculator.calculate_row_metadata(
            df=context.df,
            col_widths=context.col_widths,
            page_by=context.rtf_body.page_by,
            subline_by=subline_by,
            table_attrs=context.table_attrs,
            removed_column_indices=context.removed_column_indices,
            additional_rows_per_page=context.additional_rows_per_page,
            new_page=True,
        )

        pages = []
        import polars as pl

        unique_pages = metadata["page"].unique().sort()
        total_pages = len(unique_pages)

        for page_num in unique_pages:
            page_rows = metadata.filter(pl.col("page") == page_num)

            if page_rows.height == 0:
                continue

            start_row = cast(int, page_rows["row_index"].min())
            end_row = cast(int, page_rows["row_index"].max())

            page_df = context.df.slice(start_row, end_row - start_row + 1)
            display_page_num = int(page_num)

            is_first = display_page_num == 1

            page_ctx = PageContext(
                page_number=display_page_num,
                total_pages=total_pages,
                data=page_df,
                is_first_page=is_first,
                is_last_page=(display_page_num == total_pages),
                col_widths=context.col_widths,
                needs_header=is_first or context.rtf_body.pageby_header,
                table_attrs=context.table_attrs,
            )

            if subline_by:
                page_ctx.subline_header = self._get_group_headers(
                    context.df, subline_by, start_row
                )

            # Also handle page_by if present (spanning rows)
            page_by = context.rtf_body.page_by
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
