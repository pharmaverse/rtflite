from pathlib import Path
from unittest.mock import patch

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
def test_write_docx_passes_executable_path(
    mock_converter_cls, sample_document, tmp_path
):
    """Verify that executable_path is correctly passed to LibreOfficeConverter."""
    # Setup mock
    mock_instance = mock_converter_cls.return_value
    mock_instance.convert.return_value = Path("dummy.docx")

    # Create dummy docx file that would be moved
    output_path = tmp_path / "output.docx"

    # We need to mock shutil.move as well since the converter is mocked
    # and won't actually create files
    with patch("shutil.move"):
        sample_document.write_docx(
            output_path, executable_path="/custom/path/to/soffice"
        )

    # Verify LibreOfficeConverter was initialized with the correct path
    mock_converter_cls.assert_called_once_with(
        executable_path="/custom/path/to/soffice"
    )

    # Verify convert was called
    mock_instance.convert.assert_called_once()
