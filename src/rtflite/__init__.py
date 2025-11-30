"""rtflite: A Python library for creating RTF documents."""

from .attributes import TableAttributes
from .encode import RTFDocument
from .encoding import RTFEncodingEngine
from .input import (
    RTFBody,
    RTFColumnHeader,
    RTFFigure,
    RTFFootnote,
    RTFPage,
    RTFPageFooter,
    RTFPageHeader,
    RTFSource,
    RTFSubline,
    RTFTitle,
)
from .pagination import PageBreakCalculator, RTFPagination
from .strwidth import get_string_width
from .convert import LibreOfficeConverter

__version__ = "0.0.1"

__all__ = [
    "RTFDocument",
    "RTFEncodingEngine",
    "RTFBody",
    "RTFPage",
    "RTFTitle",
    "RTFColumnHeader",
    "RTFFootnote",
    "RTFSource",
    "RTFFigure",
    "RTFPageHeader",
    "RTFPageFooter",
    "RTFSubline",
    "TableAttributes",
    "RTFPagination",
    "PageBreakCalculator",
    "get_string_width",
    "LibreOfficeConverter",
]
