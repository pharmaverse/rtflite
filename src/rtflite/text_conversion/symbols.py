"""
LaTeX symbol mapping functionality.

This module provides a clean interface for mapping LaTeX commands to Unicode
characters. It organizes the symbols into logical categories for better
maintainability and readability.
"""

from typing import Dict, Optional
from ..dictionary.unicode_latex import latex_to_unicode, unicode_to_int


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
            "α"
            >>> mapper.get_unicode_char("\\pm") 
            "±"
            >>> mapper.get_unicode_char("\\unknown")
            "\\unknown"
        """
        if latex_command in self.latex_to_unicode:
            unicode_hex = self.latex_to_unicode[latex_command]
            unicode_int = self.unicode_to_int[unicode_hex]
            return chr(unicode_int)
        return latex_command
    
    def has_mapping(self, latex_command: str) -> bool:
        """
        Check if a LaTeX command has a Unicode mapping.
        
        Args:
            latex_command: LaTeX command to check
            
        Returns:
            True if the command has a mapping, False otherwise
        """
        return latex_command in self.latex_to_unicode
    
    def get_all_supported_commands(self) -> list[str]:
        """
        Get a list of all supported LaTeX commands.
        
        Returns:
            List of all LaTeX commands that can be converted
        """
        return list(self.latex_to_unicode.keys())
    
    def get_commands_by_category(self) -> Dict[str, list[str]]:
        """
        Organize LaTeX commands by category for better understanding.
        
        Returns:
            Dictionary mapping categories to lists of commands
        """
        categories = {
            "Greek Letters": [],
            "Mathematical Operators": [], 
            "Mathematical Symbols": [],
            "Blackboard Bold": [],
            "Accents": [],
            "Other": []
        }
        
        for command in self.latex_to_unicode.keys():
            if self._is_greek_letter(command):
                categories["Greek Letters"].append(command)
            elif self._is_mathematical_operator(command):
                categories["Mathematical Operators"].append(command)
            elif self._is_blackboard_bold(command):
                categories["Blackboard Bold"].append(command)
            elif self._is_accent(command):
                categories["Accents"].append(command)
            elif self._is_mathematical_symbol(command):
                categories["Mathematical Symbols"].append(command)
            else:
                categories["Other"].append(command)
        
        return categories
    
    def _is_greek_letter(self, command: str) -> bool:
        """Check if command is a Greek letter."""
        greek_letters = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", 
                        "eta", "theta", "iota", "kappa", "lambda", "mu", "nu", 
                        "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", 
                        "chi", "psi", "omega"]
        command_name = command.lstrip("\\").lower()
        return any(greek in command_name for greek in greek_letters)
    
    def _is_mathematical_operator(self, command: str) -> bool:
        """Check if command is a mathematical operator."""
        operators = ["pm", "mp", "times", "div", "cdot", "sum", "prod", "int",
                    "oint", "partial", "nabla", "infty", "propto", "approx",
                    "equiv", "neq", "leq", "geq", "ll", "gg", "subset", "supset"]
        command_name = command.lstrip("\\")
        return command_name in operators
    
    def _is_blackboard_bold(self, command: str) -> bool:
        """Check if command is blackboard bold."""
        return "mathbb" in command
    
    def _is_accent(self, command: str) -> bool:
        """Check if command is an accent."""
        accents = ["hat", "bar", "dot", "ddot", "tilde", "grave", "acute", 
                  "check", "breve", "vec"]
        command_name = command.lstrip("\\")
        return command_name in accents
    
    def _is_mathematical_symbol(self, command: str) -> bool:
        """Check if command is a general mathematical symbol."""
        # This catches remaining mathematical symbols not in other categories
        return True  # Default category for mathematical content