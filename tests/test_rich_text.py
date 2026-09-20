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
        assert rt.spans == [RichTextSpan(text="a {b} c", escaped=frozenset({2, 4}))]

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


class TestEscapeSerialization:
    """P2-1: literal escapes survive parsing and render as literals in RTF."""

    @staticmethod
    def _encode(value):
        df = pl.DataFrame({"A": pl.Series([value], dtype=pl.Object)})
        return rtf.RTFDocument(df=df, rtf_body=rtf.RTFBody()).rtf_encode()

    @staticmethod
    def _structural_braces_balanced(content: str) -> bool:
        stripped = content.replace("\\\\", "").replace("\\{", "").replace("\\}", "")
        return stripped.count("{") == stripped.count("}")

    def test_escaped_braces_render_as_literals(self):
        content = self._encode(rtf.rich_text(r"a \{b\} c"))
        # The braces stay literal RTF escapes; no group opens/closes.
        assert r"a \{b\} c" in content
        assert self._structural_braces_balanced(content)

    def test_escaped_backslash_not_converted_to_latex(self):
        content = self._encode(rtf.rich_text(r"a \\alpha b"))
        # Must not become the alpha character or an RTF control word.
        assert "\u03b1" not in content
        assert r"a \\alpha b" in content

    def test_escaped_close_brace_keeps_structure(self):
        content = self._encode(rtf.rich_text(r"a \} b"))
        assert r"a \} b" in content
        assert self._structural_braces_balanced(content)

    def test_escaped_backslash_before_tag_marker(self):
        # "\\{b" is a literal backslash followed by a real bold tag.
        content = self._encode(rtf.rich_text(r"\\{b x}"))
        assert r"\\" in content
        assert r"\b x}" in content
        assert self._structural_braces_balanced(content)


class TestSpanColorTable:
    """P2-2: span colors are registered in the document color table."""

    @staticmethod
    def _encode(df):
        return rtf.RTFDocument(df=df, rtf_body=rtf.RTFBody()).rtf_encode()

    def test_span_colors_registered_with_rgb_entries(self):
        import re

        theme = {".warn": {"color": "red", "background_color": "yellow"}}
        df = pl.DataFrame(
            {"A": pl.Series([rtf.rich_text("{.warn x}", theme=theme)], dtype=pl.Object)}
        )
        content = self._encode(df)
        assert r"{\colortbl" in content
        # The RGB entries from the named colors are present...
        assert r"\red255\green0\blue0" in content
        assert r"\red255\green255\blue0" in content
        # ...and the spans reference nonzero table indices.
        refs = set(re.findall(r"\\c[fb](\d+)", content))
        assert refs, "expected nonzero color references"
        assert "0" not in refs

    def test_multi_section_span_colors_all_registered(self):
        df1 = pl.DataFrame(
            {
                "A": pl.Series(
                    [rtf.rich_text("{.warn x}", theme={".warn": {"color": "red"}})],
                    dtype=pl.Object,
                )
            }
        )
        df2 = pl.DataFrame(
            {
                "A": pl.Series(
                    [
                        rtf.rich_text(
                            "{.note y}",
                            theme={".note": {"background_color": "yellow"}},
                        )
                    ],
                    dtype=pl.Object,
                )
            }
        )
        doc = rtf.RTFDocument(df=[df1, df2], rtf_body=[rtf.RTFBody(), rtf.RTFBody()])
        content = doc.rtf_encode()
        assert r"\red255\green0\blue0" in content
        assert r"\red255\green255\blue0" in content


