"""RTF encoding engine for orchestrating document generation."""

from typing import TYPE_CHECKING
import polars as pl

from .strategies import EncodingStrategy, SinglePageStrategy, PaginatedStrategy

if TYPE_CHECKING:
    from ..encode import RTFDocument


class RTFEncodingEngine:
    """Main engine for RTF document encoding.
    
    This class orchestrates the encoding process by selecting the appropriate
    strategy based on document characteristics and delegating the actual
    encoding to strategy classes.
    """
    
    def __init__(self):
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
        if self._needs_pagination(document):
            return self._paginated_strategy
        else:
            return self._single_page_strategy
    
    def _needs_pagination(self, document: "RTFDocument") -> bool:
        """Determine if the document requires pagination.
        
        Args:
            document: The RTF document to analyze
            
        Returns:
            True if pagination is needed, False otherwise
        """
        # Check if page_by is specified and enabled
        if document.rtf_body.page_by and document.rtf_body.new_page:
            return True
            
        # Check if content exceeds page capacity
        if document.rtf_page.nrow and document.df.shape[0] > document.rtf_page.nrow:
            return True
            
        return False