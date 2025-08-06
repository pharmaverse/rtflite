"""Tests for decomposed helper methods in input validation classes."""

import pytest

from rtflite.input import (
    AttributeDefaultsMixin,
    DefaultsFactory,
    RTFBody,
    RTFColumnHeader,
    RTFFootnote,
    RTFPage,
    ValidationHelpers,
)


class TestAttributeDefaultsMixin:
    """Test the AttributeDefaultsMixin class."""

    def test_set_attribute_defaults_basic(self):
        """Test basic attribute default setting."""

        class TestClass(AttributeDefaultsMixin):
            def __init__(self):
                self.text_font = 1
                self.text_size = 12
                self.text_bold = True
                self.text_color = "red"
                self.excluded_attr = "special"

        obj = TestClass()
        obj._set_attribute_defaults(exclude_attrs={"excluded_attr"})

        assert obj.text_font == [1]
        assert obj.text_size == [12]
        assert obj.text_bold == [True]
        assert obj.text_color == ["red"]
        assert obj.excluded_attr == "special"  # Should remain unchanged

    def test_set_attribute_defaults_list_to_tuple(self):
        """Test conversion of lists to tuples."""

        class TestClass(AttributeDefaultsMixin):
            def __init__(self):
                self.list_attr = [1, 2, 3]
                self.scalar_attr = 42

        obj = TestClass()
        obj._set_attribute_defaults()

        assert obj.list_attr == (1, 2, 3)
        assert obj.scalar_attr == [42]


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


class TestDefaultsFactory:
    """Test the DefaultsFactory class."""

    def test_get_text_defaults(self):
        """Test text defaults generation."""
        defaults = DefaultsFactory.get_text_defaults()

        assert "text_font" in defaults
        assert "text_font_size" in defaults
        assert "text_hyphenation" in defaults
        assert defaults["text_font"] == [1]
        assert defaults["text_font_size"] == [9]
        assert defaults["text_hyphenation"] == [True]

    def test_get_table_defaults(self):
        """Test table defaults generation."""
        defaults = DefaultsFactory.get_table_defaults()

        assert "col_rel_width" in defaults
        assert "border_width" in defaults
        assert "cell_height" in defaults
        assert defaults["col_rel_width"] == [1.0]
        assert defaults["border_width"] == [[15]]
        assert defaults["cell_height"] == [[0.15]]

    def test_get_border_defaults_as_table_true(self):
        """Test border defaults when as_table=True."""
        defaults = DefaultsFactory.get_border_defaults(as_table=True)

        assert defaults["border_left"] == [["single"]]
        assert defaults["border_right"] == [["single"]]
        assert defaults["border_top"] == [["single"]]
        assert defaults["border_bottom"] == [[""]]

    def test_get_border_defaults_as_table_false(self):
        """Test border defaults when as_table=False."""
        defaults = DefaultsFactory.get_border_defaults(as_table=False)

        assert defaults["border_left"] == [[""]]
        assert defaults["border_right"] == [[""]]
        assert defaults["border_top"] == [[""]]
        assert defaults["border_bottom"] == [[""]]


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

        assert body.border_top == [""]
        assert body.border_left == ["single"]
        assert body.cell_vertical_justification == ["center"]

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
