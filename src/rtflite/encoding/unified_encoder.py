from __future__ import annotations

from typing import Any

from rtflite import RTFDocument

from ..attributes import BroadcastValue
from ..pagination.processor import PageFeatureProcessor
from ..pagination.strategies import PageContext, PaginationContext, StrategyRegistry
from ..pagination.strategies.defaults import DefaultPaginationStrategy
from ..pagination.strategies.grouping import PageByStrategy, SublineStrategy
from ..row import Utils
from ..services import RTFEncodingService
from ..services.color_service import color_service
from ..services.document_service import RTFDocumentService
from ..services.figure_service import RTFFigureService
from ..services.grouping_service import grouping_service
from ..type_guards import is_single_body
from .base import EncodingStrategy
from .renderer import PageRenderer


class UnifiedRTFEncoder(EncodingStrategy):
    """Unified RTF Encoder using the strategy pattern for pagination and rendering."""

    def __init__(self):
        self.encoding_service = RTFEncodingService()
        self.document_service = RTFDocumentService()
        self.figure_service = RTFFigureService()
        self.feature_processor = PageFeatureProcessor()
        self.renderer = PageRenderer()

        # Register strategies (if not already registered elsewhere)
        # Ideally this happens at app startup, but for now we ensure they are available
        StrategyRegistry.register("default", DefaultPaginationStrategy)
        StrategyRegistry.register("page_by", PageByStrategy)
        StrategyRegistry.register("subline", SublineStrategy)

    def encode(self, document: Any) -> str:
        """Encode the document using the unified pipeline."""

        # 1. Figure-only handling
        if document.df is None:
            # Reuse the logic from previous implementation, adapted slightly
            # Unifying figure-only documents into one pipeline is not straightforward.
            # without a "FigurePaginationStrategy".
            # So we defer to a helper method similar to the old one.
            return self._encode_figure_only(document)

        # 2. Multi-section handling
        # The unified pipeline currently assumes a single DataFrame.
        # Multi-section docs (list of DFs) need to be processed section by section
        # or updated to support multi-df context.
        # For now, we defer to the legacy multi-section handler if needed.
        if isinstance(document.df, list):
            return self._encode_multi_section(document)

        # 3. Standard Pipeline
        color_service.set_document_context(document)

        # A. Prepare Data
        processed_df, original_df, processed_attrs = (
            self.encoding_service.prepare_dataframe_for_body_encoding(
                document.df, document.rtf_body
            )
        )

        # B. Select Strategy
        strategy_name = "default"
        if is_single_body(document.rtf_body):
            if document.rtf_body.subline_by:
                strategy_name = "subline"
            elif document.rtf_body.page_by:
                strategy_name = "page_by"
        # B. Select Strategy
        strategy_name = "default"
        if is_single_body(document.rtf_body):
            if document.rtf_body.subline_by:
                strategy_name = "subline"
            elif document.rtf_body.page_by:
                strategy_name = "page_by"

        strategy_cls = StrategyRegistry.get(strategy_name)
        strategy = strategy_cls()

        # C. Prepare Context
        col_total_width = document.rtf_page.col_width
        if is_single_body(document.rtf_body) and processed_attrs.col_rel_width:
            col_widths = Utils._col_widths(
                processed_attrs.col_rel_width,
                col_total_width if col_total_width is not None else 8.5,
            )
        else:
            col_widths = Utils._col_widths(
                [1] * processed_df.shape[1],
                col_total_width if col_total_width is not None else 8.5,
            )

        additional_rows = self.document_service.calculate_additional_rows_per_page(
            document
        )

        pagination_ctx = PaginationContext(
            df=original_df if is_single_body(document.rtf_body) else processed_df,
            rtf_body=document.rtf_body,
            rtf_page=document.rtf_page,
            col_widths=col_widths,
            table_attrs=processed_attrs,
            additional_rows_per_page=additional_rows,
        )

        # D. Paginate
        pages = strategy.paginate(pagination_ctx)

        # Handle case where no pages are generated (e.g. empty dataframe)
        if not pages:
            # Create empty page to ensure document structure (title, etc.) is rendered.
            # We use processed_df which might be empty but has correct schema
            pages = [
                PageContext(
                    page_number=1,
                    total_pages=1,
                    data=processed_df,
                    is_first_page=True,
                    is_last_page=True,
                    col_widths=col_widths,
                    needs_header=True,
                    table_attrs=processed_attrs,
                )
            ]

        # Post-pagination fixup: Replace data with processed data (sliced correctly)
        # Strategy used original_df, but we render processed_df.
        # (which has removed columns).
        if is_single_body(document.rtf_body):
            self._apply_data_post_processing(pages, processed_df, document.rtf_body)

        # E. Process & Render Pages
        page_rtf_chunks = []

        for page in pages:
            # Process features (borders, etc.)
            processed_page = self.feature_processor.process(document, page)

            # Render
            chunks = self.renderer.render(document, processed_page)
            page_rtf_chunks.extend(chunks)

        # F. Assembly
        result = "\n".join(
            [
                item
                for item in [
                    self.encoding_service.encode_document_start(),
                    self.encoding_service.encode_font_table(),
                    self.encoding_service.encode_color_table(document),
                    "\n",
                    self.encoding_service.encode_page_header(
                        document.rtf_page_header, method="line"
                    ),
                    self.encoding_service.encode_page_footer(
                        document.rtf_page_footer, method="line"
                    ),
                    self.encoding_service.encode_page_settings(document.rtf_page),
                    "\n".join(page_rtf_chunks),
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

        color_service.clear_document_context()
        return result

    def _apply_data_post_processing(self, pages, processed_df, rtf_body):
        """Sync page data with processed dataframe and handle group_by restoration."""
        # 1. Replace data slices
        # We assume the pagination strategy preserved the row order and counts
        # matching the processed_df (which corresponds to the original df structure
        # minus excluded columns).
        current_idx = 0
        for page in pages:
            rows = page.data.height
            page.data = processed_df.slice(current_idx, rows)
            current_idx += rows

        # 2. Re-implementation of group_by logic
        if rtf_body.group_by:
            # Collect page start indices for context restoration
            page_start_indices = []
            cumulative = 0
            for i, p in enumerate(pages):
                if i > 0:
                    page_start_indices.append(cumulative)
                cumulative += p.data.height

            full_df = processed_df

            suppressed = grouping_service.enhance_group_by(full_df, rtf_body.group_by)
            restored = grouping_service.restore_page_context(
                suppressed, full_df, rtf_body.group_by, page_start_indices
            )

            curr = 0
            for p in pages:
                rows = p.data.height
                p.data = restored.slice(curr, rows)
                curr += rows

    def _encode_figure_only(self, document: RTFDocument):
        # (Legacy support for figure only)
        # For brevity, I will rely on the existing FigureService logic if possible
        # or just reproduce the simple loop.
        # Matches PaginatedStrategy._encode_figure_only_document_with_pagination.
        # Since the user wants a WORKING system, I must implement it.
        from copy import deepcopy

        from ..figure import rtf_read_figure

        if not document.rtf_figure or not document.rtf_figure.figures:
            return ""

        figs, formats = rtf_read_figure(document.rtf_figure.figures)
        num = len(figs)

        # Pre-calculate shared elements
        title = self.encoding_service.encode_title(document.rtf_title, method="line")

        # For figure-only documents, footnote should be as_table=False
        footnote_component = document.rtf_footnote
        if footnote_component is not None:
            footnote_component = deepcopy(footnote_component)
            footnote_component.as_table = False

        # Determine which elements should show on each page
        show_title_on_all = document.rtf_page.page_title == "all"
        show_footnote_on_all = document.rtf_page.page_footnote == "all"
        show_source_on_all = document.rtf_page.page_source == "all"

        # Build
        parts = [
            self.encoding_service.encode_document_start(),
            self.encoding_service.encode_font_table(),
            self.encoding_service.encode_color_table(document),
            "\n",
            self.encoding_service.encode_page_header(
                document.rtf_page_header, method="line"
            ),
            self.encoding_service.encode_page_footer(
                document.rtf_page_footer, method="line"
            ),
            self.encoding_service.encode_page_settings(document.rtf_page),
        ]

        for i in range(num):
            is_first = i == 0
            is_last = i == num - 1

            # Title
            if (
                show_title_on_all
                or (document.rtf_page.page_title == "first" and is_first)
                or (document.rtf_page.page_title == "last" and is_last)
            ):
                parts.append(title)
                parts.append("\n")

            # Subline
            if is_first and document.rtf_subline:
                parts.append(
                    self.encoding_service.encode_subline(
                        document.rtf_subline, method="line"
                    )
                )

            # Figure
            w = self.figure_service._get_dimension(document.rtf_figure.fig_width, i)
            h = self.figure_service._get_dimension(document.rtf_figure.fig_height, i)
            parts.append(
                self.figure_service._encode_single_figure(
                    figs[i], formats[i], w, h, document.rtf_figure.fig_align
                )
            )
            parts.append(r"\par ")

            # Footnote based on page settings
            if footnote_component is not None and (
                show_footnote_on_all
                or (document.rtf_page.page_footnote == "first" and is_first)
                or (document.rtf_page.page_footnote == "last" and is_last)
            ):
                footnote_content = "\n".join(
                    self.encoding_service.encode_footnote(
                        footnote_component,
                        page_number=i + 1,
                        page_col_width=document.rtf_page.col_width,
                    )
                )
                if footnote_content:
                    parts.append(footnote_content)

            # Source based on page settings
            if document.rtf_source is not None and (
                show_source_on_all
                or (document.rtf_page.page_source == "first" and is_first)
                or (document.rtf_page.page_source == "last" and is_last)
            ):
                source_content = "\n".join(
                    self.encoding_service.encode_source(
                        document.rtf_source,
                        page_number=i + 1,
                        page_col_width=document.rtf_page.col_width,
                    )
                )
                if source_content:
                    parts.append(source_content)

            if not is_last:
                parts.append(r"\page ")

        parts.append("\n\n}")
        return "".join([p for p in parts if p])

    def _encode_multi_section(self, document: RTFDocument) -> str:
        """Encode a multi-section document where sections are concatenated row by row.

        Args:
            document: The RTF document with multiple df/rtf_body sections

        Returns:
            Complete RTF string
        """
        from copy import deepcopy

        from ..input import RTFColumnHeader
        from ..type_guards import (
            is_flat_header_list,
            is_nested_header_list,
            is_single_header,
        )

        # Calculate column counts for border management
        if isinstance(document.df, list):
            first_section_cols = document.df[0].shape[1] if document.df else 0
        else:
            first_section_cols = document.df.shape[1] if document.df is not None else 0

        # Document structure components
        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )

        # Handle page borders (use first section for dimensions)
        doc_border_top_list = BroadcastValue(
            value=document.rtf_page.border_first, dimension=(1, first_section_cols)
        ).to_list()
        doc_border_top = doc_border_top_list[0] if doc_border_top_list else None
        doc_border_bottom_list = BroadcastValue(
            value=document.rtf_page.border_last, dimension=(1, first_section_cols)
        ).to_list()
        doc_border_bottom = (
            doc_border_bottom_list[0] if doc_border_bottom_list else None
        )

        # Encode sections
        all_section_content = []
        is_nested_headers = is_nested_header_list(document.rtf_column_header)

        df_list = (
            document.df
            if isinstance(document.df, list)
            else [document.df]
            if document.df is not None
            else []
        )
        body_list = (
            document.rtf_body
            if isinstance(document.rtf_body, list)
            else [document.rtf_body]
            if document.rtf_body is not None
            else []
        )

        for i, (section_df, section_body) in enumerate(
            zip(df_list, body_list, strict=True)
        ):
            dim = section_df.shape

            # Handle column headers for this section
            section_headers: list[str] = []
            if is_nested_headers:
                # Nested format: [[header1], [None], [header3]]
                if (
                    i < len(document.rtf_column_header)
                    and document.rtf_column_header[i]
                ):
                    for header in document.rtf_column_header[i]:
                        if header is not None:
                            # Ensure header is RTFColumnHeader, not tuple
                            if not isinstance(header, RTFColumnHeader):
                                continue
                            # Apply top border to first section's first header
                            if (
                                i == 0
                                and not section_headers
                                and document.rtf_page.border_first
                            ):
                                doc_border_top_list = BroadcastValue(
                                    value=document.rtf_page.border_first,
                                    dimension=(1, dim[1]),
                                ).to_list()
                                doc_border_top = (
                                    doc_border_top_list[0]
                                    if doc_border_top_list
                                    else None
                                )

                                header.border_top = BroadcastValue(
                                    value=header.border_top, dimension=dim
                                ).update_row(
                                    0,
                                    doc_border_top
                                    if doc_border_top is not None
                                    else [],
                                )

                            section_headers.append(
                                self.encoding_service.encode_column_header(
                                    header.text, header, document.rtf_page.col_width
                                )
                            )
            else:
                # Flat format - only apply to first section
                if i == 0:
                    headers_to_check = []
                    if is_flat_header_list(document.rtf_column_header):
                        headers_to_check = document.rtf_column_header
                    elif is_single_header(document.rtf_column_header):  # type: ignore[arg-type]
                        headers_to_check = [document.rtf_column_header]

                    for header in headers_to_check:
                        if (
                            header is not None
                            and header.text is None
                            and section_body.as_colheader
                        ):
                            # Auto-generate headers from column names
                            columns = [
                                col
                                for col in section_df.columns
                                if col not in (section_body.page_by or [])
                            ]
                            import polars as pl

                            header_df = pl.DataFrame(
                                [columns],
                                schema=[f"col_{j}" for j in range(len(columns))],
                                orient="row",
                            )
                            header.text = header_df  # type: ignore[assignment]

                        # Apply top border to first header
                        if (
                            not section_headers
                            and document.rtf_page.border_first
                            and header is not None
                        ):
                            doc_border_top_list = BroadcastValue(
                                value=document.rtf_page.border_first,
                                dimension=(1, dim[1]),
                            ).to_list()
                            doc_border_top = (
                                doc_border_top_list[0] if doc_border_top_list else None
                            )

                            header.border_top = BroadcastValue(
                                value=header.border_top, dimension=dim
                            ).update_row(
                                0, doc_border_top if doc_border_top is not None else []
                            )

                        if header is not None:
                            section_headers.append(
                                self.encoding_service.encode_column_header(
                                    header.text, header, document.rtf_page.col_width
                                )
                            )

            # Handle borders for section body
            if i == 0 and not section_headers:  # First section, no headers
                # Apply top border to first row of first section
                doc_border_top_list = BroadcastValue(
                    value=document.rtf_page.border_first, dimension=(1, dim[1])
                ).to_list()
                doc_border_top = doc_border_top_list[0] if doc_border_top_list else None

                section_body.border_top = BroadcastValue(
                    value=section_body.border_top, dimension=dim
                ).update_row(0, doc_border_top if doc_border_top is not None else [])

            # Create a temporary document for this section to maintain compatibility
            temp_document = deepcopy(document)
            temp_document.df = section_df
            temp_document.rtf_body = section_body

            # Encode section body
            section_body_content = self.encoding_service.encode_body(
                temp_document, section_df, section_body
            )

            # Add section content
            if section_headers:
                all_section_content.extend(
                    [
                        "\n".join(
                            header for sublist in section_headers for header in sublist
                        )
                    ]
                )
            all_section_content.extend(section_body_content)

        # Handle bottom borders on last section
        if document.rtf_footnote is not None and doc_border_bottom is not None:
            document.rtf_footnote.border_bottom = BroadcastValue(
                value=document.rtf_footnote.border_bottom, dimension=(1, 1)
            ).update_row(0, [doc_border_bottom[0]])
        else:
            # Apply bottom border to last section's last row
            if isinstance(document.rtf_body, list) and isinstance(document.df, list):
                last_section_body = document.rtf_body[-1]
                last_section_dim = document.df[-1].shape
                if last_section_dim[0] > 0 and doc_border_bottom is not None:
                    last_section_body.border_bottom = BroadcastValue(
                        value=last_section_body.border_bottom,
                        dimension=last_section_dim,
                    ).update_row(last_section_dim[0] - 1, doc_border_bottom)

        return "\n".join(
            [
                item
                for item in [
                    self.encoding_service.encode_document_start(),
                    self.encoding_service.encode_font_table(),
                    "\n",
                    self.encoding_service.encode_page_header(
                        document.rtf_page_header, method="line"
                    ),
                    self.encoding_service.encode_page_footer(
                        document.rtf_page_footer, method="line"
                    ),
                    self.encoding_service.encode_page_settings(document.rtf_page),
                    rtf_title,
                    "\n",
                    self.encoding_service.encode_subline(
                        document.rtf_subline, method="line"
                    ),
                    "\n".join(all_section_content),
                    "\n".join(
                        self.encoding_service.encode_footnote(
                            document.rtf_footnote,
                            page_number=1,
                            page_col_width=document.rtf_page.col_width,
                        )
                    )
                    if document.rtf_footnote is not None
                    else None,
                    "\n".join(
                        self.encoding_service.encode_source(
                            document.rtf_source,
                            page_number=1,
                            page_col_width=document.rtf_page.col_width,
                        )
                    )
                    if document.rtf_source is not None
                    else None,
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )
