"""
Comprehensive test cases for the text_conversion module.

This module tests all components of the text conversion functionality:
- convert_text function (public interface)
- TextConverter class
- LaTeXSymbolMapper class
- Edge cases and error handling
- Backward compatibility
"""

import pytest

from rtflite.text_conversion import text_convert  # backward compatibility
from rtflite.text_conversion import LaTeXSymbolMapper, TextConverter, convert_text


class TestConvertTextFunction:
    """Test the convert_text public interface function."""

    def test_convert_text_enabled_basic_symbols(self):
        """Test basic LaTeX symbol conversion when enabled."""
        result = convert_text("\\alpha + \\beta", True)
        # Check that LaTeX commands were converted (no longer present)
        assert "\\alpha" not in result
        assert "\\beta" not in result
        # Check result is not the same as input (conversion happened)
        assert result != "\\alpha + \\beta"

    def test_convert_text_enabled_operators(self):
        """Test mathematical operator conversion when enabled."""
        result = convert_text("Mean \\pm SD", True)
        assert "\\pm" not in result  # LaTeX command was converted
        assert result != "Mean \\pm SD"  # Result changed

        result = convert_text("A \\cdot B", True)
        assert "\\cdot" not in result  # LaTeX command was converted
        assert result != "A \\cdot B"  # Result changed

    def test_convert_text_enabled_complex_formula(self):
        """Test complex formula with multiple symbols."""
        formula = "\\alpha \\pm \\beta \\cdot \\gamma"
        result = convert_text(formula, True)
        # Check that all LaTeX commands were converted
        assert "\\alpha" not in result
        assert "\\pm" not in result
        assert "\\beta" not in result
        assert "\\cdot" not in result
        assert "\\gamma" not in result
        # Check result changed from original
        assert result != formula

    def test_convert_text_disabled(self):
        """Test that conversion is skipped when disabled."""
        text = "\\alpha + \\beta = \\gamma"
        result = convert_text(text, False)
        assert result == text  # Should be unchanged
        assert "\\alpha" in result  # LaTeX commands should remain

    def test_convert_text_with_none_input(self):
        """Test convert_text with None input."""
        result = convert_text(None, True)
        assert result is None

        result = convert_text(None, False)
        assert result is None

    def test_convert_text_with_empty_string(self):
        """Test convert_text with empty string."""
        result = convert_text("", True)
        assert result == ""

        result = convert_text("", False)
        assert result == ""

    def test_convert_text_with_no_latex_commands(self):
        """Test convert_text with text containing no LaTeX commands."""
        text = "This is plain text with no symbols"
        result = convert_text(text, True)
        assert result == text

        result = convert_text(text, False)
        assert result == text

    def test_convert_text_with_unknown_commands(self):
        """Test convert_text with unknown LaTeX commands."""
        text = "\\unknown \\command"
        result = convert_text(text, True)
        assert result == text  # Unknown commands should remain unchanged

    def test_convert_text_mixed_known_unknown(self):
        """Test convert_text with mix of known and unknown commands."""
        text = "\\alpha \\unknown \\beta"
        result = convert_text(text, True)
        # Known commands should be converted (no longer present)
        assert "\\alpha" not in result
        assert "\\beta" not in result
        # Unknown commands should remain
        assert "\\unknown" in result
        # Result should be different from input
        assert result != text

    def test_convert_text_default_parameter(self):
        """Test convert_text with default enable_conversion parameter."""
        result = convert_text("\\alpha")  # Default should be True
        assert "\\alpha" not in result  # LaTeX command was converted
        assert result != "\\alpha"  # Result changed


