"""
Enhanced encoding service for subline_by functionality.

This service extends the encoding process to handle subline_by
by injecting subheader rows at appropriate positions.
"""

from typing import List, Optional, MutableSequence
import polars as pl
from ..row import Row
from ..row_subheader import SubheaderRow
from .subline_service import subline_service


class SublineEncodingService:
    """Service for encoding tables with subline_by functionality"""
    
    def encode_with_sublines(
        self,
        df: pl.DataFrame,
        rtf_attrs,
        col_widths: List[float],
        subline_by: Optional[List[str]] = None
    ) -> MutableSequence[str]:
        """Encode a DataFrame with subline_by support
        
        Args:
            df: Input DataFrame
            rtf_attrs: RTF body attributes
            col_widths: Column widths
            subline_by: List of columns to create sublines by
            
        Returns:
            List of RTF strings representing the encoded table with subheaders
        """
        if not subline_by:
            # No subline_by, use regular encoding
            return rtf_attrs._encode(df, col_widths)
        
        # Process subline_by to get modified DataFrame and subheader info
        processed_df, subheaders = subline_service.process_subline_by(
            df,
            subline_by=subline_by,
            col_widths=col_widths,
            text_format=getattr(rtf_attrs, 'subline_text_format', 'b'),
            text_justification=getattr(rtf_attrs, 'subline_text_justification', 'l'),
            text_font_size=getattr(rtf_attrs, 'subline_text_font_size', None),
            text_color=getattr(rtf_attrs, 'subline_text_color', None),
            border_top=getattr(rtf_attrs, 'subline_border_top', 'single'),
            border_bottom=getattr(rtf_attrs, 'subline_border_bottom', 'single'),
        )
        
        # Update column widths since we removed subline_by columns
        adjusted_col_widths = self._adjust_column_widths(
            col_widths, len(df.columns), len(processed_df.columns)
        )
        
        # Encode the data rows normally
        rtf_rows = rtf_attrs._encode(processed_df, adjusted_col_widths)
        
        # Now insert subheader rows at appropriate positions
        # We need to work backwards to maintain correct positions
        sorted_subheaders = sorted(subheaders, key=lambda x: x['insert_before_row'], reverse=True)
        
        for subheader in sorted_subheaders:
            # Create SubheaderRow with proper defaults
            subheader_row = SubheaderRow(
                text=subheader['text'],
                text_format=subheader.get('text_format', 'b'),
                text_justification=subheader.get('text_justification', 'l'),
                text_font_size=subheader.get('text_font_size') or 9.0,
                text_color=subheader.get('text_color') or 'black',
                text_background_color=subheader.get('text_background_color'),
                col_widths=adjusted_col_widths,
                border_top=subheader.get('border_top', 'single'),
                border_bottom=subheader.get('border_bottom', 'single'),
                border_width=subheader.get('border_width', 15),
                height=getattr(rtf_attrs, 'subline_row_height', 0.20)
            )
            
            # Get RTF for subheader
            subheader_rtf = subheader_row._as_rtf()
            
            # Find the position to insert
            # Each row in the encoded output consists of multiple RTF commands
            # We need to identify row boundaries
            row_position = self._find_row_position(rtf_rows, subheader['insert_before_row'])
            
            # Insert subheader RTF at the calculated position
            for i, rtf_line in enumerate(subheader_rtf):
                rtf_rows.insert(row_position + i, rtf_line)
        
        return rtf_rows
    
    def _adjust_column_widths(
        self,
        original_widths: List[float],
        original_cols: int,
        new_cols: int
    ) -> List[float]:
        """Adjust column widths after removing subline_by columns
        
        Args:
            original_widths: Original column widths
            original_cols: Original number of columns
            new_cols: New number of columns after removing subline_by
            
        Returns:
            Adjusted column widths
        """
        if original_cols == new_cols:
            return original_widths
        
        # If user provided widths for the final columns (after subline_by removal)
        if len(original_widths) == new_cols:
            return original_widths
        
        # Calculate how many columns were removed
        removed_cols = original_cols - new_cols
        
        # If we have exact widths for all original columns, remove the first N
        if len(original_widths) == original_cols:
            return original_widths[removed_cols:]
        
        # Otherwise, redistribute widths proportionally
        total_width = sum(original_widths)
        return [total_width / new_cols] * new_cols
    
    def _find_row_position(self, rtf_rows: List[str], row_index: int) -> int:
        """Find the position in rtf_rows list where a specific data row starts
        
        Args:
            rtf_rows: List of RTF command strings
            row_index: Index of the data row to find
            
        Returns:
            Position in rtf_rows list where the row starts
        """
        # Count occurrences of \intbl\row\pard which marks end of rows
        row_count = 0
        for i, line in enumerate(rtf_rows):
            if '\\intbl\\row\\pard' in line:
                if row_count == row_index:
                    # Find the start of this row by looking backwards
                    # for the previous row end or start of list
                    if row_count == 0:
                        return 0
                    else:
                        # Look for previous row end
                        for j in range(i-1, -1, -1):
                            if '\\intbl\\row\\pard' in rtf_rows[j]:
                                return j + 1
                        return 0
                row_count += 1
        
        # If row_index is beyond the data, return end position
        return len(rtf_rows)


# Create singleton instance
subline_encoding_service = SublineEncodingService()