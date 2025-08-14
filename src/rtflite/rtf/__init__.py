"""RTF syntax generation module.

This module provides centralized RTF syntax generation capabilities,
separating RTF formatting knowledge from business logic and supporting
multiple content types including tables, text, and future figures/lists.
"""

from .syntax import RTFDocumentAssembler, RTFSyntaxGenerator

__all__ = [
    "RTFSyntaxGenerator",
    "RTFDocumentAssembler",
]
