"""
Pagination system for rtflite.

This package provides advanced pagination capabilities inspired by r2rtf's approach,
including page_index-like functionality through the PageDict and PageIndexManager classes.
"""

# Import existing core pagination classes for backward compatibility
from .core import (
    RTFPagination,
    PageBreakCalculator,
    ContentDistributor,
)

# Import new advanced pagination classes
from .page_dict import (
    PageBreakType,
    PageConfig, 
    PageBreakRule,
    PageDict,
    PageIndexManager,
)

__all__ = [
    # Core pagination (existing)
    "RTFPagination",
    "PageBreakCalculator", 
    "ContentDistributor",
    # Advanced pagination (new)
    "PageBreakType",
    "PageConfig",
    "PageBreakRule", 
    "PageDict",
    "PageIndexManager",
]