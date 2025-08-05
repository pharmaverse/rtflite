"""Comprehensive single-page RTF tests with R2RTF comparisons."""

import polars as pl

import rtflite as rtf

from .utils import ROutputReader
from .utils_snapshot import assert_rtf_equals_semantic

r_output = ROutputReader("test_single_page_rtf")


class TestSinglePageColumnHeaders:
    """Test column header variations for single-page documents."""

    def test_multi_level_header_with_borders(self):
        """Test multi-level column headers with custom borders."""
        # ```{r, multi_level_header_borders}
        # library(r2rtf)
        # df <- data.frame(
        #   Category = c("A", "B", "C"),
        #   Value1 = c(10, 20, 30),
        #   Value2 = c(15, 25, 35),
        #   Value3 = c(12, 22, 32)
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = " | Treatment Group",
        #     col_rel_width = c(2, 3),
        #     border_bottom = c("", "single")
        #   ) |>
        #   rtf_colheader(
        #     colheader = "Category | Low Dose | Medium Dose | High Dose",
        #     col_rel_width = c(2, 1, 1, 1),
        #     border_top = c("", "single", "single", "single")
        #   ) |>
        #   rtf_body(col_rel_width = c(2, 1, 1, 1)) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Category": ["A", "B", "C"],
                "Value1": [10, 20, 30],
                "Value2": [15, 25, 35],
                "Value3": [12, 22, 32],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["", "Treatment Group"],
                    col_rel_width=[2, 3],
                    border_bottom=["", "single"],
                ),
                rtf.RTFColumnHeader(
                    text=["Category", "Low Dose", "Medium Dose", "High Dose"],
                    col_rel_width=[2, 1, 1, 1],
                    border_top=["", "single", "single", "single"],
                ),
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[2, 1, 1, 1]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("multi_level_header_borders")
        assert_rtf_equals_semantic(
            rtf_output, expected, "test_multi_level_header_borders"
        )

    def test_header_text_justification(self):
        """Test column headers with different text justifications."""
        # ```{r, header_text_justification}
        # library(r2rtf)
        # df <- data.frame(
        #   Left = c("Item 1", "Item 2"),
        #   Center = c("Value A", "Value B"),
        #   Right = c(100, 200)
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Left Aligned | Center Aligned | Right Aligned",
        #     col_rel_width = c(1, 1, 1),
        #     text_justification = c("l", "c", "r")
        #   ) |>
        #   rtf_body(
        #     col_rel_width = c(1, 1, 1),
        #     text_justification = c("l", "c", "r")
        #   ) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Left": ["Item 1", "Item 2"],
                "Center": ["Value A", "Value B"],
                "Right": [100, 200],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Left Aligned", "Center Aligned", "Right Aligned"],
                    col_rel_width=[1, 1, 1],
                    text_justification=["l", "c", "r"],
                )
            ],
            rtf_body=rtf.RTFBody(
                col_rel_width=[1, 1, 1], text_justification=["l", "c", "r"]
            ),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("header_text_justification")
        assert_rtf_equals_semantic(
            rtf_output, expected, "test_header_text_justification"
        )

    def test_header_font_formatting(self):
        """Test column headers with font formatting."""
        # ```{r, header_font_formatting}
        # library(r2rtf)
        # df <- data.frame(
        #   Normal = c("A", "B"),
        #   Bold = c("X", "Y"),
        #   Italic = c("1", "2")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Normal | Bold | Italic",
        #     col_rel_width = c(1, 1, 1),
        #     text_format = c("", "b", "i"),
        #     text_font_size = c(9, 10, 9)
        #   ) |>
        #   rtf_body(col_rel_width = c(1, 1, 1)) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {"Normal": ["A", "B"], "Bold": ["X", "Y"], "Italic": ["1", "2"]}
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Normal", "Bold", "Italic"],
                    col_rel_width=[1, 1, 1],
                    text_format=["", "b", "i"],
                    text_font_size=[9, 10, 9],
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1, 1]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("header_font_formatting")
        assert_rtf_equals_semantic(rtf_output, expected, "test_header_font_formatting")


