"""RTF encoding service that handles document component encoding."""

from typing import Optional, List, Dict, Any
from collections.abc import MutableSequence

class RTFEncodingService:
    """Service class that handles RTF component encoding operations.
    
    This class extracts encoding logic from RTFDocument to improve separation
    of concerns and enable better testing and maintainability.
    """
    
    def __init__(self):
        from ..rtf import RTFSyntaxGenerator
        self.syntax = RTFSyntaxGenerator()
    
    def encode_document_start(self) -> str:
        """Encode RTF document start."""
        return "{\\rtf1\\ansi\n\\deff0\\deflang1033"
    
    def encode_font_table(self) -> str:
        """Encode RTF font table."""
        return self.syntax.generate_font_table()
    
    def encode_page_settings(self, page_config) -> str:
        """Encode RTF page settings.
        
        Args:
            page_config: RTFPage configuration object
            
        Returns:
            RTF page settings string
        """
        return self.syntax.generate_page_settings(
            page_config.width, 
            page_config.height, 
            page_config.margin
        )
    
    def encode_page_header(self, header_config, method: str = "line") -> str:
        """Encode page header component.
        
        Args:
            header_config: RTFPageHeader configuration
            method: Encoding method
            
        Returns:
            RTF header string
        """
        if header_config is None or not header_config.text:
            return ""
        
        # Use the existing text encoding method
        return header_config._encode_text(
            text=header_config.text, method=method
        )
    
    def encode_page_footer(self, footer_config, method: str = "line") -> str:
        """Encode page footer component.
        
        Args:
            footer_config: RTFPageFooter configuration
            method: Encoding method
            
        Returns:
            RTF footer string
        """
        if footer_config is None or not footer_config.text:
            return ""
        
        # Use the existing text encoding method
        return footer_config._encode_text(
            text=footer_config.text, method=method
        )
    
    def encode_title(self, title_config, method: str = "line") -> str:
        """Encode title component.
        
        Args:
            title_config: RTFTitle configuration
            method: Encoding method
            
        Returns:
            RTF title string
        """
        if not title_config or not title_config.text:
            return ""
        
        # Use the existing text encoding method
        return title_config._encode_text(text=title_config.text, method=method)
    
    def encode_subline(self, subline_config, method: str = "line") -> str:
        """Encode subline component.
        
        Args:
            subline_config: RTFSubline configuration
            method: Encoding method
            
        Returns:
            RTF subline string
        """
        if subline_config is None or not subline_config.text:
            return ""
        
        # Use the existing text encoding method
        return subline_config._encode_text(text=subline_config.text, method=method)
    
    def encode_footnote(self, footnote_config, page_number: int = None) -> List[str]:
        """Encode footnote component.
        
        Args:
            footnote_config: RTFFootnote configuration
            page_number: Page number for footnote
            
        Returns:
            List of RTF footnote strings
        """
        if footnote_config is None:
            return []
        
        result = []
        if footnote_config.text is not None:
            # For now, delegate to existing encoding logic
            footnote_rtf = footnote_config._encode(text=footnote_config.text)
            result.extend(footnote_rtf)
        
        return result
    
    def encode_source(self, source_config, page_number: int = None) -> List[str]:
        """Encode source component.
        
        Args:
            source_config: RTFSource configuration
            page_number: Page number for source
            
        Returns:
            List of RTF source strings
        """
        if source_config is None:
            return []
        
        result = []
        if source_config.text is not None:
            # For now, delegate to existing encoding logic
            source_rtf = source_config._encode(text=source_config.text)
            result.extend(source_rtf)
        
        return result
    
    def encode_body(self, df, rtf_attrs) -> List[str]:
        """Encode table body component.
        
        Args:
            df: DataFrame containing table data
            rtf_attrs: RTFBody attributes
            
        Returns:
            List of RTF body strings
        """
        # For now, delegate to existing encoding logic
        return rtf_attrs._encode(df=df)
    
    def encode_column_header(self, df, rtf_attrs) -> List[str]:
        """Encode column header component.
        
        Args:
            df: DataFrame containing header data
            rtf_attrs: RTFColumnHeader attributes
            
        Returns:
            List of RTF header strings
        """
        # For now, delegate to existing encoding logic
        return rtf_attrs._encode(df=df)