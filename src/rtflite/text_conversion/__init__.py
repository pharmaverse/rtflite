"""
Text conversion module for LaTeX to Unicode conversion.

This module provides functionality to convert LaTeX mathematical symbols
and commands to their Unicode equivalents, matching the behavior of the
r2rtf package.

The main entry point is the `convert_text` function which handles the
text_convert parameter found throughout RTF components.
"""

from .converter import TextConverter
from .symbols import LaTeXSymbolMapper


# Main public interface
def convert_text(text: str | None, enable_conversion: bool = True) -> str | None:
    """
    Convert LaTeX symbols in text to Unicode characters.

    This function provides the main text conversion interface used throughout
    the RTF encoding pipeline. It respects the enable_conversion flag to
    allow selective enabling/disabling of conversion.

    Args:
        text: Input text that may contain LaTeX commands
        enable_conversion: Whether to perform LaTeX to Unicode conversion

    Returns:
        Text with LaTeX commands converted to Unicode (if enabled)

    Examples:
        >>> convert_text("Area: \\pm 0.05", True)
        "Area: +/- 0.05"

        >>> convert_text("\\alpha + \\beta", False)
        "\\alpha + \\beta"
    """
    if not enable_conversion or not text:
        return text

    converter = TextConverter()
    return converter.convert_latex_to_unicode(text)


# For backward compatibility with existing imports
from ..text_convert import text_convert

__all__ = [
    "convert_text",
    "TextConverter",
    "LaTeXSymbolMapper",
    "text_convert",  # backward compatibility
]
