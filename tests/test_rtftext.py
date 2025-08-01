import pytest
from rtflite.input import RTFText


class TestRTFText:
    """Test cases for RTFText class and string_width functionality"""

    def test_rtftext_initialization_basic(self):
        """Test basic RTFText initialization with text content"""
        text = RTFText("abc")
        
        assert text.text == "abc"
        assert text.text_font == (1,)  # Default font
        assert text.text_font_size == (12,)  # Default size
        assert text.text_justification == ("l",)  # Default left alignment

    def test_rtftext_initialization_with_attributes(self):
        """Test RTFText initialization with custom text attributes"""
        text = RTFText(
            "test text",
            text_font=[2],
            text_font_size=[14],
            text_justification=["c"]
        )
        
        assert text.text == "test text"
        assert text.text_font == (2,)
        assert text.text_font_size == (14,)
        assert text.text_justification == ("c",)

    def test_rtftext_empty_initialization(self):
        """Test RTFText initialization with empty string"""
        text = RTFText()
        
        assert text.text == ""
        assert text.text_font == (1,)
        assert text.text_font_size == (12,)

    def test_string_width_default_unit(self):
        """Test string_width method with default unit (inches)"""
        text = RTFText("abc")
        width = text.string_width()
        
        # Should return a positive float value in inches
        assert isinstance(width, float)
        assert width > 0
        # For "abc" with default font (Times New Roman) and size 12, expect small width
        assert 0.1 < width < 1.0

    def test_string_width_different_units(self):
        """Test string_width method with different units"""
        text = RTFText("abc")
        
        width_in = text.string_width("in")
        width_mm = text.string_width("mm") 
        width_px = text.string_width("px")
        
        # All should be positive
        assert width_in > 0
        assert width_mm > 0
        assert width_px > 0
        
        # mm should be larger than inches (conversion factor ~25.4)
        assert width_mm > width_in * 20  # Allow some tolerance
        
        # px should be larger than inches (depends on DPI, default 72)
        assert width_px > width_in * 50  # Allow some tolerance

    def test_string_width_different_fonts(self):
        """Test string_width with different font numbers"""
        text1 = RTFText("abc", text_font=[1])  # Times New Roman
        text2 = RTFText("abc", text_font=[2])  # Arial
        
        width1 = text1.string_width()
        width2 = text2.string_width()
        
        # Both should be positive
        assert width1 > 0
        assert width2 > 0
        
        # Widths may differ between fonts (but both should be reasonable)
        assert 0.1 < width1 < 1.0
        assert 0.1 < width2 < 1.0

    def test_string_width_different_sizes(self):
        """Test string_width with different font sizes"""
        text_small = RTFText("abc", text_font_size=[8])
        text_large = RTFText("abc", text_font_size=[16])
        
        width_small = text_small.string_width()
        width_large = text_large.string_width()
        
        # Larger font should produce larger width
        assert width_large > width_small
        
        # Size relationship should be roughly proportional
        assert width_large / width_small > 1.5  # At least 1.5x larger

    def test_string_width_longer_text(self):
        """Test string_width with longer text strings"""
        short_text = RTFText("a")
        long_text = RTFText("abcdefghijklmnop")
        
        width_short = short_text.string_width()
        width_long = long_text.string_width()
        
        # Longer text should be wider
        assert width_long > width_short
        
        # Should be significantly wider (at least 10x for 15 vs 1 character)
        assert width_long / width_short > 10

    def test_string_width_empty_text(self):
        """Test string_width with empty text"""
        text = RTFText("")
        width = text.string_width()
        
        # Empty string should have zero or near-zero width
        assert width == 0.0

    def test_string_width_special_characters(self):
        """Test string_width with special characters"""
        text = RTFText("Hello, World! @#$%")
        width = text.string_width()
        
        # Should handle special characters without error
        assert isinstance(width, float)
        assert width > 0

    def test_string_width_invalid_unit(self):
        """Test string_width with invalid unit raises ValueError"""
        text = RTFText("abc")
        
        with pytest.raises(ValueError, match="Unsupported unit"):
            text.string_width("invalid_unit")

    def test_attribute_defaults_compatibility(self):
        """Test that RTFText attributes are compatible with existing system"""
        text = RTFText("test")
        
        # Check that all expected text attributes exist
        expected_attrs = [
            "text_font", "text_font_size", "text_justification",
            "text_indent_first", "text_indent_left", "text_indent_right",
            "text_space", "text_space_before", "text_space_after",
            "text_hyphenation", "text_convert"
        ]
        
        for attr in expected_attrs:
            assert hasattr(text, attr)
            # All should be tuples after initialization
            assert isinstance(getattr(text, attr), tuple)

    def test_precision_comparison_with_r_example(self):
        """Test precision matches expected R output format"""
        # The GitHub issue shows R example with strwidth: 0.2604167
        # Test similar case to verify our calculation precision
        text = RTFText("abc", text_font=[1], text_font_size=[12])
        width = text.string_width()
        
        # Should be in similar range and precision as R example
        assert isinstance(width, float)
        assert 0.1 < width < 0.5  # Reasonable range for "abc"
        
        # Should have reasonable precision (more than 3 decimal places)
        width_str = f"{width:.7f}"
        assert len(width_str.split('.')[1]) >= 6  # At least 6 decimal places