from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from rtflite.encode import RTFDocument
from rtflite.input import RTFBody, RTFTitle


@pytest.fixture
def sample_document() -> RTFDocument:
    """Create a small RTFDocument for DOCX export tests."""
    df = pl.DataFrame({"A": ["alpha"]})
    return RTFDocument(
        df=df,
        rtf_title=RTFTitle(text="Sample Title"),
        rtf_body=RTFBody(col_rel_width=[1]),
    )


@patch("rtflite.encode.LibreOfficeConverter")
def test_write_docx_uses_provided_converter(
    mock_converter_cls, sample_document, tmp_path
):
    """Verify that `write_docx` uses a provided converter instance."""
    converter = MagicMock()
    converter.convert.return_value = Path("dummy.docx")

    output_path = tmp_path / "output.docx"

    with patch("rtflite.encode.shutil.move"):
        sample_document.write_docx(output_path, converter=converter)

    mock_converter_cls.assert_not_called()
    converter.convert.assert_called_once()


@patch("rtflite.encode.LibreOfficeConverter")
def test_write_docx_creates_default_converter(
    mock_converter_cls, sample_document, tmp_path
):
    """Verify that `write_docx` creates a default converter when omitted."""
    mock_instance = mock_converter_cls.return_value
    mock_instance.convert.return_value = Path("dummy.docx")

    output_path = tmp_path / "output.docx"

    with patch("rtflite.encode.shutil.move"):
        sample_document.write_docx(output_path)

    mock_converter_cls.assert_called_once_with()
    mock_instance.convert.assert_called_once()
