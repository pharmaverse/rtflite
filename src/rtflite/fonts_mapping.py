from typing import Literal, Mapping

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

FontNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class FontMapping:
    """Centralized font mapping for RTF document generation."""

    @staticmethod
    def get_font_table() -> Mapping:
        """Get complete font table with all properties."""
        return {
            "type": list(range(1, 11)),
            "name": [
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
            ],
            "style": [
                "\\froman",
                "\\froman",
                "\\fswiss",
                "\\fswiss",
                "\\fswiss",
                "\\fswiss",
                "\\froman",
                "\\ffroman",
                "\\fmodern",
                "\\ftech",
            ],
            "rtf_code": [f"\\f{i}" for i in range(10)],
            "family": [
                "Times",
                "Times",
                "ArialMT",
                "ArialMT",
                "Helvetica",
                "Calibri",
                "Georgia",
                "Cambria",
                "Courier",
                "Times",
            ],
            "charset": [
                "\\fcharset1",
                "\\fcharset161",
                "\\fcharset161",
                "\\fcharset0",
                "\\fcharset1",
                "\\fcharset1",
                "\\fcharset1",
                "\\fcharset1",
                "\\fcharset0",
                "\\fcharset2",
            ],
        }

    @staticmethod
    def get_font_name_to_number_mapping() -> dict[FontName, int]:
        """Get mapping from font names to font numbers."""
        return {
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

    @staticmethod
    def get_font_number_to_name_mapping() -> dict[int, FontName]:
        """Get mapping from font numbers to font names."""
        name_to_number = FontMapping.get_font_name_to_number_mapping()
        return {v: k for k, v in name_to_number.items()}

    @staticmethod
    def get_font_paths() -> dict[FontName, str]:
        """Get mapping from font names to font file paths."""
        return {
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
