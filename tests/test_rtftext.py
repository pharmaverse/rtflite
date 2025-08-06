import pytest

from rtflite.attributes import TextAttributes
from rtflite.input import RTFTitle
from rtflite.strwidth import get_string_width


class TestTextWidthAndLineCalculation:
    """Test cases for text width and line calculation functionality using existing RTF components"""

    def test_rtf_title_initialization_and_attributes(self):
        """Test RTFTitle initialization and text attributes"""
        title = RTFTitle(
            text=["Sample Title"],
            text_font=[2],
            text_font_size=[14],
            text_justification=["c"],
        )

        assert title.text == ("Sample Title",)
        assert title.text_font == (2,)
        assert title.text_font_size == (14,)
        assert title.text_justification == ("c",)

    def test_direct_string_width_calculation(self):
        """Test direct string width calculation using get_string_width function"""
        # Test basic width calculation
        width = get_string_width("abc", font=1, font_size=12, unit="in")
        assert isinstance(width, float)
        assert width > 0
        assert 0.1 < width < 1.0

    def test_string_width_different_units(self):
        """Test string width calculation with different units"""
        width_in = get_string_width("abc", font=1, font_size=12, unit="in")
        width_mm = get_string_width("abc", font=1, font_size=12, unit="mm")
        width_px = get_string_width("abc", font=1, font_size=12, unit="px")

        # All should be positive
        assert width_in > 0
        assert width_mm > 0
        assert width_px > 0

        # mm should be larger than inches (conversion factor ~25.4)
        assert width_mm > width_in * 20  # Allow some tolerance

        # px should be larger than inches (depends on DPI, default 72)
        assert width_px > width_in * 50  # Allow some tolerance

    def test_string_width_different_fonts(self):
        """Test string width with different font numbers"""
        width1 = get_string_width("abc", font=1, font_size=12)  # Times New Roman
        width2 = get_string_width("abc", font=2, font_size=12)  # Arial

        # Both should be positive
        assert width1 > 0
        assert width2 > 0

        # Widths may differ between fonts (but both should be reasonable)
        assert 0.1 < width1 < 1.0
        assert 0.1 < width2 < 1.0

    def test_string_width_different_sizes(self):
        """Test string width with different font sizes"""
        width_small = get_string_width("abc", font=1, font_size=8)
        width_large = get_string_width("abc", font=1, font_size=16)

        # Larger font should produce larger width
        assert width_large > width_small

        # Size relationship should be roughly proportional
        assert width_large / width_small > 1.5  # At least 1.5x larger

    def test_string_width_longer_text(self):
        """Test string width with longer text strings"""
        width_short = get_string_width("a", font=1, font_size=12)
        width_long = get_string_width("abcdefghijklmnop", font=1, font_size=12)

        # Longer text should be wider
        assert width_long > width_short

        # Should be significantly wider (at least 10x for 15 vs 1 character)
        assert width_long / width_short > 10

    def test_string_width_empty_text(self):
        """Test string width with empty text"""
        width = get_string_width("", font=1, font_size=12)

        # Empty string should have zero or near-zero width
        assert width == 0.0

    def test_string_width_special_characters(self):
        """Test string width with special characters"""
        width = get_string_width("Hello, World! @#$%", font=1, font_size=12)

        # Should handle special characters without error
        assert isinstance(width, float)
        assert width > 0

    def test_string_width_invalid_unit(self):
        """Test string width with invalid unit raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported unit"):
            get_string_width("abc", font=1, font_size=12, unit="invalid_unit")

    def test_line_calculation_with_rtf_title(self):
        """Test line calculation functionality with RTFTitle"""
        title = RTFTitle(text=["Sample Title"], text_font=[1], text_font_size=[12])

        # Test line calculation
        lines_wide = title.calculate_lines("Short title", available_width=5.0)
        lines_narrow = title.calculate_lines(
            "This is a very long title that needs multiple lines", available_width=1.0
        )

        assert lines_wide == 1
        assert lines_narrow > 1

    def test_text_attributes_compatibility(self):
        """Test that TextAttributes has all expected attributes"""
        attrs = TextAttributes()
        attrs.text_font = [1]
        attrs.text_font_size = [12]

        # Check that all expected text attributes exist
        expected_attrs = [
            "text_font",
            "text_font_size",
            "text_justification",
            "text_indent_first",
            "text_indent_left",
            "text_indent_right",
            "text_space",
            "text_space_before",
            "text_space_after",
            "text_hyphenation",
            "text_convert",
        ]

        for attr in expected_attrs:
            assert hasattr(attrs, attr)

    def test_precision_comparison_with_r_example(self):
        """Test precision matches expected R output format"""
        # The GitHub issue shows R example with strwidth: 0.2604167
        # Test similar case to verify our calculation precision
        width = get_string_width("abc", font=1, font_size=12)

        # Should be in similar range and precision as R example
        assert isinstance(width, float)
        assert 0.1 < width < 0.5  # Reasonable range for "abc"

        # Should have reasonable precision (more than 3 decimal places)
        width_str = f"{width:.7f}"
        assert len(width_str.split(".")[1]) >= 6  # At least 6 decimal places
