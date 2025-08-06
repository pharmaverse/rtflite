"""RTF encoding engine module.

This module provides a clean separation between document structure and RTF encoding logic,
supporting multiple encoding strategies and preparing for future content types.
"""

from .engine import RTFEncodingEngine
from .strategies import PaginatedStrategy, SinglePageStrategy

__all__ = [
    "RTFEncodingEngine",
    "SinglePageStrategy",
    "PaginatedStrategy",
]
