"""Builder classes for constructing RTF component configurations."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum

from ..input import DefaultsFactory


class ComponentBuilder(ABC):
    """Abstract base class for RTF component builders."""
    
    @abstractmethod
    def build_config(self, component_type: Enum, **kwargs: Any) -> Dict[str, Any]:
        """Build configuration dictionary for the specified component type.
        
        Args:
            component_type: The type of component to build configuration for
            **kwargs: Component-specific configuration options
            
        Returns:
            Configuration dictionary ready for component instantiation
        """
        pass


class TableBuilder(ComponentBuilder):
    """Builder for table-based RTF components (body, header, footnote, source)."""
    
    def build_config(self, component_type: Enum, **kwargs: Any) -> Dict[str, Any]:
        """Build configuration for table-based components.
        
        Args:
            component_type: The table component type
            **kwargs: Component-specific configuration options
            
        Returns:
            Configuration dictionary with table defaults and overrides
        """
        # Import here to avoid circular imports
        from .component_factory import ComponentType
        
        # Start with base table defaults
        config = DefaultsFactory.get_table_defaults().copy()
        
        # Apply component-specific configurations
        if component_type == ComponentType.BODY:
            config.update(self._get_body_defaults())
        elif component_type == ComponentType.COLUMN_HEADER:
            config.update(self._get_column_header_defaults())
        elif component_type == ComponentType.FOOTNOTE:
            config.update(self._get_footnote_defaults(**kwargs))
        elif component_type == ComponentType.SOURCE:
            config.update(self._get_source_defaults(**kwargs))
        
        # Apply user overrides
        config.update(kwargs)
        
        return config
    
    def _get_body_defaults(self) -> Dict[str, Any]:
        """Get defaults specific to body components."""
        return {
            "border_left": [["single"]],
            "border_right": [["single"]],
            "border_first": [["single"]],
            "border_last": [["single"]],
            "text_convert": [[True]],
            "text_hyphenation": [[False]],
        }
    
    def _get_column_header_defaults(self) -> Dict[str, Any]:
        """Get defaults specific to column header components."""
        return {
            "border_left": ["single"],
            "border_right": ["single"],
            "border_top": ["single"],
            "border_bottom": [""],
            "cell_vertical_justification": ["bottom"],
            "text_convert": [True],
            "text_hyphenation": [False],
        }
    
    def _get_footnote_defaults(self, **kwargs: Any) -> Dict[str, Any]:
        """Get defaults specific to footnote components."""
        as_table = kwargs.get("as_table", True)
        border_defaults = DefaultsFactory.get_border_defaults(as_table)
        
        footnote_defaults = {
            "text_convert": [[False]],  # Disable text conversion for footnotes
        }
        
        footnote_defaults.update(border_defaults)
        return footnote_defaults
    
    def _get_source_defaults(self, **kwargs: Any) -> Dict[str, Any]:
        """Get defaults specific to source components."""
        as_table = kwargs.get("as_table", False)
        border_defaults = DefaultsFactory.get_border_defaults(as_table)
        
        source_defaults = {
            "text_justification": [["c"]],  # Center justification for sources
            "text_convert": [[False]],  # Disable text conversion for sources
        }
        
        source_defaults.update(border_defaults)
        return source_defaults


class TextBuilder(ComponentBuilder):
    """Builder for text-based RTF components (title, subline, headers, footers)."""
    
    def build_config(self, component_type: Enum, **kwargs: Any) -> Dict[str, Any]:
        """Build configuration for text-based components.
        
        Args:
            component_type: The text component type
            **kwargs: Component-specific configuration options
            
        Returns:
            Configuration dictionary with text defaults and overrides
        """
        # Import here to avoid circular imports
        from .component_factory import ComponentType
        
        # Start with base text defaults
        config = DefaultsFactory.get_text_defaults().copy()
        
        # Apply component-specific configurations
        if component_type == ComponentType.TITLE:
            config.update(self._get_title_defaults())
        elif component_type == ComponentType.SUBLINE:
            config.update(self._get_subline_defaults())
        elif component_type == ComponentType.PAGE_HEADER:
            config.update(self._get_page_header_defaults())
        elif component_type == ComponentType.PAGE_FOOTER:
            config.update(self._get_page_footer_defaults())
        
        # Apply user overrides
        config.update(kwargs)
        
        return config
    
    def _get_title_defaults(self) -> Dict[str, Any]:
        """Get defaults specific to title components."""
        return {
            "text_font_size": [12],
            "text_justification": ["c"],
            "text_space_before": [180.0],
            "text_space_after": [180.0],
            "text_convert": [True],
        }
    
    def _get_subline_defaults(self) -> Dict[str, Any]:
        """Get defaults specific to subline components."""
        return {
            "text_font_size": [9],
            "text_justification": ["l"],
            "text_convert": [True],
        }
    
    def _get_page_header_defaults(self) -> Dict[str, Any]:
        """Get defaults specific to page header components."""
        return {
            "text_font_size": [12],
            "text_justification": ["r"],
            "text_convert": [False],  # Preserve RTF field codes
        }
    
    def _get_page_footer_defaults(self) -> Dict[str, Any]:
        """Get defaults specific to page footer components."""
        return {
            "text_font_size": [12],
            "text_justification": ["c"],
            "text_convert": [False],  # Preserve RTF field codes
        }


class PageBuilder(ComponentBuilder):
    """Builder for page configuration components."""
    
    def build_config(self, component_type: Enum, **kwargs: Any) -> Dict[str, Any]:
        """Build configuration for page components.
        
        Args:
            component_type: The page component type (should be PAGE)
            **kwargs: Page-specific configuration options
            
        Returns:
            Configuration dictionary with page defaults and overrides
        """
        # Start with base page configuration
        config = {
            "orientation": "portrait",
            "width": None,  # Will be set based on orientation
            "height": None,  # Will be set based on orientation
            "margin": None,  # Will be set based on orientation
            "nrow": None,   # Will be set based on orientation
            "border_first": "double",
            "border_last": "double",
            "col_width": None,  # Will be calculated
            "use_color": False,
            "page_title_location": "all",
            "page_footnote_location": "all",
            "page_source_location": "all",
        }
        
        # Apply user overrides
        config.update(kwargs)
        
        return config


class ListBuilder(ComponentBuilder):
    """Builder for list-based RTF components (future feature)."""
    
    def build_config(self, component_type: Enum, **kwargs: Any) -> Dict[str, Any]:
        """Build configuration for list components.
        
        Args:
            component_type: The list component type
            **kwargs: Component-specific configuration options
            
        Returns:
            Configuration dictionary for list components
            
        Raises:
            NotImplementedError: List components not yet implemented
        """
        raise NotImplementedError("List component building not yet implemented")


class FigureBuilder(ComponentBuilder):
    """Builder for figure-based RTF components (future feature)."""
    
    def build_config(self, component_type: Enum, **kwargs: Any) -> Dict[str, Any]:
        """Build configuration for figure components.
        
        Args:
            component_type: The figure component type
            **kwargs: Component-specific configuration options
            
        Returns:
            Configuration dictionary for figure components
            
        Raises:
            NotImplementedError: Figure components not yet implemented
        """
        raise NotImplementedError("Figure component building not yet implemented")