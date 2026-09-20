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

import re
from dataclasses import dataclass, field
from typing import Any

from .core.constants import RTFConstants
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
    font: int | None = None
    font_size: float | None = None


@dataclass
class _StyleFrame:
    """Accumulated style while parsing nested tags."""

    formats: set[str] = field(default_factory=set)
    color: str | None = None
    background_color: str | None = None
    font: int | None = None
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
    return formats


def _validate_theme_color(color: str, *, where: str) -> None:
    if color and not color_service.validate_color(color):
        suggestions = color_service.get_color_suggestions(color, 3)
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        raise ValueError(f"Invalid color '{color}' in {where}.{hint}")


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
                frame.font = int(spec["font"])
            if spec.get("font_size") is not None:
                size = float(spec["font_size"])
                if size <= 0:
                    raise ValueError(
                        f"Invalid font_size {spec['font_size']} in theme tag "
                        f"'{tag}'. Must be positive."
                    )
                frame.font_size = size
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
        frame.formats = set(tag)
    return frame


_TAG_RE = re.compile(r"\{([^\s{}]+)(?=[\s}])")


def _parse(text: str, theme: dict[str, Any]) -> list[RichTextSpan]:
    """Parse marked-up text into a list of :class:`RichTextSpan`."""
    spans: list[RichTextSpan] = []
    buf: list[str] = []
    stack: list[_StyleFrame] = []

    def flush() -> None:
        if not buf:
            return
        segment = "".join(buf)
        buf.clear()
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
                )
            )
        else:
            spans.append(RichTextSpan(text=segment))

    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        # Backslash escapes: \{ -> {, \} -> }, \\ -> \
        if ch == "\\" and i + 1 < n and text[i + 1] in "{}\\":
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
            converted = base._convert_text(span.text)
            codes.append(f" {converted}}}")
            parts.append("".join(codes))
        return "".join(parts)


def rich_text(text: str, theme: dict[str, Any] | None = None) -> RichText:
    """Create rich text with inline formatting for use in table cells.

    Markers use ``{tag ...}`` syntax, inspired by ``r2rtf::rtf_rich_text()``:

    - ``{b ...}`` bold, ``{i ...}`` italic, ``{u ...}`` underline,
      ``{s ...}`` strikethrough, ``{^ ...}`` superscript, ``{_ ...}``
      subscript. Tags nest, e.g. ``{b bold {i bold-italic}}``.
    - ``{.name ...}`` applies a theme entry (see ``theme``).
    - ``\\{``, ``\\}`` and ``\\\\`` produce literal ``{``, ``}`` and ``\\``.

    Args:
        text: Text with inline formatting markers.
        theme: Optional mapping of custom tag names (used as ``{.name ...}``)
            to either a format-code string (e.g. ``"bi"``) or a dict with
            ``format``, ``color``, ``background_color``, ``font`` and
            ``font_size`` keys. The default theme provides ``.emph``
            (italic) and ``.strong`` (bold), matching r2rtf.

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
        ValueError: On unknown tags, unbalanced braces, or invalid
            format/color specifications.
        TypeError: If ``text`` is not a string.
    """
    return RichText(text, theme=theme)
