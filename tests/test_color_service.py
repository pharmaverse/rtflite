"""Tests for the color service functionality."""

import pytest

from rtflite.services.color_service import ColorService, ColorValidationError


class TestColorService:
    """Test cases for the ColorService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.color_service = ColorService()

    def test_total_color_count(self):
        """Test that we have exactly 657 colors."""
        assert self.color_service.get_color_count() == 657

    def test_validate_color_valid(self):
        """Test validation of valid colors."""
        valid_colors = [
            "black",
            "red",
            "blue",
            "orange",
            "lightcoral",
            "darkseagreen",
            "white",
        ]
        for color in valid_colors:
            assert self.color_service.validate_color(color) is True

    def test_validate_color_invalid(self):
        """Test validation of invalid colors."""
        invalid_colors = ["invalidcolor", "notacolor", "123color", ""]
        for color in invalid_colors:
            assert self.color_service.validate_color(color) is False

    def test_get_color_index_valid(self):
        """Test getting color indices for valid colors."""
        # Test some known colors
        assert self.color_service.get_color_index("black") == 24
        assert self.color_service.get_color_index("red") == 552
        assert self.color_service.get_color_index("orange") == 498
        assert self.color_service.get_color_index("white") == 1

    def test_get_color_index_invalid(self):
        """Test error handling for invalid colors."""
        with pytest.raises(ColorValidationError) as exc_info:
            self.color_service.get_color_index("invalidcolor")

        assert "Invalid color name 'invalidcolor'" in str(exc_info.value)

    def test_get_color_rgb(self):
        """Test getting RGB values for colors."""
        assert self.color_service.get_color_rgb("black") == (0, 0, 0)
        assert self.color_service.get_color_rgb("red") == (255, 0, 0)
        assert self.color_service.get_color_rgb("orange") == (255, 165, 0)
        assert self.color_service.get_color_rgb("white") == (255, 255, 255)

    def test_get_color_rtf_code(self):
        """Test getting RTF color codes."""
        assert (
            self.color_service.get_color_rtf_code("black") == "\\red0\\green0\\blue0;"
        )
        assert (
            self.color_service.get_color_rtf_code("red") == "\\red255\\green0\\blue0;"
        )
        assert (
            self.color_service.get_color_rtf_code("orange")
            == "\\red255\\green165\\blue0;"
        )

    def test_get_color_suggestions(self):
        """Test color name suggestions."""
        # Test partial matches
        suggestions = self.color_service.get_color_suggestions("ora", 3)
        assert len(suggestions) <= 3
        assert any("coral" in s for s in suggestions)

        # Test exact match
        suggestions = self.color_service.get_color_suggestions("black", 3)
        assert suggestions == ["black"]

        # Test no matches - should suggest colors starting with same letter
        suggestions = self.color_service.get_color_suggestions("xyz", 3)
        assert len(suggestions) <= 3

    def test_validate_color_list_string(self):
        """Test validating a single color string."""
        validated = self.color_service.validate_color_list("red")
        assert validated == ["red"]

    def test_validate_color_list_tuple(self):
        """Test validating a tuple of colors."""
        validated = self.color_service.validate_color_list(("red", "blue", "orange"))
        assert validated == ["red", "blue", "orange"]

    def test_validate_color_list_list(self):
        """Test validating a list of colors."""
        validated = self.color_service.validate_color_list(["red", "blue", "orange"])
        assert validated == ["red", "blue", "orange"]

    def test_validate_color_list_invalid_color(self):
        """Test error handling for invalid colors in list."""
        with pytest.raises(ColorValidationError) as exc_info:
            self.color_service.validate_color_list(["red", "invalidcolor", "blue"])

        assert "Invalid color name 'invalidcolor' at index 1" in str(exc_info.value)

    def test_validate_color_list_invalid_type(self):
        """Test error handling for invalid input types."""
        with pytest.raises(ColorValidationError):
            self.color_service.validate_color_list(123)

        with pytest.raises(ColorValidationError):
            self.color_service.validate_color_list(["red", 123, "blue"])

    def test_generate_rtf_color_table_subset(self):
        """Test generating RTF color table for subset of colors."""
        used_colors = ["black", "red", "orange"]
        rtf_table = self.color_service.generate_rtf_color_table(used_colors)

        assert rtf_table.startswith("{\\colortbl")
        assert rtf_table.endswith("}")
        # Black is filtered out as it's a default color
        assert "\\red255\\green0\\blue0;" in rtf_table  # red
        assert "\\red255\\green165\\blue0;" in rtf_table  # orange

    def test_generate_rtf_color_table_all(self):
        """Test generating RTF color table for all colors."""
        rtf_table = self.color_service.generate_rtf_color_table()

        assert rtf_table.startswith("{\\colortbl")
        assert rtf_table.endswith("}")
        # Should be very long with all 657 colors
        assert len(rtf_table) > 10000

    def test_get_all_color_names(self):
        """Test getting all color names."""
        all_colors = self.color_service.get_all_color_names()
        assert len(all_colors) == 657
        assert "black" in all_colors
        assert "red" in all_colors
        assert "orange" in all_colors
        # Should be sorted
        assert all_colors == sorted(all_colors)

    def test_get_color_info(self):
        """Test getting comprehensive color information."""
        info = self.color_service.get_color_info("orange")
        expected = {
            "name": "orange",
            "index": 498,
            "rgb": (255, 165, 0),
            "rtf_code": "\\red255\\green165\\blue0;",
        }
        assert info == expected

    def test_backwards_compatibility_functions(self):
        """Test that convenience functions work for backwards compatibility."""
        from rtflite.services.color_service import (
            get_color_index,
            get_color_suggestions,
            validate_color,
        )

        assert validate_color("orange") is True
        assert validate_color("invalidcolor") is False

        assert get_color_index("orange") == 498

        suggestions = get_color_suggestions("ora", 3)
        assert len(suggestions) <= 3


class TestColorValidationInAttributes:
    """Test color validation in RTF attributes."""

    def test_text_color_validation_valid(self):
        """Test that valid text colors are accepted."""
        from rtflite.input import RTFBody

        # Single color gets converted to nested list format
        body = RTFBody(text_color="orange")
        assert body.text_color == [["orange"]]

        # Multiple colors
        body = RTFBody(text_color=("red", "blue", "orange"))
        assert body.text_color == [["red"], ["blue"], ["orange"]]

    def test_text_color_validation_invalid(self):
        """Test that invalid text colors raise validation errors."""
        from rtflite.input import RTFBody

        with pytest.raises(ValueError) as exc_info:
            RTFBody(text_color="invalidcolor")

        assert "Invalid text color: 'invalidcolor'" in str(exc_info.value)
        assert "Did you mean:" in str(exc_info.value)

    def test_text_color_validation_empty_allowed(self):
        """Test that empty strings are allowed for text colors."""
        from rtflite.input import RTFBody

        body = RTFBody(text_color=("", "black", ""))
        assert body.text_color == [[""], ["black"], [""]]

    def test_border_color_validation_valid(self):
        """Test that valid border colors are accepted."""
        from rtflite.input import RTFBody

        body = RTFBody(border_color_left=[["orange"]])
        assert body.border_color_left == [["orange"]]

    def test_border_color_validation_empty_allowed(self):
        """Test that empty string is allowed for border colors."""
        from rtflite.input import RTFBody

        body = RTFBody(border_color_left=[[""]])
        assert body.border_color_left == [[""]]

    def test_border_color_validation_invalid(self):
        """Test that invalid border colors raise validation errors."""
        from rtflite.input import RTFBody

        with pytest.raises(ValueError) as exc_info:
            RTFBody(border_color_left=[["invalidcolor"]])

        assert "Invalid border color: 'invalidcolor'" in str(exc_info.value)


class TestConditionalColorTable:
    """Test conditional color table generation."""

    def test_no_color_table_when_not_needed(self):
        """Test that color table is not generated when only black/empty colors used."""
        color_service = ColorService()

        # No colors
        result = color_service.generate_rtf_color_table([])
        assert result == ""

        # Only black
        result = color_service.generate_rtf_color_table(["black"])
        assert result == ""

        # Only empty strings
        result = color_service.generate_rtf_color_table(["", ""])
        assert result == ""

        # Mix of black and empty
        result = color_service.generate_rtf_color_table(["black", "", "black"])
        assert result == ""

    def test_color_table_when_needed(self):
        """Test that color table is generated when non-default colors used."""
        color_service = ColorService()

        # Single non-default color
        result = color_service.generate_rtf_color_table(["orange"])
        assert result.startswith("{\\colortbl")
        assert "\\red255\\green165\\blue0;" in result

        # Mix with default colors
        result = color_service.generate_rtf_color_table(["black", "orange", ""])
        assert result.startswith("{\\colortbl")
        assert "\\red255\\green165\\blue0;" in result
        # Should not include black in the table content since it's default

    def test_needs_color_table(self):
        """Test the needs_color_table helper method."""
        color_service = ColorService()

        # Cases that don't need color table
        assert not color_service.needs_color_table([])
        assert not color_service.needs_color_table([""])
        assert not color_service.needs_color_table(["black"])
        assert not color_service.needs_color_table(["", "black", ""])
        assert not color_service.needs_color_table(None)

        # Cases that need color table
        assert color_service.needs_color_table(["orange"])
        assert color_service.needs_color_table(["black", "orange"])
        assert color_service.needs_color_table(["", "red", ""])

    def test_document_color_collection(self):
        """Test collecting colors from an RTF document."""
        import polars as pl

        from rtflite.encode import RTFDocument
        from rtflite.input import RTFBody

        color_service = ColorService()

        # Document with no special colors
        doc1 = RTFDocument(
            df=pl.DataFrame({"col1": ["test"], "col2": ["data"]}), rtf_body=RTFBody()
        )
        colors1 = color_service.collect_document_colors(doc1)
        assert len(colors1) == 0

        # Document with colors
        doc2 = RTFDocument(
            df=pl.DataFrame({"col1": ["test"], "col2": ["data"]}),
            rtf_body=RTFBody(text_color="orange", border_color_left=[["red"]]),
        )
        colors2 = color_service.collect_document_colors(doc2)
        assert "orange" in colors2
        assert "red" in colors2
        assert len(colors2) == 2

    def test_rtf_generation_conditional_color_table(self):
        """Test that RTF generation includes color table only when needed."""
        import polars as pl

        from rtflite.encode import RTFDocument
        from rtflite.input import RTFBody

        # Document without colors
        doc_no_colors = RTFDocument(
            df=pl.DataFrame({"col": ["test"]}), rtf_body=RTFBody()
        )
        rtf_no_colors = doc_no_colors.rtf_encode()
        assert "\\colortbl" not in rtf_no_colors

        # Document with only black/empty colors
        doc_default_colors = RTFDocument(
            df=pl.DataFrame({"col": ["test"]}),
            rtf_body=RTFBody(text_color="black", border_color_left=[[""]]),
        )
        rtf_default_colors = doc_default_colors.rtf_encode()
        assert "\\colortbl" not in rtf_default_colors

        # Document with actual colors
        doc_with_colors = RTFDocument(
            df=pl.DataFrame({"col": ["test"]}), rtf_body=RTFBody(text_color="orange")
        )
        rtf_with_colors = doc_with_colors.rtf_encode()
        assert "\\colortbl" in rtf_with_colors
        assert "\\red255\\green165\\blue0;" in rtf_with_colors  # orange


class TestNewColorSupport:
    """Test that new comprehensive color table works as expected."""

    def test_issue_example_colors(self):
        """Test the specific colors mentioned in GitHub issue #45."""
        from rtflite.input import RTFBody

        # Test the API example from the GitHub issue
        body = RTFBody(
            text_color=("black", "orange", "red"),
            border_color_left=[["gray"], ["orange"], ["red"]],
        )

        assert body.text_color == [["black"], ["orange"], ["red"]]
        assert body.border_color_left == [["gray"], ["orange"], ["red"]]

    def test_clinical_reporting_colors(self):
        """Test colors commonly used in clinical reporting."""
        from rtflite.input import RTFBody

        clinical_colors = [
            "lightcoral",  # For warnings
            "darkseagreen",  # For normal/good results
            "gold",  # For borderline results
            "lightsteelblue",  # For headers
            "mistyrose",  # For alternating rows
        ]

        for color in clinical_colors:
            body = RTFBody(text_color=color)
            assert body.text_color == [[color]]

    def test_comprehensive_color_coverage(self):
        """Test a wide range of colors from the comprehensive table."""
        color_service = ColorService()

        # Test colors from different categories
        test_colors = [
            "aliceblue",
            "antiquewhite",
            "aquamarine",  # A colors
            "beige",
            "bisque",
            "blanchedalmond",  # B colors
            "chartreuse",
            "chocolate",
            "coral",  # C colors
            "darkblue",
            "darkcyan",
            "darkgoldenrod",  # Dark colors
            "lightblue",
            "lightcoral",
            "lightgreen",  # Light colors
            "mediumaquamarine",
            "mediumblue",
            "mediumorchid",  # Medium colors
            "palegreen",
            "paleturquoise",
            "palevioletred",  # Pale colors
        ]

        for color in test_colors:
            assert color_service.validate_color(color)
            index = color_service.get_color_index(color)
            assert isinstance(index, int)
            assert 1 <= index <= 657
