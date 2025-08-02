"""RTF syntax generation module.

This module provides centralized RTF syntax generation capabilities,
separating RTF formatting knowledge from business logic and supporting
multiple content types including tables, text, and future figures/lists.
"""

from .syntax import RTFSyntaxGenerator
from .elements import RTFElement, RTFTable, RTFText
from .formatting import RTFFormatter, BorderFormatter, TextFormatter

__all__ = [
    "RTFSyntaxGenerator",
    "RTFElement",
    "RTFTable", 
    "RTFText",
    "RTFFormatter",
    "BorderFormatter",
    "TextFormatter",
]