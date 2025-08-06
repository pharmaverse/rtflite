"""
Text conversion engine for LaTeX to Unicode conversion.

This module implements the core conversion logic that processes text containing
LaTeX commands and converts them to Unicode characters. It focuses on
readability and maintainability rather than performance.
"""

import re
from typing import Pattern

from .symbols import LaTeXSymbolMapper


class TextConverter:
    """
    Converts LaTeX commands in text to Unicode characters.

    This class handles the parsing and conversion of LaTeX mathematical
    commands within text strings. It's designed for clarity and ease of
    maintenance rather than maximum performance.
    """

    def __init__(self):
        """Initialize the converter with symbol mapping."""
        self.symbol_mapper = LaTeXSymbolMapper()
        self._latex_pattern = self._create_latex_pattern()

    def _create_latex_pattern(self) -> Pattern[str]:
        """
        Create the regular expression pattern for matching LaTeX commands.

        This pattern matches:
        - Simple commands: \\alpha, \\beta, \\pm
        - Commands with braces: \\mathbb{R}, \\mathcal{L}
        - Commands with optional parameters (future extension)

        Returns:
            Compiled regular expression pattern
        """
        # Pattern explanation:
        # \\           - Literal backslash (escaped)
        # [a-zA-Z]+    - One or more letters (command name)
        # (?:          - Non-capturing group for optional braces
        #   \{[^}]*\}  - Opening brace, any content except }, closing brace
        # )?           - Make the brace group optional
        pattern = r"\\[a-zA-Z]+(?:\{[^}]*\})?"
        return re.compile(pattern)

    def convert_latex_to_unicode(self, text: str) -> str:
        """
        Convert all LaTeX commands in text to Unicode characters.

        This method processes the input text and replaces any LaTeX commands
        with their Unicode equivalents. Commands without mappings are left
        unchanged.

        Args:
            text: Input text potentially containing LaTeX commands

        Returns:
            Text with LaTeX commands converted to Unicode

        Examples:
            >>> converter = TextConverter()
            >>> converter.convert_latex_to_unicode("\\alpha + \\beta = \\gamma")
            "alpha + beta = gamma"

            >>> converter.convert_latex_to_unicode("Mean \\pm SD")
            "Mean +/- SD"

            >>> converter.convert_latex_to_unicode("Set \\mathbb{R}")
            "Set R"
        """
        if not text:
            return text

        def replace_latex_command(match) -> str:
            """Replace a single LaTeX command match with Unicode."""
            latex_command = match.group(0)
            return self._convert_single_command(latex_command)

        # Apply the conversion to all matches
        converted_text = self._latex_pattern.sub(replace_latex_command, text)
        return converted_text

    def _convert_single_command(self, latex_command: str) -> str:
        """
        Convert a single LaTeX command to Unicode.

        This method handles the conversion logic for individual commands,
        including special cases for commands with braces.

        Args:
            latex_command: The LaTeX command to convert

        Returns:
            Unicode character or original command if no mapping exists
        """
        # Handle commands with braces (e.g., \\mathbb{R})
        if "{" in latex_command and "}" in latex_command:
            return self._handle_braced_command(latex_command)

        # Handle simple commands (e.g., \\alpha, \\pm)
        return self.symbol_mapper.get_unicode_char(latex_command)

    def _handle_braced_command(self, latex_command: str) -> str:
        """
        Handle LaTeX commands that contain braces.

        Commands like \\mathbb{R} or \\mathcal{L} need special handling
        to extract the argument and look up the full command.

        Args:
            latex_command: LaTeX command with braces

        Returns:
            Unicode character or original command
        """
        # Try the full command as-is first (for exact matches)
        unicode_result = self.symbol_mapper.get_unicode_char(latex_command)
        if unicode_result != latex_command:  # Found a mapping
            return unicode_result

        # If no exact match, we could implement more sophisticated parsing
        # For now, return the original command
        return latex_command

    def get_conversion_statistics(self, text: str) -> dict:
        """
        Get statistics about LaTeX commands in the text.

        This is useful for debugging and understanding conversion coverage.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with conversion statistics
        """
        if not text:
            return {"total_commands": 0, "converted": 0, "unconverted": []}

        matches = self._latex_pattern.findall(text)
        converted = []
        unconverted = []

        for command in matches:
            if self.symbol_mapper.has_mapping(command):
                converted.append(command)
            else:
                unconverted.append(command)

        return {
            "total_commands": len(matches),
            "converted": len(converted),
            "unconverted": unconverted,
            "conversion_rate": len(converted) / len(matches) if matches else 0,
        }