class TestSinglePageBody:
    """Test body formatting variations for single-page documents."""

    def test_body_border_combinations(self):
        """Test body with various border combinations."""
        # ```{r, body_border_combinations}
        # library(r2rtf)
        # df <- data.frame(
        #   Col1 = c("A", "B", "C"),
        #   Col2 = c(1, 2, 3),
        #   Col3 = c("X", "Y", "Z")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Column 1 | Column 2 | Column 3",
        #     col_rel_width = c(1, 1, 1)
        #   ) |>
        #   rtf_body(
        #     col_rel_width = c(1, 1, 1),
        #     border_left = c("single", "", ""),
        #     border_right = c("", "", "single"),
        #     border_top = c("", "single", ""),
        #     border_bottom = c("", "single", "")
        #   ) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {"Col1": ["A", "B", "C"], "Col2": [1, 2, 3], "Col3": ["X", "Y", "Z"]}
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Column 1", "Column 2", "Column 3"], col_rel_width=[1, 1, 1]
                )
            ],
            rtf_body=rtf.RTFBody(
                col_rel_width=[1, 1, 1],
                border_left=["single", "", ""],
                border_right=["", "", "single"],
                border_top=["", "single", ""],
                border_bottom=["", "single", ""],
            ),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("body_border_combinations")
        assert_rtf_equals_semantic(
            rtf_output, expected, "test_body_border_combinations"
        )

    def test_body_cell_height_variations(self):
        """Test body with different cell heights."""
        # ```{r, body_cell_height_variations}
        # library(r2rtf)
        # df <- data.frame(
        #   Normal = c("Row 1", "Row 2"),
        #   Tall = c("Tall 1", "Tall 2"),
        #   Short = c("Short 1", "Short 2")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Normal Height | Tall Cells | Short Cells",
        #     col_rel_width = c(1, 1, 1)
        #   ) |>
        #   rtf_body(
        #     col_rel_width = c(1, 1, 1),
        #     cell_height = 0.25
        #   ) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Normal": ["Row 1", "Row 2"],
                "Tall": ["Tall 1", "Tall 2"],
                "Short": ["Short 1", "Short 2"],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Normal Height", "Tall Cells", "Short Cells"],
                    col_rel_width=[1, 1, 1],
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1, 1], cell_height=0.25),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("body_cell_height_variations")
        assert_rtf_equals_semantic(
            rtf_output, expected, "test_body_cell_height_variations"
        )

    def test_body_font_size_per_column(self):
        """Test body with different font sizes per column."""
        # ```{r, body_font_size_per_column}
        # library(r2rtf)
        # df <- data.frame(
        #   Small = c("Small 1", "Small 2"),
        #   Normal = c("Normal 1", "Normal 2"),
        #   Large = c("Large 1", "Large 2")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Small Font | Normal Font | Large Font",
        #     col_rel_width = c(1, 1, 1)
        #   ) |>
        #   rtf_body(
        #     col_rel_width = c(1, 1, 1),
        #     text_font_size = c(7, 9, 12)
        #   ) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Small": ["Small 1", "Small 2"],
                "Normal": ["Normal 1", "Normal 2"],
                "Large": ["Large 1", "Large 2"],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Small Font", "Normal Font", "Large Font"],
                    col_rel_width=[1, 1, 1],
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1, 1], text_font_size=[7, 9, 12]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("body_font_size_per_column")
        assert_rtf_equals_semantic(
            rtf_output, expected, "test_body_font_size_per_column"
        )


