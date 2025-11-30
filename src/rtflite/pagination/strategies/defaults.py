
from ..core import PageBreakCalculator, RTFPagination
from .base import PageContext, PaginationContext, PaginationStrategy


class DefaultPaginationStrategy(PaginationStrategy):
    """Default pagination strategy based on row counts and page size."""

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

        # Calculate breaks
        page_breaks = calculator.find_page_breaks(
            df=context.df,
            col_widths=context.col_widths,
            page_by=None,
            new_page=False,
            table_attrs=context.table_attrs,
            additional_rows_per_page=context.additional_rows_per_page,
        )

        # Create PageContext objects
        pages = []
        for page_num, (start_row, end_row) in enumerate(page_breaks):
            page_df = context.df.slice(start_row, end_row - start_row + 1)

            pages.append(
                PageContext(
                    page_number=page_num + 1,
                    total_pages=len(page_breaks),
                    data=page_df,
                    is_first_page=(page_num == 0),
                    is_last_page=(page_num == len(page_breaks) - 1),
                    col_widths=context.col_widths,
                    needs_header=(context.rtf_body.pageby_header or page_num == 0),
                    table_attrs=context.table_attrs,
                )
            )

        return pages
