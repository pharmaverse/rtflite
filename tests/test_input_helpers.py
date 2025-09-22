"""Tests for decomposed helper methods in input validation classes."""

import pytest

from rtflite.input import (
    RTFBody,
    RTFColumnHeader,
    RTFFootnote,
    RTFPage,
    RTFPageFooter,
    RTFPageHeader,
    RTFSource,
    RTFSubline,
    RTFTitle,
    ValidationHelpers,
)


class TestTextComponentDefaults:
    """Ensure text-oriented components apply declarative defaults."""

    def test_page_header_defaults(self):
        """Page headers should populate all text defaults during initialization."""

        header = RTFPageHeader()

        assert header.text == ("Page \\chpgn of {\\field{\\*\\fldinst NUMPAGES }}",)
        assert header.text_font_size == (12,)
        assert header.text_justification == ("r",)
        assert header.text_convert == (False,)
        assert header.text_indent_reference == "page"

    def test_page_footer_defaults(self):
        """Footers should align center with text conversion disabled."""

        footer = RTFPageFooter()

        assert footer.text_justification == ("c",)
        assert footer.text_convert == (False,)
        assert footer.text_indent_reference == "page"

    def test_subline_defaults(self):
        """Sublines default to left alignment without text conversion."""

        subline = RTFSubline()

        assert subline.text_justification == ("l",)
        assert subline.text_convert == (False,)
        assert subline.text_indent_reference == "table"

    def test_title_spacing_defaults(self):
        """Titles should add extra spacing and keep conversion enabled."""

        title = RTFTitle()

        assert title.text_space_before == (180.0,)
        assert title.text_space_after == (180.0,)
        assert title.text_convert == (True,)
        assert title.text_indent_reference == "table"

    def test_source_defaults(self):
        """Sources default to plain text rendering with centered justification."""

        source = RTFSource()

        assert source.as_table is False
        assert source.border_left == [[""]]
        assert source.text_justification == [["c"]]

    def test_footnote_defaults(self):
        """Footnotes render as tables with borders by default."""

        footnote = RTFFootnote()

        assert footnote.as_table is True
        assert footnote.border_left == [["single"]]
        assert footnote.text_justification == [["l"]]


class TestValidationHelpers:
    """Test the ValidationHelpers class."""

    def test_convert_string_to_sequence_with_string(self):
        """Test string conversion to sequence."""
        result = ValidationHelpers.convert_string_to_sequence("test")
        assert result == ["test"]

    def test_convert_string_to_sequence_with_list(self):
        """Test list passthrough."""
        input_list = ["a", "b", "c"]
        result = ValidationHelpers.convert_string_to_sequence(input_list)
        assert result == input_list

    def test_convert_string_to_sequence_with_none(self):
        """Test None passthrough."""
        result = ValidationHelpers.convert_string_to_sequence(None)
        assert result is None

    def test_validate_boolean_field_valid(self):
        """Test valid boolean validation."""
        result = ValidationHelpers.validate_boolean_field(True, "test_field")
        assert result is True

        result = ValidationHelpers.validate_boolean_field(False, "test_field")
        assert result is False

    def test_validate_boolean_field_invalid(self):
        """Test invalid boolean validation."""
        with pytest.raises(ValueError, match="test_field must be a boolean"):
            ValidationHelpers.validate_boolean_field("not_bool", "test_field")

        with pytest.raises(ValueError, match="test_field must be a boolean"):
            ValidationHelpers.validate_boolean_field(1, "test_field")


class TestRTFPageHelpers:
    """Test RTFPage decomposed methods."""

    def test_set_portrait_defaults(self):
        """Test portrait defaults setting."""
        page = RTFPage(orientation="portrait")
        page.width = None
        page.height = None
        page.margin = None
        page.col_width = None
        page.nrow = None

        page._set_portrait_defaults()

        assert page.width == 8.5
        assert page.height == 11
        assert page.margin == [1.25, 1, 1.75, 1.25, 1.75, 1.00625]
        assert page.col_width == 6.25  # width - 2.25
        assert page.nrow == 40

    def test_set_landscape_defaults(self):
        """Test landscape defaults setting."""
        page = RTFPage(orientation="landscape")
        page.width = None
        page.height = None
        page.margin = None
        page.col_width = None
        page.nrow = None

        page._set_landscape_defaults()

        assert page.width == 11
        assert page.height == 8.5
        assert page.margin == [1.0, 1.0, 2, 1.25, 1.25, 1.25]
        assert page.col_width == 8.5  # width - 2.5
        assert page.nrow == 24

    def test_validate_margin_length_valid(self):
        """Test valid margin length validation."""
        page = RTFPage()
        page.margin = [1, 2, 3, 4, 5, 6]
        page._validate_margin_length()  # Should not raise

    def test_validate_margin_length_invalid(self):
        """Test invalid margin length validation."""
        page = RTFPage()
        page.margin = [1, 2, 3, 4, 5]  # Only 5 elements

        with pytest.raises(ValueError, match="Margin length must be 6"):
            page._validate_margin_length()


