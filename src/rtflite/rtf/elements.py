"""RTF element classes representing different content types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import polars as pl


class RTFElement(ABC):
    """Abstract base class for RTF content elements."""

    @abstractmethod
    def to_rtf(self) -> str:
        """Generate RTF code for this element.

        Returns:
            RTF string representation
        """
        pass


@dataclass
class RTFTable(RTFElement):
    """RTF table element containing tabular data and formatting."""

    data: pl.DataFrame
    attributes: "TableAttributes"
    element_type: str = "table"  # 'table', 'header', 'footnote', 'source'

    def to_rtf(self) -> str:
        """Generate RTF code for table element.

        Returns:
            RTF string representation of the table
        """
        # Delegate to attributes encoding for now
        # This maintains backward compatibility while we refactor
        return self.attributes._encode(df=self.data)


@dataclass
class RTFText(RTFElement):
    """RTF text element containing formatted text content."""

    text: Optional[Union[str, List[str]]]
    attributes: "TextAttributes"
    element_type: str = "text"  # 'title', 'subline', 'header', 'footer'

    def to_rtf(self) -> str:
        """Generate RTF code for text element.

        Returns:
            RTF string representation of the text
        """
        if self.text is None:
            return ""

        # Handle text conversion from list to string if needed
        if isinstance(self.text, list):
            text_content = "\\line ".join(self.text)
        else:
            text_content = self.text

        # Delegate to attributes encoding for now
        # This maintains backward compatibility while we refactor
        return self.attributes._encode(text=text_content)


@dataclass
class RTFPage(RTFElement):
    """RTF page element containing page settings and layout."""

    settings: "RTFPage"
    element_type: str = "page"

    def to_rtf(self) -> str:
        """Generate RTF code for page settings.

        Returns:
            RTF string representation of page settings
        """
        # This would include page size, margins, orientation, etc.
        # For now, delegate to existing page encoding methods
        return ""  # Placeholder


@dataclass
class RTFList(RTFElement):
    """RTF list element for future list support."""

    items: List[Any]
    attributes: Dict[str, Any]
    element_type: str = "list"

    def to_rtf(self) -> str:
        """Generate RTF code for list element.

        Returns:
            RTF string representation of the list

        Raises:
            NotImplementedError: List elements not yet implemented
        """
        raise NotImplementedError("RTF list elements not yet implemented")


@dataclass
class RTFFigure(RTFElement):
    """RTF figure element for future figure support."""

    content: Any
    attributes: Dict[str, Any]
    element_type: str = "figure"

    def to_rtf(self) -> str:
        """Generate RTF code for figure element.

        Returns:
            RTF string representation of the figure

        Raises:
            NotImplementedError: Figure elements not yet implemented
        """
        raise NotImplementedError("RTF figure elements not yet implemented")
