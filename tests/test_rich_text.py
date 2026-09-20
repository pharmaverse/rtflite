"""Tests for rtflite.rich_text (issue #41: inline text formatting)."""

import polars as pl
import pytest

import rtflite as rtf
from rtflite.rich_text import RichText, RichTextSpan, rich_text


class TestParsing:
    def test_plain_text_has_single_span(self):
        rt = rich_text("hello world")
        assert rt.spans == [RichTextSpan(text="hello world")]
        assert str(rt) == "hello world"

    def test_builtin_tags(self):
        rt = rich_text("n=50 {b (75%)}")
        assert [s.text for s in rt.spans] == ["n=50 ", "(75%)"]
        assert rt.spans[0].formats == frozenset()
        assert rt.spans[1].formats == frozenset({"b"})

    def test_all_format_codes(self):
        rt = rich_text("{b b}{i i}{u u}{s s}{^ sup}{_ sub}")
        assert [s.formats for s in rt.spans] == [
            frozenset({"b"}),
            frozenset({"i"}),
            frozenset({"u"}),
            frozenset({"s"}),
            frozenset({"^"}),
            frozenset({"_"}),
        ]

    def test_combined_tag(self):
        rt = rich_text("{bi bold-italic}")
        assert rt.spans[0].formats == frozenset({"b", "i"})

    def test_nested_tags_combine(self):
        rt = rich_text("{b bold {i both} bold}")
        assert [s.text for s in rt.spans] == ["bold ", "both", " bold"]
        assert rt.spans[0].formats == frozenset({"b"})
        assert rt.spans[1].formats == frozenset({"b", "i"})
        assert rt.spans[2].formats == frozenset({"b"})

    def test_escaped_braces(self):
        rt = rich_text("a \\{b\\} c")
        assert str(rt) == "a {b} c"
        assert rt.spans == [RichTextSpan(text="a {b} c")]

    def test_escaped_braces_inside_tag(self):
        rt = rich_text("{b a \\{b\\} c}")
        assert rt.spans[0].text == "a {b} c"
        assert rt.spans[0].formats == frozenset({"b"})

    def test_escaped_backslash(self):
        rt = rich_text("a \\\\ b")
        assert str(rt) == "a \\ b"

    def test_nested_close_braces(self):
        # '}}' closes two nested tags; it is NOT an escape sequence
        rt = rich_text("{b bold {i both}}")
        assert [s.text for s in rt.spans] == ["bold ", "both"]
        assert rt.spans[1].formats == frozenset({"b", "i"})

    def test_empty_tag_span(self):
        rt = rich_text("a{b}b")
        assert str(rt) == "ab"

    def test_unmatched_closing_brace_raises(self):
        with pytest.raises(ValueError, match="Unmatched closing brace"):
            rich_text("a } b")

    def test_unclosed_tag_raises(self):
        with pytest.raises(ValueError, match="Unclosed tag"):
            rich_text("a {b bold")

    def test_unknown_tag_raises(self):
        with pytest.raises(ValueError, match="Unknown tag"):
            rich_text("a {xyz bold}")

    def test_invalid_format_char_raises(self):
        with pytest.raises(ValueError, match="Unknown tag"):
            rich_text("a {q bold}")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            rich_text(123)  # type: ignore[arg-type]

    def test_repr_and_eq(self):
        assert repr(rich_text("a {b b}")) == "RichText('a {b b}')"
        assert rich_text("a {b b}") == rich_text("a {b b}")
        assert rich_text("a {b b}") != rich_text("a {i b}")


