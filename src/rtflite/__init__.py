"""rtflite: A Python library for creating RTF documents."""

from .assemble import assemble_docx, assemble_rtf, concatenate_docx
from .attributes import TableAttributes
from .convert import LibreOfficeConverter
from .core.config import RTFConfiguration
from .core.constants import RTFConstants
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

__version__ = "0.0.1"

__all__ = [
    "RTFDocument",
    "RTFEncodingEngine",
    "RTFConfiguration",
    "RTFConstants",
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
    "assemble_rtf",
    "assemble_docx",
    "concatenate_docx",
]
