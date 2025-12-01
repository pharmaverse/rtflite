from collections.abc import Mapping, MutableSequence, Sequence

from pydantic import BaseModel, Field

from .core.constants import RTFConstants, RTFMeasurements
from .fonts_mapping import FontMapping

# Import constants from centralized location for backwards compatibility
FORMAT_CODES = RTFConstants.FORMAT_CODES

TEXT_JUSTIFICATION_CODES = RTFConstants.TEXT_JUSTIFICATION_CODES

ROW_JUSTIFICATION_CODES = RTFConstants.ROW_JUSTIFICATION_CODES

BORDER_CODES = RTFConstants.BORDER_CODES

VERTICAL_ALIGNMENT_CODES = RTFConstants.VERTICAL_ALIGNMENT_CODES


class Utils:
    @staticmethod
    def _font_type() -> Mapping:
        """Define font types"""
        return FontMapping.get_font_table()

    @staticmethod
    def _inch_to_twip(inch: float) -> int:
        """Convert inches to twips."""
        return RTFMeasurements.inch_to_twip(inch)

    @staticmethod
    def _col_widths(rel_widths: Sequence[float], col_width: float) -> list[float]:
        """Convert relative widths to absolute widths.
        Returns mutable list since we are building it.
        """
        total_width = sum(rel_widths)
        cumulative_sum = 0.0
        return [
            cumulative_sum := cumulative_sum + (width * col_width / total_width)
            for width in rel_widths
        ]

    @staticmethod
    def _get_color_index(color: str, used_colors=None) -> int:
        """Get the index of a color in the color table."""
        if not color or color == "black":
            return 0  # Default/black color

        from .services.color_service import ColorValidationError, color_service

        try:
            # If no explicit used_colors provided, the color service
            # will uses document context
            return color_service.get_rtf_color_index(color, used_colors)
        except ColorValidationError:
            # Invalid color name - return default
            return 0


class TextContent(BaseModel):
    """Represents RTF text with formatting."""

    text: str = Field(..., description="The text content")
    font: int = Field(default=1, description="Font index")
    size: int = Field(default=9, description="Font size")
    format: str | None = Field(
        default=None,
        description=(
            "Text formatting codes: b=bold, i=italic, u=underline, "
            "s=strikethrough, ^=superscript, _=subscript"
        ),
    )
    color: str | None = Field(default=None, description="Text color")
    background_color: str | None = Field(default=None, description="Background color")
    justification: str = Field(
        default="l", description="Text justification (l, c, r, d, j)"
    )
    indent_first: int = Field(default=0, description="First line indent")
    indent_left: int = Field(default=0, description="Left indent")
    indent_right: int = Field(default=0, description="Right indent")
    space: int = Field(default=1, description="Line spacing")
    space_before: int = Field(
        default=RTFConstants.DEFAULT_SPACE_BEFORE, description="Space before paragraph"
    )
    space_after: int = Field(
        default=RTFConstants.DEFAULT_SPACE_AFTER, description="Space after paragraph"
    )
    convert: bool = Field(
        default=True, description="Enable LaTeX to Unicode conversion"
    )
    hyphenation: bool = Field(default=True, description="Enable hyphenation")

    def _get_paragraph_formatting(self) -> str:
        """Get RTF paragraph formatting codes."""
        rtf = []

        # Hyphenation
        if self.hyphenation:
            rtf.append("\\hyphpar")
        else:
            rtf.append("\\hyphpar0")

        # Spacing
        rtf.append(f"\\sb{self.space_before}")
        rtf.append(f"\\sa{self.space_after}")
        if self.space != 1:
            rtf.append(
                f"\\sl{int(self.space * RTFConstants.LINE_SPACING_FACTOR)}\\slmult1"
            )

        # Indentation
        indent_first = self.indent_first / RTFConstants.TWIPS_PER_INCH
        indent_left = self.indent_left / RTFConstants.TWIPS_PER_INCH
        indent_right = self.indent_right / RTFConstants.TWIPS_PER_INCH
        rtf.append(f"\\fi{Utils._inch_to_twip(indent_first)}")
        rtf.append(f"\\li{Utils._inch_to_twip(indent_left)}")
        rtf.append(f"\\ri{Utils._inch_to_twip(indent_right)}")

        # Justification
        if self.justification not in TEXT_JUSTIFICATION_CODES:
            allowed = ", ".join(TEXT_JUSTIFICATION_CODES.keys())
            raise ValueError(
                "Text: Invalid justification "
                f"'{self.justification}'. Must be one of: {allowed}"
            )
        rtf.append(TEXT_JUSTIFICATION_CODES[self.justification])

        return "".join(rtf)

    def _get_text_formatting(self) -> str:
        """Get RTF text formatting codes."""
        rtf = []

        # Size (RTF uses half-points)
        rtf.append(f"\\fs{self.size * 2}")

        # Font
        rtf.append(f"{{\\f{int(self.font - 1)}")

        # Color
        if self.color:
            rtf.append(f"\\cf{Utils._get_color_index(self.color)}")

        # Background color
        if self.background_color:
            bp_color = Utils._get_color_index(self.background_color)
            rtf.append(f"\\chshdng0\\chcbpat{bp_color}\\cb{bp_color}")

        # Format (bold, italic, etc)
        if self.format:
            for fmt in sorted(list(set(self.format))):
                if fmt in FORMAT_CODES:
                    rtf.append(FORMAT_CODES[fmt])
                else:
                    allowed = ", ".join(FORMAT_CODES.keys())
                    raise ValueError(
                        "Text: Invalid format character "
                        f"'{fmt}' in '{self.format}'. Must be one of: {allowed}"
                    )

        return "".join(rtf)

    def _convert_special_chars(self) -> str:
        """Convert special characters to RTF codes."""
        text = self.text

        # Basic RTF character conversion (matching r2rtf char_rtf mapping)
        # Only apply character conversions if text conversion is enabled
        if self.convert:
            rtf_chars = RTFConstants.RTF_CHAR_MAPPING
            for char, rtf in rtf_chars.items():
                text = text.replace(char, rtf)

        # Apply LaTeX to Unicode conversion if enabled
        from .services.text_conversion_service import TextConversionService

        service = TextConversionService()
        converted_text = service.convert_text_content(text, self.convert)

        if converted_text is None:
            return ""

        text = str(converted_text)

        converted_text = ""
        for char in text:
            unicode_int = ord(char)
            if unicode_int <= 255 and unicode_int != 177:
                converted_text += char
            else:
                rtf_value = unicode_int - (0 if unicode_int < 32768 else 65536)
                converted_text += f"\\uc1\\u{rtf_value}*"

        text = converted_text

        return text

    def _as_rtf(self, method: str) -> str:
        """Format source as RTF."""
        formatted_text = self._convert_special_chars()
        if method == "paragraph":
            return (
                "{\\pard"
                f"{self._get_paragraph_formatting()}"
                f"{self._get_text_formatting()} "
                f"{formatted_text}}}\\par}}"
            )
        if method == "cell":
            return (
                "\\pard"
                f"{self._get_paragraph_formatting()}"
                f"{self._get_text_formatting()} "
                f"{formatted_text}}}\\cell"
            )

        if method == "plain":
            return f"{self._get_text_formatting()} {formatted_text}}}"

        if method == "paragraph_format":
            return f"{{\\pard{self._get_paragraph_formatting()}{self.text}\\par}}"

        if method == "cell_format":
            return f"\\pard{self._get_paragraph_formatting()}{self.text}\\cell"

        raise ValueError(f"Invalid method: {method}")


