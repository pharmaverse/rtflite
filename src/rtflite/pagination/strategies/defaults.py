from typing import cast

from ..core import PageBreakCalculator, RTFPagination
from .base import PageContext, PaginationContext, PaginationStrategy


class DefaultPaginationStrategy(PaginationStrategy):
    """Default pagination strategy based on row counts and page size."""

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

        # Calculate metadata
        metadata = calculator.calculate_row_metadata(
            df=context.df,
            col_widths=context.col_widths,
            table_attrs=context.table_attrs,
            removed_column_indices=context.removed_column_indices,
            additional_rows_per_page=context.additional_rows_per_page,
        )

        # Create PageContext objects
        pages = []
        import polars as pl

        # Get unique pages and sort them
        unique_pages = metadata["page"].unique().sort()
        total_pages = len(unique_pages)

        for page_num in unique_pages:
            # Filter metadata for this page
            page_rows = metadata.filter(pl.col("page") == page_num)

            if page_rows.height == 0:
                continue

            start_row = cast(int, page_rows["row_index"].min())
            end_row = cast(int, page_rows["row_index"].max())

            # Slice the original dataframe
            # Note: end_row is inclusive index, slice takes length
            page_df = context.df.slice(start_row, end_row - start_row + 1)

            # 1-based page number for display
            display_page_num = int(page_num)

            pages.append(
                PageContext(
                    page_number=display_page_num,
                    total_pages=total_pages,
                    data=page_df,
                    is_first_page=(display_page_num == 1),
                    is_last_page=(display_page_num == total_pages),
                    col_widths=context.col_widths,
                    needs_header=(
                        context.rtf_body.pageby_header or display_page_num == 1
                    ),
                    table_attrs=context.table_attrs,
                )
            )

        return pages
