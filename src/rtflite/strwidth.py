import importlib.resources as pkg_resources
from typing import Literal, overload

from PIL import ImageFont

import rtflite.fonts

from .fonts_mapping import FontMapping, FontName, FontNumber

Unit = Literal["in", "mm", "px"]

_FONT_PATHS = FontMapping.get_font_paths()

RTF_FONT_NUMBERS = FontMapping.get_font_name_to_number_mapping()
RTF_FONT_NAMES: dict[int, FontName] = FontMapping.get_font_number_to_name_mapping()


@overload
def get_string_width(
    text: str,
    font_name: FontName = "Times New Roman",
    font_size: int = 12,
    unit: Unit = "in",
    dpi: float = 72.0,
) -> float: ...


@overload
def get_string_width(
    text: str,
    font_type: FontNumber,
    font_size: int = 12,
    unit: Unit = "in",
    dpi: float = 72.0,
) -> float: ...


def get_string_width(
    text: str,
    font: FontName | FontNumber = "Times New Roman",
    font_size: int = 12,
    unit: Unit = "in",
    dpi: float = 72.0,
) -> float:
    """
    Calculate the width of a string for a given font and size.
    Uses metric-compatible fonts that match the metrics of common proprietary fonts.

    Args:
        text: The string to measure.
        font: RTF font name or RTF font number (1-10).
        font_size: Font size in points.
        unit: Unit to return the width in.
        dpi: Dots per inch for unit conversion.

    Returns:
        Width of the string in the specified unit.

    Raises:
        ValueError: If an unsupported font name/number or unit is provided.
    """
    # Convert font type number to name if needed
    if isinstance(font, int):
        if font not in RTF_FONT_NAMES:
            raise ValueError(f"Unsupported font number: {font}")
        font_name = RTF_FONT_NAMES[font]
    else:
        font_name = font

    if font_name not in _FONT_PATHS:
        raise ValueError(f"Unsupported font name: {font_name}")

    font_path = pkg_resources.files(rtflite.fonts) / _FONT_PATHS[font_name]
    font = ImageFont.truetype(str(font_path), size=font_size)
    width_px = font.getlength(text)

    conversions = {
        "px": lambda x: x,
        "in": lambda x: x / dpi,
        "mm": lambda x: (x / dpi) * 25.4,
    }

    if unit not in conversions:
        raise ValueError(f"Unsupported unit: {unit}")

    return conversions[unit](width_px)
