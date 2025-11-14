"""RTF encoding engine module.

This module separates document structure from RTF encoding logic,
supports multiple encoding strategies, and prepares for future content types.
"""

from .engine import RTFEncodingEngine
from .strategies import PaginatedStrategy, SinglePageStrategy

__all__ = [
    "RTFEncodingEngine",
    "SinglePageStrategy",
    "PaginatedStrategy",
]