class TestTheme:
    def test_default_theme_emph_strong(self):
        rt = rich_text("This is {.emph important}. This is {.strong relevant}.")
        formats = [s.formats for s in rt.spans]
        assert frozenset({"i"}) in formats
        assert frozenset({"b"}) in formats

    def test_unknown_theme_tag_raises(self):
        with pytest.raises(ValueError, match="Unknown theme tag"):
            rich_text("a {.nope x}")

    def test_custom_theme_format_string(self):
        rt = rich_text("a {.note x}", theme={".note": "bi"})
        assert rt.spans[0].formats == frozenset()
        assert rt.spans[1].formats == frozenset({"b", "i"})

    def test_custom_theme_overrides_default(self):
        rt = rich_text("{.emph x}", theme={".emph": "b"})
        assert rt.spans[0].formats == frozenset({"b"})

    def test_custom_theme_dict_with_color(self):
        rt = rich_text(
            "a {.warn x}",
            theme={".warn": {"format": "b", "color": "red"}},
        )
        assert rt.spans[1].formats == frozenset({"b"})
        assert rt.spans[1].color == "red"

    def test_custom_theme_dict_with_background(self):
        rt = rich_text("{.hl x}", theme={".hl": {"background_color": "yellow"}})
        assert rt.spans[0].background_color == "yellow"

    def test_custom_theme_invalid_color_raises(self):
        with pytest.raises(ValueError, match="Invalid color"):
            rich_text("{.warn x}", theme={".warn": {"color": "notacolor"}})

    def test_custom_theme_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid format"):
            rich_text("{.warn x}", theme={".warn": {"format": "q"}})

    def test_custom_theme_unknown_option_raises(self):
        with pytest.raises(ValueError, match="Unknown theme option"):
            rich_text("{.warn x}", theme={".warn": {"bogus": 1}})

    def test_custom_theme_bad_type_raises(self):
        with pytest.raises(TypeError):
            rich_text("{.warn x}", theme={".warn": 42})


class TestRTFRendering:
    @staticmethod
    def _read(path):
        with open(path) as f:
            return f.read()

    def _cell_rtf(self, value, **kwargs):
        df = pl.DataFrame({"A": [value]})
        doc = rtf.RTFDocument(df=df, **kwargs)
        path = "/tmp/test_rich_text.rtf"
        doc.write_rtf(path)
        return path

    def test_bold_italic_spans_in_output(self):
        path = self._cell_rtf(rtf.rich_text("Normal {b Bold} and {i italic}"))
        content = self._read(path)
        assert r"{\f0\fs18 Normal }" in content
        assert r"{\f0\fs18\b Bold}" in content
        assert r"{\f0\fs18\i italic}" in content
        # No raw markers leak into output
        assert "{b " not in content
        assert "{i " not in content

    def test_plain_string_cells_unaffected(self):
        path = self._cell_rtf("just plain")
        content = self._read(path)
        assert "just plain" in content
        assert r"\b" not in content.split("just plain")[0][-20:]

    def test_mixed_plain_and_rich_cells(self):
        # Mixed columns need Object dtype so polars keeps RichText objects
        df = pl.DataFrame(
            {
                "A": pl.Series(["plain", rtf.rich_text("{b bold}")], dtype=pl.Object),
                "B": [1, 2],
            }
        )
        doc = rtf.RTFDocument(df=df)
        path = "/tmp/test_rich_text.rtf"
        doc.write_rtf(path)
        content = self._read(path)
        assert "plain" in content
        assert r"{\f0\fs18\b bold}" in content

    def test_cell_level_format_combines_with_spans(self):
        path = self._cell_rtf(
            rtf.rich_text("a {i b}"),
            rtf_body=rtf.RTFBody(text_format="b"),
        )
        content = self._read(path)
        # Cell-level bold applies; span adds italic inside its group
        assert r"{\f0\fs18\i b}" in content
        assert r"\b" in content

    def test_theme_color_span_in_output(self):
        path = self._cell_rtf(
            rtf.rich_text("{.warn x}", theme={".warn": {"color": "red"}})
        )
        content = self._read(path)
        assert r"\cf" in content
        assert " x}" in content

    def test_special_chars_still_converted_in_spans(self):
        path = self._cell_rtf(rtf.rich_text("{b 50% < 60%}"))
        content = self._read(path)
        assert "50" in content and "60" in content

    def test_nested_span_output(self):
        path = self._cell_rtf(rtf.rich_text("{b bold {i both}}"))
        content = self._read(path)
        assert r"{\f0\fs18\b bold }" in content
        assert r"{\f0\fs18\b\i both}" in content

    def test_issue_41_minimal_example(self):
        df = pl.DataFrame(
            {
                "Treatment": ["Placebo", "Drug A"],
                "Response": [
                    rtf.rich_text("n=50 {b (75%)}"),
                    rtf.rich_text("n=48 {b (92%)}"),
                ],
            }
        )
        doc = rtf.RTFDocument(df=df)
        path = "/tmp/test_rich_text.rtf"
        doc.write_rtf(path)
        content = self._read(path)
        assert r"{\f0\fs18\b (75%)}" in content
        assert r"{\f0\fs18\b (92%)}" in content
        assert "Placebo" in content and "Drug A" in content

    def test_rich_text_exported_at_package_level(self):
        assert rtf.rich_text is rich_text
        assert rtf.RichText is RichText
        assert "rich_text" in rtf.__all__
        assert "RichText" in rtf.__all__
