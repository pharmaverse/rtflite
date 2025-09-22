"""RTF Document Service - handles all document-level operations."""

from collections.abc import Mapping, Sequence
from typing import Any, Tuple

from ..pagination import ContentDistributor, PageBreakCalculator, RTFPagination
from ..row import Utils


class PaginationPlanner:
    """Compute pagination-specific metrics for an RTF document."""

    def __init__(self, document) -> None:
        self.document = document
        self._pagination = RTFPagination(
            page_width=document.rtf_page.width,
            page_height=document.rtf_page.height,
            margin=document.rtf_page.margin,
            nrow=document.rtf_page.nrow,
            orientation=document.rtf_page.orientation,
        )
        self._calculator: PageBreakCalculator | None = None
        self._content_rows: list[int] | None = None
        self._additional_rows: int | None = None

    @property
    def pagination(self) -> RTFPagination:
        return self._pagination

    @property
    def calculator(self) -> PageBreakCalculator:
        if self._calculator is None:
            self._calculator = PageBreakCalculator(pagination=self._pagination)
        return self._calculator

    def additional_rows_per_page(self) -> int:
        if self._additional_rows is None:
            self._additional_rows = self._compute_additional_rows()
        return self._additional_rows

    def requires_pagination(self) -> bool:
        if self._has_multiple_figures():
            return True

        if self.document.df is None:
            return False

        if self._is_multi_section():
            return self._multi_section_requires_pagination()

        if self._single_section_forces_pagination():
            return True

        additional_rows = self.additional_rows_per_page()
        if additional_rows >= self.document.rtf_page.nrow:
            return True

        data_rows = sum(self.content_rows())
        available_data_rows = max(1, self.document.rtf_page.nrow - additional_rows)
        return data_rows > available_data_rows

    def build_distributor(self) -> ContentDistributor:
        return ContentDistributor(pagination=self.pagination, calculator=self.calculator)

    def content_rows(self) -> list[int]:
        if self._content_rows is None:
            self._content_rows = self._compute_content_rows()
        return self._content_rows

    def _has_multiple_figures(self) -> bool:
        figure = getattr(self.document, "rtf_figure", None)
        if not figure or not getattr(figure, "figures", None):
            return False

        figures = figure.figures
        return isinstance(figures, (list, tuple)) and len(figures) > 1

    def _is_multi_section(self) -> bool:
        return isinstance(self.document.df, list)

    def _multi_section_requires_pagination(self) -> bool:
        bodies = self._iter_bodies()
        for body in bodies:
            if (body.page_by and body.new_page) or body.subline_by:
                return True
        return False

    def _single_section_forces_pagination(self) -> bool:
        body = self.document.rtf_body
        return bool(
            (getattr(body, "page_by", None) and getattr(body, "new_page", False))
            or getattr(body, "subline_by", None)
        )

    def _compute_additional_rows(self) -> int:
        document = self.document
        additional_rows = 0

        for body in self._iter_bodies():
            if getattr(body, "subline_by", None):
                additional_rows += 1
                break

        headers = getattr(document, "rtf_column_header", None)
        if headers:
            first_header = headers[0] if len(headers) > 0 else None
            if isinstance(first_header, list):
                for section_headers in headers:
                    if not section_headers:
                        continue
                    for header in section_headers:
                        if header and header.text is not None:
                            additional_rows += 1
            else:
                for header in headers:
                    if header and header.text is not None:
                        additional_rows += 1

        if document.rtf_footnote and document.rtf_footnote.text:
            additional_rows += 1

        if document.rtf_source and document.rtf_source.text:
            additional_rows += 1

        return additional_rows

    def _compute_content_rows(self) -> list[int]:
        if self.document.df is None:
            return []

        col_total_width = self.document.rtf_page.col_width
        if self._is_multi_section():
            rows: list[int] = []
            for df, body in self._iter_sections():
                col_widths = Utils._col_widths(body.col_rel_width, col_total_width)
                rows.extend(self.calculator.calculate_content_rows(df, col_widths, body))
            return rows

        col_widths = Utils._col_widths(
            self.document.rtf_body.col_rel_width, col_total_width
        )
        return list(
            self.calculator.calculate_content_rows(
                self.document.df, col_widths, self.document.rtf_body
            )
        )

    def _iter_bodies(self) -> Sequence:
        bodies = getattr(self.document, "rtf_body", None)
        if isinstance(bodies, list):
            return bodies
        return [bodies] if bodies is not None else []

    def _iter_sections(self) -> Sequence[tuple[Any, Any]]:
        bodies = self._iter_bodies()
        if not isinstance(self.document.df, list):
            return []
        return list(zip(self.document.df, bodies))


