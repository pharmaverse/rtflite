"""Inline rich text formatting for RTF table cells.

This module provides :func:`rich_text`, the Python counterpart of
``r2rtf::rtf_rich_text()``. It lets users mix text styles (bold, italic,
etc.) inside a single table cell using lightweight ``{tag ...}`` markers::

    import rtflite as rtf

    rtf.rich_text("n=50 {b (75%)}")

The resulting :class:`RichText` object can be placed directly in a
DataFrame cell; the RTF encoder renders each marked span with its own
inline formatting.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, cast

from .core.constants import RTFConstants
from .fonts_mapping import FontMapping, FontNumber
from .services.color_service import color_service

FORMAT_CODES = RTFConstants.FORMAT_CODES

# Built-in shorthand tags, always available. Each character maps to an
# entry of FORMAT_CODES (b=bold, i=italic, u=underline, s=strikethrough,
# ^=superscript, _=subscript).
_BUILTIN_TAGS = frozenset({"b", "i", "u", "s", "^", "_"})

# Default theme, mirroring r2rtf's default (`.emph` -> italic, `.strong` -> bold).
DEFAULT_THEME: dict[str, Any] = {
    ".emph": "i",
    ".strong": "b",
}

_THEME_SPEC_KEYS = frozenset(
    {"format", "color", "background_color", "font", "font_size"}
)


@dataclass
class RichTextSpan:
    """A single run of text with uniform inline formatting."""

    text: str
    formats: frozenset[str] = frozenset()
    color: str | None = None
    background_color: str | None = None
    font: FontNumber | None = None
    font_size: float | None = None
    # Indices into ``text`` that came from ``\{``, ``\}`` or ``\\`` escapes.
    # These characters serialize as literal RTF characters and are never
    # reinterpreted as RTF structure or LaTeX commands.
    escaped: frozenset[int] = frozenset()


@dataclass
class _StyleFrame:
    """Accumulated style while parsing nested tags."""

    formats: set[str] = field(default_factory=set)
    color: str | None = None
    background_color: str | None = None
    font: FontNumber | None = None
    font_size: float | None = None

    def child(self) -> _StyleFrame:
        return _StyleFrame(
            formats=set(self.formats),
            color=self.color,
            background_color=self.background_color,
            font=self.font,
            font_size=self.font_size,
        )


def _validate_format_string(format: str, *, where: str) -> set[str]:
    """Validate a format-code string like ``"bi"`` and return its characters."""
    formats = set(format)
    invalid = sorted(f for f in formats if f not in FORMAT_CODES)
    if invalid:
        allowed = ", ".join(sorted(FORMAT_CODES))
        raise ValueError(
            f"Invalid format character(s) {invalid} in {where}. "
            f"Must be one of: {allowed}"
        )
    if "^" in formats and "_" in formats:
        raise ValueError(
            f"Invalid format {format!r} in {where}: superscript '^' and "
            "subscript '_' are mutually exclusive. Nest the tags instead, "
            "e.g. '{_ sub {^ sup} sub}'."
        )
    return formats


def _validate_theme_color(color: str, *, where: str) -> None:
    if color and not color_service.validate_color(color):
        suggestions = color_service.get_color_suggestions(color, 3)
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        raise ValueError(f"Invalid color '{color}' in {where}.{hint}")


_VALID_FONT_NUMBERS = frozenset(FontMapping.get_font_table()["type"])


def _validate_theme_font(font: Any, *, tag: str) -> FontNumber:
    """Validate a theme font identifier against the document font table."""
    where = f"theme tag '{tag}'"
    if isinstance(font, bool):
        raise ValueError(f"Invalid font {font!r} in {where}. Must be an integer 1-10.")
    try:
        number = int(font)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid font {font!r} in {where}. Must be an integer 1-10."
        ) from None
    try:
        integral = float(font) == number
    except (TypeError, ValueError):
        integral = False
    if not integral or number not in _VALID_FONT_NUMBERS:
        valid = ", ".join(str(n) for n in sorted(_VALID_FONT_NUMBERS))
        raise ValueError(
            f"Invalid font {font!r} in {where}. Must be an integer from: {valid}."
        )
    return cast(FontNumber, number)


def _validate_theme_font_size(size: Any, *, tag: str) -> float:
    """Validate a theme font size is finite and positive."""
    where = f"theme tag '{tag}'"
    try:
        value = float(size)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid font_size {size!r} in {where}. Must be a number."
        ) from None
    if not math.isfinite(value) or value <= 0:
        raise ValueError(
            f"Invalid font_size {size!r} in {where}. Must be a finite positive number."
        )
    return value


def _resolve_tag_style(tag: str, theme: dict[str, Any]) -> _StyleFrame:
    """Build the style frame contributed by a single tag."""
    frame = _StyleFrame()
    if tag.startswith("."):
        if tag not in theme:
            available = ", ".join(sorted(theme))
            raise ValueError(
                f"Unknown theme tag '{{{tag} ...}}'. Available theme tags: {available}"
            )
        spec = theme[tag]
        if isinstance(spec, str):
            frame.formats = _validate_format_string(spec, where=f"theme tag '{tag}'")
        elif isinstance(spec, dict):
            unknown = set(spec) - _THEME_SPEC_KEYS
            if unknown:
                allowed = ", ".join(sorted(_THEME_SPEC_KEYS))
                raise ValueError(
                    f"Unknown theme option(s) {sorted(unknown)} in theme tag "
                    f"'{tag}'. Must be one of: {allowed}"
                )
            if "format" in spec and spec["format"] is not None:
                frame.formats = _validate_format_string(
                    str(spec["format"]), where=f"theme tag '{tag}'"
                )
            if spec.get("color"):
                _validate_theme_color(spec["color"], where=f"theme tag '{tag}'")
                frame.color = spec["color"]
            if spec.get("background_color"):
                _validate_theme_color(
                    spec["background_color"], where=f"theme tag '{tag}'"
                )
                frame.background_color = spec["background_color"]
            if spec.get("font") is not None:
                frame.font = _validate_theme_font(spec["font"], tag=tag)
            if spec.get("font_size") is not None:
                frame.font_size = _validate_theme_font_size(spec["font_size"], tag=tag)
        else:
            raise TypeError(
                f"Theme tag '{tag}' must be a format string or a dict, "
                f"got {type(spec).__name__}."
            )
    else:
        if not tag or any(c not in _BUILTIN_TAGS for c in tag):
            allowed = ", ".join(sorted(_BUILTIN_TAGS))
            raise ValueError(
                f"Unknown tag '{{{tag} ...}}'. Built-in tags are: {allowed}. "
                "Custom styles use theme tags like '{.name ...}'."
            )
        frame.formats = _validate_format_string(tag, where=f"tag '{{{tag}}}'")
    return frame


_TAG_RE = re.compile(r"\{([^\s{}]+)(?=[\s}])")


def _parse(text: str, theme: dict[str, Any]) -> list[RichTextSpan]:
    """Parse marked-up text into a list of :class:`RichTextSpan`."""
    spans: list[RichTextSpan] = []
    buf: list[str] = []
    # Buffer positions (indices into ``buf``) holding escape-produced
    # characters; cleared together with ``buf`` on flush.
    escaped: set[int] = set()
    stack: list[_StyleFrame] = []

    def flush() -> None:
        if not buf:
            return
        segment = "".join(buf)
        escaped_positions = frozenset(escaped)
        buf.clear()
        escaped.clear()
        if stack:
            top = stack[-1]
            spans.append(
                RichTextSpan(
                    text=segment,
                    formats=frozenset(top.formats),
                    color=top.color,
                    background_color=top.background_color,
                    font=top.font,
                    font_size=top.font_size,
                    escaped=escaped_positions,
                )
            )
        else:
            spans.append(RichTextSpan(text=segment, escaped=escaped_positions))

    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        # Backslash escapes: \{ -> {, \} -> }, \\ -> \
        if ch == "\\" and i + 1 < n and text[i + 1] in "{}\\":
            escaped.add(len(buf))
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == "{":
            match = _TAG_RE.match(text, i)
            if match is None:
                raise ValueError(
                    f"Invalid tag at position {i} in {text!r}. "
                    "Tags look like '{b ...}' or '{.name ...}'; "
                    "use '\\{' for a literal '{'."
                )
            tag = match.group(1)
            flush()
            parent = stack[-1] if stack else _StyleFrame()
            child = parent.child()
            tag_style = _resolve_tag_style(tag, theme)
            # Superscript and subscript are mutually exclusive: an inner
            # tag overrides the inherited one, which resumes after the
            # inner tag closes (each frame keeps its own format set).
            if "^" in tag_style.formats:
                child.formats.discard("_")
            if "_" in tag_style.formats:
                child.formats.discard("^")
            child.formats |= tag_style.formats
            if tag_style.color is not None:
                child.color = tag_style.color
            if tag_style.background_color is not None:
                child.background_color = tag_style.background_color
            if tag_style.font is not None:
                child.font = tag_style.font
            if tag_style.font_size is not None:
                child.font_size = tag_style.font_size
            stack.append(child)
            i = match.end()
            # Skip the single space separating tag from content, if present
            if i < n and text[i] == " ":
                i += 1
            continue
        if ch == "}":
            if not stack:
                raise ValueError(
                    f"Unmatched closing brace at position {i} in {text!r}. "
                    "Use '\\}' for a literal '}'."
                )
            flush()
            stack.pop()
            i += 1
            continue
        buf.append(ch)
        i += 1

    if stack:
        raise ValueError(f"Unclosed tag in {text!r}: missing '}}'.")
    flush()
    return spans


# RTF literal escapes for characters that arrived via \{, \} or \\.
# They must serialize as literal characters, never as RTF structure.
_RTF_LITERAL_ESCAPES = {"\\": "\\\\", "{": "\\{", "}": "\\}"}


def _render_span_text(span: RichTextSpan, convert: Any) -> str:
    """Render a span's text, preserving escape-produced characters.

    Characters recorded in ``span.escaped`` are emitted as RTF-escaped
    literals (``\\{``, ``\\}``, ``\\\\``). Everything else goes through the
    normal text conversion (special characters, LaTeX commands, Unicode).
    """
    parts: list[str] = []
    buf: list[str] = []

    def flush_buf() -> None:
        if buf:
            parts.append(convert("".join(buf)))
            buf.clear()

    for idx, ch in enumerate(span.text):
        if idx in span.escaped:
            flush_buf()
            parts.append(_RTF_LITERAL_ESCAPES[ch])
        else:
            buf.append(ch)
    flush_buf()
    return "".join(parts)


class RichText:
    """Text with inline formatting markers, for use in table cells.

    Create instances with :func:`rich_text` rather than directly.
    """

    def __init__(self, text: str, theme: dict[str, Any] | None = None):
        if not isinstance(text, str):
            raise TypeError(f"rich_text() expects a string, got {type(text).__name__}.")
        self.text = text
        self.theme: dict[str, Any] = {**DEFAULT_THEME, **(theme or {})}
        self.spans: list[RichTextSpan] = _parse(text, self.theme)

    @property
    def plain_text(self) -> str:
        """The text with all formatting markers removed."""
        return "".join(span.text for span in self.spans)

    def __str__(self) -> str:
        return self.plain_text

    def __repr__(self) -> str:
        return f"RichText({self.text!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RichText):
            return NotImplemented
        return self.text == other.text and self.theme == other.theme

    def render_spans(self, base: Any) -> str:
        """Render spans as inline RTF groups.

        Args:
            base: The enclosing :class:`rtflite.row.TextContent`, providing
                default font, size, and colors plus text conversion.
        """
        # Local import to avoid a hard dependency cycle (row.py references
        # RichText objects without importing this module).
        from .row import Utils

        parts: list[str] = []
        for span in self.spans:
            font = span.font if span.font is not None else base.font
            size = span.font_size if span.font_size is not None else base.size
            color = span.color if span.color is not None else base.color
            background = (
                span.background_color
                if span.background_color is not None
                else base.background_color
            )

            codes = [f"{{\\f{int(font) - 1}", f"\\fs{int(size * 2)}"]
            if color:
                codes.append(f"\\cf{Utils._get_color_index(color)}")
            if background:
                bg_index = Utils._get_color_index(background)
                codes.append(f"\\chshdng0\\chcbpat{bg_index}\\cb{bg_index}")
            for fmt in sorted(span.formats):
                codes.append(FORMAT_CODES[fmt])
            converted = _render_span_text(span, base._convert_text)
            codes.append(f" {converted}}}")
            parts.append("".join(codes))
        return "".join(parts)

    def measured_width(self, font: FontNumber = 1, font_size: float = 9) -> float:
        """Total rendered width in inches, honoring per-span font/size.

        Each span is measured with its own font and font size (falling back
        to the given cell defaults), so pagination and line estimation can
        account for inline size overrides.

        Args:
            font: Default font number for spans without a font override.
            font_size: Default font size in points for spans without an
                override.
        """
        from .strwidth import get_string_width

        total = 0.0
        for span in self.spans:
            total += get_string_width(
                span.text,
                font=span.font if span.font is not None else font,
                font_size=span.font_size if span.font_size is not None else font_size,
            )
        return total


def rich_text(text: str, theme: dict[str, Any] | None = None) -> RichText:
    """Create rich text with inline formatting for use in table cells.

    Markers use ``{tag ...}`` syntax, inspired by ``r2rtf::rtf_rich_text()``:

    - ``{b ...}`` bold, ``{i ...}`` italic, ``{u ...}`` underline,
      ``{s ...}`` strikethrough, ``{^ ...}`` superscript, ``{_ ...}``
      subscript. Tags nest, e.g. ``{b bold {i bold-italic}}``.
      Superscript and subscript are mutually exclusive within one tag:
      combining them (``{^_ ...}``) is rejected; nest the tags instead, and
      an inner ``{^ ...}``/``{_ ...}`` temporarily overrides an inherited
      ``_``/``^`` (the outer script resumes after the inner tag closes).
    - ``{.name ...}`` applies a theme entry (see ``theme``).
    - ``\\{``, ``\\}`` and ``\\\\`` produce literal ``{``, ``}`` and ``\\``.
      Escaped characters are emitted as literal RTF and are never
      reinterpreted as RTF control words or LaTeX commands.

    Args:
        text: Text with inline formatting markers.
        theme: Optional mapping of custom tag names (used as ``{.name ...}``)
            to either a format-code string (e.g. ``"bi"``) or a dict with
            ``format``, ``color``, ``background_color``, ``font`` and
            ``font_size`` keys. ``font`` must be an integer font id from 1
            to 10 (matching the document font table); ``font_size`` must
            be a finite positive number of points. The default theme
            provides ``.emph`` (italic) and ``.strong`` (bold), matching
            r2rtf.

    Returns:
        A :class:`RichText` object. Place it directly in a DataFrame cell::

            df = pl.DataFrame({
                "Treatment": ["Placebo", "Drug A"],
                "Response": [
                    rtf.rich_text("n=50 {b (75%)}"),
                    rtf.rich_text("n=48 {b (92%)}"),
                ],
            })

        Note: a column mixing plain strings and ``rich_text()`` values must
        use ``dtype=pl.Object`` so polars keeps the ``RichText`` objects::

            pl.Series(["plain", rtf.rich_text("{b bold}")], dtype=pl.Object)

    Raises:
        ValueError: On unknown tags, unbalanced braces, combined
            superscript/subscript in one tag, or invalid
            format/color/font/font_size specifications.
        TypeError: If ``text`` is not a string.
    """
    return RichText(text, theme=theme)
