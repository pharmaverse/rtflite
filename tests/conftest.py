"""Shared optional dependency checks for pytest."""

import pytest

from rtflite.convert import LibreOfficeConverter
from rtflite.dictionary.libreoffice import MIN_VERSION


def has_python_docx() -> bool:
    """Return True when python-docx is installed."""
    try:
        import docx  # noqa: F401
    except ImportError:
        return False
    return True


def has_libreoffice() -> bool:
    """Return True when LibreOffice is available on the system."""
    try:
        LibreOfficeConverter()
        return True
    except (FileNotFoundError, RuntimeError):
        return False


PYTHON_DOCX_INSTALLED = has_python_docx()
PYTHON_DOCX_REASON = "python-docx is required for DOCX assembly tests"
LIBREOFFICE_REASON = f"LibreOffice (>= {MIN_VERSION}) not found on system"

skip_if_no_python_docx = pytest.mark.skipif(
    not PYTHON_DOCX_INSTALLED,
    reason=PYTHON_DOCX_REASON,
)

skip_if_no_libreoffice = pytest.mark.skipif(
    not has_libreoffice(),
    reason=LIBREOFFICE_REASON,
)

skip_if_no_libreoffice_and_python_docx = pytest.mark.skipif(
    not (has_libreoffice() and PYTHON_DOCX_INSTALLED),
    reason=(f"LibreOffice (>= {MIN_VERSION}) and python-docx are required"),
)