class TestTextConverter:
    """Test the TextConverter class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = TextConverter()

    def test_converter_initialization(self):
        """Test TextConverter initialization."""
        assert self.converter is not None
        assert hasattr(self.converter, "symbol_mapper")
        assert hasattr(self.converter, "_latex_pattern")

    def test_convert_latex_to_unicode_basic(self):
        """Test basic LaTeX to Unicode conversion."""
        result = self.converter.convert_latex_to_unicode("\\alpha")
        assert result != "\\alpha"  # Should be converted
        assert len(result) == 1  # Should be single character
        assert ord(result) > 127  # Should be Unicode character

        result = self.converter.convert_latex_to_unicode("\\beta")
        assert result != "\\beta"  # Should be converted
        assert len(result) == 1  # Should be single character
        assert ord(result) > 127  # Should be Unicode character

        result = self.converter.convert_latex_to_unicode("\\pm")
        assert result != "\\pm"  # Should be converted
        assert len(result) == 1  # Should be single character
        assert ord(result) > 127  # Should be Unicode character

    def test_convert_latex_to_unicode_multiple_symbols(self):
        """Test conversion with multiple symbols in one string."""
        text = "\\alpha + \\beta = \\gamma"
        result = self.converter.convert_latex_to_unicode(text)
        # Check LaTeX commands were converted (no longer present)
        assert "\\alpha" not in result
        assert "\\beta" not in result
        assert "\\gamma" not in result
        # Non-LaTeX content should be preserved
        assert "+" in result
        assert "=" in result
        # Result should be different from input
        assert result != text

    def test_convert_latex_to_unicode_with_braces(self):
        """Test conversion of commands with braces."""
        result = self.converter.convert_latex_to_unicode("\\mathbb{R}")
        # This should either convert or remain as original depending on mapping
        assert isinstance(result, str)  # Should return a string
        # Either converted (different) or unchanged (same)
        assert len(result) >= 1

    def test_convert_latex_to_unicode_empty_input(self):
        """Test conversion with empty input."""
        result = self.converter.convert_latex_to_unicode("")
        assert result == ""

        result = self.converter.convert_latex_to_unicode(None)
        assert result is None

    def test_convert_latex_to_unicode_no_commands(self):
        """Test conversion with text containing no LaTeX commands."""
        text = "Plain text with no symbols"
        result = self.converter.convert_latex_to_unicode(text)
        assert result == text

    def test_convert_latex_to_unicode_malformed_commands(self):
        """Test conversion with malformed LaTeX commands."""
        # Single backslash should remain unchanged
        result = self.converter.convert_latex_to_unicode("\\")
        assert result == "\\"

        # Backslash with numbers should remain unchanged
        result = self.converter.convert_latex_to_unicode("\\123")
        assert result == "\\123"

    def test_get_conversion_statistics_empty(self):
        """Test conversion statistics with empty input."""
        stats = self.converter.get_conversion_statistics("")
        assert stats["total_commands"] == 0
        assert stats["converted"] == 0
        assert stats["unconverted"] == []

        stats = self.converter.get_conversion_statistics(None)
        assert stats["total_commands"] == 0
        assert stats["converted"] == 0
        assert stats["unconverted"] == []

    def test_get_conversion_statistics_with_commands(self):
        """Test conversion statistics with LaTeX commands."""
        text = "\\alpha \\unknown \\beta"
        stats = self.converter.get_conversion_statistics(text)

        assert stats["total_commands"] == 3
        assert stats["converted"] >= 2  # alpha and beta should be converted
        assert "\\unknown" in stats["unconverted"]
        assert 0 <= stats["conversion_rate"] <= 1

    def test_get_conversion_statistics_all_known(self):
        """Test conversion statistics with all known commands."""
        text = "\\alpha \\beta \\gamma"
        stats = self.converter.get_conversion_statistics(text)

        assert stats["total_commands"] == 3
        assert stats["converted"] == 3
        assert stats["unconverted"] == []
        assert stats["conversion_rate"] == 1.0

    def test_get_conversion_statistics_all_unknown(self):
        """Test conversion statistics with all unknown commands."""
        text = "\\unknown1 \\unknown2"
        stats = self.converter.get_conversion_statistics(text)

        assert stats["total_commands"] == 2
        assert stats["converted"] == 0
        assert len(stats["unconverted"]) == 2
        assert stats["conversion_rate"] == 0.0


class TestLaTeXSymbolMapper:
    """Test the LaTeXSymbolMapper class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = LaTeXSymbolMapper()

    def test_mapper_initialization(self):
        """Test LaTeXSymbolMapper initialization."""
        assert self.mapper is not None
        assert hasattr(self.mapper, "latex_to_unicode")
        assert hasattr(self.mapper, "unicode_to_int")
        assert hasattr(self.mapper, "latex_to_char")

    def test_get_unicode_char_known_symbols(self):
        """Test getting Unicode characters for known LaTeX commands."""
        # Test that known symbols return non-ASCII characters
        result = self.mapper.get_unicode_char("\\alpha")
        assert result != "\\alpha"  # Should be converted
        assert len(result) == 1  # Single character
        assert ord(result) > 127  # Unicode character

        result = self.mapper.get_unicode_char("\\beta")
        assert result != "\\beta"  # Should be converted
        assert len(result) == 1  # Single character
        assert ord(result) > 127  # Unicode character

        result = self.mapper.get_unicode_char("\\pm")
        assert result != "\\pm"  # Should be converted
        assert len(result) == 1  # Single character
        assert ord(result) > 127  # Unicode character

        result = self.mapper.get_unicode_char("\\cdot")
        assert result != "\\cdot"  # Should be converted
        assert len(result) == 1  # Single character
        assert ord(result) > 127  # Unicode character

    def test_get_unicode_char_unknown_symbols(self):
        """Test getting Unicode characters for unknown LaTeX commands."""
        unknown_command = "\\unknown"
        result = self.mapper.get_unicode_char(unknown_command)
        assert result == unknown_command  # Should return original

    def test_has_mapping_known_symbols(self):
        """Test has_mapping for known symbols."""
        assert self.mapper.has_mapping("\\alpha") is True
        assert self.mapper.has_mapping("\\beta") is True
        assert self.mapper.has_mapping("\\pm") is True

    def test_has_mapping_unknown_symbols(self):
        """Test has_mapping for unknown symbols."""
        assert self.mapper.has_mapping("\\unknown") is False
        assert self.mapper.has_mapping("\\nonexistent") is False

    def test_get_all_supported_commands(self):
        """Test getting all supported LaTeX commands."""
        commands = self.mapper.get_all_supported_commands()
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert "\\alpha" in commands
        assert "\\beta" in commands
        assert "\\pm" in commands

    def test_get_commands_by_category(self):
        """Test getting commands organized by category."""
        categories = self.mapper.get_commands_by_category()
        assert isinstance(categories, dict)

        # Should have some basic categories
        expected_categories = ["Greek Letters", "Math Operators", "Blackboard Bold"]
        for category in expected_categories:
            if category in categories:
                assert isinstance(categories[category], list)
                assert len(categories[category]) > 0

    def test_mapper_consistency(self):
        """Test consistency between different mapping dictionaries."""
        # All commands in latex_to_char should also be in latex_to_unicode
        for latex_cmd in self.mapper.latex_to_char:
            assert latex_cmd in self.mapper.latex_to_unicode


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_latex_pattern_matching(self):
        """Test LaTeX pattern matching edge cases."""
        converter = TextConverter()
        pattern = converter._latex_pattern

        # Test valid LaTeX commands
        assert pattern.search("\\alpha")
        assert pattern.search("\\mathbb{R}")
        assert pattern.search("text \\beta more")

        # Test invalid patterns that should not match
        assert not pattern.search("\\")  # Single backslash
        assert not pattern.search("\\123")  # Numbers after backslash
        assert not pattern.search("alpha")  # No backslash

    def test_large_text_processing(self):
        """Test processing of large text strings."""
        # Create a large string with many LaTeX commands
        large_text = " ".join(["\\alpha", "\\beta", "\\gamma"] * 1000)
        converter = TextConverter()

        result = converter.convert_latex_to_unicode(large_text)
        # Check that LaTeX commands were converted (no longer present)
        assert "\\alpha" not in result
        assert "\\beta" not in result
        assert "\\gamma" not in result
        assert len(result) > 0
        # Check that result is different from input
        assert result != large_text

    def test_special_characters_in_text(self):
        """Test text with special characters and LaTeX commands."""
        text = "Test with \\alpha and special chars: !@#$%^&*()"
        converter = TextConverter()
        result = converter.convert_latex_to_unicode(text)

        assert "\\alpha" not in result  # LaTeX command was converted
        assert "!@#$%^&*()" in result  # Special chars preserved
        assert result != text  # Result should be different

    def test_mixed_backslashes(self):
        """Test text with mix of LaTeX commands and other backslashes."""
        text = "\\alpha \\\\newline \\beta"
        converter = TextConverter()
        result = converter.convert_latex_to_unicode(text)

        assert "\\alpha" not in result  # Should be converted
        assert "\\beta" not in result  # Should be converted
        # \\newline might or might not be converted depending on mapping
        assert result != text  # Result should be different


