import importlib.resources as pkg_resources
from typing import Literal, overload

from PIL import ImageFont

import rtflite.fonts

Unit = Literal["in", "mm", "px"]

FontName = Literal[
    "Times New Roman",
    "Times New Roman Greek",
    "Arial Greek",
    "Arial",
    "Helvetica",
    "Calibri",
    "Georgia",
    "Cambria",
    "Courier New",
    "Symbol",
]

_FONT_PATHS = {
    "Times New Roman": "liberation/LiberationSerif-Regular.ttf",
    "Times New Roman Greek": "liberation/LiberationSerif-Regular.ttf",
    "Arial Greek": "liberation/LiberationSans-Regular.ttf",
    "Arial": "liberation/LiberationSans-Regular.ttf",
    "Helvetica": "liberation/LiberationSans-Regular.ttf",
    "Calibri": "cros/Carlito-Regular.ttf",
    "Georgia": "cros/Gelasio-Regular.ttf",
    "Cambria": "cros/Caladea-Regular.ttf",
    "Courier New": "liberation/LiberationMono-Regular.ttf",
    "Symbol": "liberation/LiberationSerif-Regular.ttf",
}

# Add type number type
FontNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Define bidirectional mappings
RTF_FONT_NUMBERS = {
    "Times New Roman": 1,
    "Times New Roman Greek": 2,
    "Arial Greek": 3,
    "Arial": 4,
    "Helvetica": 5,
    "Calibri": 6,
    "Georgia": 7,
    "Cambria": 8,
    "Courier New": 9,
    "Symbol": 10,
}

RTF_FONT_NAMES: dict[int, FontName] = {v: k for k, v in RTF_FONT_NUMBERS.items()}


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
