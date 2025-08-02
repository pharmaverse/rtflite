"""Factory for creating RTF components with consistent defaults and validation."""

from typing import Any, Dict, Optional, Type, Union
from enum import Enum

from ..input import (
    RTFBody, RTFColumnHeader, RTFFootnote, RTFPage, RTFPageFooter,
    RTFPageHeader, RTFSource, RTFSubline, RTFTitle, TableAttributes, TextAttributes
)
from .builders import TableBuilder, TextBuilder, PageBuilder


class ComponentType(Enum):
    """Enumeration of supported RTF component types."""
    
    # Table-based components
    BODY = "body"
    COLUMN_HEADER = "column_header"
    FOOTNOTE = "footnote"
    SOURCE = "source"
    
    # Text-based components
    TITLE = "title"
    SUBLINE = "subline"
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
    
    # Page components
    PAGE = "page"


class RTFComponentFactory:
    """Factory for creating RTF components with consistent configuration.
    
    This factory provides a centralized way to create RTF components with
    appropriate defaults, validation, and future extensibility for lists
    and figures.
    """
    
    def __init__(self):
        self._table_builder = TableBuilder()
        self._text_builder = TextBuilder()
        self._page_builder = PageBuilder()
        
        # Component type mappings
        self._component_classes = {
            ComponentType.BODY: RTFBody,
            ComponentType.COLUMN_HEADER: RTFColumnHeader,
            ComponentType.FOOTNOTE: RTFFootnote,
            ComponentType.SOURCE: RTFSource,
            ComponentType.TITLE: RTFTitle,
            ComponentType.SUBLINE: RTFSubline,
            ComponentType.PAGE_HEADER: RTFPageHeader,
            ComponentType.PAGE_FOOTER: RTFPageFooter,
            ComponentType.PAGE: RTFPage,
        }
        
        self._component_builders = {
            ComponentType.BODY: self._table_builder,
            ComponentType.COLUMN_HEADER: self._table_builder,
            ComponentType.FOOTNOTE: self._table_builder,
            ComponentType.SOURCE: self._table_builder,
            ComponentType.TITLE: self._text_builder,
            ComponentType.SUBLINE: self._text_builder,
            ComponentType.PAGE_HEADER: self._text_builder,
            ComponentType.PAGE_FOOTER: self._text_builder,
            ComponentType.PAGE: self._page_builder,
        }
    
    def create_component(
        self, 
        component_type: Union[ComponentType, str], 
        **kwargs: Any
    ) -> Union[TableAttributes, TextAttributes, RTFPage]:
        """Create an RTF component of the specified type.
        
        Args:
            component_type: Type of component to create
            **kwargs: Component-specific configuration options
            
        Returns:
            Configured RTF component instance
            
        Raises:
            ValueError: If component type is not supported
        """
        if isinstance(component_type, str):
            try:
                component_type = ComponentType(component_type)
            except ValueError:
                raise ValueError(f"Unsupported component type: {component_type}")
        
        if component_type not in self._component_classes:
            raise ValueError(f"Unsupported component type: {component_type}")
        
        # Get the appropriate builder and component class
        builder = self._component_builders[component_type]
        component_class = self._component_classes[component_type]
        
        # Build configuration using the builder
        config = builder.build_config(component_type, **kwargs)
        
        # Create and return the component
        return component_class(**config)
    
    def create_table_component(
        self, 
        component_type: str, 
        **kwargs: Any
    ) -> TableAttributes:
        """Create a table-based RTF component.
        
        Args:
            component_type: Type of table component ('body', 'column_header', 'footnote', 'source')
            **kwargs: Component-specific configuration options
            
        Returns:
            Configured table component instance
        """
        table_types = {
            ComponentType.BODY, ComponentType.COLUMN_HEADER, 
            ComponentType.FOOTNOTE, ComponentType.SOURCE
        }
        
        comp_type = ComponentType(component_type)
        if comp_type not in table_types:
            raise ValueError(f"'{component_type}' is not a table-based component")
        
        return self.create_component(comp_type, **kwargs)
    
    def create_text_component(
        self, 
        component_type: str, 
        **kwargs: Any
    ) -> TextAttributes:
        """Create a text-based RTF component.
        
        Args:
            component_type: Type of text component ('title', 'subline', 'page_header', 'page_footer')
            **kwargs: Component-specific configuration options
            
        Returns:
            Configured text component instance
        """
        text_types = {
            ComponentType.TITLE, ComponentType.SUBLINE,
            ComponentType.PAGE_HEADER, ComponentType.PAGE_FOOTER
        }
        
        comp_type = ComponentType(component_type)
        if comp_type not in text_types:
            raise ValueError(f"'{component_type}' is not a text-based component")
        
        return self.create_component(comp_type, **kwargs)
    
    def create_page_component(self, **kwargs: Any) -> RTFPage:
        """Create a page configuration component.
        
        Args:
            **kwargs: Page-specific configuration options
            
        Returns:
            Configured page component instance
        """
        return self.create_component(ComponentType.PAGE, **kwargs)
    
    # Future extension methods for new content types
    
    def create_list_component(self, list_type: str, **kwargs: Any):
        """Create a list-based RTF component (future feature).
        
        Args:
            list_type: Type of list component
            **kwargs: Component-specific configuration options
            
        Returns:
            Configured list component instance
            
        Raises:
            NotImplementedError: List components not yet implemented
        """
        raise NotImplementedError("List component creation not yet implemented")
    
    def create_figure_component(self, figure_type: str, **kwargs: Any):
        """Create a figure-based RTF component (future feature).
        
        Args:
            figure_type: Type of figure component
            **kwargs: Component-specific configuration options
            
        Returns:
            Configured figure component instance
            
        Raises:
            NotImplementedError: Figure components not yet implemented
        """
        raise NotImplementedError("Figure component creation not yet implemented")