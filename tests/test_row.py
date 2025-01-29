import pytest

from rtflite.row import Border, Cell, Row, TextContent, Utils

from .utils import ROutputReader

r_output = ROutputReader("test_row")


# Test Utils class
def test_inch_to_twip():
    # Test common conversions (1 inch = 1440 twips)
    assert Utils._inch_to_twip(1) == 1440
    assert Utils._inch_to_twip(0.5) == 720
    assert Utils._inch_to_twip(0) == 0

    # Test small values
    assert Utils._inch_to_twip(0.0069444) == 10  # Approximately 10 twips


def test_get_color_index():
    # Test existing colors
    assert Utils._get_color_index("black") == 1
    assert Utils._get_color_index("red") == 2
    assert Utils._get_color_index("blue") == 4

    # Test non-existent color (should return 0 for black)
    assert Utils._get_color_index("nonexistent") == 0


# Test Text class
def test_text_initialization():
    text = TextContent(text="title")

    # ```{r, rtf_cell}
    # r2rtf:::rtf_paragraph(
    #   r2rtf:::rtf_text("title", font_size = 9),
    #   cell = TRUE,
    #   justification = "l",
    #   space_before = 15,
    #   space_after = 15
    # )[1, 1] |> cat(sep = "\n")
    # ```
    assert text._as_rtf(method="cell") == r_output.read("rtf_cell")
    # ```{r, rtf_paragraph}
    # r2rtf:::rtf_paragraph(
    #   r2rtf:::rtf_text("title", font_size = 9),
    #   cell = FALSE,
    #   justification = "l",
    #   space_before = 15,
    #   space_after = 15
    # )[1, 1] |> cat(sep = "\n")
    # ```
    assert text._as_rtf(method="paragraph") == r_output.read("rtf_paragraph")


def test_border_initialization():
    border = Border()

    # Test default border RTF string
    assert border._as_rtf() == "\\brdrs\\brdrw15"


def test_cell_initialization():
    cell = Cell(text=TextContent(text="sample"), width=1)


# Test default cell RTF string
def test_row_initialization():
    # Create a simple row with one cell
    row = Row(
        row_cells=[
            Cell(
                text=TextContent(text="col1", hyphenation=False, justification="c"),
                border_top=Border(style="double"),
                border_bottom=Border(style=""),
                border_right=None,
                width=3.125,
            ),
            Cell(
                text=TextContent(text="col2", hyphenation=False, justification="c"),
                border_top=Border(style="double"),
                border_bottom=Border(style=""),
                width=6.25,
            ),
        ]
    )

    # Test row RTF string generation
    # ```{r, rtf_row}
    # tbl <- cars |>
    #   head(2) |>
    #   r2rtf::rtf_title("title") |>
    #   r2rtf::rtf_colheader("col1|col2") |>
    #   r2rtf::rtf_body()
    # r2rtf:::rtf_encode_table(tbl, verbose = TRUE)$colheader |> cat(sep = "\n")
    # ```
    assert "\n".join(row._as_rtf()) == r_output.read("rtf_row")


def test_text_justification():
    # Test valid justification values
    assert (
        TextContent(text="test", justification="l")._get_paragraph_formatting()
        == "\\hyphpar\\sb15\\sa15\\fi0\\li0\\ri0\\ql"
    )
    assert (
        TextContent(text="test", justification="c")._get_paragraph_formatting()
        == "\\hyphpar\\sb15\\sa15\\fi0\\li0\\ri0\\qc"
    )
    assert (
        TextContent(text="test", justification="r")._get_paragraph_formatting()
        == "\\hyphpar\\sb15\\sa15\\fi0\\li0\\ri0\\qr"
    )
    assert (
        TextContent(text="test", justification="d")._get_paragraph_formatting()
        == "\\hyphpar\\sb15\\sa15\\fi0\\li0\\ri0\\qd"
    )
    assert (
        TextContent(text="test", justification="j")._get_paragraph_formatting()
        == "\\hyphpar\\sb15\\sa15\\fi0\\li0\\ri0\\qj"
    )

    # Test invalid justification value
    try:
        TextContent(text="test", justification="left")._get_paragraph_formatting()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        pass


def test_get_text_formatting():
    # Test basic text formatting
    assert (
        TextContent(text="Bold text", format="b")._as_rtf("plain")
        == "\\fs18{\\f0\\b Bold text}"
    )

    # Test multiple format characters
    assert (
        TextContent(text="Bold text", format="ibi")._as_rtf("plain")
        == "\\fs18{\\f0\\b\\i Bold text}"
    )
    assert (
        TextContent(text="Bold text", format="b^i")._as_rtf("plain")
        == "\\fs18{\\f0\\super\\b\\i Bold text}"
    )

    # Test with different font and size
    assert (
        TextContent(text="Custom text", font=2, size=12, format="u")._as_rtf("plain")
        == "\\fs24{\\f1\\ul Custom text}"
    )

    # Test invalid format character
    try:
        TextContent(text="test", format="xi")._get_text_formatting()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        pass


@pytest.mark.skip(reason="code not ready")
def test_get_text_colors():
    # Test text color
    # ```{r, rtf_fg}
    # r2rtf:::rtf_text("test", color = c("red"))[1, 1] |>
    #   cat(sep = "\n")
    # ```
    #
    # Test background color
    # ```{r, rtf_bg}
    # r2rtf:::rtf_text("test", background_color = c("blue"))[1, 1] |>
    #   cat(sep = "\n")
    # ```
    #
    # Test both colors together
    # ```{r, rtf_fg_bg}
    # r2rtf:::rtf_text("test", color = "red", background_color = c("blue"))[1, 1] |>
    #   cat(sep = "\n")
    # ```

    # Test text color
    assert TextContent(text="test", color="red")._as_rtf("plain") == r_output.read(
        "rtf_fg"
    )
    assert TextContent(text="test", color="#FF0000")._as_rtf("plain") == r_output.read(
        "rtf_fg"
    )

    # Test background color
    assert TextContent(text="test", background_color="blue")._as_rtf(
        "plain"
    ) == r_output.read("rtf_bg")
    assert TextContent(text="test", background_color="#0000FF")._as_rtf(
        "plain"
    ) == r_output.read("rtf_bg")

    # Test both colors together
    assert TextContent(text="test", color="red", background_color="blue")._as_rtf(
        "plain"
    ) == r_output.read("rtf_fg_bg")
