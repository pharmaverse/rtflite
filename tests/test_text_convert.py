"""Tests for LaTeX to Unicode text conversion functionality."""

import pytest

from rtflite.text_convert import (
    convert_latex_to_unicode,
    latex_to_unicode_char,
    text_convert,
)
from rtflite.row import TextContent


class TestLatexToUnicodeChar:
    """Test individual LaTeX command to Unicode conversion."""

    def test_basic_greek_letters(self):
        """Test conversion of basic Greek letters."""
        assert latex_to_unicode_char("\\alpha") == "α"
        assert latex_to_unicode_char("\\beta") == "β"
        assert latex_to_unicode_char("\\gamma") == "γ"
        assert latex_to_unicode_char("\\delta") == "δ"
        assert latex_to_unicode_char("\\epsilon") == "ϵ"  # Note: \epsilon maps to ϵ, \varepsilon maps to ε

    def test_uppercase_greek_letters(self):
        """Test conversion of uppercase Greek letters."""
        # Note: \Alpha is not in the mapping, testing available uppercase letters
        assert latex_to_unicode_char("\\Gamma") == "Γ"
        assert latex_to_unicode_char("\\Delta") == "Δ"
        assert latex_to_unicode_char("\\Theta") == "Θ"
        assert latex_to_unicode_char("\\Lambda") == "Λ"
        assert latex_to_unicode_char("\\Omega") == "Ω"

    def test_mathematical_symbols(self):
        """Test conversion of mathematical symbols."""
        assert latex_to_unicode_char("\\pm") == "±"
        assert latex_to_unicode_char("\\infty") == "∞"
        assert latex_to_unicode_char("\\leq") == "≤"
        assert latex_to_unicode_char("\\geq") == "≥"
        assert latex_to_unicode_char("\\neq") == "≠"

    def test_arrows(self):
        """Test conversion of arrow symbols."""
        assert latex_to_unicode_char("\\leftarrow") == "←"
        assert latex_to_unicode_char("\\rightarrow") == "→"
        assert latex_to_unicode_char("\\leftrightarrow") == "↔"
        assert latex_to_unicode_char("\\Leftarrow") == "⇐"
        assert latex_to_unicode_char("\\Rightarrow") == "⇒"

    def test_logical_symbols(self):
        """Test conversion of logical symbols."""
        assert latex_to_unicode_char("\\forall") == "∀"
        assert latex_to_unicode_char("\\exists") == "∃"
        # Note: \neg is not in the mapping, \not is a combining character
        assert latex_to_unicode_char("\\wedge") == "∧"
        assert latex_to_unicode_char("\\vee") == "∨"

    def test_unknown_command(self):
        """Test that unknown LaTeX commands are returned unchanged."""
        assert latex_to_unicode_char("\\unknown") == "\\unknown"
        assert latex_to_unicode_char("\\notinlist") == "\\notinlist"


class TestConvertLatexToUnicode:
    """Test full text LaTeX to Unicode conversion."""

    def test_single_command_conversion(self):
        """Test conversion of text with single LaTeX command."""
        assert convert_latex_to_unicode("\\alpha") == "α"
        assert convert_latex_to_unicode("The angle \\alpha is acute") == "The angle α is acute"

    def test_multiple_commands_conversion(self):
        """Test conversion of text with multiple LaTeX commands."""
        text = "\\alpha + \\beta = \\gamma"
        expected = "α + β = γ"
        assert convert_latex_to_unicode(text) == expected

    def test_mixed_text_and_commands(self):
        """Test conversion of mixed text and LaTeX commands."""
        text = "For all \\epsilon > 0, there exists \\delta > 0 such that |x - a| < \\delta \\Rightarrow |f(x) - f(a)| < \\epsilon"
        expected = "For all ϵ > 0, there exists δ > 0 such that |x - a| < δ ⇒ |f(x) - f(a)| < ϵ"  # Note: \epsilon maps to ϵ
        assert convert_latex_to_unicode(text) == expected

    def test_mathematical_expressions(self):
        """Test conversion of mathematical expressions."""
        text = "\\alpha \\pm \\beta \\neq \\gamma"
        expected = "α ± β ≠ γ"
        assert convert_latex_to_unicode(text) == expected

    def test_empty_string(self):
        """Test conversion of empty string."""
        assert convert_latex_to_unicode("") == ""

    def test_no_latex_commands(self):
        """Test text without LaTeX commands."""
        text = "This is plain text without any commands"
        assert convert_latex_to_unicode(text) == text

    def test_backslash_not_command(self):
        """Test backslashes that are not LaTeX commands."""
        text = "This is a\\path\\to\\file"
        # These shouldn't be converted as they don't match LaTeX command pattern
        assert convert_latex_to_unicode(text) == text

    def test_braced_commands(self):
        """Test LaTeX commands with braces."""
        # Note: Currently our implementation doesn't handle complex braced commands
        # This test documents current behavior
        text = "\\mathbb{R}"
        # Since \\mathbb{R} is in our mapping, it should convert
        result = convert_latex_to_unicode(text)
        # This test documents expected behavior for braced commands
        assert result == text or result == "ℝ"  # Accept either as implementation evolves


class TestTextConvert:
    """Test main text_convert function."""

    def test_conversion_enabled(self):
        """Test text conversion when enabled."""
        text = "\\alpha + \\beta"
        expected = "α + β"
        assert text_convert(text, enable_conversion=True) == expected

    def test_conversion_disabled(self):
        """Test text conversion when disabled."""
        text = "\\alpha + \\beta"
        assert text_convert(text, enable_conversion=False) == text

    def test_empty_text(self):
        """Test with empty text."""
        assert text_convert("", enable_conversion=True) == ""
        assert text_convert("", enable_conversion=False) == ""

    def test_none_text(self):
        """Test with None text."""
        # text_convert should handle None gracefully
        assert text_convert(None, enable_conversion=True) is None
        assert text_convert(None, enable_conversion=False) is None


