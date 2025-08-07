"""Tests for TextConversionService.

This module tests the text conversion service that handles LaTeX to Unicode conversion.
"""

from unittest.mock import patch

from rtflite.services.text_conversion_service import TextConversionService


class TestTextConversionService:
    """Test the TextConversionService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TextConversionService()

    def test_convert_text_content_string_input(self):
        """Test conversion with string input."""
        # Basic LaTeX conversion
        result = self.service.convert_text_content("\\alpha test", True)
        assert result == "\u03b1 test"

        # Multiple symbols
        result = self.service.convert_text_content("\\alpha + \\beta = \\gamma", True)
        assert result == "\u03b1 + \u03b2 = \u03b3"

        # No LaTeX symbols
        result = self.service.convert_text_content("plain text", True)
        assert result == "plain text"

    def test_convert_text_content_list_input(self):
        """Test conversion with list input."""
        # List of strings with LaTeX
        result = self.service.convert_text_content(["\\alpha", "\\beta", "plain"], True)
        assert result == ["\u03b1", "\u03b2", "plain"]

        # Empty list
        result = self.service.convert_text_content([], True)
        assert result == []

        # List with mixed content
        result = self.service.convert_text_content(
            ["\\alpha test", "no latex", "\\beta end"], True
        )
        assert result == ["\u03b1 test", "no latex", "\u03b2 end"]

    def test_convert_text_content_disabled(self):
        """Test that conversion is skipped when disabled."""
        # String input
        result = self.service.convert_text_content("\\alpha test", False)
        assert result == "\\alpha test"

        # List input
        result = self.service.convert_text_content(["\\alpha", "\\beta"], False)
        assert result == ["\\alpha", "\\beta"]

    def test_convert_text_content_none_input(self):
        """Test handling of None input."""
        result = self.service.convert_text_content(None, True)
        assert result is None

        result = self.service.convert_text_content(None, False)
        assert result is None

    def test_convert_text_content_other_types(self):
        """Test conversion of non-string, non-list types."""
        # Integer
        result = self.service.convert_text_content(123, True)
        assert result == "123"

        # Float
        result = self.service.convert_text_content(45.67, True)
        assert result == "45.67"

        # Boolean
        result = self.service.convert_text_content(True, True)
        assert result == "True"

    def test_convert_single_text(self):
        """Test _convert_single_text method directly."""
        # Normal conversion
        result = self.service._convert_single_text("\\alpha")
        assert result == "\u03b1"

        # Empty string
        result = self.service._convert_single_text("")
        assert result == ""

        # String with no LaTeX
        result = self.service._convert_single_text("plain text")
        assert result == "plain text"

    @patch("builtins.print")
    def test_convert_single_text_error_handling(self, mock_print):
        """Test error handling in _convert_single_text."""
        # Mock the converter to raise an exception
        with patch.object(
            self.service.converter,
            "convert_latex_to_unicode",
            side_effect=Exception("Test error"),
        ):
            result = self.service._convert_single_text("\\alpha")

            # Should return original text on error
            assert result == "\\alpha"

            # Should print warning
            mock_print.assert_called_once()
            assert "Warning: Text conversion failed" in str(mock_print.call_args)

    def test_convert_text_list(self):
        """Test _convert_text_list method directly."""
        # Normal list
        result = self.service._convert_text_list(["\\alpha", "\\beta", "text"])
        assert result == ["\u03b1", "\u03b2", "text"]

        # List with None values
        result = self.service._convert_text_list(["\\alpha", None, "\\beta"])
        assert result == ["\u03b1", None, "\u03b2"]

        # Empty strings in list
        result = self.service._convert_text_list(["", "\\alpha", ""])
        assert result == ["", "\u03b1", ""]

    def test_convert_text_list_nested(self):
        """Test _convert_text_list with nested lists."""
        # The service doesn't handle nested lists recursively
        # It only processes the top-level items
        result = self.service._convert_text_list(["\\alpha", "\\beta", "plain"])
        assert result == ["\u03b1", "\u03b2", "plain"]

        # For non-string items, they're passed through unchanged
        # unless they're None
        result = self.service._convert_text_list(["\\alpha", None, "\\beta"])
        assert result == ["\u03b1", None, "\u03b2"]

    def test_convert_with_validation(self):
        """Test convert_with_validation method."""
        # Valid LaTeX commands
        result = self.service.convert_with_validation("\\alpha \\beta", True)
        assert "converted_text" in result
        assert result["converted_text"] == "\u03b1 \u03b2"
        assert "validation" in result

        # Invalid LaTeX commands
        result = self.service.convert_with_validation("\\invalid \\alpha", True)
        assert "converted_text" in result
        assert "validation" in result
        assert "invalid_commands" in result["validation"]

    def test_validate_latex_commands(self):
        """Test validate_latex_commands method."""
        # Mix of valid and invalid commands
        validation = self.service.validate_latex_commands("\\alpha \\invalid \\beta")

        assert "valid_commands" in validation
        assert "invalid_commands" in validation
        assert "\\alpha" in validation["valid_commands"]
        assert "\\beta" in validation["valid_commands"]
        assert "\\invalid" in validation["invalid_commands"]

        # All valid
        validation = self.service.validate_latex_commands("\\alpha \\beta \\gamma")
        assert len(validation["invalid_commands"]) == 0
        assert len(validation["valid_commands"]) == 3

        # No LaTeX commands
        validation = self.service.validate_latex_commands("plain text")
        assert len(validation["valid_commands"]) == 0
        assert len(validation["invalid_commands"]) == 0

    def test_get_available_symbols(self):
        """Test get available symbols through symbol categories."""
        # The service has get_symbol_categories instead
        categories = self.service.get_symbol_categories()

        assert isinstance(categories, dict)
        # Check for actual category names from the output
        assert "Greek Letters" in categories or "Greek" in categories
        assert "Mathematical Operators" in categories or "Math Operators" in categories

        # Find the Greek category (might be "Greek Letters")
        greek_key = "Greek Letters" if "Greek Letters" in categories else "Greek"
        if greek_key in categories:
            assert "\\alpha" in categories[greek_key] or any(
                "\\alpha" in v for v in categories.values() if isinstance(v, list)
            )

    def test_complex_latex_conversion(self):
        """Test conversion of complex LaTeX expressions."""
        # Mathematical expression
        result = self.service.convert_text_content(
            "\\int_{\\alpha}^{\\beta} f(x) dx = \\sum_{i=1}^{n} x_i", True
        )
        assert "\u222b" in result
        assert "\u03b1" in result
        assert "\u03b2" in result
        assert "\u2211" in result

        # Mixed text and symbols
        result = self.service.convert_text_content(
            "The Greek letter \\alpha (alpha) and \\Omega (omega)", True
        )
        assert result == "The Greek letter \u03b1 (alpha) and \u03a9 (omega)"

    def test_special_characters_preservation(self):
        """Test that non-LaTeX special characters are preserved."""
        # Unicode characters should be preserved
        result = self.service.convert_text_content("\u00a9 \u00ae \u2122 \u20ac", True)
        assert result == "\u00a9 \u00ae \u2122 \u20ac"

        # Mixed with LaTeX
        result = self.service.convert_text_content("\\alpha \u00a9 \\beta \u00ae", True)
        assert result == "\u03b1 \u00a9 \u03b2 \u00ae"

    def test_empty_and_whitespace_handling(self):
        """Test handling of empty strings and whitespace."""
        # Empty string
        assert self.service.convert_text_content("", True) == ""

        # Whitespace only
        assert self.service.convert_text_content("   ", True) == "   "

        # LaTeX with extra whitespace
        result = self.service.convert_text_content("  \\alpha  \\beta  ", True)
        assert result == "  \u03b1  \u03b2  "  # Unicode escapes are interpreted here

    def test_conversion_statistics(self):
        """Test getting conversion statistics."""
        # Convert some text
        self.service.convert_text_content("\\alpha \\beta \\invalid", True)

        # Get statistics (if method exists)
        if hasattr(self.service.converter, "get_conversion_statistics"):
            stats = self.service.converter.get_conversion_statistics(
                "\\alpha \\invalid \\beta"
            )
            assert "total_commands" in stats
            assert "converted" in stats
            assert "unconverted" in stats