class TestRTFFootnoteHelpers:
    """Test RTFFootnote decomposed methods."""

    # Removed obsolete tests for internal methods that were consolidated

    def test_process_text_conversion_with_list(self):
        """Test text conversion with list input."""
        footnote = RTFFootnote()
        footnote.text = ["Line 1", "Line 2", "Line 3"]

        footnote._process_text_conversion()

        assert footnote.text == "Line 1\\line Line 2\\line Line 3"

    def test_process_text_conversion_with_empty_list(self):
        """Test text conversion with empty list."""
        footnote = RTFFootnote()
        footnote.text = []

        footnote._process_text_conversion()

        assert footnote.text == []

    def test_process_text_conversion_with_none(self):
        """Test text conversion with None."""
        footnote = RTFFootnote()
        footnote.text = None

        footnote._process_text_conversion()

        assert footnote.text is None


class TestRTFColumnHeaderHelpers:
    """Test RTFColumnHeader decomposed methods."""

    def test_handle_backwards_compatibility_with_df(self):
        """Test DataFrame backwards compatibility handling."""
        column_header = RTFColumnHeader()
        data = {"df": "mock_df", "other_param": "value"}

        # Mock the conversion method to avoid polars dependency
        original_method = column_header._convert_dataframe_to_text
        column_header._convert_dataframe_to_text = lambda df: ["col1", "col2", "col3"]

        result = column_header._handle_backwards_compatibility(data)

        assert "df" not in result
        assert result["text"] == ["col1", "col2", "col3"]
        assert result["other_param"] == "value"

        # Restore original method
        column_header._convert_dataframe_to_text = original_method

    def test_handle_backwards_compatibility_without_df(self):
        """Test data passthrough when no df parameter."""
        column_header = RTFColumnHeader()
        data = {"text": ["existing"], "other_param": "value"}

        result = column_header._handle_backwards_compatibility(data)

        assert result == data  # Should be unchanged

    def test_get_column_header_defaults(self):
        """Test column header defaults generation."""
        column_header = RTFColumnHeader()
        defaults = column_header._get_column_header_defaults()

        assert "border_left" in defaults
        assert "cell_vertical_justification" in defaults
        assert "text_convert" in defaults
        assert defaults["border_left"] == ["single"]
        assert defaults["cell_vertical_justification"] == ["bottom"]
        assert defaults["text_convert"] == [True]


class TestRTFBodyHelpers:
    """Test RTFBody decomposed methods."""

    def test_set_table_attribute_defaults(self):
        """Test table attribute defaults setting."""
        body = RTFBody()
        body.text_font = 1
        body.text_font_size = 12
        body.as_colheader = True  # Should be excluded
        body.page_by = ["col"]  # Should be excluded

        body._set_table_attribute_defaults()

        assert body.text_font == [1]
        assert body.text_font_size == [12]
        assert body.as_colheader == True  # Should remain unchanged
        assert body.page_by == ["col"]  # Should remain unchanged

    def test_set_border_defaults(self):
        """Test border defaults setting."""
        body = RTFBody()
        body.border_top = None
        body.border_left = None
        body.cell_vertical_justification = None

        body._set_border_defaults()

        assert body.border_top == [[""]]
        assert body.border_left == [["single"]]
        assert body.cell_vertical_justification == [["center"]]

    def test_validate_page_by_logic_valid(self):
        """Test valid page_by logic."""
        body = RTFBody()
        body.page_by = ["column"]
        body.new_page = True

        body._validate_page_by_logic()  # Should not raise

        body.page_by = None
        body.new_page = False

        body._validate_page_by_logic()  # Should not raise

    def test_validate_page_by_logic_invalid(self):
        """Test invalid page_by logic."""
        body = RTFBody()
        body.page_by = None
        body.new_page = True

        with pytest.raises(
            ValueError, match="`new_page` must be `False` if `page_by` is not specified"
        ):
            body._validate_page_by_logic()
