"""Tests for text conversion functionality.

This module tests the LaTeX to Unicode conversion functionality across
all components of the RTF generation pipeline. It ensures that text
conversion works correctly and maintains compatibility with r2rtf.
"""

import pytest
import polars as pl

from rtflite import RTFDocument, RTFTitle, RTFFootnote, RTFSource
from rtflite.text_conversion import convert_text, TextConverter, LaTeXSymbolMapper
from rtflite.services import TextConversionService, RTFEncodingService


class TestLaTeXSymbolMapper:
    """Test the LaTeX symbol mapping functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = LaTeXSymbolMapper()
    
    def test_basic_symbol_conversion(self):
        """Test basic Greek letter conversion."""
        assert self.mapper.get_unicode_char("\\alpha") == "α"
        assert self.mapper.get_unicode_char("\\beta") == "β"
        assert self.mapper.get_unicode_char("\\gamma") == "γ"
    
    def test_mathematical_symbols(self):
        """Test mathematical symbol conversion."""
        assert self.mapper.get_unicode_char("\\pm") == "±"
        assert self.mapper.get_unicode_char("\\mp") == "∓"
        assert self.mapper.get_unicode_char("\\otimes") == "⊗"  # Available symbol
    
    def test_blackboard_bold_symbols(self):
        """Test blackboard bold symbol conversion."""
        assert self.mapper.get_unicode_char("\\mathbb{R}") == "ℝ"
        assert self.mapper.get_unicode_char("\\mathbb{N}") == "ℕ"
        assert self.mapper.get_unicode_char("\\mathbb{Q}") == "ℚ"
    
    def test_unknown_symbols(self):
        """Test handling of unknown symbols."""
        unknown_symbol = "\\unknown"
        assert self.mapper.get_unicode_char(unknown_symbol) == unknown_symbol
        assert not self.mapper.has_mapping(unknown_symbol)
    
    def test_symbol_categories(self):
        """Test symbol categorization."""
        categories = self.mapper.get_commands_by_category()
        
        # Check that categories exist and contain expected symbols
        assert "Greek Letters" in categories
        assert "Mathematical Operators" in categories
        assert "Blackboard Bold" in categories
        
        # Check specific symbols are in correct categories
        greek_letters = categories["Greek Letters"]
        assert "\\alpha" in greek_letters
        assert "\\beta" in greek_letters
        
        math_ops = categories["Mathematical Operators"]
        assert "\\pm" in math_ops


class TestTextConverter:
    """Test the text conversion engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = TextConverter()
    
    def test_simple_latex_conversion(self):
        """Test simple LaTeX command conversion."""
        text = "\\alpha + \\beta = \\gamma"
        result = self.converter.convert_latex_to_unicode(text)
        assert result == "α + β = γ"
    
    def test_mixed_text_conversion(self):
        """Test conversion of mixed text with LaTeX."""
        text = "The parameter \\alpha is significant (p < 0.05)"
        result = self.converter.convert_latex_to_unicode(text)
        assert "α" in result
        assert "significant" in result
        assert "0.05" in result
    
    def test_mathematical_expression(self):
        """Test mathematical expression conversion."""
        text = "Mean \\pm Standard Deviation"
        result = self.converter.convert_latex_to_unicode(text)
        assert result == "Mean ± Standard Deviation"
    
    def test_blackboard_bold_conversion(self):
        """Test blackboard bold symbol conversion."""
        text = "Set of real numbers: \\mathbb{R}"
        result = self.converter.convert_latex_to_unicode(text)
        assert "ℝ" in result
    
    def test_no_latex_commands(self):
        """Test text without LaTeX commands."""
        text = "Regular text without any symbols"
        result = self.converter.convert_latex_to_unicode(text)
        assert result == text
    
    def test_empty_and_none_text(self):
        """Test handling of empty and None text."""
        assert self.converter.convert_latex_to_unicode("") == ""
        assert self.converter.convert_latex_to_unicode(None) is None
    
    def test_conversion_statistics(self):
        """Test conversion statistics functionality."""
        text = "\\alpha + \\unknown + \\beta"
        stats = self.converter.get_conversion_statistics(text)
        
        assert stats["total_commands"] == 3
        assert stats["converted"] == 2
        assert "\\unknown" in stats["unconverted"]
        assert abs(stats["conversion_rate"] - 0.6667) < 0.001


