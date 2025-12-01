from copy import deepcopy
from typing import Any

import polars as pl

from ..attributes import BroadcastValue
from ..pagination.strategies.base import PageContext
from ..services import RTFEncodingService
from ..services.document_service import RTFDocumentService
from ..services.figure_service import RTFFigureService
from ..type_guards import (
    is_flat_header_list,
    is_nested_header_list,
    is_single_body,
    is_single_header,
)


class PageRenderer:
    """Renders a single PageContext into RTF string chunks."""

    def __init__(self):
        self.encoding_service = RTFEncodingService()
        self.document_service = RTFDocumentService()
        self.figure_service = RTFFigureService()

    def render(self, document: Any, page: PageContext) -> list[str]:
        """Render a single page to RTF."""

        page_elements = []

        # 1. Page Break (except first page)
        if not page.is_first_page:
            page_elements.append(self.document_service.generate_page_break(document))

        # 2. Title
        if (
            document.rtf_title
            and document.rtf_title.text
            and self._should_show(document.rtf_page.page_title, page)
        ):
            title_content = self.encoding_service.encode_title(
                document.rtf_title, method="line"
            )
            if title_content:
                page_elements.append(title_content)
                page_elements.append("\n")

        # 3. Subline
        if (
            document.rtf_subline
            and document.rtf_subline.text
            and self._should_show(
                document.rtf_page.page_title, page
            )  # Using page_title rule for subline visibility as per original
        ):
            subline_content = self.encoding_service.encode_subline(
                document.rtf_subline, method="line"
            )
            if subline_content:
                page_elements.append(subline_content)

        # 4. Subline Header (from Strategy)
        if page.subline_header:
            subline_header_content = self._generate_subline_header(page.subline_header)
            if subline_header_content:
                page_elements.append(subline_header_content)

        # 5. Figures (Position: Before)
        if (
            document.rtf_figure
            and document.rtf_figure.figures
            and document.rtf_figure.fig_pos == "before"
            and page.is_first_page
        ):
            figure_content = self.figure_service.encode_figure(document.rtf_figure)
            if figure_content:
                page_elements.append(figure_content)
                page_elements.append("\n")

        # 6. Column Headers
        if page.needs_header and document.rtf_column_header:
            header_elements = self._render_column_headers(document, page)
            page_elements.extend(header_elements)

        # 7. Page By Spanning Row (Header)
        if (
            is_single_body(document.rtf_body)
            and page.pageby_header_info
            and (
                not document.rtf_body.new_page
                or document.rtf_body.pageby_row != "column"
            )
            and "group_values" in page.pageby_header_info
        ):
            for col_name, val in page.pageby_header_info["group_values"].items():
                if val is None:
                    continue

                # Find col index for attributes
                current_col_idx = 0
                if isinstance(document.df, pl.DataFrame):
                    try:
                        current_col_idx = document.df.columns.index(col_name)
                    except ValueError:
                        current_col_idx = 0

                header_text = str(val)
                spanning_row = self.encoding_service.encode_spanning_row(
                    text=header_text,
                    page_width=document.rtf_page.col_width or 8.5,
                    rtf_body_attrs=document.rtf_body,
                    col_idx=current_col_idx,
                )
                page_elements.extend(spanning_row)

        # 8. Body (with potential internal group boundaries)
        body_elements = self._render_body(document, page)
        page_elements.extend(body_elements)

        # 9. Footnotes
        if (
            document.rtf_footnote
            and document.rtf_footnote.text
            and self._should_show(document.rtf_page.page_footnote, page)
        ):
            # Check for border override from processor
            border_style = page.component_borders.get("footnote")

            footnote_content = self.encoding_service.encode_footnote(
                document.rtf_footnote,
                page.page_number,
                document.rtf_page.col_width,
                border_style=border_style,
            )
            if footnote_content:
                page_elements.extend(footnote_content)

        # 10. Sources
        if (
            document.rtf_source
            and document.rtf_source.text
            and self._should_show(document.rtf_page.page_source, page)
        ):
            # Check for border override from processor
            border_style = page.component_borders.get("source")

            source_content = self.encoding_service.encode_source(
                document.rtf_source,
                page.page_number,
                document.rtf_page.col_width,
                border_style=border_style,
            )
            if source_content:
                page_elements.extend(source_content)

        # 11. Figures (Position: After)
        if (
            document.rtf_figure
            and document.rtf_figure.figures
            and document.rtf_figure.fig_pos == "after"
            and page.is_last_page
        ):
            figure_content = self.figure_service.encode_figure(document.rtf_figure)
            if figure_content:
                page_elements.append(figure_content)

        return page_elements

    def _should_show(self, location: str, page: PageContext) -> bool:
        if location == "all":
            return True
        if location == "first":
            return page.is_first_page
        if location == "last":
            return page.is_last_page
        return False

    def _format_group_header(self, info: dict) -> str:
        if "group_values" in info:
            parts = [str(v) for v in info["group_values"].values() if v is not None]
            return ", ".join(parts)
        return ""

    def _generate_subline_header(self, info: dict) -> str:
        text = self._format_group_header(info)
        if not text:
            return ""
        return rf"{{\pard\hyphpar\fi0\li0\ri0\ql\fs18{{\f0 {text}}}\par}}"

    def _render_column_headers(self, document: Any, page: PageContext) -> list[str]:
        # Similar logic to PaginatedStrategy.encode header section

        header_elements = []
        headers_to_process = []

        if is_nested_header_list(document.rtf_column_header):
            for section in document.rtf_column_header:
                if section:
                    headers_to_process.extend(section)
        elif is_flat_header_list(document.rtf_column_header):
            headers_to_process = document.rtf_column_header
        elif is_single_header(document.rtf_column_header):
            headers_to_process = [document.rtf_column_header]

        for i, header in enumerate(headers_to_process):
            if header is None:
                continue
            header_copy = deepcopy(header)

            # Auto-populate header text from columns if missing and as_colheader is True
            if (
                header_copy.text is None
                and is_single_body(document.rtf_body)
                and document.rtf_body.as_colheader
            ):
                # Use processed page data columns
                page_df = page.data
                if isinstance(page_df, pl.DataFrame):
                    columns = list(page_df.columns)
                    header_df = pl.DataFrame(
                        [columns],
                        schema=[f"col_{j}" for j in range(len(columns))],
                        orient="row",
                    )
                    header_copy.text = header_df  # type: ignore[assignment]

                    # Adjust col_rel_width if needed (logic from PaginatedStrategy)
                    # Since we are using page.data which is already sliced/processed,
                    # Might need to adjust widths if defined for full table.
                    if document.rtf_body.col_rel_width is not None:
                        # If body has specific widths, try to map them.
                        # If header text exists, proceed.
                        pass

            # Remove columns if necessary (page_by/subline_by)
            # Note: page.data already has columns removed if populated from it.
            # Filter only if text is from original document with extra columns.
            # Since we simplified text to be a list, we can't easily filter by name
            # unless we assume order or have metadata.
            # For now, we assume header text matches the current page columns.
            pass

            # Apply top border for first page/first header
            if (
                page.is_first_page
                and i == 0
                and document.rtf_page.border_first
                and header_copy.text is not None
            ):
                if isinstance(header_copy.text, pl.DataFrame):
                    dims = header_copy.text.shape
                else:
                    dims = (1, len(header_copy.text) if header_copy.text else 0)

                header_copy.border_top = BroadcastValue(
                    value=header_copy.border_top, dimension=dims
                ).update_row(0, [document.rtf_page.border_first] * dims[1])

            header_rtf = self.encoding_service.encode_column_header(
                header_copy.text, header_copy, document.rtf_page.col_width
            )
            header_elements.extend(header_rtf)

        return header_elements

    def _render_body(self, document: Any, page: PageContext) -> list[str]:
        page_attrs = page.final_body_attrs or page.table_attrs or document.rtf_body
        page_df = page.data
        col_widths = page.col_widths

        elements: list[str] = []

        # Check for internal group boundaries
        if (
            is_single_body(document.rtf_body)
            and page.group_boundaries
            and (
                not document.rtf_body.new_page
                or document.rtf_body.pageby_row != "column"
            )
        ):
            # Find col idx for spanning
            if document.rtf_body.page_by and isinstance(document.df, pl.DataFrame):
                # Just check if column exists, index not strictly needed here
                # as we iterate page_by_cols later
                pass

            # Initialize last_values from page header info to track state
            last_values = {}
            if page.pageby_header_info and "group_values" in page.pageby_header_info:
                last_values = page.pageby_header_info["group_values"].copy()

            prev_row = 0
            for boundary in page.group_boundaries:
                page_rel_row = boundary["page_relative_row"]

                if page_rel_row > prev_row:
                    segment = page_df[prev_row:page_rel_row]
                    # Use internal _encode method (attributes already finalized).
                    # Note: We need to ensure page_attrs is the TableAttributes object
                    elements.extend(
                        page_attrs._encode(segment, col_widths, row_offset=prev_row)
                    )

                # Spanning Row (Nested)
                if "group_values" in boundary:
                    new_values = boundary["group_values"]
                    force_render = False

                    # Iterate in order of page_by columns to handle hierarchy
                    page_by_cols = document.rtf_body.page_by or []

                    for col_name in page_by_cols:
                        val = new_values.get(col_name)
                        last_val = last_values.get(col_name)

                        if val is None:
                            continue

                        # Check for change
                        # If a higher level changed (force_render),
                        # we must render this level too.
                        if str(val) != str(last_val) or force_render:
                            force_render = True

                            # Find col index for attributes
                            current_col_idx = 0
                            if isinstance(document.df, pl.DataFrame):
                                try:
                                    current_col_idx = document.df.columns.index(
                                        col_name
                                    )
                                except ValueError:
                                    current_col_idx = 0

                            header_text = str(val)
                            spanning = self.encoding_service.encode_spanning_row(
                                text=header_text,
                                page_width=document.rtf_page.col_width or 8.5,
                                rtf_body_attrs=document.rtf_body,
                                col_idx=current_col_idx,
                            )
                            elements.extend(spanning)

                    # Update state
                    last_values.update(new_values)

                prev_row = page_rel_row

            if prev_row < len(page_df):
                segment = page_df[prev_row:]
                elements.extend(
                    page_attrs._encode(segment, col_widths, row_offset=prev_row)
                )
        else:
            # Simple body render
            elements.extend(page_attrs._encode(page_df, col_widths, row_offset=0))

        return elements
