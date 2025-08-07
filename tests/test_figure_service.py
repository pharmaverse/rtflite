"""Tests for RTF figure/image handling functionality.

This module tests the critical figure handling features that were previously untested,
including image encoding, multi-page figures, and error handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rtflite.figure import rtf_read_figure
from rtflite.input import RTFFigure
from rtflite.services.figure_service import RTFFigureService


class TestRTFFigureService:
    """Test the RTFFigureService class for image encoding."""

    def test_encode_figure_none_input(self):
        """Test that None figure input returns empty string."""
        result = RTFFigureService.encode_figure(None)
        assert result == ""

    def test_encode_figure_no_figures(self):
        """Test that RTFFigure with no figures returns empty string."""
        rtf_figure = RTFFigure(figures=None)
        result = RTFFigureService.encode_figure(rtf_figure)
        assert result == ""

    @patch("rtflite.services.figure_service.rtf_read_figure")
    @patch("pathlib.Path.exists")
    def test_encode_single_png_figure(self, mock_exists, mock_read_figure):
        """Test encoding a single PNG image to RTF."""
        # Mock file existence check
        mock_exists.return_value = True
        # Mock the figure reading to return test data
        mock_read_figure.return_value = ([b"fake_png_data"], ["png"])

        rtf_figure = RTFFigure(
            figures=["test.png"], fig_width=5.0, fig_height=3.0, fig_align="center"
        )

        result = RTFFigureService.encode_figure(rtf_figure)

        # Verify the result contains RTF image commands
        assert isinstance(result, str)
        assert len(result) > 0
        assert "\\par " in result  # Paragraph marker
        mock_read_figure.assert_called_once_with(["test.png"])

    @patch("rtflite.services.figure_service.rtf_read_figure")
    @patch("pathlib.Path.exists")
    def test_encode_multiple_figures_with_pagination(
        self, mock_exists, mock_read_figure
    ):
        """Test encoding multiple figures creates page breaks between them."""
        # Mock file existence check
        mock_exists.return_value = True
        # Mock reading multiple figures
        mock_read_figure.return_value = (
            [b"png_data_1", b"png_data_2", b"png_data_3"],
            ["png", "jpeg", "png"],
        )

        rtf_figure = RTFFigure(
            figures=["fig1.png", "fig2.jpg", "fig3.png"],
            fig_width=[4.0, 5.0, 6.0],
            fig_height=[3.0, 4.0, 5.0],
            fig_align="left",
        )

        result = RTFFigureService.encode_figure(rtf_figure)

        # Verify page breaks between figures
        assert "\\page " in result
        # Should have 2 page breaks for 3 figures
        assert result.count("\\page ") == 2
        assert "\\par " in result

    @patch("rtflite.services.figure_service.rtf_read_figure")
    @patch("pathlib.Path.exists")
    def test_encode_figure_dimension_broadcasting(self, mock_exists, mock_read_figure):
        """Test that single dimension values are broadcast to all figures."""
        # Mock file existence check
        mock_exists.return_value = True
        mock_read_figure.return_value = ([b"data1", b"data2"], ["png", "png"])

        # Single width/height should apply to all figures
        rtf_figure = RTFFigure(
            figures=["fig1.png", "fig2.png"],
            fig_width=5.0,  # Single value
            fig_height=3.0,  # Single value
            fig_align="center",
        )

        result = RTFFigureService.encode_figure(rtf_figure)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("rtflite.services.figure_service.rtf_read_figure")
    @patch("pathlib.Path.exists")
    def test_encode_figure_dimension_list_handling(self, mock_exists, mock_read_figure):
        """Test dimension list handling with fallback to last value."""
        # Mock file existence check
        mock_exists.return_value = True
        mock_read_figure.return_value = (
            [b"data1", b"data2", b"data3"],
            ["png", "png", "png"],
        )

        # Fewer dimensions than figures - should use last value
        rtf_figure = RTFFigure(
            figures=["fig1.png", "fig2.png", "fig3.png"],
            fig_width=[4.0, 5.0],  # Only 2 values for 3 figures
            fig_height=[3.0],  # Only 1 value for 3 figures
            fig_align="right",
        )

        result = RTFFigureService.encode_figure(rtf_figure)
        assert isinstance(result, str)
        # Should complete without error, using last values for missing dimensions


class TestRTFReadFigure:
    """Test the rtf_read_figure function for reading image files."""

    def test_read_single_png_file(self):
        """Test reading a single PNG file."""
        # Create a temporary PNG file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")  # PNG header
            tmp_path = tmp.name

        try:
            data_list, formats = rtf_read_figure(tmp_path)

            assert len(data_list) == 1
            assert len(formats) == 1
            assert formats[0] == "png"
            assert b"PNG" in data_list[0]
        finally:
            Path(tmp_path).unlink()

    def test_read_single_jpeg_file(self):
        """Test reading a single JPEG file."""
        # Create a temporary JPEG file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(b"\xff\xd8\xff")  # JPEG header
            tmp_path = tmp.name

        try:
            data_list, formats = rtf_read_figure(tmp_path)

            assert len(data_list) == 1
            assert len(formats) == 1
            assert formats[0] == "jpeg"
        finally:
            Path(tmp_path).unlink()

    def test_read_multiple_image_files(self):
        """Test reading multiple image files of different formats."""
        temp_files = []

        try:
            # Create temporary files
            for suffix, header in [(".png", b"\x89PNG"), (".jpg", b"\xff\xd8")]:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(header)
                    temp_files.append(tmp.name)

            data_list, formats = rtf_read_figure(temp_files)

            assert len(data_list) == 2
            assert len(formats) == 2
            assert formats[0] == "png"
            assert formats[1] == "jpeg"
        finally:
            for tmp_path in temp_files:
                Path(tmp_path).unlink()

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Image file not found"):
            rtf_read_figure("nonexistent_file.png")

    def test_read_unsupported_format_raises_error(self):
        """Test that unsupported image formats raise ValueError."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
            tmp.write(b"BM")  # BMP header
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="Unsupported image format"):
                rtf_read_figure(tmp_path)
        finally:
            Path(tmp_path).unlink()

    def test_path_object_support(self):
        """Test that Path objects are supported as input."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")
            tmp_path = Path(tmp.name)

        try:
            data_list, formats = rtf_read_figure(tmp_path)

            assert len(data_list) == 1
            assert formats[0] == "png"
        finally:
            tmp_path.unlink()

    def test_mixed_path_types(self):
        """Test mixing string and Path objects in file list."""
        temp_files = []

        try:
            # Create files with different path types
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(b"\x89PNG")
                temp_files.append(tmp.name)  # String path

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp.write(b"\xff\xd8")
                temp_files.append(Path(tmp.name))  # Path object

            data_list, formats = rtf_read_figure(temp_files)

            assert len(data_list) == 2
            assert len(formats) == 2
            assert formats[0] == "png"
            assert formats[1] == "jpeg"
        finally:
            for tmp_path in temp_files:
                if isinstance(tmp_path, Path):
                    tmp_path.unlink()
                else:
                    Path(tmp_path).unlink()


class TestRTFFigureIntegration:
    """Integration tests for figure handling in complete documents."""

    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    def test_figure_in_rtf_document(self, mock_exists, mock_open):
        """Test that figures can be integrated into RTF documents."""
        from io import BytesIO

        from rtflite.encode import RTFDocument

        # Mock file operations
        mock_exists.return_value = True
        # Mock the file reading with context manager
        mock_file = BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        # Create document with figure only (no df, as they can't be combined)
        rtf_figure = RTFFigure(
            figures=["test_image.png"], fig_width=4.0, fig_height=3.0
        )

        doc = RTFDocument(rtf_figure=rtf_figure)

        # Should not raise an error
        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0

    @patch("pathlib.Path.exists")
    def test_figure_error_handling_in_document(self, mock_exists):
        """Test graceful error handling for invalid figure paths."""
        from rtflite.encode import RTFDocument

        # Mock that file doesn't exist for validation
        mock_exists.return_value = False

        # Should raise error when creating RTFFigure with non-existent file
        with pytest.raises(FileNotFoundError, match="Figure file not found"):
            rtf_figure = RTFFigure(
                figures=["nonexistent_image.png"], fig_width=4.0, fig_height=3.0
            )
