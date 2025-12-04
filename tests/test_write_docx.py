import polars as pl
import pytest

from rtflite.convert import LibreOfficeConverter
from rtflite.dictionary.libreoffice import MIN_VERSION
from rtflite.encode import RTFDocument
from rtflite.input import RTFBody, RTFColumnHeader, RTFTitle


def has_libreoffice() -> bool:
    """Check if LibreOffice is available on the system."""
    try:
        LibreOfficeConverter()
        return True
    except (FileNotFoundError, RuntimeError):
        return False


def has_python_docx() -> bool:
    """Check if python-docx is installed."""
    try:
        import docx  # noqa: F401

        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(
    not (has_libreoffice() and has_python_docx()),
    reason=(
        f"LibreOffice (>= {MIN_VERSION}) and python-docx are required for "
        "DOCX export tests"
    ),
)


@pytest.fixture
def sample_document() -> RTFDocument:
    """Create a small RTFDocument for DOCX export tests."""
    df = pl.DataFrame({"A": ["alpha"], "B": ["beta"]})
    return RTFDocument(
        df=df,
        rtf_title=RTFTitle(text="Sample Title"),
        rtf_column_header=RTFColumnHeader(text=["A", "B"]),
        rtf_body=RTFBody(col_rel_width=[1, 1]),
    )


def test_write_docx_creates_docx(sample_document: RTFDocument, tmp_path):
    """DOCX export writes file and preserves table content."""
    output_path = tmp_path / "reports" / "table.docx"
    sample_document.write_docx(output_path)

    assert output_path.exists()

    import docx

    document = docx.Document(output_path)
    extracted_text = " ".join(
        [p.text for p in document.paragraphs]
        + [
            cell.text
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        ]
    )

    assert "Sample Title" in extracted_text
    assert "alpha" in extracted_text
    assert "beta" in extracted_text


def test_write_docx_uses_temp_files(sample_document: RTFDocument, tmp_path):
    """DOCX export should not leave intermediate artifacts in output dir."""
    output_dir = tmp_path / "final"
    output_path = output_dir / "clean.docx"

    sample_document.write_docx(output_path)

    assert output_path.exists()
    assert not any(path.suffix == ".rtf" for path in output_dir.iterdir())
