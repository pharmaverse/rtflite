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
        self.encoding_service = RTFEncodingService()
    
    def encode(self, document: "RTFDocument") -> str:
        """Encode a single-page document with complete border and layout handling.
        
        Args:
            document: The RTF document to encode
            
        Returns:
            Complete RTF string
        """
        import polars as pl
        from ..attributes import BroadcastValue
        
        # Original single-page encoding logic
        dim = document.df.shape

        # Title
        rtf_title = self.encoding_service.encode_title(document.rtf_title, method="line")

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
            if document.rtf_column_header[0].text is None and document.rtf_body.as_colheader:
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
                self.encoding_service.encode_column_header(header.text, header, document.rtf_page.col_width)
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
        rtf_body = self.encoding_service.encode_body(document, document.df, document.rtf_body)

        return "\n".join(
            [
                item
                for item in [
                    self.encoding_service.encode_document_start(),
                    self.encoding_service.encode_font_table(),
                    "\n",
                    self.encoding_service.encode_page_header(document.rtf_page_header, method="line"),
                    self.encoding_service.encode_page_footer(document.rtf_page_footer, method="line"),
                    self.encoding_service.encode_page_settings(document.rtf_page),
                    rtf_title,
                    "\n",
                    self.encoding_service.encode_subline(document.rtf_subline, method="line"),
                    "\n".join(
                        header for sublist in rtf_column_header for header in sublist
                    )
                    if rtf_column_header
                    else None,
                    "\n".join(rtf_body),
                    "\n".join(self.encoding_service.encode_footnote(
                        document.rtf_footnote, page_number=1, page_col_width=document.rtf_page.col_width
                    ))
                    if document.rtf_footnote is not None
                    else None,
                    "\n".join(self.encoding_service.encode_source(
                        document.rtf_source, page_number=1, page_col_width=document.rtf_page.col_width
                    ))
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
        self.encoding_service = RTFEncodingService()
    
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
        
        dim = document.df.shape

        # Get pagination instance and distribute content
        _, distributor = document._create_pagination_instance()
        col_total_width = document.rtf_page.col_width
        col_widths = Utils._col_widths(document.rtf_body.col_rel_width, col_total_width)

        # Calculate additional rows per page for r2rtf compatibility
        additional_rows = document._calculate_additional_rows_per_page()
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
                page_elements.append(document._rtf_page_break_encode())

            # Add title if it should appear on this page
            if (
                document.rtf_title
                and document.rtf_title.text
                and document._should_show_element_on_page(
                    document.rtf_page.page_title_location, page_info
                )
            ):
                title_content = self.encoding_service.encode_title(document.rtf_title, method="line")
                if title_content:
                    page_elements.append(title_content)
                    page_elements.append("\n")

            # Add subline if it should appear on this page
            if (
                document.rtf_subline
                and document.rtf_subline.text
                and document._should_show_element_on_page(
                    document.rtf_page.page_title_location, page_info
                )
            ):
                subline_content = self.encoding_service.encode_subline(document.rtf_subline, method="line")
                if subline_content:
                    page_elements.append(subline_content)
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
                        if document.rtf_page.border_first and header_copy.text is not None:
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
            page_attrs = document._apply_pagination_borders(
                document.rtf_body, page_info, len(pages)
            )

            # Encode page content with modified borders
            page_body = page_attrs._encode(page_df, col_widths)
            page_elements.extend(page_body)

            # Add footnote if it should appear on this page
            if (
                document.rtf_footnote
                and document.rtf_footnote.text
                and document._should_show_element_on_page(
                    document.rtf_page.page_footnote_location, page_info
                )
            ):
                footnote_content = self.encoding_service.encode_footnote(
                    document.rtf_footnote, page_info["page_number"], document.rtf_page.col_width
                )
                if footnote_content:
                    page_elements.extend(footnote_content)

            # Add source if it should appear on this page
            if (
                document.rtf_source
                and document.rtf_source.text
                and document._should_show_element_on_page(
                    document.rtf_page.page_source_location, page_info
                )
            ):
                source_content = self.encoding_service.encode_source(
                    document.rtf_source, page_info["page_number"], document.rtf_page.col_width
                )
                if source_content:
                    page_elements.extend(source_content)

            page_contents.extend(page_elements)

        # Build complete RTF document
        return "\n".join(
            [
                item
                for item in [
                    self.encoding_service.encode_document_start(),
                    self.encoding_service.encode_font_table(),
                    "\n",
                    self.encoding_service.encode_page_header(document.rtf_page_header, method="line"),
                    self.encoding_service.encode_page_footer(document.rtf_page_footer, method="line"),
                    self.encoding_service.encode_page_settings(document.rtf_page),
                    "\n".join(page_contents),
                    "\n\n",
                    "}",
                ]
                if item is not None
            ]
        )


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