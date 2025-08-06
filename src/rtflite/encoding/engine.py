"""RTF encoding engine for orchestrating document generation."""

from typing import TYPE_CHECKING

from .strategies import EncodingStrategy, PaginatedStrategy, SinglePageStrategy

if TYPE_CHECKING:
    from ..encode import RTFDocument


class RTFEncodingEngine:
    """Main engine for RTF document encoding.

    This class orchestrates the encoding process by selecting the appropriate
    strategy based on document characteristics and delegating the actual
    encoding to strategy classes.
    """

    def __init__(self):
        from ..services.document_service import RTFDocumentService

        self._document_service = RTFDocumentService()
        self._single_page_strategy = SinglePageStrategy()
        self._paginated_strategy = PaginatedStrategy()

    def encode_document(self, document: "RTFDocument") -> str:
        """Encode an RTF document using the appropriate strategy.

        Args:
            document: The RTF document to encode

        Returns:
            Complete RTF string
        """
        strategy = self._select_strategy(document)
        return strategy.encode(document)

    def _select_strategy(self, document: "RTFDocument") -> "EncodingStrategy":
        """Select the appropriate encoding strategy based on document characteristics.

        Args:
            document: The RTF document to analyze

        Returns:
            The selected encoding strategy
        """
        if self._document_service.needs_pagination(document):
            return self._paginated_strategy
        else:
            return self._single_page_strategy