class Border(BaseModel):
    """Represents a single border's style, color, and width."""

    style: str = Field(
        default="single", description="Border style (single, double, dashed, etc)"
    )
    width: int = Field(
        default=RTFConstants.DEFAULT_BORDER_WIDTH, description="Border width in twips"
    )
    color: str | None = Field(default=None, description="Border color")

    def _as_rtf(self) -> str:
        """Get RTF border style codes."""
        if self.style not in BORDER_CODES:
            raise ValueError(f"Invalid border type: {self.style}")

        rtf = f"{BORDER_CODES[self.style]}\\brdrw{self.width}"

        # Add color if specified
        if self.color is not None:
            rtf = rtf + f"\\brdrcf{Utils._get_color_index(self.color)}"

        return rtf


class Cell(BaseModel):
    """Represents a cell in an RTF table."""

    text: TextContent
    width: float = Field(..., description="Cell width")
    vertical_justification: str | None = Field(
        default="bottom", description="Vertical alignment"
    )
    border_top: Border | None = Field(default=Border(), description="Top border")
    border_right: Border | None = Field(default=Border(), description="Right border")
    border_bottom: Border | None = Field(default=Border(), description="Bottom border")
    border_left: Border | None = Field(default=Border(), description="Left border")

    def _as_rtf(self) -> str:
        """Format a single table cell in RTF."""
        # Cell Border
        rtf = []

        if self.border_left is not None:
            rtf.append("\\clbrdrl" + self.border_left._as_rtf())

        if self.border_top is not None:
            rtf.append("\\clbrdrt" + self.border_top._as_rtf())

        if self.border_right is not None:
            rtf.append("\\clbrdrr" + self.border_right._as_rtf())

        if self.border_bottom is not None:
            rtf.append("\\clbrdrb" + self.border_bottom._as_rtf())

        # Cell vertical alignment
        if self.vertical_justification is not None:
            rtf.append(VERTICAL_ALIGNMENT_CODES[self.vertical_justification])

        # Cell width
        rtf.append(f"\\cellx{Utils._inch_to_twip(self.width)}")

        return "".join(rtf)


class Row(BaseModel):
    """Represents a row in an RTF table."""

    row_cells: Sequence[Cell] = Field(..., description="List of cells in the row")
    justification: str = Field(default="c", description="Row justification (l, c, r)")
    height: float = Field(default=0.15, description="Row height")

    def _as_rtf(self) -> MutableSequence[str]:
        """Format a row of cells in RTF.
        Returns mutable list since we are building it."""
        # Justification
        if self.justification not in ROW_JUSTIFICATION_CODES:
            allowed = ", ".join(ROW_JUSTIFICATION_CODES.keys())
            raise ValueError(
                "Row: Invalid justification "
                f"'{self.justification}'. Must be one of: {allowed}"
            )

        row_height = int(Utils._inch_to_twip(self.height) / 2)
        justification_code = ROW_JUSTIFICATION_CODES[self.justification]
        rtf = [(f"\\trowd\\trgaph{row_height}\\trleft0{justification_code}")]
        rtf.extend(cell._as_rtf() for cell in self.row_cells)
        rtf.extend(cell.text._as_rtf(method="cell") for cell in self.row_cells)
        rtf.append("\\intbl\\row\\pard")
        return rtf
