"""RTF component factory module.

This module provides factory classes for creating RTF components with
consistent defaults and validation, supporting both current and future
content types like tables, figures, and lists.
"""

from .component_factory import RTFComponentFactory, ComponentType
from .builders import TableBuilder, TextBuilder, PageBuilder

__all__ = [
    "RTFComponentFactory",
    "ComponentType",
    "TableBuilder",
    "TextBuilder", 
    "PageBuilder",
]