class RTFDocumentService:
    """Service for handling RTF document operations including pagination and layout."""

    def __init__(self):
        from .encoding_service import RTFEncodingService

        self.encoding_service = RTFEncodingService()

    def calculate_additional_rows_per_page(self, document) -> int:
        """Calculate additional rows needed per page for headers, footnotes, sources."""
        return PaginationPlanner(document).additional_rows_per_page()

    def needs_pagination(self, document) -> bool:
        """Check if document needs pagination based on content size and page limits."""

        return PaginationPlanner(document).requires_pagination()

    def create_pagination_instance(self, document) -> Tuple:
        """Create pagination and content distributor instances."""
        planner = PaginationPlanner(document)
        return planner.pagination, planner.build_distributor()

    def generate_page_break(self, document) -> str:
        """Generate proper RTF page break sequence."""
        return self.encoding_service.encode_page_break(
            document.rtf_page,
            lambda: self.encoding_service.encode_page_margin(document.rtf_page),
        )

    def should_show_element_on_page(
        self, element_location: str, page_info: dict
    ) -> bool:
        """Determine if an element should be shown on a specific page."""
        if element_location == "all":
            return True
        elif element_location == "first":
            return page_info["is_first_page"]
        elif element_location == "last":
            return page_info["is_last_page"]
        else:
            return False

    def process_page_by(
        self, document
    ) -> Sequence[Sequence[Tuple[int, int, int]]] | None:
        """Create components for page_by format."""
        # Obtain input data
        data = document.df.to_dicts()
        var = document.rtf_body.page_by

        # Handle empty DataFrame
        if len(data) == 0:
            return None

        # Obtain column names and dimensions
        columns = list(data[0].keys())

        if var is None:
            return None

        def get_column_index(column_name: str) -> int:
            """Get the index of a column in the column list."""
            return columns.index(column_name)

        def get_matching_rows(group_values: Mapping) -> Sequence[int]:
            """Get row indices that match the group values."""
            return [
                i
                for i, row in enumerate(data)
                if all(row[k] == v for k, v in group_values.items())
            ]

        def get_unique_combinations(variables: Sequence[str]) -> Sequence[Mapping]:
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

    def apply_pagination_borders(
        self, document, rtf_attrs, page_info: dict, total_pages: int
    ):
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

        from ..attributes import BroadcastValue
        from ..input import TableAttributes

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
        has_column_headers = (
            document.rtf_column_header and len(document.rtf_column_header) > 0
        )
        if page_info["is_first_page"] and not has_column_headers:
            if document.rtf_page.border_first:
                # Apply border to all cells in the first row
                for col_idx in range(page_df_width):
                    page_attrs = self._apply_border_to_cell(
                        page_attrs,
                        0,
                        col_idx,
                        "top",
                        document.rtf_page.border_first,
                        page_shape,
                    )

        # For first page with column headers: ensure consistent border style
        if page_info["is_first_page"] and has_column_headers:
            # Apply same border style as non-first pages to maintain consistency
            if document.rtf_body.border_first:
                border_style = (
                    document.rtf_body.border_first[0][0]
                    if isinstance(document.rtf_body.border_first, list)
                    else document.rtf_body.border_first
                )
                # Apply single border style to first data row (same as other pages)
                for col_idx in range(page_df_width):
                    page_attrs = self._apply_border_to_cell(
                        page_attrs, 0, col_idx, "top", border_style, page_shape
                    )

        # Apply page-level borders for non-first/last pages
        if not page_info["is_first_page"] and document.rtf_body.border_first:
            # Apply border_first to first row of non-first pages
            border_style = (
                document.rtf_body.border_first[0][0]
                if isinstance(document.rtf_body.border_first, list)
                else document.rtf_body.border_first
            )
            for col_idx in range(page_df_width):
                page_attrs = self._apply_border_to_cell(
                    page_attrs, 0, col_idx, "top", border_style, page_shape
                )

        # Check if footnotes or sources will appear on this page
        has_footnote_on_page = (
            document.rtf_footnote
            and document.rtf_footnote.text
            and self.should_show_element_on_page(
                document.rtf_page.page_footnote, page_info
            )
        )
        has_source_on_page = (
            document.rtf_source
            and document.rtf_source.text
            and self.should_show_element_on_page(
                document.rtf_page.page_source, page_info
            )
        )

        # Determine if footnotes/sources appear as tables on the last page
        # This is crucial for border placement when components are set to "first" only
        footnote_as_table_on_last = (
            document.rtf_footnote
            and document.rtf_footnote.text
            and getattr(document.rtf_footnote, "as_table", True)
            and document.rtf_page.page_footnote in ("last", "all")
        )
        source_as_table_on_last = (
            document.rtf_source
            and document.rtf_source.text
            and getattr(document.rtf_source, "as_table", False)
            and document.rtf_page.page_source in ("last", "all")
        )

        # Apply border logic based on page position and footnote/source presence
        if not page_info["is_last_page"]:
            # Non-last pages: apply single border after footnote/source, or after data if no footnote/source
            if document.rtf_body.border_last:
                border_style = (
                    document.rtf_body.border_last[0][0]
                    if isinstance(document.rtf_body.border_last, list)
                    else document.rtf_body.border_last
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
                        document, page_info, border_style, is_last_page=False
                    )

        else:  # is_last_page
            # Last page: check if we should apply border to data or footnote/source
            if document.rtf_page.border_last:
                # Check if this page contains the absolute last row
                total_rows = document.df.height
                is_absolute_last_row = page_info["end_row"] == total_rows - 1

                if is_absolute_last_row:
                    # If footnotes/sources are set to "first" only and appear as tables,
                    # they won't be on the last page, so apply border to last data row
                    if not (footnote_as_table_on_last or source_as_table_on_last):
                        # No footnote/source on last page: apply border to last data row
                        last_row_idx = page_df_height - 1
                        for col_idx in range(page_df_width):
                            page_attrs = self._apply_border_to_cell(
                                page_attrs,
                                last_row_idx,
                                col_idx,
                                "bottom",
                                document.rtf_page.border_last,
                                page_shape,
                            )
                    else:
                        # Has footnote/source on last page: set border for footnote/source
                        self._apply_footnote_source_borders(
                            document,
                            page_info,
                            document.rtf_page.border_last,
                            is_last_page=True,
                        )

        return page_attrs

    def _apply_footnote_source_borders(
        self, document, page_info: dict, border_style: str, is_last_page: bool
    ):
        """Apply borders to footnote and source components based on page position."""
        # Determine which component should get the border
        has_footnote = (
            document.rtf_footnote
            and document.rtf_footnote.text
            and self.should_show_element_on_page(
                document.rtf_page.page_footnote, page_info
            )
        )
        has_source = (
            document.rtf_source
            and document.rtf_source.text
            and self.should_show_element_on_page(
                document.rtf_page.page_source, page_info
            )
        )

        # Apply border to components based on as_table setting
        # Priority: Source with as_table=True > Footnote with as_table=True > any component
        target_component = None

        # Extract as_table values (now stored as booleans)
        footnote_as_table = None
        if has_footnote:
            footnote_as_table = getattr(document.rtf_footnote, "as_table", True)

        source_as_table = None
        if has_source:
            source_as_table = getattr(document.rtf_source, "as_table", False)

        if has_source and source_as_table:
            # Source is rendered as table: prioritize source for borders
            target_component = ("source", document.rtf_source)
        elif has_footnote and footnote_as_table:
            # Footnote is rendered as table: use footnote for borders
            target_component = ("footnote", document.rtf_footnote)
        # Note: Removed fallback to plain text components - borders should only be applied
        # to components that are rendered as tables (as_table=True)

        if target_component:
            component_name, component = target_component
            if not hasattr(component, "_page_border_style"):
                component._page_border_style = {}
            component._page_border_style[page_info["page_number"]] = border_style

    def _apply_border_to_cell(
        self,
        page_attrs,
        row_idx: int,
        col_idx: int,
        border_side: str,
        border_style: str,
        page_shape: tuple,
    ):
        """Apply specified border style to a specific cell using BroadcastValue"""
        from ..attributes import BroadcastValue

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
