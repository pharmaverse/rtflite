"""
Text conversion service for the RTF encoding pipeline.

This service provides a clean interface for text conversion operations
within the RTF document generation process. It integrates the text
conversion functionality with the broader service architecture.
"""

from typing import List, Union

from ..text_conversion import LaTeXSymbolMapper, TextConverter


class TextConversionService:
    """
    Service for handling text conversion operations in RTF documents.

    This service provides a unified interface for text conversion that
    can be used throughout the RTF encoding pipeline. It handles the
    conversion of LaTeX commands to Unicode characters with proper
    error handling and logging capabilities.
    """

    def __init__(self):
        """Initialize the text conversion service."""
        self.converter = TextConverter()
        self.symbol_mapper = LaTeXSymbolMapper()

    def convert_text_content(
        self, text: Union[str, List[str], None], enable_conversion: bool = True
    ) -> Union[str, List[str], None]:
        """
        Convert text content with LaTeX commands to Unicode.

        This method handles various text input formats commonly found
        in RTF components and applies conversion consistently.

        Args:
            text: Text content to convert (string, list of strings, or None)
            enable_conversion: Whether to enable LaTeX to Unicode conversion

        Returns:
            Converted text in the same format as input

        Examples:
            >>> service = TextConversionService()
            >>> service.convert_text_content("\\alpha test", True)
            "\\u03b1 test"

            >>> service.convert_text_content(["\\alpha", "\\beta"], True)
            ["\\u03b1", "\\u03b2"]
        """
        if not enable_conversion or text is None:
            return text

        if isinstance(text, str):
            return self._convert_single_text(text)
        elif isinstance(text, list):
            return self._convert_text_list(text)
        else:
            # Handle other types by converting to string first
            return self._convert_single_text(str(text))

    def _convert_single_text(self, text: str) -> str:
        """
        Convert a single text string.

        Args:
            text: Text string to convert

        Returns:
            Converted text string
        """
        if not text:
            return text

        try:
            return self.converter.convert_latex_to_unicode(text)
        except Exception as e:
            # Log the error but don't fail the conversion
            # In a production environment, this would use proper logging
            print(f"Warning: Text conversion failed for '{text}': {e}")
            return text

    def _convert_text_list(self, text_list: List[str]) -> List[str]:
        """
        Convert a list of text strings.

        Args:
            text_list: List of text strings to convert

        Returns:
            List of converted text strings
        """
        return [self._convert_single_text(item) for item in text_list]

    def get_supported_symbols(self) -> List[str]:
        """
        Get a list of all supported LaTeX symbols.

        Returns:
            List of supported LaTeX commands
        """
        return self.symbol_mapper.get_all_supported_commands()

    def get_symbol_categories(self) -> dict:
        """
        Get LaTeX symbols organized by category.

        Returns:
            Dictionary mapping categories to symbol lists
        """
        return self.symbol_mapper.get_commands_by_category()

    def validate_latex_commands(self, text: str) -> dict:
        """
        Validate LaTeX commands in text and provide feedback.

        This method analyzes text for LaTeX commands and reports
        which ones will be converted and which ones are unsupported.

        Args:
            text: Text to validate

        Returns:
            Dictionary with validation results
        """
        if not text:
            return {
                "valid_commands": [],
                "invalid_commands": [],
                "validation_status": "empty_text",
            }

        stats = self.converter.get_conversion_statistics(text)

        # Extract valid commands from the stats (need to get the actual converted commands)
        import re

        latex_pattern = re.compile(r"\\[a-zA-Z]+(?:\{[^}]*\})?")
        all_commands = latex_pattern.findall(text)

        valid_commands = []
        for cmd in all_commands:
            if self.symbol_mapper.has_mapping(cmd):
                valid_commands.append(cmd)

        return {
            "valid_commands": valid_commands,
            "invalid_commands": stats.get("unconverted", []),
            "total_commands": stats.get("total_commands", 0),
            "conversion_rate": stats.get("conversion_rate", 0),
            "validation_status": "analyzed",
        }

    def convert_with_validation(
        self, text: str, enable_conversion: bool = True
    ) -> dict:
        """
        Convert text and return both result and validation information.

        This method provides comprehensive information about the conversion
        process, useful for debugging and quality assurance.

        Args:
            text: Text to convert
            enable_conversion: Whether to enable conversion

        Returns:
            Dictionary with converted text and validation info
        """
        if not enable_conversion:
            return {
                "original_text": text,
                "converted_text": text,
                "conversion_enabled": False,
                "validation": {"status": "conversion_disabled"},
            }

        validation = self.validate_latex_commands(text)
        converted_text = self.convert_text_content(text, enable_conversion)

        return {
            "original_text": text,
            "converted_text": converted_text,
            "conversion_enabled": True,
            "validation": validation,
            "conversion_applied": converted_text != text,
        }
