import importlib.resources as pkg_resources
import math
from collections.abc import Mapping
from typing import Literal

from PIL import ImageFont
from PIL import __version__ as PILLOW_VERSION

import rtflite.fonts

from .fonts_mapping import FontMapping, FontName, FontNumber

Unit = Literal["in", "mm", "px"]

_FONT_PATHS = FontMapping.get_font_paths()

RTF_FONT_NUMBERS = FontMapping.get_font_name_to_number_mapping()
RTF_FONT_NAMES: Mapping[int, FontName] = FontMapping.get_font_number_to_name_mapping()

# Check Pillow version to determine if size parameter should be int or float
_PILLOW_VERSION = tuple(map(int, PILLOW_VERSION.split(".")[:2]))
_PILLOW_REQUIRES_INT_SIZE = _PILLOW_VERSION < (10, 0)


def get_string_width(
    text: str,
    font: FontName | FontNumber = "Times New Roman",
    font_size: float = 12,
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
    # Convert size to int for Pillow < 10.0.0 compatibility
    # (use ceiling for conservative pagination)
    size_param = int(math.ceil(font_size)) if _PILLOW_REQUIRES_INT_SIZE else font_size
    font_obj = ImageFont.truetype(str(font_path), size=size_param)
    width_px = font_obj.getlength(text)

    conversions = {
        "px": lambda x: x,
        "in": lambda x: x / dpi,
        "mm": lambda x: (x / dpi) * 25.4,
    }

    if unit not in conversions:
        raise ValueError(f"Unsupported unit: {unit}")

    return conversions[unit](width_px)