class TestRichTextGrouping:
    """P2-3: RichText values participate in group_by processing."""

    @staticmethod
    def _frame():
        return pl.DataFrame(
            {
                "A": pl.Series(
                    [
                        rtf.rich_text("{b Group}"),
                        rtf.rich_text("{b Group}"),
                        rtf.rich_text("{b Other}"),
                    ],
                    dtype=pl.Object,
                ),
                "B": ["x", "y", "z"],
            }
        )

    def test_duplicate_suppression_keeps_rich_text_objects(self):
        from rtflite.services.grouping_service import GroupingService

        suppressed = GroupingService().enhance_group_by(self._frame(), ["A"])
        values = suppressed["A"].to_list()
        assert isinstance(values[0], RichText)
        assert values[1] is None
        assert isinstance(values[2], RichText)

    def test_restore_page_context_restores_rich_text(self):
        from rtflite.services.grouping_service import GroupingService

        df = self._frame()
        gs = GroupingService()
        suppressed = gs.enhance_group_by(df, ["A"])
        # Page 2 starts at the suppressed duplicate row; the original
        # formatted group header must come back.
        restored = gs.restore_page_context(suppressed, df, ["A"], [1])
        assert isinstance(restored["A"][1], RichText)
        assert restored["A"][1].plain_text == "Group"
        assert str(restored["A"][1].spans[0].formats) == str(frozenset({"b"}))

    def test_hierarchical_group_by_with_object_column(self):
        from rtflite.services.grouping_service import GroupingService

        df = pl.DataFrame(
            {
                "A": pl.Series(
                    [
                        rtf.rich_text("{b G}"),
                        rtf.rich_text("{b G}"),
                        rtf.rich_text("{b H}"),
                    ],
                    dtype=pl.Object,
                ),
                "B": ["x", "x", "y"],
                "C": [1, 2, 3],
            }
        )
        suppressed = GroupingService().enhance_group_by(df, ["A", "B"])
        a_values = suppressed["A"].to_list()
        assert isinstance(a_values[0], RichText)
        assert a_values[1] is None
        assert isinstance(a_values[2], RichText)

    def test_sorting_validation_accepts_contiguous_rich_text(self):
        from rtflite.services.grouping_service import GroupingService

        # Must not raise for contiguous groups of RichText values.
        GroupingService().validate_data_sorting(self._frame(), ["A"])

    def test_sorting_validation_rejects_split_rich_text_group(self):
        from rtflite.services.grouping_service import GroupingService

        df = pl.DataFrame(
            {
                "A": pl.Series(
                    [
                        rtf.rich_text("{b G}"),
                        rtf.rich_text("{b H}"),
                        rtf.rich_text("{b G}"),
                    ],
                    dtype=pl.Object,
                )
            }
        )
        with pytest.raises(ValueError, match="not properly grouped"):
            GroupingService().validate_data_sorting(df, ["A"])

    def test_document_group_by_renders_rich_text_headers(self):
        df = self._frame()
        doc = rtf.RTFDocument(df=df, rtf_body=rtf.RTFBody(group_by=["A"]))
        content = doc.rtf_encode()
        assert r"\b Group" in content
        assert r"\b Other" in content


