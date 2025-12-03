from __future__ import annotations

from typing import Any

import polars as pl

from rtflite import RTFDocument

from ..attributes import BroadcastValue
from ..input import RTFBody
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

    def _encode_body_section(
        self, document: RTFDocument, df: Any, rtf_body: Any
    ) -> list[str]:
        """Encode a single body section using the unified pipeline.

        Args:
            document: The RTF document context
            df: DataFrame for this section
            rtf_body: RTFBody attributes for this section

        Returns:
            List of RTF strings (rendered pages/rows)
        """

        # A. Prepare Data
        processed_df, original_df, processed_attrs = (
            self.encoding_service.prepare_dataframe_for_body_encoding(df, rtf_body)
        )

        # B. Select Strategy
        strategy_name = "default"
        if is_single_body(rtf_body):
            if rtf_body.subline_by:
                strategy_name = "subline"
            elif rtf_body.page_by:
                strategy_name = "page_by"

        strategy_cls = StrategyRegistry.get(strategy_name)
        strategy = strategy_cls()

        # C. Prepare Context
        col_total_width = document.rtf_page.col_width
        if is_single_body(rtf_body) and processed_attrs.col_rel_width:
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

        # Calculate removed column indices
        # Calculate removed column indices
        removed_column_indices = []
        # Ensure we are working with a DataFrame and RTFBody for single section encoding
        if isinstance(original_df, pl.DataFrame) and isinstance(rtf_body, RTFBody):
            if processed_df.shape[1] < original_df.shape[1]:
                # Find indices of columns that were removed
                # We assume columns are removed, not reordered significantly enough to
                # break this simple check for the purpose of pagination context
                processed_cols = set(processed_df.columns)
                for i, col in enumerate(original_df.columns):
                    if col not in processed_cols:
                        removed_column_indices.append(i)

            pagination_ctx = PaginationContext(
                df=original_df,  # Use original DF for context
                rtf_body=rtf_body,
                rtf_page=document.rtf_page,
                col_widths=col_widths,
                table_attrs=processed_attrs,
                additional_rows_per_page=additional_rows,
                removed_column_indices=removed_column_indices,
            )
        else:
            # Fallback or error for unexpected types in this context
            # Should not happen given is_single_body checks usually
            pagination_ctx = PaginationContext(
                df=processed_df,
                rtf_body=processed_attrs,  # Best effort fallback
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

        # Post-pagination fixup
        if is_single_body(rtf_body):
            self._apply_data_post_processing(pages, processed_df, rtf_body)

        # E. Process & Render Pages
        section_rtf_chunks = []

        for _i, page in enumerate(pages):
            # Process features (borders, etc.)
            processed_page = self.feature_processor.process(document, page)

            # Render
            chunks = self.renderer.render(document, processed_page)
            section_rtf_chunks.extend(chunks)

            # Add page break between pages (except last page)
            # Note: PageRenderer handles page breaks at the start of non-first pages.
            # So we do NOT add them here to avoid double breaks.
            pass

        return section_rtf_chunks

    def encode(self, document: Any) -> str:
        """Encode the document using the unified pipeline."""

        # 1. Figure-only handling
        if document.df is None:
            return self._encode_figure_only(document)

        # 2. Multi-section handling
        if isinstance(document.df, list):
            return self._encode_multi_section(document)

        # 3. Standard Pipeline
        color_service.set_document_context(document)

        page_rtf_chunks = self._encode_body_section(
            document, document.df, document.rtf_body
        )

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
        """Encode a figure-only document."""
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

        from ..type_guards import is_nested_header_list

        # Calculate column counts for border management
        if isinstance(document.df, list):
            first_section_cols = document.df[0].shape[1] if document.df else 0
        else:
            first_section_cols = document.df.shape[1] if document.df is not None else 0

        # Document structure components
        # rtf_title is handled per section via temp_document and renderer
        # so we don't need to pre-calculate it here.

        # Handle page borders (use first section for dimensions)
        # doc_border_top is not used in this scope
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
            # Determine column headers for this section
            section_headers_obj = None
            if is_nested_headers:
                if isinstance(document.rtf_column_header, list) and i < len(
                    document.rtf_column_header
                ):
                    section_headers_obj = document.rtf_column_header[i]
            else:
                # Flat format - only apply to first section
                if i == 0:
                    section_headers_obj = document.rtf_column_header

            # Create a temporary document for this section
            # We need to adjust page borders:
            # - border_first only applies to the first section
            # - border_last only applies to the last section
            section_page = document.rtf_page.model_copy()
            if i > 0:
                section_page.border_first = None
            if i < len(df_list) - 1:
                section_page.border_last = None

            # Handle component visibility across sections
            # Use model_copy to avoid modifying original document components
            section_title = (
                document.rtf_title.model_copy() if document.rtf_title else None
            )
            section_footnote = (
                document.rtf_footnote.model_copy() if document.rtf_footnote else None
            )
            section_source = (
                document.rtf_source.model_copy() if document.rtf_source else None
            )
            section_subline = (
                document.rtf_subline.model_copy() if document.rtf_subline else None
            )
            section_page_header = (
                document.rtf_page_header.model_copy()
                if document.rtf_page_header
                else None
            )
            section_page_footer = (
                document.rtf_page_footer.model_copy()
                if document.rtf_page_footer
                else None
            )

            # Title: if "first", only show on first section
            # Also suppress if this section continues on the same page (new_page=False)
            if i > 0:
                should_suppress = not section_body.new_page

                if (document.rtf_page.page_title == "first") or should_suppress:
                    if section_title:
                        section_title.text = None
                    if section_subline:
                        section_subline.text = None

                # Suppress Page Header/Footer for continuous sections
                if should_suppress:
                    if section_page_header:
                        section_page_header.text = None
                    if section_page_footer:
                        section_page_footer.text = None

            # Footnote/Source: if "last", only show on last section
            # For continuous sections, suppress them unless it's the last one.
            if i < len(df_list) - 1:
                should_suppress = not body_list[
                    i + 1
                ].new_page  # Next section continues

                if document.rtf_page.page_footnote == "last" and section_footnote:
                    section_footnote.text = None
                if document.rtf_page.page_source == "last" and section_source:
                    section_source.text = None

            # Use model_copy to safely create a new instance with updated fields
            temp_document = document.model_copy(
                update={
                    "df": section_df,
                    "rtf_body": section_body,
                    "rtf_column_header": section_headers_obj,
                    "rtf_page": section_page,
                    "rtf_title": section_title,
                    "rtf_subline": section_subline,
                    "rtf_page_header": section_page_header,
                    "rtf_page_footer": section_page_footer,
                    "rtf_footnote": section_footnote,
                    "rtf_source": section_source,
                }
            )

            # Encode section body (headers will be handled by PageRenderer)
            section_body_content = self._encode_body_section(
                temp_document, section_df, section_body
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
                    self.encoding_service.encode_color_table(document),
                    "\n",
                    self.encoding_service.encode_page_header(
                        document.rtf_page_header, method="line"
                    ),
                    self.encoding_service.encode_page_footer(
                        document.rtf_page_footer, method="line"
                    ),
                    self.encoding_service.encode_page_settings(document.rtf_page),
                    "\n".join(all_section_content),
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

        # 3. Standard Pipeline
        color_service.set_document_context(document)

        page_rtf_chunks = self._encode_body_section(
            document, document.df, document.rtf_body
        )

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