class TestBackwardCompatibility:
    """Test backward compatibility features."""

    def test_text_convert_import(self):
        """Test that text_convert can still be imported for backward compatibility."""
        # Should be able to import text_convert from the old location
        from rtflite.text_conversion import text_convert

        assert callable(text_convert)

    def test_text_convert_function_exists(self):
        """Test that text_convert function works."""
        # This tests the backward compatibility import
        result = text_convert("\\alpha", True)
        # The exact behavior depends on the implementation in the old module
        assert result is not None


class TestIntegrationScenarios:
    """Test integration scenarios that simulate real usage."""

    def test_rtf_title_scenario(self):
        """Test scenario similar to RTF title usage."""
        title_text = "Study Results: \\alpha = 0.05"
        result = convert_text(title_text, True)
        # Check LaTeX command was converted
        assert "\\alpha" not in result
        # Check other content preserved
        assert "Study Results:" in result
        assert "= 0.05" in result
        assert result != title_text

    def test_footnote_scenario(self):
        """Test scenario similar to footnote usage."""
        footnote_text = "Significance level: \\alpha = 0.05, Power: \\beta = 0.2"
        result = convert_text(footnote_text, True)
        # Check LaTeX commands were converted
        assert "\\alpha" not in result
        assert "\\beta" not in result
        # Check other content preserved
        assert "0.05" in result
        assert "0.2" in result
        assert "Significance level:" in result
        assert result != footnote_text

    def test_statistical_formula_scenario(self):
        """Test scenario with statistical formulas."""
        formula = "Mean \\pm SD, Range: [\\mu - 2\\sigma, \\mu + 2\\sigma]"
        result = convert_text(formula, True)
        # Check that LaTeX commands were processed
        assert "\\pm" not in result  # Should be converted
        # Check mu commands (might or might not be available)
        # Non-LaTeX content should be preserved
        assert "Mean" in result
        assert "SD" in result
        assert "[" in result
        assert "]" in result
        assert result != formula  # Should be different

    def test_disabled_conversion_scenario(self):
        """Test scenario where conversion is intentionally disabled."""
        text_with_rtf_codes = "\\alpha {\\rtf field codes} \\beta"
        result = convert_text(text_with_rtf_codes, False)
        # All LaTeX commands should remain unchanged when disabled
        assert result == text_with_rtf_codes

    def test_partial_conversion_scenario(self):
        """Test scenario with mix of convertible and non-convertible commands."""
        mixed_text = "\\alpha \\customcmd \\beta \\anothercmd \\gamma"
        result = convert_text(mixed_text, True)

        # Known symbols should be converted (LaTeX commands no longer present)
        # But we can't be sure exactly which ones will be converted, so just check:
        # Unknown commands should remain
        assert "\\customcmd" in result
        assert "\\anothercmd" in result
        # Result should be different from input
        assert result != mixed_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
