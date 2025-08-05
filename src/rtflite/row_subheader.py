"""
Subheader row implementation for rtflite.

This module provides a SubheaderRow class that creates special
rows spanning all columns for subline_by functionality.
"""

from collections.abc import MutableSequence
from pydantic import BaseModel, Field
from .row import Utils, ROW_JUSTIFICATION_CODES
from .row import TextContent


class SubheaderRow(BaseModel):
    """Represents a subheader row that spans all columns in an RTF table."""
    
    text: str = Field(..., description="Subheader text")
    text_format: str = Field(default="b", description="Text format (b, i, bi, etc.)")
    text_justification: str = Field(default="l", description="Text justification")
    text_font_size: float = Field(default=9, description="Font size in points")
    text_color: str = Field(default="black", description="Text color")
    text_background_color: str | None = Field(default=None, description="Background color")
    col_widths: list[float] = Field(..., description="Column widths for spanning")
    border_top: str = Field(default="single", description="Top border style")
    border_bottom: str = Field(default="single", description="Bottom border style")
    border_width: int = Field(default=15, description="Border width in twips")
    height: float = Field(default=0.20, description="Row height in inches")
    
    def _as_rtf(self) -> MutableSequence[str]:
        """Format a subheader row in RTF that spans all columns."""
        rtf = []
        
        # Calculate total width in twips
        total_width_twips = Utils._inch_to_twip(sum(self.col_widths))
        
        # Row definition
        rtf.append(
            f"\\trowd\\trgaph{int(Utils._inch_to_twip(self.height) / 2)}"
            f"\\trleft0{ROW_JUSTIFICATION_CODES['c']}"
        )
        
        # Single cell that spans all columns
        # Top border
        if self.border_top and self.border_top != "":
            from .core.constants import RTFConstants
            border_style = RTFConstants.BORDER_CODES.get(self.border_top, "")
            if border_style:
                rtf.append(f"\\clbrdrt{border_style}\\brdrw{self.border_width}")
        
        # Bottom border
        if self.border_bottom and self.border_bottom != "":
            from .core.constants import RTFConstants
            border_style = RTFConstants.BORDER_CODES.get(self.border_bottom, "")
            if border_style:
                rtf.append(f"\\clbrdrb{border_style}\\brdrw{self.border_width}")
        
        # Left and right borders (typically none for subheaders)
        rtf.append(f"\\clbrdrl\\brdrnil\\clbrdrr\\brdrnil")
        
        # Cell vertical alignment
        rtf.append("\\clvertalb")
        
        # Cell position (spans entire width)
        rtf.append(f"\\cellx{total_width_twips}")
        
        # Create TextContent for the subheader content
        rtf_text = TextContent(
            text=self.text,
            format=self.text_format,
            justification=self.text_justification,
            size=int(self.text_font_size),
            font=1,  # Times New Roman
            color=self.text_color,
            background_color=self.text_background_color,
            indent_first=0,
            indent_left=0,
            indent_right=0,
            space_before=15,
            space_after=15
        )
        
        # Add text content
        rtf.append(rtf_text._as_rtf(method="cell"))
        
        # End row
        rtf.append("\\intbl\\row\\pard")
        
        return rtf