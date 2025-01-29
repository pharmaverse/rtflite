import os
from pathlib import Path

import pytest

from rtflite.convert import LibreOfficeConverter
from rtflite.dictionary.libreoffice import MIN_VERSION


@pytest.fixture
def sample_rtf(tmp_path) -> Path:
    """Create a simple RTF file for testing."""
    rtf_content = r"""{\rtf1\ansi
{\fonttbl\f0\fswiss Helvetica;}
\f0\pard
This is a test RTF document.\par
}"""
    rtf_file = tmp_path / "test.rtf"
    rtf_file.write_text(rtf_content)
    return rtf_file


@pytest.fixture
def multiple_rtf_files(tmp_path) -> list[Path]:
    """Create multiple RTF files for testing."""
    files = []
    for i in range(3):
        rtf_content = (
            r"""{\rtf1\ansi
{\fonttbl\f0\fswiss Helvetica;}
\f0\pard
This is test RTF document """
            + f"{i + 1}"
            + r".\par}"
        )
        rtf_file = tmp_path / f"test{i + 1}.rtf"
        rtf_file.write_text(rtf_content)
        files.append(rtf_file)
    return files


@pytest.fixture
def output_dir(tmp_path) -> Path:
    """Create output directory for converted files."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    return out_dir


def has_libreoffice():
    """Check if LibreOffice is available on the system."""
    try:
        converter = LibreOfficeConverter()
        return True
    except (FileNotFoundError, RuntimeError):
        return False


# Mark all tests in this module to be skipped if LibreOffice isn't available
pytestmark = pytest.mark.skipif(
    not has_libreoffice(), reason=f"LibreOffice (>= {MIN_VERSION}) not found on system"
)


class TestLibreOfficeConverter:
    def test_init_default(self):
        """Test converter initialization with default executable path."""
        converter = LibreOfficeConverter()
        assert converter.executable_path is not None
        assert os.path.isfile(converter.executable_path)

    def test_init_custom_valid_path(self, tmp_path):
        """Test converter initialization with invalid executable path."""
        with pytest.raises(FileNotFoundError):
            LibreOfficeConverter(executable_path=str(tmp_path / "nonexistent"))

    def test_convert_to_pdf(self, sample_rtf, output_dir):
        """Test converting RTF to PDF."""
        converter = LibreOfficeConverter()
        output_file = converter.convert(
            input_files=sample_rtf, output_dir=output_dir, format="pdf"
        )
        assert output_file.exists()
        assert output_file.suffix == ".pdf"

    def test_convert_multiple_to_pdf(self, multiple_rtf_files, output_dir):
        """Test converting multiple RTF files to PDF."""
        converter = LibreOfficeConverter()
        output_files = converter.convert(
            input_files=multiple_rtf_files, output_dir=output_dir, format="pdf"
        )
        assert isinstance(output_files, list)
        assert len(output_files) == len(multiple_rtf_files)
        for output_file in output_files:
            assert output_file.exists()
            assert output_file.suffix == ".pdf"

    def test_convert_to_docx(self, sample_rtf, output_dir):
        """Test converting RTF to DOCX."""
        converter = LibreOfficeConverter()
        output_file = converter.convert(
            input_files=sample_rtf, output_dir=output_dir, format="docx"
        )
        assert output_file.exists()
        assert output_file.suffix == ".docx"

    def test_convert_multiple_to_docx(self, multiple_rtf_files, output_dir):
        """Test converting multiple RTF files to DOCX."""
        converter = LibreOfficeConverter()
        output_files = converter.convert(
            input_files=multiple_rtf_files, output_dir=output_dir, format="docx"
        )
        assert isinstance(output_files, list)
        assert len(output_files) == len(multiple_rtf_files)
        for output_file in output_files:
            assert output_file.exists()
            assert output_file.suffix == ".docx"

    def test_convert_to_html(self, sample_rtf, output_dir):
        """Test converting RTF to HTML."""
        converter = LibreOfficeConverter()
        output_file = converter.convert(
            input_files=sample_rtf, output_dir=output_dir, format="html"
        )
        assert output_file.exists()
        assert output_file.suffix == ".html"

    def test_convert_multiple_to_html(self, multiple_rtf_files, output_dir):
        """Test converting multiple RTF files to HTML."""
        converter = LibreOfficeConverter()
        output_files = converter.convert(
            input_files=multiple_rtf_files, output_dir=output_dir, format="html"
        )
        assert isinstance(output_files, list)
        assert len(output_files) == len(multiple_rtf_files)
        for output_file in output_files:
            assert output_file.exists()
            assert output_file.suffix == ".html"

    def test_convert_nonexistent_input(self, output_dir):
        """Test conversion with nonexistent input file."""
        converter = LibreOfficeConverter()
        with pytest.raises(FileNotFoundError):
            converter.convert(input_files="nonexistent.rtf", output_dir=output_dir)

    def test_convert_overwrite(self, sample_rtf, output_dir):
        """Test overwrite behavior when converting files."""
        converter = LibreOfficeConverter()

        # First conversion
        output_file = converter.convert(
            input_files=sample_rtf, output_dir=output_dir, format="pdf"
        )
        assert output_file.exists()

        # Second conversion without overwrite should fail
        with pytest.raises(FileExistsError):
            converter.convert(
                input_files=sample_rtf,
                output_dir=output_dir,
                format="pdf",
                overwrite=False,
            )

        # Second conversion with overwrite should succeed
        output_file = converter.convert(
            input_files=sample_rtf, output_dir=output_dir, format="pdf", overwrite=True
        )
        assert output_file.exists()

    def test_convert_multiple_overwrite(self, multiple_rtf_files, output_dir):
        """Test overwrite behavior when converting multiple files."""
        converter = LibreOfficeConverter()

        # First conversion
        output_files = converter.convert(
            input_files=multiple_rtf_files, output_dir=output_dir, format="pdf"
        )
        for output_file in output_files:
            assert output_file.exists()

        # Second conversion without overwrite should fail
        with pytest.raises(FileExistsError):
            converter.convert(
                input_files=multiple_rtf_files,
                output_dir=output_dir,
                format="pdf",
                overwrite=False,
            )

        # Second conversion with overwrite should succeed
        output_files = converter.convert(
            input_files=multiple_rtf_files,
            output_dir=output_dir,
            format="pdf",
            overwrite=True,
        )
        for output_file in output_files:
            assert output_file.exists()

    def test_convert_creates_output_dir(self, sample_rtf, tmp_path):
        """Test that conversion creates output directory if it doesn't exist."""
        output_dir = tmp_path / "nonexistent"
        converter = LibreOfficeConverter()

        assert not output_dir.exists()
        output_file = converter.convert(input_files=sample_rtf, output_dir=output_dir)
        assert output_dir.exists()
        assert output_file.exists()
