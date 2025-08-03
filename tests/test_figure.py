"""Tests for RTF figure functionality."""

import pytest
from pathlib import Path
import polars as pl

from rtflite import RTFDocument
from rtflite.input import RTFFigure, RTFTitle, RTFFootnote
from rtflite.figure import rtf_read_figure


class TestRTFFigure:
    """Test RTFFigure component."""
    
    def test_rtf_figure_creation(self):
        """Test creating RTFFigure with basic settings."""
        figure = RTFFigure(
            figures=[b"dummy_image_data"],
            figure_formats=["png"],
            fig_height=3.5,
            fig_width=5.0,
            fig_align="center",
            fig_pos="after"
        )
        
        assert figure.figures[0] == b"dummy_image_data"
        assert figure.figure_formats[0] == "png"
        assert figure.fig_height == [3.5]
        assert figure.fig_width == [5.0]
        assert figure.fig_align == "center"
        assert figure.fig_pos == "after"
    
    def test_rtf_figure_multiple_images(self):
        """Test RTFFigure with multiple images and dimensions."""
        figure = RTFFigure(
            figures=[b"image1", b"image2", b"image3"],
            figure_formats=["png", "jpeg", "png"],
            fig_height=[3.0, 4.0, 5.0],
            fig_width=[4.0, 5.0, 6.0]
        )
        
        assert len(figure.figures) == 3
        assert len(figure.figure_formats) == 3
        assert len(figure.fig_height) == 3
        assert len(figure.fig_width) == 3
    
    def test_rtf_figure_validation(self):
        """Test RTFFigure validation."""
        # Test mismatched figures and formats
        with pytest.raises(ValueError, match="Number of figures must match"):
            RTFFigure(
                figures=[b"image1", b"image2"],
                figure_formats=["png"]
            )
        
        # Test invalid alignment
        with pytest.raises(ValueError, match="Invalid fig_align"):
            RTFFigure(fig_align="invalid")
        
        # Test invalid position
        with pytest.raises(ValueError, match="Invalid fig_pos"):
            RTFFigure(fig_pos="invalid")


class TestRTFFigureReading:
    """Test figure reading functionality."""
    
    def test_rtf_read_figure_not_found(self):
        """Test reading non-existent file."""
        with pytest.raises(FileNotFoundError):
            rtf_read_figure("non_existent_file.png")
    
    def test_rtf_read_figure_unsupported_format(self, tmp_path):
        """Test reading unsupported format."""
        # Create a dummy file with unsupported extension
        test_file = tmp_path / "test.bmp"
        test_file.write_bytes(b"dummy data")
        
        with pytest.raises(ValueError, match="Unsupported image format"):
            rtf_read_figure(test_file)


class TestRTFDocumentWithFigure:
    """Test RTFDocument with figure integration."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return pl.DataFrame({
            "Treatment": ["Placebo", "Drug A"],
            "N": [100, 101],
            "Mean": [5.2, 6.1]
        })
    
    def test_rtf_document_with_figure_after(self, sample_data):
        """Test RTF document with figure after table."""
        # Create dummy image data
        dummy_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        
        doc = RTFDocument(
            df=sample_data,
            rtf_title=RTFTitle(text="Study Results"),
            rtf_figure=RTFFigure(
                figures=[dummy_image],
                figure_formats=["png"],
                fig_height=4.0,
                fig_width=6.0,
                fig_align="center",
                fig_pos="after"
            ),
            rtf_footnote=RTFFootnote(text="Data as of 2024")
        )
        
        # Generate RTF
        rtf_output = doc.rtf_encode()
        
        # Check that RTF contains figure elements
        assert "\\pict" in rtf_output
        assert "\\pngblip" in rtf_output
        assert "\\picwgoal" in rtf_output
        assert "\\pichgoal" in rtf_output
        
        # Check ordering - figure should be after footnote
        pict_pos = rtf_output.find("\\pict")
        footnote_pos = rtf_output.find("Data as of 2024")
        assert pict_pos > footnote_pos
    
    def test_rtf_document_with_figure_before(self, sample_data):
        """Test RTF document with figure before table."""
        dummy_image = b"\x89PNG\r\n\x1a\n"
        
        doc = RTFDocument(
            df=sample_data,
            rtf_title=RTFTitle(text="Study Results"),
            rtf_figure=RTFFigure(
                figures=[dummy_image],
                figure_formats=["png"],
                fig_pos="before"
            )
        )
        
        rtf_output = doc.rtf_encode()
        
        # Check that figure appears before table content
        pict_pos = rtf_output.find("\\pict")
        table_pos = rtf_output.find("Treatment")
        assert pict_pos < table_pos
    
    def test_rtf_document_multiple_figures(self, sample_data):
        """Test RTF document with multiple figures."""
        dummy_images = [
            b"\x89PNG\r\n\x1a\n",
            b"\xFF\xD8\xFF\xE0",  # JPEG header
            b"\x89PNG\r\n\x1a\n"
        ]
        
        doc = RTFDocument(
            df=sample_data,
            rtf_figure=RTFFigure(
                figures=dummy_images,
                figure_formats=["png", "jpeg", "png"],
                fig_height=[3.0, 4.0, 5.0],
                fig_width=[4.0, 5.0, 6.0],
                fig_align="center"
            )
        )
        
        rtf_output = doc.rtf_encode()
        
        # Check for multiple picture groups
        assert rtf_output.count("\\pict") == 3
        assert rtf_output.count("\\pngblip") == 2
        assert rtf_output.count("\\jpegblip") == 1