class TestSinglePageComplete:
    """Test complete single-page documents with all components."""

    def test_minimal_document(self):
        """Test minimal RTF document with just data."""
        # ```{r, minimal_document}
        # library(r2rtf)
        # df <- data.frame(
        #   A = c(1, 2, 3),
        #   B = c(4, 5, 6)
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_body() |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        doc = rtf.RTFDocument(df=df)

        rtf_output = doc.rtf_encode()
        expected = r_output.read("minimal_document")
        assert_rtf_equals_semantic(rtf_output, expected, "test_minimal_document")

    def test_title_header_body(self):
        """Test document with title, column header, and body."""
        # ```{r, title_header_body}
        # library(r2rtf)
        # df <- data.frame(
        #   Subject = c("001", "002", "003"),
        #   Treatment = c("A", "B", "A"),
        #   Response = c("Yes", "No", "Yes")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_title(
        #     title = c("Clinical Trial Results", "Study XYZ-123"),
        #     text_format = c("b", "")
        #   ) |>
        #   rtf_colheader(
        #     colheader = "Subject ID | Treatment Group | Response",
        #     col_rel_width = c(1, 1, 1)
        #   ) |>
        #   rtf_body(col_rel_width = c(1, 1, 1)) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Subject": ["001", "002", "003"],
                "Treatment": ["A", "B", "A"],
                "Response": ["Yes", "No", "Yes"],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_title=rtf.RTFTitle(
                text=["Clinical Trial Results", "Study XYZ-123"], text_format=["b", ""]
            ),
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Subject ID", "Treatment Group", "Response"],
                    col_rel_width=[1, 1, 1],
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1, 1]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("title_header_body")
        assert_rtf_equals_semantic(rtf_output, expected, "test_title_header_body")

    def test_all_components_basic(self):
        """Test document with all components: title, header, body, footnote, source."""
        # ```{r, all_components_basic}
        # library(r2rtf)
        # df <- data.frame(
        #   Variable = c("Age", "Weight", "Height"),
        #   Mean = c(45.2, 70.5, 168.3),
        #   SD = c(12.1, 15.3, 10.2)
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_title("Summary Statistics") |>
        #   rtf_colheader(
        #     colheader = "Variable | Mean | SD",
        #     col_rel_width = c(2, 1, 1)
        #   ) |>
        #   rtf_body(col_rel_width = c(2, 1, 1)) |>
        #   rtf_footnote("SD = Standard Deviation") |>
        #   rtf_source("Data collected: 2024") |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Variable": ["Age", "Weight", "Height"],
                "Mean": [45.2, 70.5, 168.3],
                "SD": [12.1, 15.3, 10.2],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_title=rtf.RTFTitle(text="Summary Statistics"),
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Variable", "Mean", "SD"], col_rel_width=[2, 1, 1]
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[2, 1, 1]),
            rtf_footnote=rtf.RTFFootnote(text="SD = Standard Deviation"),
            rtf_source=rtf.RTFSource(text="Data collected: 2024"),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("all_components_basic")
        assert_rtf_equals_semantic(rtf_output, expected, "test_all_components_basic")

    def test_single_row_table(self):
        """Test handling of single row table."""
        # ```{r, single_row_table}
        # library(r2rtf)
        # df <- data.frame(
        #   Col1 = "Single Value",
        #   Col2 = 42
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_title("Single Row Table") |>
        #   rtf_colheader(
        #     colheader = "Column 1 | Column 2",
        #     col_rel_width = c(1, 1)
        #   ) |>
        #   rtf_body(col_rel_width = c(1, 1)) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame({"Col1": ["Single Value"], "Col2": [42]})

        doc = rtf.RTFDocument(
            df=df,
            rtf_title=rtf.RTFTitle(text="Single Row Table"),
            rtf_column_header=[
                rtf.RTFColumnHeader(text=["Column 1", "Column 2"], col_rel_width=[1, 1])
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("single_row_table")
        assert_rtf_equals_semantic(rtf_output, expected, "test_single_row_table")


class TestSinglePageTextConversion:
    """Test text conversion features in single-page documents."""

    def test_latex_in_body_cells(self):
        """Test LaTeX symbols in body cells with conversion enabled."""
        # ```{r, latex_in_body_cells}
        # library(r2rtf)
        # df <- data.frame(
        #   Symbol = c("\\alpha", "\\beta", "\\gamma"),
        #   Value = c("\\leq 0.05", "\\pm 1.96", "\\sum x_i"),
        #   Description = c("Greek alpha", "Greek beta", "Greek gamma")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Symbol | Value | Description",
        #     col_rel_width = c(1, 2, 2)
        #   ) |>
        #   rtf_body(
        #     col_rel_width = c(1, 2, 2),
        #     text_convert = TRUE
        #   ) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Symbol": ["\\alpha", "\\beta", "\\gamma"],
                "Value": ["\\leq 0.05", "\\pm 1.96", "\\sum x_i"],
                "Description": ["Greek alpha", "Greek beta", "Greek gamma"],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Symbol", "Value", "Description"], col_rel_width=[1, 2, 2]
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 2, 2], text_convert=[True]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("latex_in_body_cells")
        assert_rtf_equals_semantic(rtf_output, expected, "test_latex_in_body_cells")

    def test_special_chars_in_headers(self):
        """Test special characters in column headers."""
        # ```{r, special_chars_in_headers}
        # library(r2rtf)
        # df <- data.frame(
        #   Col1 = c("A", "B"),
        #   Col2 = c("X", "Y"),
        #   Col3 = c(1, 2)
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "\\alpha Level | \\beta Value | n\\geq10",
        #     col_rel_width = c(1, 1, 1),
        #     text_convert = TRUE
        #   ) |>
        #   rtf_body(col_rel_width = c(1, 1, 1)) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame({"Col1": ["A", "B"], "Col2": ["X", "Y"], "Col3": [1, 2]})

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["\\alpha Level", "\\beta Value", "n\\geq10"],
                    col_rel_width=[1, 1, 1],
                    text_convert=[True],
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1, 1]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("special_chars_in_headers")
        assert_rtf_equals_semantic(
            rtf_output, expected, "test_special_chars_in_headers"
        )

    def test_conversion_toggle(self):
        """Test toggling text conversion on/off for different components."""
        # ```{r, conversion_toggle}
        # library(r2rtf)
        # df <- data.frame(
        #   Raw = c("\\alpha", "\\beta"),
        #   Converted = c("\\alpha", "\\beta")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_title("\\alpha = 0.05", text_convert = TRUE) |>
        #   rtf_colheader(
        #     colheader = "Raw \\LaTeX | Converted \\LaTeX",
        #     col_rel_width = c(1, 1),
        #     text_convert = c(FALSE, TRUE)
        #   ) |>
        #   rtf_body(
        #     col_rel_width = c(1, 1),
        #     text_convert = c(FALSE, TRUE)
        #   ) |>
        #   rtf_footnote("\\dagger p < 0.05", text_convert = TRUE) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {"Raw": ["\\alpha", "\\beta"], "Converted": ["\\alpha", "\\beta"]}
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_title=rtf.RTFTitle(text="\\alpha = 0.05", text_convert=[True]),
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Raw \\LaTeX", "Converted \\LaTeX"],
                    col_rel_width=[1, 1],
                    text_convert=[False, True],
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 1], text_convert=[False, True]),
            rtf_footnote=rtf.RTFFootnote(text="\\dagger p < 0.05", text_convert=[True]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("conversion_toggle")
        assert_rtf_equals_semantic(rtf_output, expected, "test_conversion_toggle")


class TestSinglePageEdgeCases:
    """Test edge cases for single-page documents."""

    def test_single_column_table(self):
        """Test table with only one column."""
        # ```{r, single_column_table}
        # library(r2rtf)
        # df <- data.frame(
        #   Items = c("First Item", "Second Item", "Third Item", "Fourth Item")
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "List of Items",
        #     col_rel_width = 1
        #   ) |>
        #   rtf_body(col_rel_width = 1) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {"Items": ["First Item", "Second Item", "Third Item", "Fourth Item"]}
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(text=["List of Items"], col_rel_width=[1])
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("single_column_table")
        assert_rtf_equals_semantic(rtf_output, expected, "test_single_column_table")

    def test_long_cell_content(self):
        """Test handling of very long cell content."""
        # ```{r, long_cell_content}
        # library(r2rtf)
        # df <- data.frame(
        #   Short = c("A", "B"),
        #   Long = c(
        #     "This is a very long text that might wrap to multiple lines in the RTF cell",
        #     "Another long piece of text that demonstrates how the RTF handles wrapping"
        #   )
        # )
        #
        # df |>
        #   rtf_page() |>
        #   rtf_colheader(
        #     colheader = "Short | Long Description",
        #     col_rel_width = c(1, 4)
        #   ) |>
        #   rtf_body(col_rel_width = c(1, 4)) |>
        #   rtf_encode() |>
        #   write_rtf(tempfile()) |>
        #   readLines() |>
        #   cat(sep = "\n")
        # ```
        df = pl.DataFrame(
            {
                "Short": ["A", "B"],
                "Long": [
                    "This is a very long text that might wrap to multiple lines in the RTF cell",
                    "Another long piece of text that demonstrates how the RTF handles wrapping",
                ],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_column_header=[
                rtf.RTFColumnHeader(
                    text=["Short", "Long Description"], col_rel_width=[1, 4]
                )
            ],
            rtf_body=rtf.RTFBody(col_rel_width=[1, 4]),
        )

        rtf_output = doc.rtf_encode()
        expected = r_output.read("long_cell_content")
        assert_rtf_equals_semantic(rtf_output, expected, "test_long_cell_content")
