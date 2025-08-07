"""Encoding strategies for different types of RTF documents."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..services.grouping_service import grouping_service

if TYPE_CHECKING:
    from ..encode import RTFDocument


class EncodingStrategy(ABC):
    """Abstract base class for RTF encoding strategies."""

    @abstractmethod
    def encode(self, document: "RTFDocument") -> str:
        """Encode the document using this strategy.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        pass


class SinglePageStrategy(EncodingStrategy):
    """Encoding strategy for single-page documents without pagination."""

    def __init__(self):
        from ..services import RTFEncodingService
        from ..services.document_service import RTFDocumentService
        from ..services.figure_service import RTFFigureService

        self.encoding_service = RTFEncodingService()
        self.document_service = RTFDocumentService()
        self.figure_service = RTFFigureService()

    def encode(self, document: "RTFDocument") -> str:
        """Encode a single-page document with complete border and layout handling.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        import polars as pl

        from ..attributes import BroadcastValue

        # Handle figure-only documents (no table)
        if document.df is None:
            return self._encode_figure_only_document_simple(document)

        # Check if this is a multi-section document
        if isinstance(document.df, list):
            return self._encode_multi_section_document(document)

        # Original single-page encoding logic for table documents
        dim = document.df.shape

        # Title
        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )

        # Page Border
        doc_border_top = BroadcastValue(
            value=document.rtf_page.border_first, dimension=(1, dim[1])
        ).to_list()[0]
        doc_border_bottom = BroadcastValue(
            value=document.rtf_page.border_last, dimension=(1, dim[1])
        ).to_list()[0]
        page_border_top = BroadcastValue(
            value=document.rtf_body.border_first, dimension=(1, dim[1])
        ).to_list()[0]
        page_border_bottom = BroadcastValue(
            value=document.rtf_body.border_last, dimension=(1, dim[1])
        ).to_list()[0]

        # Column header
        if document.rtf_column_header is None:
            rtf_column_header = ""
            # Only update borders if DataFrame has rows
            if dim[0] > 0:
                document.rtf_body.border_top = BroadcastValue(
                    value=document.rtf_body.border_top, dimension=dim
                ).update_row(0, doc_border_top)
        else:
            if (
                document.rtf_column_header[0].text is None
                and document.rtf_body.as_colheader
            ):
                # Determine which columns to exclude from headers
                excluded_columns = (document.rtf_body.page_by or []) + (
                    document.rtf_body.subline_by or []
                )
                columns = [
                    col for col in document.df.columns if col not in excluded_columns
                ]
                # Create DataFrame with explicit column names to ensure single row
                document.rtf_column_header[0].text = pl.DataFrame(
                    [columns],
                    schema=[f"col_{i}" for i in range(len(columns))],
                    orient="row",
                )

                # Adjust col_rel_width to match the processed columns
                if excluded_columns:
                    original_cols = list(document.df.columns)
                    excluded_cols_set = set(excluded_columns)
                    processed_col_indices = [
                        i
                        for i, col in enumerate(original_cols)
                        if col not in excluded_cols_set
                    ]

                    # Ensure we have enough col_rel_width values for all original columns
                    if len(document.rtf_body.col_rel_width) >= len(original_cols):
                        document.rtf_column_header[0].col_rel_width = [
                            document.rtf_body.col_rel_width[i]
                            for i in processed_col_indices
                        ]
                    else:
                        # Fallback: use equal widths if col_rel_width doesn't match
                        document.rtf_column_header[0].col_rel_width = [1] * len(columns)

                document.rtf_column_header = document.rtf_column_header[:1]

            # Only update borders if DataFrame has rows
            if dim[0] > 0:
                document.rtf_column_header[0].border_top = BroadcastValue(
                    value=document.rtf_column_header[0].border_top, dimension=dim
                ).update_row(0, doc_border_top)

            rtf_column_header = [
                self.encoding_service.encode_column_header(
                    header.text, header, document.rtf_page.col_width
                )
                for header in document.rtf_column_header
            ]

        # Only update borders if DataFrame has rows
        if dim[0] > 0:
            document.rtf_body.border_top = BroadcastValue(
                value=document.rtf_body.border_top, dimension=dim
            ).update_row(0, page_border_top)

        # Bottom border last line update
        if document.rtf_footnote is not None:
            document.rtf_footnote.border_bottom = BroadcastValue(
                value=document.rtf_footnote.border_bottom, dimension=(1, 1)
            ).update_row(0, page_border_bottom[0])

            document.rtf_footnote.border_bottom = BroadcastValue(
                value=document.rtf_footnote.border_bottom, dimension=(1, 1)
            ).update_row(0, doc_border_bottom[0])
        else:
            # Only update borders if DataFrame has rows
            if dim[0] > 0:
                document.rtf_body.border_bottom = BroadcastValue(
                    value=document.rtf_body.border_bottom, dimension=dim
                ).update_row(dim[0] - 1, page_border_bottom)

                document.rtf_body.border_bottom = BroadcastValue(
                    value=document.rtf_body.border_bottom, dimension=dim
                ).update_row(dim[0] - 1, doc_border_bottom)

        # Set document color context for accurate color index resolution
        from ..services.color_service import color_service

        color_service.set_document_context(document)

        # Body
        rtf_body = self.encoding_service.encode_body(
            document, document.df, document.rtf_body, force_single_page=True
        )

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
                    rtf_title,
                    "\n",
                    self.encoding_service.encode_subline(
                        document.rtf_subline, method="line"
                    ),
                    self.figure_service.encode_figure(document.rtf_figure)
                    if document.rtf_figure is not None
                    and document.rtf_figure.fig_pos == "before"
                    else None,
                    "\n".join(
                        header for sublist in rtf_column_header for header in sublist
                    )
                    if rtf_column_header
                    else None,
                    "\n".join(rtf_body),
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
                    self.figure_service.encode_figure(document.rtf_figure)
                    if document.rtf_figure is not None
                    and document.rtf_figure.fig_pos == "after"
                    else None,
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

        # Clear document context after encoding
        color_service.clear_document_context()

        return result

    def _encode_multi_section_document(self, document: "RTFDocument") -> str:
        """Encode a multi-section document where sections are concatenated row by row.

        Args:
            document: The RTF document with multiple df/rtf_body sections

        Returns:
            Complete RTF string
        """
        from ..attributes import BroadcastValue

        # Calculate total rows across all sections for border management
        total_rows = sum(df.shape[0] for df in document.df)
        first_section_cols = document.df[0].shape[1]

        # Document structure components
        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )

        # Handle page borders (use first section for dimensions)
        doc_border_top = BroadcastValue(
            value=document.rtf_page.border_first, dimension=(1, first_section_cols)
        ).to_list()[0]
        doc_border_bottom = BroadcastValue(
            value=document.rtf_page.border_last, dimension=(1, first_section_cols)
        ).to_list()[0]

        # Encode sections
        all_section_content = []
        is_nested_headers = isinstance(document.rtf_column_header[0], list)

        for i, (section_df, section_body) in enumerate(
            zip(document.df, document.rtf_body)
        ):
            dim = section_df.shape

            # Handle column headers for this section
            section_headers = []
            if is_nested_headers:
                # Nested format: [[header1], [None], [header3]]
                if (
                    i < len(document.rtf_column_header)
                    and document.rtf_column_header[i]
                ):
                    for header in document.rtf_column_header[i]:
                        if header is not None:
                            # Apply top border to first section's first header
                            if i == 0 and not section_headers:
                                header.border_top = BroadcastValue(
                                    value=header.border_top, dimension=dim
                                ).update_row(0, doc_border_top)

                            section_headers.append(
                                self.encoding_service.encode_column_header(
                                    header.text, header, document.rtf_page.col_width
                                )
                            )
            else:
                # Flat format - only apply to first section
                if i == 0:
                    for header in document.rtf_column_header:
                        if header.text is None and section_body.as_colheader:
                            # Auto-generate headers from column names
                            columns = [
                                col
                                for col in section_df.columns
                                if col not in (section_body.page_by or [])
                            ]
                            import polars as pl

                            header.text = pl.DataFrame(
                                [columns],
                                schema=[f"col_{j}" for j in range(len(columns))],
                                orient="row",
                            )

                        # Apply top border to first header
                        if not section_headers:
                            header.border_top = BroadcastValue(
                                value=header.border_top, dimension=dim
                            ).update_row(0, doc_border_top)

                        section_headers.append(
                            self.encoding_service.encode_column_header(
                                header.text, header, document.rtf_page.col_width
                            )
                        )

            # Handle borders for section body
            if i == 0 and not section_headers:  # First section, no headers
                # Apply top border to first row of first section
                section_body.border_top = BroadcastValue(
                    value=section_body.border_top, dimension=dim
                ).update_row(0, doc_border_top)

            # Create a temporary document for this section to maintain compatibility
            from copy import deepcopy

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
        if document.rtf_footnote is not None:
            document.rtf_footnote.border_bottom = BroadcastValue(
                value=document.rtf_footnote.border_bottom, dimension=(1, 1)
            ).update_row(0, doc_border_bottom[0])
        else:
            # Apply bottom border to last section's last row
            last_section_body = document.rtf_body[-1]
            last_section_dim = document.df[-1].shape
            if last_section_dim[0] > 0:
                last_section_body.border_bottom = BroadcastValue(
                    value=last_section_body.border_bottom, dimension=last_section_dim
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

    def _encode_figure_only_document_simple(self, document: "RTFDocument") -> str:
        """Encode a figure-only document with simple page layout.

        This handles figure-only documents with default page settings.
        Multiple figures will have page breaks between them (handled by FigureService).

        Args:
            document: The RTF document with only figure content

        Returns:
            Complete RTF string
        """
        # Build RTF components for simple figure-only document
        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )

        # Assemble final RTF document
        return "".join(
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
                    rtf_title,
                    "\n",
                    self.encoding_service.encode_subline(
                        document.rtf_subline, method="line"
                    ),
                    # FigureService handles page breaks between multiple figures
                    self.figure_service.encode_figure(document.rtf_figure),
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


class PaginatedStrategy(EncodingStrategy):
    """Encoding strategy for multi-page documents with pagination."""

    def __init__(self):
        from ..services import RTFEncodingService
        from ..services.document_service import RTFDocumentService
        from ..services.figure_service import RTFFigureService

        self.encoding_service = RTFEncodingService()
        self.document_service = RTFDocumentService()
        self.figure_service = RTFFigureService()

    def encode(self, document: "RTFDocument") -> str:
        """Encode a paginated document with full pagination support.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        from copy import deepcopy

        import polars as pl

        from ..attributes import BroadcastValue
        from ..row import Utils

        # Handle figure-only documents with multi-page behavior
        if document.df is None:
            return self._encode_figure_only_document_with_pagination(document)

        dim = document.df.shape

        # Set document color context for accurate color index resolution
        from ..services.color_service import color_service

        color_service.set_document_context(document)

        # Prepare DataFrame for processing (remove subline_by columns, apply group_by if needed)
        processed_df, original_df = (
            self.encoding_service.prepare_dataframe_for_body_encoding(
                document.df, document.rtf_body
            )
        )

        # Validate subline_by formatting consistency before processing
        if document.rtf_body.subline_by is not None:
            import warnings

            formatting_warnings = (
                grouping_service.validate_subline_formatting_consistency(
                    original_df, document.rtf_body.subline_by, document.rtf_body
                )
            )
            for warning_msg in formatting_warnings:
                warnings.warn(
                    f"subline_by formatting: {warning_msg}", UserWarning, stacklevel=3
                )

        # Get pagination instance and distribute content (use processed data for distribution)
        _, distributor = self.document_service.create_pagination_instance(document)
        col_total_width = document.rtf_page.col_width
        col_widths = Utils._col_widths(document.rtf_body.col_rel_width, col_total_width)

        # Calculate additional rows per page for r2rtf compatibility
        additional_rows = self.document_service.calculate_additional_rows_per_page(
            document
        )

        # Use original DataFrame for pagination logic (to identify subline_by breaks)
        # but processed DataFrame for the actual content
        pages = distributor.distribute_content(
            df=original_df,  # Use original DataFrame for proper pagination distribution logic
            col_widths=col_widths,
            page_by=document.rtf_body.page_by,
            new_page=document.rtf_body.new_page,
            pageby_header=document.rtf_body.pageby_header,
            table_attrs=document.rtf_body,
            additional_rows_per_page=additional_rows,
            subline_by=document.rtf_body.subline_by,
        )

        # Replace page data with processed data (without subline_by columns)
        for i, page_info in enumerate(pages):
            start_row = page_info["start_row"]
            end_row = page_info["end_row"]
            page_info["data"] = processed_df.slice(start_row, end_row - start_row + 1)

        # Apply group_by processing to each page if needed
        if document.rtf_body.group_by:
            # Calculate global page start indices for context restoration
            page_start_indices = []
            cumulative_rows = 0
            for i, page_info in enumerate(pages):
                if i > 0:  # Skip first page (starts at 0)
                    page_start_indices.append(cumulative_rows)
                cumulative_rows += len(page_info["data"])

            # Process all pages together for proper group_by and page context restoration
            all_page_data = []
            for page_info in pages:
                all_page_data.append(page_info["data"])

            # Concatenate all page data
            full_df = all_page_data[0]
            for page_df in all_page_data[1:]:
                full_df = full_df.vstack(page_df)

            # Apply group_by suppression to the full dataset
            suppressed_df = grouping_service.enhance_group_by(
                full_df, document.rtf_body.group_by
            )

            # Apply page context restoration
            restored_df = grouping_service.restore_page_context(
                suppressed_df, full_df, document.rtf_body.group_by, page_start_indices
            )

            # Split the processed data back to pages
            start_idx = 0
            for page_info in pages:
                page_rows = len(page_info["data"])
                page_info["data"] = restored_df.slice(start_idx, page_rows)
                start_idx += page_rows

        # Prepare border settings
        BroadcastValue(
            value=document.rtf_page.border_first, dimension=(1, dim[1])
        ).to_list()[0]
        BroadcastValue(
            value=document.rtf_page.border_last, dimension=(1, dim[1])
        ).to_list()[0]

        # Generate RTF for each page
        page_contents = []

        for page_info in pages:
            page_elements = []

            # Add page break before each page (except first)
            if not page_info["is_first_page"]:
                page_elements.append(
                    self.document_service.generate_page_break(document)
                )

            # Add title if it should appear on this page
            if (
                document.rtf_title
                and document.rtf_title.text
                and self.document_service.should_show_element_on_page(
                    document.rtf_page.page_title, page_info
                )
            ):
                title_content = self.encoding_service.encode_title(
                    document.rtf_title, method="line"
                )
                if title_content:
                    page_elements.append(title_content)
                    page_elements.append("\n")

            # Add subline if it should appear on this page
            if (
                document.rtf_subline
                and document.rtf_subline.text
                and self.document_service.should_show_element_on_page(
                    document.rtf_page.page_title, page_info
                )
            ):
                subline_content = self.encoding_service.encode_subline(
                    document.rtf_subline, method="line"
                )
                if subline_content:
                    page_elements.append(subline_content)

            # Add subline_by header paragraph if specified
            if page_info.get("subline_header"):
                subline_header_content = self._generate_subline_header(
                    page_info["subline_header"], document.rtf_body
                )
                if subline_header_content:
                    page_elements.append(subline_header_content)

            # Add figures if they should appear on the first page and position is 'before'
            if (
                document.rtf_figure
                and document.rtf_figure.figures
                and document.rtf_figure.fig_pos == "before"
                and page_info["is_first_page"]
            ):
                figure_content = self.figure_service.encode_figure(document.rtf_figure)
                if figure_content:
                    page_elements.append(figure_content)
                    page_elements.append("\n")

            # Add column headers if needed
            if page_info["needs_header"] and document.rtf_column_header:
                if (
                    document.rtf_column_header[0].text is None
                    and document.rtf_body.as_colheader
                ):
                    # Use the processed page data columns (which already have subline_by columns removed)
                    page_df = page_info["data"]
                    columns = list(page_df.columns)
                    document.rtf_column_header[0].text = pl.DataFrame(
                        [columns],
                        schema=[f"col_{i}" for i in range(len(columns))],
                        orient="row",
                    )

                    # Adjust col_rel_width to match the processed columns (without subline_by)
                    if document.rtf_body.subline_by:
                        original_cols = list(document.df.columns)
                        subline_cols = set(document.rtf_body.subline_by)
                        processed_col_indices = [
                            i
                            for i, col in enumerate(original_cols)
                            if col not in subline_cols
                        ]

                        # Ensure we have enough col_rel_width values for all original columns
                        if len(document.rtf_body.col_rel_width) >= len(original_cols):
                            document.rtf_column_header[0].col_rel_width = [
                                document.rtf_body.col_rel_width[i]
                                for i in processed_col_indices
                            ]
                        else:
                            # Fallback: use equal widths if col_rel_width doesn't match
                            document.rtf_column_header[0].col_rel_width = [1] * len(
                                columns
                            )

                # Apply pagination borders to column headers
                # Process each column header with proper borders
                header_elements = []
                for i, header in enumerate(document.rtf_column_header):
                    header_copy = deepcopy(header)

                    # Apply page-level borders to column headers (matching non-paginated behavior)
                    if (
                        page_info["is_first_page"] and i == 0
                    ):  # First header on first page
                        if (
                            document.rtf_page.border_first
                            and header_copy.text is not None
                        ):
                            header_dims = header_copy.text.shape
                            # Apply page border_first to top of first column header
                            header_copy.border_top = BroadcastValue(
                                value=header_copy.border_top, dimension=header_dims
                            ).update_row(
                                0, [document.rtf_page.border_first] * header_dims[1]
                            )

                    # Encode the header with modified borders
                    # Use the header_copy to preserve border modifications
                    header_rtf = self.encoding_service.encode_column_header(
                        header_copy.text, header_copy, document.rtf_page.col_width
                    )
                    header_elements.extend(header_rtf)

                page_elements.extend(header_elements)

            # Add page content (table body) with proper border handling
            page_df = page_info["data"]

            # Apply pagination borders to the body attributes
            page_attrs = self.document_service.apply_pagination_borders(
                document, document.rtf_body, page_info, len(pages)
            )

            # Encode page content with modified borders
            page_body = page_attrs._encode(page_df, col_widths)
            page_elements.extend(page_body)

            # Add footnote if it should appear on this page
            if (
                document.rtf_footnote
                and document.rtf_footnote.text
                and self.document_service.should_show_element_on_page(
                    document.rtf_page.page_footnote, page_info
                )
            ):
                footnote_content = self.encoding_service.encode_footnote(
                    document.rtf_footnote,
                    page_info["page_number"],
                    document.rtf_page.col_width,
                )
                if footnote_content:
                    page_elements.extend(footnote_content)

            # Add source if it should appear on this page
            if (
                document.rtf_source
                and document.rtf_source.text
                and self.document_service.should_show_element_on_page(
                    document.rtf_page.page_source, page_info
                )
            ):
                source_content = self.encoding_service.encode_source(
                    document.rtf_source,
                    page_info["page_number"],
                    document.rtf_page.col_width,
                )
                if source_content:
                    page_elements.extend(source_content)

            # Add figures if they should appear on the last page and position is 'after'
            if (
                document.rtf_figure
                and document.rtf_figure.figures
                and document.rtf_figure.fig_pos == "after"
                and page_info["is_last_page"]
            ):
                figure_content = self.figure_service.encode_figure(document.rtf_figure)
                if figure_content:
                    page_elements.append(figure_content)

            page_contents.extend(page_elements)

        # Build complete RTF document
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
                    "\n".join(page_contents),
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

        # Clear document context after encoding
        color_service.clear_document_context()

        return result

    def _encode_figure_only_document_with_pagination(
        self, document: "RTFDocument"
    ) -> str:
        """Encode a figure-only document with multi-page behavior.

        This method handles figure-only documents where the user has requested
        elements to appear on all pages (page_title="all", etc.)

        For multiple figures, each figure will be on a separate page with
        repeated titles/footnotes/sources as specified.

        Args:
            document: The RTF document with only figure content

        Returns:
            Complete RTF string
        """
        from copy import deepcopy

        from ..figure import rtf_read_figure

        # Get figure information
        if document.rtf_figure is None or document.rtf_figure.figures is None:
            return ""

        # Read figure data to determine number of figures
        figure_data_list, figure_formats = rtf_read_figure(document.rtf_figure.figures)
        num_figures = len(figure_data_list)

        # Build RTF components
        rtf_title = self.encoding_service.encode_title(
            document.rtf_title, method="line"
        )

        # For figure-only documents, footnote should be as_table=False
        footnote_component = document.rtf_footnote
        if footnote_component is not None:
            footnote_component = deepcopy(footnote_component)
            footnote_component.as_table = False

        # Determine which elements should show on each page
        show_title_on_all = document.rtf_page.page_title == "all"
        show_footnote_on_all = document.rtf_page.page_footnote == "all"
        show_source_on_all = document.rtf_page.page_source == "all"

        page_elements = []

        # Add document start
        page_elements.append(self.encoding_service.encode_document_start())
        page_elements.append(self.encoding_service.encode_font_table())
        page_elements.append(self.encoding_service.encode_color_table(document))
        page_elements.append("\n")

        # Add page settings (headers/footers)
        page_elements.append(
            self.encoding_service.encode_page_header(
                document.rtf_page_header, method="line"
            )
        )
        page_elements.append(
            self.encoding_service.encode_page_footer(
                document.rtf_page_footer, method="line"
            )
        )
        page_elements.append(
            self.encoding_service.encode_page_settings(document.rtf_page)
        )

        # Create each page with figure and repeated elements
        for i in range(num_figures):
            is_first_page = i == 0
            is_last_page = i == num_figures - 1

            # Add title based on page settings
            if (
                show_title_on_all
                or (document.rtf_page.page_title == "first" and is_first_page)
                or (document.rtf_page.page_title == "last" and is_last_page)
            ):
                page_elements.append(rtf_title)
                page_elements.append("\n")

            # Add subline
            if is_first_page:  # Only on first page
                page_elements.append(
                    self.encoding_service.encode_subline(
                        document.rtf_subline, method="line"
                    )
                )

            # Add single figure
            width = self.figure_service._get_dimension(document.rtf_figure.fig_width, i)
            height = self.figure_service._get_dimension(
                document.rtf_figure.fig_height, i
            )

            figure_rtf = self.figure_service._encode_single_figure(
                figure_data_list[i],
                figure_formats[i],
                width,
                height,
                document.rtf_figure.fig_align,
            )
            page_elements.append(figure_rtf)
            page_elements.append("\\par ")

            # Add footnote based on page settings
            if footnote_component is not None and (
                show_footnote_on_all
                or (document.rtf_page.page_footnote == "first" and is_first_page)
                or (document.rtf_page.page_footnote == "last" and is_last_page)
            ):
                footnote_content = "\n".join(
                    self.encoding_service.encode_footnote(
                        footnote_component,
                        page_number=i + 1,
                        page_col_width=document.rtf_page.col_width,
                    )
                )
                if footnote_content:
                    page_elements.append(footnote_content)

            # Add source based on page settings
            if document.rtf_source is not None and (
                show_source_on_all
                or (document.rtf_page.page_source == "first" and is_first_page)
                or (document.rtf_page.page_source == "last" and is_last_page)
            ):
                source_content = "\n".join(
                    self.encoding_service.encode_source(
                        document.rtf_source,
                        page_number=i + 1,
                        page_col_width=document.rtf_page.col_width,
                    )
                )
                if source_content:
                    page_elements.append(source_content)

            # Add page break between figures (except after last figure)
            if not is_last_page:
                page_elements.append("\\page ")

        # Close document
        page_elements.append("\n\n")
        page_elements.append("}")

        return "".join([item for item in page_elements if item is not None])

    def _generate_subline_header(self, subline_header_info: dict, rtf_body) -> str:
        """Generate RTF paragraph for subline_by header.

        Args:
            subline_header_info: Dictionary with column values for the subline header
            rtf_body: RTFBody attributes for formatting

        Returns:
            RTF string for the subline paragraph
        """
        if not subline_header_info:
            return ""

        # Use the raw group values without column names
        if "group_values" in subline_header_info:
            # Extract just the values without column prefixes
            header_parts = []
            for col, value in subline_header_info["group_values"].items():
                if value is not None:
                    header_parts.append(str(value))

            if not header_parts:
                return ""

            header_text = ", ".join(header_parts)
        else:
            # Fallback for backward compatibility
            header_parts = []
            for col, value in subline_header_info.items():
                if value is not None and col not in ["group_by_columns", "header_text"]:
                    header_parts.append(str(value))

            if not header_parts:
                return ""

            header_text = ", ".join(header_parts)

        # Create RTF paragraph with minimal spacing (no sb180/sa180 to eliminate space between header and table)
        return (
            f"{{\\pard\\hyphpar\\fi0\\li0\\ri0\\ql\\fs18{{\\f0 {header_text}}}\\par}}"
        )