class TestTextConversionService:
    """Test the text conversion service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TextConversionService()
    
    def test_string_conversion(self):
        """Test single string conversion."""
        result = self.service.convert_text_content("\\alpha test", True)
        assert result == "α test"
    
    def test_list_conversion(self):
        """Test list of strings conversion."""
        input_list = ["\\alpha", "\\beta", "\\gamma"]
        result = self.service.convert_text_content(input_list, True)
        assert result == ["α", "β", "γ"]
    
    def test_disabled_conversion(self):
        """Test disabled conversion."""
        text = "\\alpha + \\beta"
        result = self.service.convert_text_content(text, False)
        assert result == text
    
    def test_none_input(self):
        """Test None input handling."""
        assert self.service.convert_text_content(None, True) is None
        assert self.service.convert_text_content(None, False) is None
    
    def test_validation_functionality(self):
        """Test text validation functionality."""
        text = "\\alpha + \\unknown + \\beta"
        validation = self.service.validate_latex_commands(text)
        
        assert validation["validation_status"] == "analyzed"
        assert len(validation["valid_commands"]) == 2
        assert len(validation["invalid_commands"]) == 1
        assert "\\unknown" in validation["invalid_commands"]
    
    def test_convert_with_validation(self):
        """Test conversion with validation information."""
        text = "\\alpha \\pm \\beta"
        result = self.service.convert_with_validation(text, True)
        
        assert result["original_text"] == text
        assert result["converted_text"] == "α ± β"
        assert result["conversion_enabled"] is True
        assert result["conversion_applied"] is True
        assert result["validation"]["conversion_rate"] == 1.0


class TestEncodingServiceIntegration:
    """Test text conversion integration with encoding service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = RTFEncodingService()
    
    def test_text_conversion_through_encoding_service(self):
        """Test text conversion through encoding service."""
        text = "\\alpha + \\beta"
        result = self.service.convert_text_for_encoding(text, True)
        assert result == "α + β"
    
    def test_validation_through_encoding_service(self):
        """Test validation through encoding service."""
        text = "\\alpha \\pm \\unknown"
        result = self.service.validate_and_convert_text(text, True)
        
        assert result["conversion_applied"] is True
        assert "α" in result["converted_text"]
        assert "±" in result["converted_text"]
        assert "\\unknown" in result["converted_text"]


class TestRTFDocumentIntegration:
    """Test text conversion integration with full RTF documents."""
    
    def test_title_text_conversion(self):
        """Test text conversion in document titles."""
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        doc = RTFDocument(df=df, rtf_title=RTFTitle(text="Analysis: \\alpha"))
        
        rtf_output = doc.rtf_encode()
        assert "α" in rtf_output
        assert "Analysis:" in rtf_output
    
    def test_footnote_text_conversion(self):
        """Test text conversion in footnotes."""
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        doc = RTFDocument(df=df)
        # Enable text conversion for footnotes (disabled by default)
        doc.rtf_footnote = RTFFootnote(text="Significance: \\alpha = 0.05", text_convert=[[True]])
        
        rtf_output = doc.rtf_encode()
        assert "α" in rtf_output
        assert "0.05" in rtf_output
    
    def test_source_text_conversion(self):
        """Test text conversion in sources."""
        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        doc = RTFDocument(df=df)
        # Enable text conversion for sources (disabled by default)
        doc.rtf_source = RTFSource(text="Software: R \\pm Python", text_convert=[[True]])
        
        rtf_output = doc.rtf_encode()
        assert "±" in rtf_output
        assert "Software:" in rtf_output
    
    def test_data_content_conversion(self):
        """Test text conversion in table data."""
        data = {
            "Parameter": ["\\alpha", "\\beta", "\\gamma"],
            "Value": [1.0, 2.0, 3.0],
            "Formula": ["\\alpha^2", "\\beta \\pm 1", "\\gamma/2"]
        }
        df = pl.DataFrame(data)
        doc = RTFDocument(df=df)
        
        rtf_output = doc.rtf_encode()
        
        # Check that Greek letters were converted
        assert "α" in rtf_output
        assert "β" in rtf_output  
        assert "γ" in rtf_output
        assert "±" in rtf_output
    
    def test_comprehensive_document_conversion(self):
        """Test text conversion across all document components."""
        data = {
            "Greek": ["\\alpha", "\\beta"],
            "Math": ["\\pm 1", "\\otimes 2"],  # Use available symbol
            "Sets": ["\\mathbb{R}", "\\mathbb{N}"]
        }
        df = pl.DataFrame(data)
        
        doc = RTFDocument(
            df=df,
            rtf_title=RTFTitle(text="Study of \\alpha and \\beta")
        )
        # Enable text conversion for footnotes and sources (disabled by default)
        doc.rtf_footnote = RTFFootnote(text="Level: \\alpha = 0.05", text_convert=[[True]])
        doc.rtf_source = RTFSource(text="Math: \\mathbb{R} \\subset \\mathbb{C}", text_convert=[[True]])
        
        rtf_output = doc.rtf_encode()
        
        # Verify all expected conversions occurred
        expected_symbols = ["α", "β", "±", "⊗", "ℝ", "ℕ"]  # Use available symbols
        for symbol in expected_symbols:
            assert symbol in rtf_output, f"Symbol {symbol} not found in output"
        
        # Verify document structure is preserved
        assert "{\\rtf1\\ansi" in rtf_output
        assert "Study of" in rtf_output
        assert "Level:" in rtf_output


class TestTextConversionCompatibility:
    """Test compatibility with existing text_convert function."""
    
    def test_backward_compatibility(self):
        """Test that old text_convert function still works."""
        from rtflite.text_convert import text_convert
        
        result = text_convert("\\alpha test", True)
        assert "α" in result
        
        result_disabled = text_convert("\\alpha test", False)
        assert result_disabled == "\\alpha test"
    
    def test_new_interface_compatibility(self):
        """Test that new convert_text function works."""
        result = convert_text("\\alpha test", True)
        assert "α" in result
        
        result_disabled = convert_text("\\alpha test", False)
        assert result_disabled == "\\alpha test"