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
            page_config.margin,
            page_config.orientation
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
        result= header_config._encode_text(
            text=header_config.text, method=method
        )
        
        return f"{{\\header{result}}}"
    
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
        result = footer_config._encode_text(
            text=footer_config.text, method=method
        )
        return f"{{\\footer{result}}}"
    
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
    
    def encode_footnote(self, footnote_config, page_number: int = None, page_col_width: float = None) -> List[str]:
        """Encode footnote component with advanced formatting.
        
        Args:
            footnote_config: RTFFootnote configuration
            page_number: Page number for footnote
            page_col_width: Page column width for calculations
            
        Returns:
            List of RTF footnote strings
        """
        if footnote_config is None:
            return []
        
        rtf_attrs = footnote_config
        
        # Apply page-specific border if set
        if (
            hasattr(rtf_attrs, "_page_border_style")
            and page_number is not None
            and page_number in rtf_attrs._page_border_style
        ):
            border_style = rtf_attrs._page_border_style[page_number]
            # Create a copy with modified border
            rtf_attrs = rtf_attrs.model_copy()
            rtf_attrs.border_bottom = [[border_style]]
        
        # Check if footnote should be rendered as table or paragraph
        if hasattr(rtf_attrs, 'as_table') and not rtf_attrs.as_table:
            # Render as paragraph (plain text)
            if isinstance(rtf_attrs.text, list):
                text_list = rtf_attrs.text
            else:
                text_list = [rtf_attrs.text] if rtf_attrs.text else []
            
            # Use TextAttributes._encode_text method directly for paragraph rendering
            return rtf_attrs._encode_text(text_list, method="paragraph")
        else:
            # Render as table (default behavior)
            if page_col_width is not None:
                from ..row import Utils
                col_total_width = page_col_width
                col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)
                
                # Create DataFrame from text string
                import polars as pl
                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df, col_widths)
            else:
                # Fallback without column width calculations
                import polars as pl
                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df)
    
    def encode_source(self, source_config, page_number: int = None, page_col_width: float = None) -> List[str]:
        """Encode source component with advanced formatting.
        
        Args:
            source_config: RTFSource configuration
            page_number: Page number for source
            page_col_width: Page column width for calculations
            
        Returns:
            List of RTF source strings
        """
        if source_config is None:
            return []
        
        rtf_attrs = source_config
        
        # Apply page-specific border if set
        if (
            hasattr(rtf_attrs, "_page_border_style")
            and page_number is not None
            and page_number in rtf_attrs._page_border_style
        ):
            border_style = rtf_attrs._page_border_style[page_number]
            # Create a copy with modified border
            rtf_attrs = rtf_attrs.model_copy()
            rtf_attrs.border_bottom = [[border_style]]
        
        # Check if source should be rendered as table or paragraph
        if hasattr(rtf_attrs, 'as_table') and not rtf_attrs.as_table:
            # Render as paragraph (plain text)
            if isinstance(rtf_attrs.text, list):
                text_list = rtf_attrs.text
            else:
                text_list = [rtf_attrs.text] if rtf_attrs.text else []
            
            # Use TextAttributes._encode_text method directly for paragraph rendering
            return rtf_attrs._encode_text(text_list, method="paragraph")
        else:
            # Render as table (default behavior)
            if page_col_width is not None:
                from ..row import Utils
                col_total_width = page_col_width
                col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)
                
                # Create DataFrame from text string
                import polars as pl
                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df, col_widths)
            else:
                # Fallback without column width calculations
                import polars as pl
                df = pl.DataFrame([[rtf_attrs.text]])
                return rtf_attrs._encode(df)
    
    def encode_body(self, document, df, rtf_attrs) -> List[str]:
        """Encode table body component with full pagination support.
        
        Args:
            document: RTFDocument instance for accessing pagination logic
            df: DataFrame containing table data
            rtf_attrs: RTFBody attributes
            
        Returns:
            List of RTF body strings
        """
        if rtf_attrs is None:
            return None

        # Initialize dimensions and widths
        from ..row import Utils
        from .document_service import RTFDocumentService
        
        document_service = RTFDocumentService()
        col_total_width = document.rtf_page.col_width
        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, col_total_width)

        # Check if pagination is needed
        if document_service.needs_pagination(document):
            return self._encode_body_paginated(document, df, rtf_attrs, col_widths)

        # Handle existing page_by grouping (non-paginated)
        page_by = document_service.process_page_by(document)
        if page_by is None:
            return rtf_attrs._encode(df, col_widths)

        rows = []
        for section in page_by:
            # Skip empty sections
            indices = [(row, col) for row, col, level in section]
            if not indices:
                continue

            # Create DataFrame for current section
            from ..attributes import BroadcastValue
            import polars as pl
            section_df = pl.DataFrame(
                {
                    str(i): [BroadcastValue(value=df).iloc(row, col)]
                    for i, (row, col) in enumerate(indices)
                }
            )

            # Collect all text and table attributes
            from ..input import TableAttributes
            section_attrs_dict = rtf_attrs._get_section_attributes(indices)
            section_attrs = TableAttributes(**section_attrs_dict)

            # Calculate column widths and encode section
            section_col_widths = Utils._col_widths(
                section_attrs.col_rel_width, col_total_width
            )
            rows.extend(section_attrs._encode(section_df, section_col_widths))

        return rows
    
    def _encode_body_paginated(self, document, df, rtf_attrs, col_widths) -> List[str]:
        """Encode body content with pagination support."""
        from .document_service import RTFDocumentService
        
        document_service = RTFDocumentService()
        _, distributor = document_service.create_pagination_instance(document)

        # Distribute content across pages (r2rtf compatible)
        additional_rows = document_service.calculate_additional_rows_per_page(document)
        pages = distributor.distribute_content(
            df=df,
            col_widths=col_widths,
            table_attributes=rtf_attrs,
            additional_rows_per_page=additional_rows,
        )

        # Generate RTF for each page
        all_rows = []
        for page_num, page_content in enumerate(pages, 1):
            page_rows = []

            # Add page header content
            if page_content.get("headers"):
                for header_content in page_content["headers"]:
                    header_text = header_content.get("text", "")
                    if header_text:
                        page_rows.append(header_text)

            # Add table data
            if page_content.get("data"):
                data_rows = page_content["data"]
                if data_rows:
                    page_rows.extend(data_rows)

            # Add footer content
            if page_content.get("footers"):
                for footer_content in page_content["footers"]:
                    footer_text = footer_content.get("text", "")
                    if footer_text:
                        page_rows.append(footer_text)

            # Add page break between pages (except last page)
            if page_num < len(pages):
                page_rows.append(document._rtf_page_break_encode())

            all_rows.extend(page_rows)

        return all_rows
    
    def encode_column_header(self, df, rtf_attrs, page_col_width: float) -> List[str]:
        """Encode column header component with column width support.
        
        Args:
            df: DataFrame containing header data
            rtf_attrs: RTFColumnHeader attributes
            page_col_width: Page column width for calculations
            
        Returns:
            List of RTF header strings
        """
        if rtf_attrs is None:
            return None

        dim = df.shape
        
        rtf_attrs.col_rel_width = rtf_attrs.col_rel_width or [1] * dim[1]
        rtf_attrs = rtf_attrs._set_default()

        from ..row import Utils
        col_widths = Utils._col_widths(rtf_attrs.col_rel_width, page_col_width)

        return rtf_attrs._encode(df, col_widths)
    
    def encode_page_break(self, page_config, page_margin_encode_func) -> str:
        """Generate proper RTF page break sequence matching r2rtf format.
        
        Args:
            page_config: RTFPage configuration
            page_margin_encode_func: Function to encode page margins
            
        Returns:
            RTF page break string
        """
        from ..core import RTFConstants
        page_setup = (
            f"\\paperw{int(page_config.width * RTFConstants.TWIPS_PER_INCH)}"
            f"\\paperh{int(page_config.height * RTFConstants.TWIPS_PER_INCH)}\n\n"
            f"{page_margin_encode_func()}\n"
        )

        return f"{{\\pard\\fs2\\par}}\\page{{\\pard\\fs2\\par}}\n{page_setup}"
    
    def encode_page_margin(self, page_config) -> str:
        """Define RTF margin settings.
        
        Args:
            page_config: RTFPage configuration with margin settings
            
        Returns:
            RTF margin settings string
        """
        from ..row import Utils
        margin_codes = [
            "\\margl",
            "\\margr",
            "\\margt",
            "\\margb",
            "\\headery",
            "\\footery",
        ]
        margins = [Utils._inch_to_twip(m) for m in page_config.margin]
        margin = "".join(
            f"{code}{margin}" for code, margin in zip(margin_codes, margins)
        )
        return margin + "\n"
    
