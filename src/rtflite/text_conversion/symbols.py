"""
LaTeX symbol mapping functionality.

This module provides a clean interface for mapping LaTeX commands to Unicode
characters. It organizes the symbols into logical categories for better
maintainability and readability.
"""

from typing import Dict

from ..dictionary.unicode_latex import latex_to_char, latex_to_unicode, unicode_to_int


class LaTeXSymbolMapper:
    """
    Manages LaTeX to Unicode symbol mappings.

    This class provides a clean interface for converting individual LaTeX
    commands to their Unicode equivalents. It encapsulates the symbol
    lookup logic and provides helpful methods for symbol management.
    """

    def __init__(self):
        """Initialize the symbol mapper with the standard LaTeX mappings."""
        self.latex_to_unicode = latex_to_unicode
        self.unicode_to_int = unicode_to_int
        self.latex_to_char = latex_to_char  # Optimized single-lookup mapping

    def get_unicode_char(self, latex_command: str) -> str:
        """
        Convert a single LaTeX command to its Unicode character.

        Args:
            latex_command: LaTeX command (e.g., "\\alpha", "\\pm", "\\mathbb{R}")

        Returns:
            Unicode character if the command is found, otherwise the original command

        Examples:
            >>> mapper = LaTeXSymbolMapper()
            >>> mapper.get_unicode_char("\\alpha")
            "alpha"
            >>> mapper.get_unicode_char("\\pm")
            "+/-"
            >>> mapper.get_unicode_char("\\unknown")
            "\\unknown"
        """
        # Optimized: single dictionary lookup instead of double lookup
        return self.latex_to_char.get(latex_command, latex_command)

    def has_mapping(self, latex_command: str) -> bool:
        """
        Check if a LaTeX command has a Unicode mapping.

        Args:
            latex_command: LaTeX command to check

        Returns:
            True if the command has a mapping, False otherwise
        """
        # Optimized: use the single-lookup dictionary for consistency
        return latex_command in self.latex_to_char

    def get_all_supported_commands(self) -> list[str]:
        """
        Get a list of all supported LaTeX commands.

        Returns:
            List of all LaTeX commands that can be converted
        """
        # Optimized: use the single-lookup dictionary
        return list(self.latex_to_char.keys())

    def get_commands_by_category(self) -> Dict[str, list[str]]:
        """
        Organize LaTeX commands by category for better understanding.

        Returns:
            Dictionary mapping categories to lists of commands
        """
        # Optimized categorization with pre-defined sets for O(1) lookup
        greek_letters = {
            "\\alpha",
            "\\beta",
            "\\gamma",
            "\\delta",
            "\\epsilon",
            "\\varepsilon",
            "\\zeta",
            "\\eta",
            "\\theta",
            "\\vartheta",
            "\\iota",
            "\\kappa",
            "\\varkappa",
            "\\lambda",
            "\\mu",
            "\\nu",
            "\\xi",
            "\\pi",
            "\\varpi",
            "\\rho",
            "\\varrho",
            "\\sigma",
            "\\varsigma",
            "\\tau",
            "\\upsilon",
            "\\phi",
            "\\varphi",
            "\\chi",
            "\\psi",
            "\\omega",
            "\\Gamma",
            "\\Delta",
            "\\Theta",
            "\\Lambda",
            "\\Xi",
            "\\Pi",
            "\\Sigma",
            "\\Upsilon",
            "\\Phi",
            "\\Psi",
            "\\Omega",
        }

        operators = {
            "\\pm",
            "\\mp",
            "\\times",
            "\\div",
            "\\cdot",
            "\\sum",
            "\\prod",
            "\\int",
            "\\oint",
            "\\partial",
            "\\nabla",
            "\\infty",
            "\\propto",
            "\\approx",
            "\\equiv",
            "\\neq",
            "\\leq",
            "\\geq",
            "\\ll",
            "\\gg",
            "\\subset",
            "\\supset",
            "\\in",
            "\\notin",
            "\\cup",
            "\\cap",
            "\\setminus",
            "\\oplus",
            "\\otimes",
        }

        accents = {
            "\\hat",
            "\\bar",
            "\\dot",
            "\\ddot",
            "\\dddot",
            "\\ddddot",
            "\\tilde",
            "\\grave",
            "\\acute",
            "\\check",
            "\\breve",
            "\\vec",
            "\\overline",
            "\\underline",
        }

        categories = {
            "Greek Letters": [],
            "Mathematical Operators": [],
            "Blackboard Bold": [],
            "Accents": [],
            "Other": [],
        }

        # Optimized: use single dictionary and set lookups
        for command in self.latex_to_char.keys():
            if command in greek_letters:
                categories["Greek Letters"].append(command)
            elif command in operators:
                categories["Mathematical Operators"].append(command)
            elif "\\mathbb{" in command:
                categories["Blackboard Bold"].append(command)
            elif command in accents:
                categories["Accents"].append(command)
            else:
                categories["Other"].append(command)

        return categories
