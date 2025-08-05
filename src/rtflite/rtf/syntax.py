"""RTF syntax generation utilities."""

from typing import Any, Dict, List, Optional

from ..core.constants import RTFConstants


class RTFSyntaxGenerator:
    """Central RTF syntax generator for common RTF operations."""

    @staticmethod
    def generate_document_start() -> str:
        """Generate RTF document start code."""
        return "{\\rtf1\\ansi\\deff0"

    @staticmethod
    def generate_document_end() -> str:
        """Generate RTF document end code."""
        return "}"

    @staticmethod
    def generate_font_table() -> str:
        """Generate RTF font table using system fonts.

        Returns:
            RTF font table string
        """
        from ..row import Utils

        font_types = Utils._font_type()
        font_rtf = [f"\\f{i}" for i in range(10)]
        font_style = font_types["style"]
        font_name = font_types["name"]
        font_charset = font_types["charset"]

        font_table = RTFConstants.Control.FONT_TABLE_START
        for rtf, style, name, charset in zip(
            font_rtf, font_style, font_name, font_charset
        ):
            font_table = (
                font_table + "{" + rtf + style + charset + "\\fprq2 " + name + ";}\n"
            )
        font_table += "}"
        return font_table

    @staticmethod
    def generate_color_table(used_colors: Optional[List[str]] = None) -> str:
        """Generate RTF color table using comprehensive 657-color support.

        Args:
            used_colors: List of color names used in document. If None, includes all 657 colors.

        Returns:
            RTF color table string
        """
        from ..services.color_service import color_service

        return color_service.generate_rtf_color_table(used_colors)

    @staticmethod
    def generate_page_settings(
        width: float, height: float, margins: List[float], orientation: str = "portrait"
    ) -> str:
        """Generate RTF page settings.

        Args:
            width: Page width in inches
            height: Page height in inches
            margins: Margins [left, right, top, bottom, header, footer] in inches
            orientation: Page orientation ('portrait' or 'landscape')

        Returns:
            RTF page settings string
        """
        from ..row import Utils

        # Convert to twips
        width_twips = int(Utils._inch_to_twip(width))
        height_twips = int(Utils._inch_to_twip(height))

        margin_twips = [int(Utils._inch_to_twip(m)) for m in margins]

        # Add landscape command if needed
        landscape_cmd = "\\landscape " if orientation == "landscape" else ""

        return (
            f"\\paperw{width_twips}\\paperh{height_twips}{landscape_cmd}\n"
            f"\\margl{margin_twips[0]}\\margr{margin_twips[1]}"
            f"\\margt{margin_twips[2]}\\margb{margin_twips[3]}"
            f"\\headery{margin_twips[4]}\\footery{margin_twips[5]}"
        )

    @staticmethod
    def generate_page_break() -> str:
        """Generate RTF page break."""
        return "\\page"

    @staticmethod
    def generate_paragraph_break() -> str:
        """Generate RTF paragraph break."""
        return "\\par"

    @staticmethod
    def generate_line_break() -> str:
        """Generate RTF line break."""
        return "\\line"


class RTFDocumentAssembler:
    """Assembles complete RTF documents from components."""

    def __init__(self):
        self.syntax = RTFSyntaxGenerator()

    def assemble_document(self, components: Dict[str, Any]) -> str:
        """Assemble a complete RTF document from components.

        Args:
            components: Dictionary containing document components

        Returns:
            Complete RTF document string
        """
        parts = []

        # Document start
        parts.append(self.syntax.generate_document_start())

        # Font table
        if "fonts" in components:
            parts.append(self.syntax.generate_font_table(components["fonts"]))

        # Page settings
        if "page_settings" in components:
            settings = components["page_settings"]
            parts.append(
                self.syntax.generate_page_settings(
                    settings["width"],
                    settings["height"],
                    settings["margins"],
                    settings.get("orientation", "portrait"),
                )
            )

        # Content sections
        content_sections = [
            "page_header",
            "page_footer",
            "title",
            "subline",
            "column_headers",
            "body",
            "footnotes",
            "sources",
        ]

        for section in content_sections:
            if section in components and components[section]:
                if isinstance(components[section], list):
                    parts.extend(components[section])
                else:
                    parts.append(components[section])

        # Document end
        parts.append(self.syntax.generate_document_end())

        # Join with newlines, filtering out None/empty values
        return "\n".join(str(part) for part in parts if part)
