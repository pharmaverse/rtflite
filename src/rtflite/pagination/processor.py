from copy import deepcopy
from typing import Any

from ..attributes import BroadcastValue
from .strategies.base import PageContext


class PageFeatureProcessor:
    """Processes page features like borders, headers, and footers for each page."""

    def process(self, document: Any, page: PageContext) -> PageContext:
        """Process a single page to apply all feature-specific logic."""

        # Calculate final attributes for the table body on this page
        # (This includes applying top/bottom borders correctly)
        page.final_body_attrs = self._apply_pagination_borders(document, page)

        return page

    def _should_show_element(self, element_location: str, page: PageContext) -> bool:
        """Determine if an element should be shown on a specific page."""
        logic = {
            "all": True,
            "first": page.is_first_page,
            "last": page.is_last_page,
        }
        return logic.get(element_location, False)

    def _apply_pagination_borders(self, document, page: PageContext) -> Any:
        """Apply proper borders for paginated context following r2rtf design."""

        # Start with a deep copy of the page's table attributes (processed/sliced)
        # or document's body attributes if not available
        base_attrs = page.table_attrs or document.rtf_body
        page_attrs = deepcopy(base_attrs)

        page_df_height = page.data.height
        page_df_width = page.data.width
        page_shape = (page_df_height, page_df_width)

        if page_df_height == 0:
            return page_attrs

        # Clear border_first and border_last from being broadcast to all rows
        if hasattr(page_attrs, "border_first") and page_attrs.border_first:
            page_attrs.border_first = None

        if hasattr(page_attrs, "border_last") and page_attrs.border_last:
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

        # --- Logic from DocumentService.apply_pagination_borders ---

        # 1. First Page Logic
        has_column_headers = (
            document.rtf_column_header and len(document.rtf_column_header) > 0
        )

        # If first page, NO headers, apply PAGE border_first to top of body
        if (
            page.is_first_page
            and not has_column_headers
            and document.rtf_page.border_first
        ):
            for col_idx in range(page_df_width):
                page_attrs = self._apply_border_to_cell(
                    page_attrs,
                    0,
                    col_idx,
                    "top",
                    document.rtf_page.border_first,
                    page_shape,
                )

        # If first page, WITH headers, apply BODY border_first to top of body
        if page.is_first_page and has_column_headers and document.rtf_body.border_first:
            self._apply_body_border_first(
                document, page_attrs, page_df_width, page_shape
            )

        # 2. Middle Page Logic (Non-First)
        # Apply BODY border_first to top of body
        if not page.is_first_page and document.rtf_body.border_first:
            self._apply_body_border_first(
                document, page_attrs, page_df_width, page_shape
            )

        # 3. Footnote/Source Logic
        has_footnote_on_page = (
            document.rtf_footnote
            and document.rtf_footnote.text
            and self._should_show_element(document.rtf_page.page_footnote, page)
        )
        has_source_on_page = (
            document.rtf_source
            and document.rtf_source.text
            and self._should_show_element(document.rtf_page.page_source, page)
        )

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

        # 4. Bottom Border Logic
        if not page.is_last_page:
            # Not last page: use BODY border_last
            if document.rtf_body.border_last:
                border_style = (
                    document.rtf_body.border_last[0][0]
                    if isinstance(document.rtf_body.border_last, list)
                    else document.rtf_body.border_last
                )

                if not (has_footnote_on_page or has_source_on_page):
                    # Apply to last data row
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
                    # Apply to component
                    self._apply_footnote_source_borders(
                        document,
                        page,
                        has_footnote_on_page,
                        has_source_on_page,
                        border_style,
                    )
        else:
            # Last page: use PAGE border_last
            if document.rtf_page.border_last:
                # Only if this is truly the end (not just last page of a section,
                # but for now we assume 1 section or last section)
                # The original code checked `page_info["end_row"] == total_rows - 1`.
                # Here we rely on `is_last_page` flag which comes from strategy.

                if not (footnote_as_table_on_last or source_as_table_on_last):
                    # Apply to last data row
                    for col_idx in range(page_df_width):
                        page_attrs = self._apply_border_to_cell(
                            page_attrs,
                            page_df_height - 1,
                            col_idx,
                            "bottom",
                            document.rtf_page.border_last,
                            page_shape,
                        )
                else:
                    # Apply to component
                    self._apply_footnote_source_borders(
                        document,
                        page,
                        has_footnote_on_page,
                        has_source_on_page,
                        document.rtf_page.border_last,
                    )

        return page_attrs

    def _apply_body_border_first(self, document, page_attrs, page_df_width, page_shape):
        """Helper to apply body border_first logic."""
        if isinstance(document.rtf_body.border_first, list):
            border_first_row = document.rtf_body.border_first[0]
            has_border_top = (
                document.rtf_body.border_top
                and isinstance(document.rtf_body.border_top, list)
                and len(document.rtf_body.border_top[0]) > len(border_first_row)
            )

            for col_idx in range(page_df_width):
                if col_idx < len(border_first_row):
                    border_style = border_first_row[col_idx]
                else:
                    border_style = border_first_row[0]

                if (
                    has_border_top
                    and col_idx < len(document.rtf_body.border_top[0])
                    and document.rtf_body.border_top[0][col_idx]
                ):
                    border_style = document.rtf_body.border_top[0][col_idx]

                self._apply_border_to_cell(
                    page_attrs, 0, col_idx, "top", border_style, page_shape
                )
        else:
            for col_idx in range(page_df_width):
                self._apply_border_to_cell(
                    page_attrs,
                    0,
                    col_idx,
                    "top",
                    document.rtf_body.border_first,
                    page_shape,
                )

    def _apply_footnote_source_borders(
        self,
        document,
        page: PageContext,
        has_footnote: bool,
        has_source: bool,
        border_style: str,
    ):
        """Apply borders to footnote/source in the page context."""
        target_component = None

        footnote_as_table = None
        if has_footnote:
            footnote_as_table = getattr(document.rtf_footnote, "as_table", True)

        source_as_table = None
        if has_source:
            source_as_table = getattr(document.rtf_source, "as_table", False)

        if has_source and source_as_table:
            target_component = "source"
        elif has_footnote and footnote_as_table:
            target_component = "footnote"

        if target_component:
            page.component_borders[target_component] = border_style

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
        border_attr = f"border_{border_side}"

        if not hasattr(page_attrs, border_attr):
            return page_attrs

        current_borders = getattr(page_attrs, border_attr)
        border_broadcast = BroadcastValue(value=current_borders, dimension=page_shape)
        border_broadcast.update_cell(row_idx, col_idx, border_style)
        setattr(page_attrs, border_attr, border_broadcast.value)
        return page_attrs
