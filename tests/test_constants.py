"""Tests for RTF constants and configuration modules."""

from rtflite.core.config import (
    BorderConfiguration,
    ColorConfiguration,
    FontConfiguration,
    PageConfiguration,
    RTFConfiguration,
    TextConfiguration,
)
from rtflite.core.constants import RTFConstants, RTFDefaults, RTFMeasurements


class TestRTFConstants:
    """Test RTF constants are properly defined and accessible."""

    def test_measurement_constants(self):
        """Test measurement constants have correct values."""
        assert RTFConstants.TWIPS_PER_INCH == 1440
        assert RTFConstants.POINTS_PER_INCH == 72
        assert RTFConstants.LINE_SPACING_FACTOR == 240

    def test_default_dimensions(self):
        """Test default dimension constants."""
        assert RTFConstants.DEFAULT_BORDER_WIDTH == 15
        assert RTFConstants.DEFAULT_CELL_HEIGHT == 0.15
        assert RTFConstants.DEFAULT_SPACE_BEFORE == 15
        assert RTFConstants.DEFAULT_SPACE_AFTER == 15

    def test_format_codes_complete(self):
        """Test format codes dictionary is complete."""
        expected_codes = ["", "b", "i", "u", "s", "^", "_"]
        assert all(code in RTFConstants.FORMAT_CODES for code in expected_codes)

    def test_border_codes_complete(self):
        """Test border codes dictionary includes common styles."""
        expected_borders = ["single", "double", "dotted", "dashed", ""]
        assert all(border in RTFConstants.BORDER_CODES for border in expected_borders)

    def test_rtf_char_mapping(self):
        """Test RTF character mapping includes special characters."""
        mapping = RTFConstants.RTF_CHAR_MAPPING
        assert "^" in mapping
        assert "_" in mapping
        assert ">=" in mapping
        assert "<=" in mapping
        assert "\\pagenumber" in mapping

    def test_control_codes(self):
        """Test RTF control codes are properly defined."""
        assert RTFConstants.Control.SUPER == "\\super "
        assert RTFConstants.Control.SUB == "\\sub "
        assert RTFConstants.Control.LINE_BREAK == "\\line "
        assert RTFConstants.Control.PAGE_BREAK == "\\page"


class TestRTFMeasurements:
    """Test RTF measurement conversion utilities."""

    def test_inch_to_twip_conversion(self):
        """Test inch to twip conversion."""
        assert RTFMeasurements.inch_to_twip(1.0) == 1440
        assert RTFMeasurements.inch_to_twip(0.5) == 720
        assert RTFMeasurements.inch_to_twip(2.0) == 2880

    def test_twip_to_inch_conversion(self):
        """Test twip to inch conversion."""
        assert RTFMeasurements.twip_to_inch(1440) == 1.0
        assert RTFMeasurements.twip_to_inch(720) == 0.5
        assert RTFMeasurements.twip_to_inch(2880) == 2.0

    def test_point_to_halfpoint_conversion(self):
        """Test point to half-point conversion for font sizes."""
        assert RTFMeasurements.point_to_halfpoint(9.0) == 18
        assert RTFMeasurements.point_to_halfpoint(12.0) == 24
        assert RTFMeasurements.point_to_halfpoint(10.5) == 21


class TestRTFDefaults:
    """Test RTF default values."""

    def test_page_defaults(self):
        """Test page default settings."""
        assert RTFDefaults.ORIENTATION == "portrait"
        assert RTFDefaults.BORDER_FIRST == "double"
        assert RTFDefaults.BORDER_LAST == "double"
        assert RTFDefaults.USE_COLOR is False

    def test_text_defaults(self):
        """Test text default settings."""
        assert RTFDefaults.TEXT_FONT == 1
        assert RTFDefaults.TEXT_ALIGNMENT == "l"
        assert RTFDefaults.TEXT_HYPHENATION is True
        assert RTFDefaults.TEXT_CONVERT is True