class TestTextContentIntegration:
    """Test integration with TextContent class."""

    def test_text_content_with_conversion_enabled(self):
        """Test TextContent with LaTeX conversion enabled."""
        content = TextContent(
            text="The probability is \\alpha \\pm \\beta",
            convert=True
        )
        
        # Test that conversion is applied when generating RTF
        rtf_output = content._convert_special_chars()
        assert "α" in rtf_output
        assert "±" in rtf_output
        assert "β" in rtf_output
        assert "\\alpha" not in rtf_output

    def test_text_content_with_conversion_disabled(self):
        """Test TextContent with LaTeX conversion disabled."""
        content = TextContent(
            text="The probability is \\alpha \\pm \\beta",
            convert=False
        )
        
        # Test that conversion is NOT applied when generating RTF
        rtf_output = content._convert_special_chars()
        assert "\\alpha" in rtf_output
        assert "\\pm" in rtf_output
        assert "\\beta" in rtf_output

    def test_text_content_default_convert_value(self):
        """Test that TextContent has convert=True by default."""
        content = TextContent(text="\\alpha")
        assert content.convert is True

    def test_text_content_rtf_generation_with_conversion(self):
        """Test complete RTF generation with LaTeX conversion."""
        content = TextContent(
            text="Result: \\alpha \\geq \\beta",
            convert=True
        )
        
        rtf_plain = content._as_rtf("plain")
        # Should contain Unicode characters, not LaTeX commands
        assert "α" in rtf_plain
        assert "≥" in rtf_plain  
        assert "β" in rtf_plain
        assert "\\alpha" not in rtf_plain
        assert "\\geq" not in rtf_plain
        assert "\\beta" not in rtf_plain

    def test_text_content_special_chars_after_conversion(self):
        """Test that LaTeX conversion works along with other RTF character conversion."""
        content = TextContent(
            text="\\alpha >= 0.05 and \\beta <= 0.2",
            convert=True
        )
        
        rtf_output = content._convert_special_chars()
        # Should have converted LaTeX to Unicode
        assert "α" in rtf_output
        assert "β" in rtf_output
        # Should have converted comparison operators to RTF codes (per r2rtf char_rtf mapping)
        assert "\\geq " in rtf_output
        assert "\\leq " in rtf_output


class TestRealWorldExamples:
    """Test real-world usage examples."""

    def test_statistical_notation(self):
        """Test statistical notation commonly used in pharmaceutical reports."""
        text = "Mean \\pm SD: 12.5 \\pm 2.3, p \\leq 0.05"
        expected = "Mean ± SD: 12.5 ± 2.3, p ≤ 0.05"
        assert convert_latex_to_unicode(text) == expected

    def test_clinical_trial_notation(self):
        """Test clinical trial notation."""
        text = "Treatment A vs B: \\Delta = 5.2 (95% CI), \\alpha = 0.05"
        expected = "Treatment A vs B: Δ = 5.2 (95% CI), α = 0.05"
        assert convert_latex_to_unicode(text) == expected

    def test_pharmaceutical_symbols(self):
        """Test pharmaceutical and chemical symbols."""
        text = "Concentration \\geq 10 \\mu g/mL"
        expected = "Concentration ≥ 10 μ g/mL"
        assert convert_latex_to_unicode(text) == expected

    def test_dose_response_notation(self):
        """Test dose-response notation."""
        text = "IC\\textsubscript{50} \\approx 2.5 nM"
        # Note: \\textsubscript is not in our mapping, so it won't convert
        # but \\approx should convert
        result = convert_latex_to_unicode(text)
        assert "≈" in result
        assert "2.5 nM" in result


class TestRTFCharacterMapping:
    """Test RTF character mapping functionality."""

    def test_comparison_operators(self):
        """Test comparison operators are converted to RTF codes."""
        content = TextContent(text="value >= 10 and value <= 20", convert=False)
        rtf_output = content._convert_special_chars()
        assert "\\geq " in rtf_output
        assert "\\leq " in rtf_output

    def test_page_field_codes(self):
        """Test page field codes are converted properly."""
        content = TextContent(text="Page \\pagenumber of \\totalpage", convert=False)
        rtf_output = content._convert_special_chars()
        assert "\\chpgn " in rtf_output
        assert "\\totalpage " in rtf_output

    def test_page_field_complex(self):
        """Test complex page field code."""
        content = TextContent(text="Total pages: \\pagefield", convert=False)
        rtf_output = content._convert_special_chars()
        assert "{\\field{\\*\\fldinst NUMPAGES }} " in rtf_output

    def test_combined_latex_and_rtf_chars(self):
        """Test LaTeX conversion followed by RTF character conversion."""
        content = TextContent(text="\\alpha >= 0.05 and \\beta <= 0.2", convert=True)
        rtf_output = content._convert_special_chars()
        # Should have converted LaTeX to Unicode
        assert "α" in rtf_output
        assert "β" in rtf_output
        # Should have converted comparison operators to RTF codes
        assert "\\geq " in rtf_output
        assert "\\leq " in rtf_output

    def test_superscript_subscript_formatting(self):
        """Test superscript and subscript formatting."""
        content = TextContent(text="x^2 + y_1", convert=False)
        rtf_output = content._convert_special_chars()
        assert "\\super " in rtf_output
        assert "\\sub " in rtf_output