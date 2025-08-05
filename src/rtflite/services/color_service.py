"""Color management service for RTF documents.

This service provides comprehensive color validation, lookup, and RTF generation
capabilities using the full 657-color table from r2rtf.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from rtflite.dictionary.color_table import (
    color_table,
    name_to_rgb,
    name_to_rtf,
    name_to_type,
)


class ColorValidationError(ValueError):
    """Raised when a color validation fails."""

    pass


class ColorService:
    """Service for color validation, lookup, and RTF generation operations."""

    def __init__(self):
        """Initialize the color service with the comprehensive color table."""
        self._color_table = color_table
        self._name_to_type = name_to_type
        self._name_to_rgb = name_to_rgb
        self._name_to_rtf = name_to_rtf
        self._current_document_colors = (
            None  # Context for current document being encoded
        )

    def validate_color(self, color: str) -> bool:
        """Validate if a color name exists in the color table.

        Args:
            color: Color name to validate

        Returns:
            True if color exists, False otherwise
        """
        return color in self._name_to_type

    def get_color_index(self, color: str) -> int:
        """Get the RTF color table index for a color name.

        Args:
            color: Color name to look up

        Returns:
            Color index (1-based) for RTF color table

        Raises:
            ColorValidationError: If color name is invalid
        """
        if not self.validate_color(color):
            suggestions = self.get_color_suggestions(color)
            suggestion_text = (
                f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
            )
            raise ColorValidationError(
                f"Invalid color name '{color}'. Must be one of 657 supported colors.{suggestion_text}"
            )

        return self._name_to_type[color]

    def get_color_rgb(self, color: str) -> Tuple[int, int, int]:
        """Get RGB values for a color name.

        Args:
            color: Color name to look up

        Returns:
            RGB tuple (red, green, blue) with values 0-255

        Raises:
            ColorValidationError: If color name is invalid
        """
        if not self.validate_color(color):
            raise ColorValidationError(f"Invalid color name '{color}'")

        return self._name_to_rgb[color]

    def get_color_rtf_code(self, color: str) -> str:
        """Get RTF color definition code for a color name.

        Args:
            color: Color name to look up

        Returns:
            RTF color definition (e.g., "\\red255\\green0\\blue0;")

        Raises:
            ColorValidationError: If color name is invalid
        """
        if not self.validate_color(color):
            raise ColorValidationError(f"Invalid color name '{color}'")

        return self._name_to_rtf[color]

    def get_color_suggestions(
        self, partial_color: str, max_suggestions: int = 5
    ) -> List[str]:
        """Get color name suggestions for partial matches.

        Args:
            partial_color: Partial or misspelled color name
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested color names
        """
        partial_lower = partial_color.lower()

        # Exact match first
        if partial_lower in self._name_to_type:
            return [partial_lower]

        # Find colors that contain the partial string
        suggestions = []
        for color_name in self._name_to_type.keys():
            if partial_lower in color_name.lower():
                suggestions.append(color_name)
                if len(suggestions) >= max_suggestions:
                    break

        # If no substring matches, find colors that start with same letter
        if not suggestions:
            first_char = partial_lower[0] if partial_lower else ""
            for color_name in self._name_to_type.keys():
                if color_name.lower().startswith(first_char):
                    suggestions.append(color_name)
                    if len(suggestions) >= max_suggestions:
                        break

        return suggestions

    def validate_color_list(
        self, colors: Union[str, List[str], Tuple[str, ...]]
    ) -> List[str]:
        """Validate a list of colors, converting single color to list.

        Args:
            colors: Single color name or list/tuple of color names

        Returns:
            Validated list of color names

        Raises:
            ColorValidationError: If any color name is invalid
        """
        if isinstance(colors, str):
            colors = [colors]
        elif isinstance(colors, tuple):
            colors = list(colors)
        elif not isinstance(colors, list):
            raise ColorValidationError(
                f"Colors must be string, list, or tuple, got {type(colors)}"
            )

        validated_colors = []
        for i, color in enumerate(colors):
            if not isinstance(color, str):
                raise ColorValidationError(
                    f"Color at index {i} must be string, got {type(color)}"
                )

            if not self.validate_color(color):
                suggestions = self.get_color_suggestions(color)
                suggestion_text = (
                    f" Did you mean: {', '.join(suggestions[:3])}?"
                    if suggestions
                    else ""
                )
                raise ColorValidationError(
                    f"Invalid color name '{color}' at index {i}.{suggestion_text}"
                )

            validated_colors.append(color)

        return validated_colors

    def needs_color_table(self, used_colors: Optional[List[str]] = None) -> bool:
        """Check if a color table is needed based on used colors.

        Args:
            used_colors: List of color names used in document

        Returns:
            True if color table is needed, False otherwise
        """
        if not used_colors:
            return False

        # Filter out empty strings and check for non-default colors
        significant_colors = [
            color for color in used_colors if color and color != "black"
        ]
        return len(significant_colors) > 0

    def generate_rtf_color_table(self, used_colors: Optional[List[str]] = None) -> str:
        """Generate RTF color table definition for used colors.

        Args:
            used_colors: List of color names used in document. If None, includes all 657 colors.

        Returns:
            RTF color table definition string, or empty string if no color table needed
        """
        # Check if color table is actually needed
        if used_colors is not None and not self.needs_color_table(used_colors):
            return ""

        if used_colors is None:
            # Include all colors in full r2rtf format
            colors_to_include = list(self._name_to_type.keys())
            colors_to_include.sort(key=lambda x: self._name_to_type[x])

            # Generate full R2RTF color table
            rtf_parts = ["{\\colortbl\n;"]  # Start with empty color (index 0)

            for color_name in colors_to_include:
                rtf_code = self._name_to_rtf[color_name]
                rtf_parts.append(f"\n{rtf_code}")

            rtf_parts.append("\n}")
            return "".join(rtf_parts)

        else:
            # Create dense sequential color table for used colors (R2RTF style)
            filtered_colors = [
                color for color in used_colors if color and color != "black"
            ]
            if not filtered_colors:
                return ""

            validated_colors = self.validate_color_list(filtered_colors)

            # Sort colors by their original r2rtf index for consistent ordering
            sorted_colors = sorted(
                validated_colors, key=lambda x: self._name_to_type[x]
            )

            # Create dense color table with only used colors (R2RTF format)
            rtf_parts = ["{\\colortbl;"]  # Start with empty color (index 0)

            # Add each used color sequentially
            for color_name in sorted_colors:
                rtf_code = self._name_to_rtf[color_name]
                rtf_parts.append(f"\n{rtf_code}")

            rtf_parts.append("\n}")
            return "".join(rtf_parts)

    def get_rtf_color_index(
        self, color: str, used_colors: Optional[List[str]] = None
    ) -> int:
        """Get the RTF color table index for a color in the context of a specific document.

        Args:
            color: Color name to look up
            used_colors: List of colors used in the document (determines table structure)

        Returns:
            Sequential color index in the RTF table (1-based for dense table, original index for full table)
        """
        if not color or color == "black":
            return 0  # Default/black color

        # Use document context if available and no explicit used_colors provided
        if used_colors is None and self._current_document_colors is not None:
            used_colors = self._current_document_colors

        if used_colors is None:
            # Use original r2rtf index if no specific color list (full table)
            return self.get_color_index(color)

        # For document-specific color tables, use sequential indices in dense table
        filtered_colors = [c for c in used_colors if c and c != "black"]
        if not filtered_colors:
            return 0

        validated_colors = self.validate_color_list(filtered_colors)
        sorted_colors = sorted(validated_colors, key=lambda x: self._name_to_type[x])

        try:
            # Return 1-based sequential index in the dense table
            return sorted_colors.index(color) + 1
        except ValueError:
            return 0

    def get_all_color_names(self) -> List[str]:
        """Get list of all available color names.

        Returns:
            Sorted list of all 657 color names
        """
        return sorted(self._name_to_type.keys())

    def get_color_count(self) -> int:
        """Get total number of available colors.

        Returns:
            Total count of available colors (657)
        """
        return len(self._name_to_type)

    def collect_document_colors(self, document) -> List[str]:
        """Collect all colors used in a document.

        Args:
            document: RTF document object

        Returns:
            List of unique color names used in the document
        """
        used_colors = set()

        # Helper function to extract colors from nested lists
        def extract_colors_from_attribute(attr):
            if attr is None:
                return
            if isinstance(attr, str):
                if attr:  # Skip empty strings
                    used_colors.add(attr)
            elif isinstance(attr, (list, tuple)):
                for item in attr:
                    extract_colors_from_attribute(item)

        # Collect colors from RTF body
        if document.rtf_body:
            bodies = (
                [document.rtf_body]
                if not isinstance(document.rtf_body, list)
                else document.rtf_body
            )
            for body in bodies:
                extract_colors_from_attribute(body.text_color)
                extract_colors_from_attribute(body.text_background_color)
                extract_colors_from_attribute(body.border_color_left)
                extract_colors_from_attribute(body.border_color_right)
                extract_colors_from_attribute(body.border_color_top)
                extract_colors_from_attribute(body.border_color_bottom)
                extract_colors_from_attribute(body.border_color_first)
                extract_colors_from_attribute(body.border_color_last)

        # Collect colors from other components
        components = [
            document.rtf_title,
            document.rtf_subline,
            document.rtf_footnote,
            document.rtf_source,
            document.rtf_page_header,
            document.rtf_page_footer,
        ]

        for component in components:
            if component:
                extract_colors_from_attribute(getattr(component, "text_color", None))
                extract_colors_from_attribute(
                    getattr(component, "text_background_color", None)
                )

        # Collect colors from column headers
        if document.rtf_column_header:
            headers = document.rtf_column_header
            if isinstance(headers[0], list):
                # Nested format
                for header_section in headers:
                    for header in header_section:
                        if header:
                            extract_colors_from_attribute(
                                getattr(header, "text_color", None)
                            )
                            extract_colors_from_attribute(
                                getattr(header, "text_background_color", None)
                            )
            else:
                # Flat format
                for header in headers:
                    if header:
                        extract_colors_from_attribute(
                            getattr(header, "text_color", None)
                        )
                        extract_colors_from_attribute(
                            getattr(header, "text_background_color", None)
                        )

        return list(used_colors)

    def set_document_context(
        self, document=None, used_colors: Optional[List[str]] = None
    ):
        """Set the document context for color index resolution.

        Args:
            document: RTF document to analyze for colors
            used_colors: Explicit list of colors used in document
        """
        if document is not None and used_colors is None:
            used_colors = self.collect_document_colors(document)
        self._current_document_colors = used_colors

    def clear_document_context(self):
        """Clear the document context."""
        self._current_document_colors = None

    def get_color_info(self, color: str) -> Dict[str, Any]:
        """Get comprehensive information about a color.

        Args:
            color: Color name to look up

        Returns:
            Dictionary with color information (name, index, rgb, rtf_code)

        Raises:
            ColorValidationError: If color name is invalid
        """
        if not self.validate_color(color):
            raise ColorValidationError(f"Invalid color name '{color}'")

        return {
            "name": color,
            "index": self._name_to_type[color],
            "rgb": self._name_to_rgb[color],
            "rtf_code": self._name_to_rtf[color],
        }


# Global color service instance
color_service = ColorService()


# Convenience functions for backward compatibility
def validate_color(color: str) -> bool:
    """Validate if a color name exists in the color table."""
    return color_service.validate_color(color)


def get_color_index(color: str) -> int:
    """Get the RTF color table index for a color name."""
    return color_service.get_color_index(color)


def get_color_suggestions(partial_color: str, max_suggestions: int = 5) -> List[str]:
    """Get color name suggestions for partial matches."""
    return color_service.get_color_suggestions(partial_color, max_suggestions)
