"""Encoding strategies for different types of RTF documents."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

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
                columns = [
                    col
                    for col in document.df.columns
                    if col not in (document.rtf_body.page_by or [])
                ]
                # Create DataFrame with explicit column names to ensure single row
                document.rtf_column_header[0].text = pl.DataFrame(
                    [columns],
                    schema=[f"col_{i}" for i in range(len(columns))],
                    orient="row",
                )
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

        # Body
        rtf_body = self.encoding_service.encode_body(
            document, document.df, document.rtf_body
        )

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
        
        for i, (section_df, section_body) in enumerate(zip(document.df, document.rtf_body)):
            dim = section_df.shape
            
            # Handle column headers for this section
            section_headers = []
            if is_nested_headers:
                # Nested format: [[header1], [None], [header3]]
                if i < len(document.rtf_column_header) and document.rtf_column_header[i]:
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
                            columns = [col for col in section_df.columns
                                     if col not in (section_body.page_by or [])]
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
                all_section_content.extend(["\n".join(
                    header for sublist in section_headers for header in sublist
                )])
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

        return "\n".join([
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
        ])

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
        import polars as pl
        from ..row import Utils
        from ..attributes import BroadcastValue
        from copy import deepcopy

        # Handle figure-only documents with multi-page behavior
        if document.df is None:
            return self._encode_figure_only_document_with_pagination(document)

        dim = document.df.shape

        # Get pagination instance and distribute content
        _, distributor = self.document_service.create_pagination_instance(document)
        col_total_width = document.rtf_page.col_width
        col_widths = Utils._col_widths(document.rtf_body.col_rel_width, col_total_width)

        # Calculate additional rows per page for r2rtf compatibility
        additional_rows = self.document_service.calculate_additional_rows_per_page(
            document
        )
        pages = distributor.distribute_content(
            df=document.df,
            col_widths=col_widths,
            page_by=document.rtf_body.page_by,
            new_page=document.rtf_body.new_page,
            pageby_header=document.rtf_body.pageby_header,
            table_attrs=document.rtf_body,
            additional_rows_per_page=additional_rows,
        )

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
                    columns = [
                        col
                        for col in document.df.columns
                        if col not in (document.rtf_body.page_by or [])
                    ]
                    document.rtf_column_header[0].text = pl.DataFrame(
                        [columns],
                        schema=[f"col_{i}" for i in range(len(columns))],
                        orient="row",
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
                    "\n".join(page_contents),
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )

    def _encode_figure_only_document_with_pagination(self, document: "RTFDocument") -> str:
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
        page_elements.append("\n")
        
        # Add page settings (headers/footers)
        page_elements.append(self.encoding_service.encode_page_header(
            document.rtf_page_header, method="line"
        ))
        page_elements.append(self.encoding_service.encode_page_footer(
            document.rtf_page_footer, method="line"
        ))
        page_elements.append(self.encoding_service.encode_page_settings(document.rtf_page))
        
        # Create each page with figure and repeated elements
        for i in range(num_figures):
            is_first_page = (i == 0)
            is_last_page = (i == num_figures - 1)
            
            # Add title based on page settings
            if (show_title_on_all or 
                (document.rtf_page.page_title == "first" and is_first_page) or
                (document.rtf_page.page_title == "last" and is_last_page)):
                page_elements.append(rtf_title)
                page_elements.append("\n")
            
            # Add subline
            if is_first_page:  # Only on first page
                page_elements.append(self.encoding_service.encode_subline(
                    document.rtf_subline, method="line"
                ))
            
            # Add single figure
            width = self.figure_service._get_dimension(document.rtf_figure.fig_width, i)
            height = self.figure_service._get_dimension(document.rtf_figure.fig_height, i)
            
            figure_rtf = self.figure_service._encode_single_figure(
                figure_data_list[i], figure_formats[i], width, height, 
                document.rtf_figure.fig_align
            )
            page_elements.append(figure_rtf)
            page_elements.append("\\par ")
            
            # Add footnote based on page settings
            if (footnote_component is not None and
                (show_footnote_on_all or 
                 (document.rtf_page.page_footnote == "first" and is_first_page) or
                 (document.rtf_page.page_footnote == "last" and is_last_page))):
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
            if (document.rtf_source is not None and
                (show_source_on_all or 
                 (document.rtf_page.page_source == "first" and is_first_page) or
                 (document.rtf_page.page_source == "last" and is_last_page))):
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


class ListEncodingStrategy(EncodingStrategy):
    """Encoding strategy for RTF documents containing lists (future feature)."""

    def encode(self, document: "RTFDocument") -> str:
        """Encode a document with list content.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        # Placeholder for future rtf_encode_list functionality
        raise NotImplementedError("List encoding strategy not yet implemented")


class FigureEncodingStrategy(EncodingStrategy):
    """Encoding strategy for RTF documents containing figures (future feature)."""

    def encode(self, document: "RTFDocument") -> str:
        """Encode a document with figure content.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        # Placeholder for future rtf_encode_figure functionality
        raise NotImplementedError("Figure encoding strategy not yet implemented")
