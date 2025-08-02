"""Tests for RTF component factory classes."""

import pytest
from rtflite.factory import RTFComponentFactory, ComponentType
from rtflite.input import (
    RTFBody, RTFColumnHeader, RTFFootnote, RTFSource,
    RTFTitle, RTFSubline, RTFPageHeader, RTFPageFooter, RTFPage
)


class TestRTFComponentFactory:
    """Test the RTFComponentFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RTFComponentFactory()
    
    def test_create_body_component(self):
        """Test creating a body component."""
        body = self.factory.create_component(ComponentType.BODY)
        
        assert isinstance(body, RTFBody)
        assert body.border_left == [["single"]]
        assert body.text_convert == [[True]]
    
    def test_create_column_header_component(self):
        """Test creating a column header component."""
        header = self.factory.create_component(ComponentType.COLUMN_HEADER)
        
        assert isinstance(header, RTFColumnHeader)
        assert header.border_left == ["single"]
        assert header.cell_vertical_justification == ["bottom"]
    
    def test_create_footnote_component_as_table_true(self):
        """Test creating a footnote component with as_table=True."""
        footnote = self.factory.create_component(
            ComponentType.FOOTNOTE, 
            as_table=True
        )
        
        assert isinstance(footnote, RTFFootnote)
        assert footnote.as_table == True
        assert footnote.border_left == [["single"]]
        assert footnote.text_convert == [[False]]
    
    def test_create_footnote_component_as_table_false(self):
        """Test creating a footnote component with as_table=False."""
        footnote = self.factory.create_component(
            ComponentType.FOOTNOTE,
            as_table=False
        )
        
        assert isinstance(footnote, RTFFootnote)
        assert footnote.as_table == False
        assert footnote.border_left == [[""]]
        assert footnote.text_convert == [[False]]
    
    def test_create_source_component_as_table_true(self):
        """Test creating a source component with as_table=True."""
        source = self.factory.create_component(
            ComponentType.SOURCE,
            as_table=True
        )
        
        assert isinstance(source, RTFSource)
        assert source.as_table == True
        assert source.border_left == [["single"]]
        assert source.text_justification == [["c"]]
        assert source.text_convert == [[False]]
    
    def test_create_source_component_as_table_false(self):
        """Test creating a source component with as_table=False."""
        source = self.factory.create_component(
            ComponentType.SOURCE,
            as_table=False
        )
        
        assert isinstance(source, RTFSource)
        assert source.as_table == False
        assert source.border_left == [[""]]
        assert source.text_justification == [["c"]]
        assert source.text_convert == [[False]]
    
    def test_create_title_component(self):
        """Test creating a title component."""
        title = self.factory.create_component(ComponentType.TITLE)
        
        assert isinstance(title, RTFTitle)
        assert title.text_font_size == (12.0,)
        assert title.text_justification == ("c",)
        assert title.text_convert == (True,)
    
    def test_create_subline_component(self):
        """Test creating a subline component."""
        subline = self.factory.create_component(ComponentType.SUBLINE)
        
        assert isinstance(subline, RTFSubline)
        assert subline.text_font_size == (9.0,)
        assert subline.text_justification == ("l",)
        assert subline.text_convert == (True,)
    
    def test_create_page_header_component(self):
        """Test creating a page header component."""
        header = self.factory.create_component(ComponentType.PAGE_HEADER)
        
        assert isinstance(header, RTFPageHeader)
        assert header.text_font_size == (12.0,)
        assert header.text_justification == ("r",)
        assert header.text_convert == (False,)
    
    def test_create_page_footer_component(self):
        """Test creating a page footer component."""
        footer = self.factory.create_component(ComponentType.PAGE_FOOTER)
        
        assert isinstance(footer, RTFPageFooter)
        assert footer.text_font_size == (12.0,)
        assert footer.text_justification == ("c",)
        assert footer.text_convert == (False,)
    
    def test_create_page_component(self):
        """Test creating a page component."""
        page = self.factory.create_component(ComponentType.PAGE)
        
        assert isinstance(page, RTFPage)
        assert page.orientation == "portrait"
        assert page.border_first == "double"
        assert page.border_last == "double"
    
    def test_create_component_with_string_type(self):
        """Test creating a component using string type."""
        body = self.factory.create_component("body")
        
        assert isinstance(body, RTFBody)
        assert body.border_left == [["single"]]
    
    def test_create_component_with_overrides(self):
        """Test creating a component with custom overrides."""
        title = self.factory.create_component(
            ComponentType.TITLE,
            text_font_size=[14],
            text_justification=["l"]
        )
        
        assert isinstance(title, RTFTitle)
        assert title.text_font_size == (14.0,)  # Override applied
        assert title.text_justification == ("l",)  # Override applied
        assert title.text_convert == (True,)  # Default preserved
    
    def test_create_component_invalid_type(self):
        """Test creating a component with invalid type."""
        with pytest.raises(ValueError, match="Unsupported component type"):
            self.factory.create_component("invalid_type")
    
    def test_create_table_component_valid(self):
        """Test creating table components using the convenience method."""
        body = self.factory.create_table_component("body")
        header = self.factory.create_table_component("column_header")
        footnote = self.factory.create_table_component("footnote")
        source = self.factory.create_table_component("source")
        
        assert isinstance(body, RTFBody)
        assert isinstance(header, RTFColumnHeader)
        assert isinstance(footnote, RTFFootnote)
        assert isinstance(source, RTFSource)
    
    def test_create_table_component_invalid(self):
        """Test creating table component with non-table type."""
        with pytest.raises(ValueError, match="is not a table-based component"):
            self.factory.create_table_component("title")
    
    def test_create_text_component_valid(self):
        """Test creating text components using the convenience method."""
        title = self.factory.create_text_component("title")
        subline = self.factory.create_text_component("subline")
        header = self.factory.create_text_component("page_header")
        footer = self.factory.create_text_component("page_footer")
        
        assert isinstance(title, RTFTitle)
        assert isinstance(subline, RTFSubline)
        assert isinstance(header, RTFPageHeader)
        assert isinstance(footer, RTFPageFooter)
    
    def test_create_text_component_invalid(self):
        """Test creating text component with non-text type."""
        with pytest.raises(ValueError, match="is not a text-based component"):
            self.factory.create_text_component("body")
    
    def test_create_page_component_convenience(self):
        """Test creating page component using convenience method."""
        page = self.factory.create_page_component(orientation="landscape")
        
        assert isinstance(page, RTFPage)
        assert page.orientation == "landscape"
    
    def test_create_list_component_not_implemented(self):
        """Test that list component creation raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="List component creation not yet implemented"):
            self.factory.create_list_component("ordered")
    
    def test_create_figure_component_not_implemented(self):
        """Test that figure component creation raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Figure component creation not yet implemented"):
            self.factory.create_figure_component("image")


class TestComponentType:
    """Test the ComponentType enum."""
    
    def test_component_type_values(self):
        """Test that all expected component types are defined."""
        expected_types = {
            "body", "column_header", "footnote", "source",
            "title", "subline", "page_header", "page_footer", "page"
        }
        
        actual_types = {ct.value for ct in ComponentType}
        assert actual_types == expected_types
    
    def test_component_type_from_string(self):
        """Test creating ComponentType from string values."""
        assert ComponentType("body") == ComponentType.BODY
        assert ComponentType("title") == ComponentType.TITLE
        assert ComponentType("page") == ComponentType.PAGE
    
    def test_component_type_invalid_string(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            ComponentType("invalid_type")