"""Text conversion utilities for LaTeX to Unicode mapping."""

import re

from .dictionary.unicode_latex import latex_to_unicode, unicode_to_int


def latex_to_unicode_char(latex_command: str) -> str:
    """Convert a single LaTeX command to Unicode character.

    Args:
        latex_command: LaTeX command (e.g., "\\alpha", "\\pm")

    Returns:
        Unicode character if found, otherwise the original LaTeX command
    """
    if latex_command in latex_to_unicode:
        unicode_hex = latex_to_unicode[latex_command]
        unicode_int = unicode_to_int[unicode_hex]
        return chr(unicode_int)
    return latex_command


def convert_latex_to_unicode(text: str) -> str:
    """Convert LaTeX commands in text to Unicode characters.

    This function finds LaTeX commands (starting with backslash) and converts
    them to their Unicode equivalents based on the r2rtf mapping.

    Args:
        text: Input text potentially containing LaTeX commands

    Returns:
        Text with LaTeX commands converted to Unicode characters
    """
    if not text:
        return text

    # Pattern to match LaTeX commands: \command or \command{}
    # This matches:
    # - Backslash followed by letters (e.g., \alpha, \beta)
    # - Optionally followed by {} (e.g., \alpha{}, \mathbb{R})
    latex_pattern = r"\\[a-zA-Z]+(?:\{[^}]*\})?"

    def replace_latex(match):
        latex_cmd = match.group(0)

        # Handle commands with braces like \mathbb{R}
        if "{" in latex_cmd and "}" in latex_cmd:
            # For now, try the full command as-is
            return latex_to_unicode_char(latex_cmd)
        else:
            # Simple command like \alpha
            return latex_to_unicode_char(latex_cmd)

    # Replace all LaTeX commands with their Unicode equivalents
    converted_text = re.sub(latex_pattern, replace_latex, text)

    return converted_text


def text_convert(text: str | None, enable_conversion: bool = True) -> str | None:
    """Main text conversion function matching r2rtf behavior.

    Args:
        text: Input text
        enable_conversion: Whether to enable LaTeX to Unicode conversion

    Returns:
        Converted text
    """
    if not enable_conversion or not text:
        return text

    return convert_latex_to_unicode(text)
