"""Shared optional dependency checks for tests."""

import pytest


def has_python_docx() -> bool:
    """Return True when python-docx is installed."""
    try:
        import docx  # noqa: F401
    except ImportError:
        return False
    return True


PYTHON_DOCX_INSTALLED = has_python_docx()
PYTHON_DOCX_REASON = "python-docx is required for DOCX assembly tests"
skip_if_no_python_docx = pytest.mark.skipif(
    not PYTHON_DOCX_INSTALLED,
    reason=PYTHON_DOCX_REASON,
)
