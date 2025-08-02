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
        from ..rtf import RTFDocumentAssembler, RTFComponentEncoder
        self.assembler = RTFDocumentAssembler()
        self.encoder = RTFComponentEncoder()
    
    def encode(self, document: "RTFDocument") -> str:
        """Encode a single-page document.
        
        Args:
            document: The RTF document to encode
            
        Returns:
            Complete RTF string
        """
        # For now, still delegate to maintain compatibility
        # Full migration will come in the next step
        return document._rtf_encode_single_page()


class PaginatedStrategy(EncodingStrategy):
    """Encoding strategy for multi-page documents with pagination."""
    
    def encode(self, document: "RTFDocument") -> str:
        """Encode a paginated document.
        
        Args:
            document: The RTF document to encode
            
        Returns:
            Complete RTF string
        """
        # Delegate to the original paginated encoding method for now
        # This maintains backward compatibility while we refactor
        return document._rtf_encode_paginated()


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