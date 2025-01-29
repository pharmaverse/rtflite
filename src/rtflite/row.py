from collections.abc import Mapping, MutableSequence, Sequence

from pydantic import BaseModel, Field


class Utils:
    @staticmethod
    def _color_table() -> Mapping:
        """Define color table."""
        return {
            "color": [
                "black",
                "red",
                "green",
                "blue",
                "white",
                "lightgray",
                "darkgray",
                "yellow",
                "magenta",
                "cyan",
            ],
            "type": list(range(1, 11)),
            "rtf_code": [
                "\\red0\\green0\\blue0;",  # black
                "\\red255\\green0\\blue0;",  # red
                "\\red0\\green255\\blue0;",  # green
                "\\red0\\green0\\blue255;",  # blue
                "\\red255\\green255\\blue255;",  # white
                "\\red211\\green211\\blue211;",  # lightgray
                "\\red169\\green169\\blue169;",  # darkgray
                "\\red255\\green255\\blue0;",  # yellow
                "\\red255\\green0\\blue255;",  # magenta
                "\\red0\\green255\\blue255;",  # cyan
            ],
        }

    @staticmethod
    def _font_type() -> Mapping:
        """Define font types"""
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
        }

    @staticmethod
    def _inch_to_twip(inch: float) -> int:
        """Convert inches to twips."""
        return round(inch * 1440)

    @staticmethod
    def _col_widths(
        rel_widths: Sequence[float], col_width: float
    ) -> MutableSequence[float]:
        """Convert relative widths to absolute widths. Returns mutable list since we're building it."""
        total_width = sum(rel_widths)
        cumulative_sum = 0
        return [
            cumulative_sum := cumulative_sum + (width * col_width / total_width)
            for width in rel_widths
        ]

    @staticmethod
    def _get_color_index(color: str) -> int:
        """Get the index of a color in the color table."""
        colors = Utils._color_table()
        try:
            return colors["color"].index(color) + 1
        except ValueError:
            return 0  # Default to black


class TextContent(BaseModel):
    """Represents RTF text with formatting."""

    text: str = Field(..., description="The text content")
    font: int = Field(default=1, description="Font index")
    size: int = Field(default=9, description="Font size")
    format: str | None = Field(
        default=None,
        description="Text formatting codes: b=bold, i=italic, u=underline, s=strikethrough, ^=superscript, _=subscript",
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
    space_before: int = Field(default=15, description="Space before paragraph")
    space_after: int = Field(default=15, description="Space after paragraph")
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
            rtf.append(f"\\sl{int(self.space * 240)}\\slmult1")

        # Indentation
        rtf.append(f"\\fi{Utils._inch_to_twip(self.indent_first / 1440)}")
        rtf.append(f"\\li{Utils._inch_to_twip(self.indent_left / 1440)}")
        rtf.append(f"\\ri{Utils._inch_to_twip(self.indent_right / 1440)}")

        # Justification
        just_codes = {"l": "\\ql", "c": "\\qc", "r": "\\qr", "d": "\\qd", "j": "\\qj"}
        if self.justification not in just_codes:
            raise ValueError(
                f"Text: Invalid justification '{self.justification}'. Must be one of: {', '.join(just_codes.keys())}"
            )
        rtf.append(just_codes[self.justification])

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
            format_codes = {
                "b": "\\b",
                "i": "\\i",
                "u": "\\ul",
                "s": "\\strike",
                "^": "\\super",
                "_": "\\sub",
            }
            for fmt in sorted(list(set(self.format))):
                if fmt in format_codes:
                    rtf.append(format_codes[fmt])
                else:
                    raise ValueError(
                        f"Text: Invalid format character '{fmt}' in '{self.format}'. Must be one of: {', '.join(format_codes.keys())}"
                    )

        return "".join(rtf)

    def _convert_special_chars(self) -> str:
        """Convert special characters to RTF codes."""
        # Basic RTF character conversion
        rtf_chars = {
            "\\": "\\\\",
            "{": "\\{",
            "}": "\\}",
            "\n": "\\line ",
            "^": "\\super ",
            "_": "\\sub ",
            "≥": "\\geq ",
            "≤": "\\leq ",
        }

        for char, rtf in rtf_chars.items():
            text = self.text.replace(char, rtf)

        return text

    def _as_rtf(self, method: str) -> str:
        """Format source as RTF."""
        if method == "paragraph":
            return f"{{\\pard{self._get_paragraph_formatting()}{self._get_text_formatting()} {self._convert_special_chars()}}}\\par}}"
        if method == "cell":
            return f"\\pard{self._get_paragraph_formatting()}{self._get_text_formatting()} {self._convert_special_chars()}}}\\cell"

        if method == "plain":
            return f"{self._get_text_formatting()} {self._convert_special_chars()}}}"

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
    width: int = Field(default=15, description="Border width in twips")
    color: str | None = Field(default=None, description="Border color")

    def _as_rtf(self) -> str:
        """Get RTF border style codes."""
        border_codes = {
            "single": "\\brdrs",
            "double": "\\brdrdb",
            "thick": "\\brdrth",
            "dotted": "\\brdrdot",
            "dashed": "\\brdrdash",
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

        if self.style not in border_codes:
            raise ValueError(f"Invalid border type: {self.style}")

        rtf = f"{border_codes[self.style]}\\brdrw{self.width}"

        # Add color if specified
        if self.color is not None:
            rtf = rtf + f"\\brdrcf{Utils._get_color_index(self.color)}"

        return rtf


class Cell(BaseModel):
    """Represents a cell in an RTF table."""

    text: TextContent
    width: float = Field(..., description="Cell width")
    vertical_justification: str = Field(
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
        valign_codes = {
            "top": "\\clvertalt",
            "center": "\\clvertalc",
            "bottom": "\\clvertalb",
        }
        rtf.append(valign_codes[self.vertical_justification])

        # Cell width
        rtf.append(f"\\cellx{Utils._inch_to_twip(self.width)}")

        return "".join(rtf)


class Row(BaseModel):
    """Represents a row in an RTF table."""

    row_cells: Sequence[Cell] = Field(..., description="List of cells in the row")
    justification: str = Field(default="c", description="Row justification (l, c, r)")
    height: float = Field(default=0.15, description="Row height")

    def _as_rtf(self) -> MutableSequence[str]:
        """Format a row of cells in RTF. Returns mutable list since we're building it."""
        # Justification
        just_codes = {"l": "\\trql", "c": "\\trqc", "r": "\\trqr"}
        if self.justification not in just_codes:
            raise ValueError(
                f"Row: Invalid justification '{self.justification}'. Must be one of: {', '.join(just_codes.keys())}"
            )

        rtf = [
            f"\\trowd\\trgaph{int(Utils._inch_to_twip(self.height) / 2)}\\trleft0{just_codes[self.justification]}"
        ]
        rtf.extend(cell._as_rtf() for cell in self.row_cells)
        rtf.extend(cell.text._as_rtf(method="cell") for cell in self.row_cells)
        rtf.append("\\intbl\\row\\pard")
        return rtf
