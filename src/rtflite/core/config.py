"""Configuration architecture for RTF document generation.

This module provides a centralized configuration system that replaces scattered
settings throughout the codebase with a hierarchical, type-safe approach.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .constants import RTFConstants, RTFDefaults


@dataclass(frozen=True)
class PageConfiguration:
    """Configuration for page layout and dimensions."""

    orientation: str = RTFDefaults.ORIENTATION
    width: Optional[float] = None  # inches
    height: Optional[float] = None  # inches
    margins: Optional[Tuple[float, float, float, float, float, float]] = (
        None  # left, right, top, bottom, header, footer
    )

    @classmethod
    def create_default(cls) -> "PageConfiguration":
        """Create default page configuration."""
        return cls()

    @classmethod
    def create_landscape(cls) -> "PageConfiguration":
        """Create landscape page configuration."""
        return cls(orientation="landscape")


@dataclass(frozen=True)
class FontConfiguration:
    """Configuration for font settings."""

    default_font: int = RTFDefaults.TEXT_FONT
    default_size: int = RTFConstants.DEFAULT_FONT_SIZE
    charset: int = 1  # Default charset for r2rtf compatibility

    @classmethod
    def create_default(cls) -> "FontConfiguration":
        """Create default font configuration."""
        return cls()


@dataclass(frozen=True)
class ColorConfiguration:
    """Configuration for color settings."""

    use_color: bool = RTFDefaults.USE_COLOR
    color_table: Dict[str, str] = None

    def __post_init__(self):
        if self.color_table is None:
            object.__setattr__(self, "color_table", RTFDefaults.DEFAULT_COLORS())

    @classmethod
    def create_default(cls) -> "ColorConfiguration":
        """Create default color configuration."""
        return cls()


@dataclass(frozen=True)
class BorderConfiguration:
    """Configuration for border settings."""

    default_style: str = "single"
    default_width: int = RTFConstants.DEFAULT_BORDER_WIDTH
    first_row_style: str = RTFDefaults.BORDER_FIRST
    last_row_style: str = RTFDefaults.BORDER_LAST

    @classmethod
    def create_default(cls) -> "BorderConfiguration":
        """Create default border configuration."""
        return cls()


@dataclass(frozen=True)
class TextConfiguration:
    """Configuration for text formatting and conversion."""

    default_alignment: str = RTFDefaults.TEXT_ALIGNMENT
    enable_hyphenation: bool = RTFDefaults.TEXT_HYPHENATION
    enable_latex_conversion: bool = RTFDefaults.TEXT_CONVERT
    space_before: float = RTFConstants.DEFAULT_SPACE_BEFORE
    space_after: float = RTFConstants.DEFAULT_SPACE_AFTER

    @classmethod
    def create_default(cls) -> "TextConfiguration":
        """Create default text configuration."""
        return cls()


@dataclass(frozen=True)
class RTFConfiguration:
    """Master configuration container for RTF document generation."""

    page: PageConfiguration
    fonts: FontConfiguration
    colors: ColorConfiguration
    borders: BorderConfiguration
    text: TextConfiguration

    @classmethod
    def create_default(cls) -> "RTFConfiguration":
        """Create default RTF configuration."""
        return cls(
            page=PageConfiguration.create_default(),
            fonts=FontConfiguration.create_default(),
            colors=ColorConfiguration.create_default(),
            borders=BorderConfiguration.create_default(),
            text=TextConfiguration.create_default(),
        )

    @classmethod
    def create_pharmaceutical_standard(cls) -> "RTFConfiguration":
        """Create configuration optimized for pharmaceutical reporting."""
        return cls(
            page=PageConfiguration(orientation="portrait"),
            fonts=FontConfiguration(default_font=1, default_size=9),
            colors=ColorConfiguration(use_color=False),
            borders=BorderConfiguration(
                first_row_style="double",
                last_row_style="double",
                default_style="single",
            ),
            text=TextConfiguration(
                enable_latex_conversion=True,
                enable_hyphenation=True,
                default_alignment="l",
            ),
        )

    @classmethod
    def create_landscape(cls) -> "RTFConfiguration":
        """Create landscape-oriented configuration."""
        config = cls.create_default()
        return cls(
            page=PageConfiguration.create_landscape(),
            fonts=config.fonts,
            colors=config.colors,
            borders=config.borders,
            text=config.text,
        )
