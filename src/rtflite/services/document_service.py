"""RTF Document Service - handles all document-level operations."""


class RTFDocumentService:
    """Service for handling RTF document operations including pagination and layout."""

    def __init__(self):
        from .encoding_service import RTFEncodingService

        self.encoding_service = RTFEncodingService()

    def get_pagination_strategy(self, document):
        """Get the appropriate pagination strategy for the document.

        Returns:
            PaginationStrategy instance
        """
        from ..pagination.strategies import StrategyRegistry

        # Determine strategy
        strategy_name = "default"
        if document.rtf_body.subline_by:
            strategy_name = "subline"
        elif document.rtf_body.page_by:
            strategy_name = "page_by"

        # Get strategy class
        strategy_cls = StrategyRegistry.get(strategy_name)
        return strategy_cls()

    def calculate_additional_rows_per_page(self, document) -> int:
        """Calculate additional rows needed per page for headers, footnotes, sources."""
        additional_rows = 0

        # Count subline_by header (appears on each page)
        if document.rtf_body.subline_by:
            additional_rows += 1  # Each subline_by header consumes 1 row

        # Count column headers (repeat on each page)
        if document.rtf_column_header:
            # Handle nested column headers for multi-section documents
            if isinstance(document.rtf_column_header[0], list):
                # Nested format: count all non-None headers across all sections
                for section_headers in document.rtf_column_header:
                    if section_headers:  # Skip [None] sections
                        for header in section_headers:
                            if header and header.text is not None:
                                additional_rows += 1
            else:
                # Flat format: original logic
                for header in document.rtf_column_header:
                    if header is not None and header.text is not None:
                        additional_rows += 1

        # Count footnote rows
        if document.rtf_footnote and document.rtf_footnote.text:
            additional_rows += 1

        # Count source rows
        if document.rtf_source and document.rtf_source.text:
            additional_rows += 1

        return additional_rows

    def generate_page_break(self, document) -> str:
        """Generate proper RTF page break sequence."""
        return self.encoding_service.encode_page_break(
            document.rtf_page,
            lambda: self.encoding_service.encode_page_margin(document.rtf_page),
        )