class TestSupSubNesting:
    """P2-4: inner superscript/subscript overrides the outer one."""

    def test_inner_sup_replaces_outer_sub(self):
        rt = rich_text("{_ sub {^ sup} sub}")
        assert [s.text for s in rt.spans] == ["sub ", "sup", " sub"]
        assert rt.spans[0].formats == frozenset({"_"})
        assert rt.spans[1].formats == frozenset({"^"})
        assert rt.spans[2].formats == frozenset({"_"})

    def test_inner_sub_replaces_outer_sup(self):
        rt = rich_text("{^ sup {_ sub} sup}")
        assert rt.spans[0].formats == frozenset({"^"})
        assert rt.spans[1].formats == frozenset({"_"})

    def test_nested_same_script_still_combines(self):
        rt = rich_text("{b bold {^ sup} bold}")
        assert rt.spans[1].formats == frozenset({"b", "^"})

    def test_combined_sup_sub_tag_rejected(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            rich_text("{^_ x}")
        with pytest.raises(ValueError, match="mutually exclusive"):
            rich_text("{_^ x}")

    def test_theme_format_combining_sup_sub_rejected(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            rich_text("{.t x}", theme={".t": {"format": "^_"}})

    def test_rendered_inner_span_has_single_script(self):
        import re

        df = pl.DataFrame({"A": [rtf.rich_text("{_ a {^ b}}")]})
        content = rtf.RTFDocument(df=df, rtf_body=rtf.RTFBody()).rtf_encode()
        groups = re.findall(r"\{\\f\d+\\fs\d+[^}]*\}", content)
        inner = [g for g in groups if " b}" in g]
        assert inner, "expected an inner span group"
        assert r"\super" in inner[0]
        assert r"\sub" not in inner[0]


class TestFontValidation:
    """P2-5: theme font ids and sizes are validated."""

    def test_font_id_zero_rejected(self):
        with pytest.raises(ValueError, match="Invalid font"):
            rich_text("{.f x}", theme={".f": {"font": 0}})

    def test_font_id_eleven_rejected(self):
        with pytest.raises(ValueError, match="Invalid font"):
            rich_text("{.f x}", theme={".f": {"font": 11}})

    def test_font_id_fractional_rejected(self):
        with pytest.raises(ValueError, match="Invalid font"):
            rich_text("{.f x}", theme={".f": {"font": 1.9}})

    def test_font_id_bool_rejected(self):
        with pytest.raises(ValueError, match="Invalid font"):
            rich_text("{.f x}", theme={".f": {"font": True}})

    def test_font_size_nan_rejected(self):
        with pytest.raises(ValueError, match="font_size"):
            rich_text("{.f x}", theme={".f": {"font_size": float("nan")}})

    def test_font_size_inf_rejected(self):
        with pytest.raises(ValueError, match="font_size"):
            rich_text("{.f x}", theme={".f": {"font_size": float("inf")}})

    def test_font_size_nonpositive_rejected(self):
        with pytest.raises(ValueError, match="font_size"):
            rich_text("{.f x}", theme={".f": {"font_size": 0}})
        with pytest.raises(ValueError, match="font_size"):
            rich_text("{.f x}", theme={".f": {"font_size": -3}})

    def test_font_size_non_numeric_rejected(self):
        with pytest.raises(ValueError, match="font_size"):
            rich_text("{.f x}", theme={".f": {"font_size": "big"}})

    def test_valid_font_and_size_render(self):
        df = pl.DataFrame(
            {"A": [rtf.rich_text("{.f x}", theme={".f": {"font": 4, "font_size": 14}})]}
        )
        content = rtf.RTFDocument(df=df, rtf_body=rtf.RTFBody()).rtf_encode()
        # Font 4 -> \f3, 14pt -> \fs28.
        assert r"\f3" in content
        assert r"\fs28" in content


class TestPaginationMetrics:
    """P2-6: inline font/size metrics feed pagination estimates."""

    @staticmethod
    def _calculator():
        from rtflite.pagination import RTFPagination
        from rtflite.pagination.core import PageBreakCalculator

        return PageBreakCalculator(
            pagination=RTFPagination(
                page_width=8.5,
                page_height=11,
                margin=[1, 1, 1, 1, 0.5, 0.5],
                nrow=40,
                orientation="portrait",
            )
        )

    def test_measured_width_honors_span_font_size(self):
        theme = {".big": {"font_size": 36}}
        text = "word " * 15
        base = rtf.rich_text(text)
        big = rtf.rich_text("{.big " + text + "}", theme=theme)
        assert big.measured_width(font_size=9) > 3 * base.measured_width(font_size=9)

    def test_mixed_size_pagination_estimates_more_rows(self):
        theme = {".big": {"font_size": 36}}
        text = "word " * 15
        df_small = pl.DataFrame(
            {"A": pl.Series([rtf.rich_text(text)], dtype=pl.Object)}
        )
        df_big = pl.DataFrame(
            {
                "A": pl.Series(
                    [rtf.rich_text("{.big " + text + "}", theme=theme)],
                    dtype=pl.Object,
                )
            }
        )
        calc = self._calculator()
        small = calc.calculate_row_metadata(df_small, col_widths=[1.0], font_size=9)
        big = calc.calculate_row_metadata(df_big, col_widths=[1.0], font_size=9)
        small_rows = small["data_rows"].to_list()[0]
        big_rows = big["data_rows"].to_list()[0]
        assert small_rows == 5
        assert big_rows > small_rows

    def test_calculate_lines_uses_span_width(self):
        attrs = rtf.TableAttributes(text_font=1, text_font_size=9)
        text = "word " * 15
        plain_lines = attrs.calculate_lines(
            text=text, available_width=1.0, row_idx=0, col_idx=0
        )
        rich_lines = attrs.calculate_lines(
            text=rtf.rich_text(
                "{.big " + text + "}", theme={".big": {"font_size": 36}}
            ),
            available_width=1.0,
            row_idx=0,
            col_idx=0,
        )
        assert rich_lines > plain_lines
