"""Shared optional dependency checks for pytest."""

import tempfile
from pathlib import Path

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


def has_pypdf() -> bool:
    """Return True when pypdf is installed."""
    try:
        import pypdf  # noqa: F401
    except ImportError:
        return False
    return True


def has_libreoffice() -> bool:
    """Return True when LibreOffice is available and can convert documents."""
    try:
        converter = LibreOfficeConverter()
    except (FileNotFoundError, RuntimeError):
        return False

    # LibreOffice can report a valid version while still failing in headless
    # conversion mode (for example due to sandboxing).
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            rtf_path = tmp_path / "rtflite_smoke.rtf"
            rtf_path.write_text(
                r"{\rtf1\ansi\deff0\fs24 rtflite}",
                encoding="utf-8",
            )
            converter.convert(
                input_files=rtf_path,
                output_dir=tmp_path,
                format="pdf",
                overwrite=True,
            )
    except Exception:
        return False
    return True


PYTHON_DOCX_INSTALLED = has_python_docx()
PYTHON_DOCX_REASON = "python-docx is required for DOCX assembly tests"
PYPDF_INSTALLED = has_pypdf()
PYPDF_REASON = "pypdf is required for PDF content extraction tests"
LIBREOFFICE_INSTALLED = has_libreoffice()
LIBREOFFICE_REASON = (
    f"LibreOffice (>= {MIN_VERSION}) not found on system or cannot convert files"
)

skip_if_no_python_docx = pytest.mark.skipif(
    not PYTHON_DOCX_INSTALLED,
    reason=PYTHON_DOCX_REASON,
)

skip_if_no_libreoffice = pytest.mark.skipif(
    not LIBREOFFICE_INSTALLED,
    reason=LIBREOFFICE_REASON,
)

skip_if_no_libreoffice_and_python_docx = pytest.mark.skipif(
    not (LIBREOFFICE_INSTALLED and PYTHON_DOCX_INSTALLED),
    reason=(f"LibreOffice (>= {MIN_VERSION}) and python-docx are required"),
)

skip_if_no_libreoffice_and_pypdf = pytest.mark.skipif(
    not (LIBREOFFICE_INSTALLED and PYPDF_INSTALLED),
    reason=(f"LibreOffice (>= {MIN_VERSION}) and pypdf are required"),
)
