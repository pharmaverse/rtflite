"""RTF constants and magic numbers consolidated in a single source of truth.

This module eliminates magic numbers scattered throughout the codebase and provides
clear documentation for all RTF-related constants used in the library.
"""

from typing import Dict, Final


class RTFConstants:
    """Core RTF constants for measurements, formatting, and control codes."""

    # === Measurement Constants ===
    TWIPS_PER_INCH: Final[int] = 1440
    """Number of twips in one inch. RTF uses twips as the base unit."""

    POINTS_PER_INCH: Final[int] = 72
    """Number of points in one inch."""

    LINE_SPACING_FACTOR: Final[int] = 240
    """Factor used for line spacing calculations in RTF."""

    # === Default Dimensions ===
    DEFAULT_BORDER_WIDTH: Final[int] = 15
    """Default border width in twips."""

    DEFAULT_CELL_HEIGHT: Final[float] = 0.15
    """Default cell height in inches."""

    DEFAULT_SPACE_BEFORE: Final[int] = 15
    """Default space before paragraph in points."""

    DEFAULT_SPACE_AFTER: Final[int] = 15
    """Default space after paragraph in points."""

    # === Font Sizes ===
    DEFAULT_FONT_SIZE: Final[int] = 9
    """Default font size in points."""

    # === RTF Control Codes ===
    class Control:
        """RTF control word constants."""

        # Text formatting
        SUPER: Final[str] = "\\super "
        SUB: Final[str] = "\\sub "
        LINE_BREAK: Final[str] = "\\line "
        PAGE_BREAK: Final[str] = "\\page"

        # Document structure
        RTF_HEADER: Final[str] = "{\\rtf1\\ansi"
        FONT_TABLE_START: Final[str] = "{\\fonttbl"
        COLOR_TABLE_START: Final[str] = "{\\colortbl"

        # Page formatting
        PAGE_NUMBER: Final[str] = "\\chpgn "
        TOTAL_PAGES: Final[str] = "\\totalpage "
        PAGE_FIELD: Final[str] = "{\\field{\\*\\fldinst NUMPAGES }} "

        # Paragraph formatting
        PARAGRAPH_START: Final[str] = "\\pard"
        CELL_END: Final[str] = "\\cell"
        ROW_END: Final[str] = "\\row"

    # === Format Codes ===
    FORMAT_CODES: Final[Dict[str, str]] = {
        "": "",
        "b": "\\b",  # Bold
        "i": "\\i",  # Italic
        "u": "\\ul",  # Underline
        "s": "\\strike",  # Strikethrough
        "^": "\\super",  # Superscript
        "_": "\\sub",  # Subscript
    }

    # === Text Justification Codes ===
    TEXT_JUSTIFICATION_CODES: Final[Dict[str, str]] = {
        "": "",
        "l": "\\ql",  # Left
        "c": "\\qc",  # Center
        "r": "\\qr",  # Right
        "d": "\\qd",  # Distributed
        "j": "\\qj",  # Justified
    }

    # === Row Justification Codes ===
    ROW_JUSTIFICATION_CODES: Final[Dict[str, str]] = {
        "": "",
        "l": "\\trql",  # Left
        "c": "\\trqc",  # Center
        "r": "\\trqr",  # Right
    }

    # === Border Style Codes ===
    BORDER_CODES: Final[Dict[str, str]] = {
        "single": "\\brdrs",
        "double": "\\brdrdb",
        "thick": "\\brdrth",
        "dotted": "\\brdrdot",
        "dashed": "\\brdrdash",
        "small-dash": "\\brdrdashsm",
        "dash-dotted": "\\brdrdashd",
        "dash-dot-dotted": "\\brdrdashdd",
        "triple": "\\brdrtriple",
        "wavy": "\\brdrwavy",
        "double-wavy": "\\brdrwavydb",
        "striped": "\\brdrengrave",
        "embossed": "\\brdremboss",
        "engraved": "\\brdrengrave",
        "frame": "\\brdrframe",
        "": "",  # No border
    }

    # === Vertical Alignment Codes ===
    VERTICAL_ALIGNMENT_CODES: Final[Dict[str, str]] = {
        "top": "\\clvertalt",
        "center": "\\clvertalc",
        "bottom": "\\clvertalb",
        "merge_first": "\\clvertalc\\clvmgf",
        "merge_rest": "\\clvertalc\\clvmrg",
        "": "",
    }

    # === Character Conversion Mapping ===
    RTF_CHAR_MAPPING: Final[Dict[str, str]] = {
        "^": "\\super ",
        "_": "\\sub ",
        ">=": "\\geq ",
        "<=": "\\leq ",
        "\n": "\\line ",
        "\\pagenumber": "\\chpgn ",
        "\\totalpage": "\\totalpage ",
        "\\pagefield": "{\\field{\\*\\fldinst NUMPAGES }} ",
    }


class RTFDefaults:
    """Default values for RTF document configuration."""

    # === Page Settings ===
    ORIENTATION: Final[str] = "portrait"
    BORDER_FIRST: Final[str] = "double"
    BORDER_LAST: Final[str] = "double"
    USE_COLOR: Final[bool] = False

    # === Text Settings ===
    TEXT_FONT: Final[int] = 1
    TEXT_ALIGNMENT: Final[str] = "l"  # Left
    TEXT_HYPHENATION: Final[bool] = True
    TEXT_CONVERT: Final[bool] = True  # Enable LaTeX to Unicode conversion

    # === Table Settings ===
    TABLE_ALIGNMENT: Final[str] = "c"  # Center

    # === Color Defaults ===
    @classmethod
    def get_default_colors(cls) -> Dict[str, str]:
        """Get all colors from the comprehensive color table."""
        from rtflite.dictionary.color_table import name_to_rtf

        return name_to_rtf

    # Provide DEFAULT_COLORS as a cached property for backward compatibility
    _default_colors_cache = None

    @classmethod
    def DEFAULT_COLORS(cls) -> Dict[str, str]:
        """Get all colors from the comprehensive color table (cached)."""
        if cls._default_colors_cache is None:
            cls._default_colors_cache = cls.get_default_colors()
        return cls._default_colors_cache


class RTFMeasurements:
    """Utility class for RTF measurement conversions."""

    @staticmethod
    def inch_to_twip(inches: float) -> int:
        """Convert inches to twips.

        Args:
            inches: Length in inches

        Returns:
            Length in twips (1/1440 of an inch)
        """
        return round(inches * RTFConstants.TWIPS_PER_INCH)

    @staticmethod
    def twip_to_inch(twips: int) -> float:
        """Convert twips to inches.

        Args:
            twips: Length in twips

        Returns:
            Length in inches
        """
        return twips / RTFConstants.TWIPS_PER_INCH

    @staticmethod
    def point_to_halfpoint(points: float) -> int:
        """Convert points to half-points for RTF font sizes.

        Args:
            points: Font size in points

        Returns:
            Font size in half-points (RTF format)
        """
        return int(points * 2)