class TestRTFConfiguration:
    """Test RTF configuration classes."""

    def test_page_configuration_default(self):
        """Test default page configuration."""
        config = PageConfiguration.create_default()
        assert config.orientation == "portrait"
        assert config.width is None
        assert config.height is None
        assert config.margins is None

    def test_page_configuration_landscape(self):
        """Test landscape page configuration."""
        config = PageConfiguration.create_landscape()
        assert config.orientation == "landscape"

    def test_font_configuration_default(self):
        """Test default font configuration."""
        config = FontConfiguration.create_default()
        assert config.default_font == 1
        assert config.default_size == 9
        assert config.charset == 1

    def test_rtf_configuration_default(self):
        """Test default RTF configuration creation."""
        config = RTFConfiguration.create_default()
        assert isinstance(config.page, PageConfiguration)
        assert isinstance(config.fonts, FontConfiguration)
        assert isinstance(config.colors, ColorConfiguration)
        assert isinstance(config.borders, BorderConfiguration)
        assert isinstance(config.text, TextConfiguration)

    def test_rtf_configuration_pharmaceutical(self):
        """Test pharmaceutical standard configuration."""
        config = RTFConfiguration.create_pharmaceutical_standard()
        assert config.page.orientation == "portrait"
        assert config.fonts.default_size == 9
        assert config.colors.use_color is False
        assert config.borders.first_row_style == "double"
        assert config.text.enable_latex_conversion is True

    def test_rtf_configuration_landscape(self):
        """Test landscape configuration creation."""
        config = RTFConfiguration.create_landscape()
        assert config.page.orientation == "landscape"


class TestBackwardsCompatibility:
    """Test that constants refactoring maintains backwards compatibility."""

    def test_legacy_imports_still_work(self):
        """Test that legacy constant imports still work."""
        # These should work for backwards compatibility
        from rtflite.row import BORDER_CODES, FORMAT_CODES, TEXT_JUSTIFICATION_CODES

        # Test they have the expected values
        assert FORMAT_CODES["b"] == "\\b"
        assert BORDER_CODES["single"] == "\\brdrs"
        assert TEXT_JUSTIFICATION_CODES["c"] == "\\qc"

    def test_constants_values_unchanged(self):
        """Test that constant values haven't changed from original implementation."""
        # Critical constants that must not change
        assert RTFConstants.TWIPS_PER_INCH == 1440
        assert RTFConstants.DEFAULT_BORDER_WIDTH == 15
        assert RTFConstants.DEFAULT_SPACE_BEFORE == 15
        assert RTFConstants.DEFAULT_SPACE_AFTER == 15

    def test_utils_inch_to_twip_still_works(self):
        """Test that Utils._inch_to_twip still works as before."""
        from rtflite.row import Utils

        # This should still work and return the same results
        assert Utils._inch_to_twip(1.0) == 1440
        assert Utils._inch_to_twip(0.5) == 720

    def test_format_codes_dictionary_structure(self):
        """Test that format codes maintain their structure."""
        codes = RTFConstants.FORMAT_CODES

        # Must have all original keys
        expected_keys = ["", "b", "i", "u", "s", "^", "_"]
        assert all(key in codes for key in expected_keys)

        # Must have correct RTF values
        assert codes["b"] == "\\b"
        assert codes["i"] == "\\i"
        assert codes["u"] == "\\ul"


class TestConstantsIntegration:
    """Test constants integration with existing modules."""

    def test_row_module_uses_constants(self):
        """Test that row module correctly uses centralized constants."""
        from rtflite.row import TextContent

        # Create a text content instance
        content = TextContent(
            text="Test text",
            space_before=RTFConstants.DEFAULT_SPACE_BEFORE,
            space_after=RTFConstants.DEFAULT_SPACE_AFTER,
        )

        # Verify defaults are applied correctly
        assert content.space_before == 15.0
        assert content.space_after == 15.0

    def test_constants_accessible_from_main_module(self):
        """Test that constants are accessible from main rtflite module."""
        from rtflite import RTFConfiguration, RTFConstants

        # Should be able to access constants
        assert RTFConstants.TWIPS_PER_INCH == 1440

        # Should be able to create configurations
        config = RTFConfiguration.create_default()
        assert config is not None
