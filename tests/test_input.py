from rtflite.encode import RTFDocument
from rtflite.input import RTFTitle, TextAttributes, RTFPageHeader, RTFPageFooter, RTFSubline
import polars as pl
import pytest

from .utils import ROutputReader, TestData

r_output = ROutputReader("test_input")


def test_rtf_encode_minimal():
    # ```{r, rtf_minimal}
    # tbl <- data.frame(
    #   `Column1` = c("Data 1.1", "Data 2.1"),
    #   `Column2` = c("Data 1.2", "Data 2.2")
    # )
    #
    # tbl_input <- tbl |>
    #   r2rtf::rtf_page() |>
    #   r2rtf::rtf_title(c("title 1", "title 2")) |>
    #   r2rtf::rtf_body()
    #
    # tbl_encode <- tbl_input |>
    #   r2rtf::rtf_encode(verbose = FALSE)
    #
    # tbl_encode |>
    #   r2rtf::write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```
    rtf_doc = RTFDocument(
        df=TestData.df1(), rtf_title=RTFTitle(text=["title 1", "title 2"])
    )

    assert rtf_doc.rtf_encode() == r_output.read("rtf_minimal")


def test_rtf_encode_with_title():
    # ```{r, rtf_title_line}
    # tbl <- data.frame(
    #   `Column 1` = c("Data 1.1", "Data 2.1"),
    #   `Column 2` = c("Data 1.2", "Data 2.2")
    # )
    #
    # tbl_input <- tbl |>
    #   r2rtf::rtf_title(c("title 1", "title 2")) |>
    #   r2rtf::rtf_body()
    #
    # tbl_encode <- tbl_input |>
    #   r2rtf::rtf_encode(verbose = TRUE)
    #
    # cat(tbl_encode$header, sep = "\n")
    # ```
    #
    # ```{r, rtf_page_line}
    # cat(tbl_encode$page, sep = "\n")
    # ```
    #
    # ```{r, rtf_page_margin_line}
    # cat(tbl_encode$margin, sep = "\n")
    # ```
    rtf_doc = RTFDocument(
        df=TestData.df1(), rtf_title=RTFTitle(text=["title 1", "title 2"])
    )
    assert rtf_doc._rtf_title_encode(method="line") == r_output.read("rtf_title_line")
    assert rtf_doc._rtf_page_encode() == r_output.read("rtf_page_line")
    assert rtf_doc._rtf_page_margin_encode() == r_output.read("rtf_page_margin_line")

    # Test text_font_size as a list
    rtf_doc = RTFDocument(
        df=TestData.df1(),
        rtf_title=RTFTitle(text=["title 1", "title 2"], text_font_size=[1, 2]),
    )
    assert rtf_doc.rtf_title.text_font_size == (1.0, 2.0)

    expected_output = "{\\pard\\hyphpar\\sb180\\sa180\\fi0\\li0\\ri0\\qc\\fs2{\\f0 title 1}\\line\\fs4{\\f0 title 2}\\par}"
    assert rtf_doc._rtf_title_encode(method="line") == expected_output


def test_rtf_title_validation():
    """Test RTFTitle validation."""

    # Test with invalid text type
    with pytest.raises(ValueError):
        RTFTitle(text=123)


def test_text_attributes_default():
    """Test TextAttributes with default values."""
    attrs = TextAttributes()
    assert attrs.text_font is None
    assert attrs.text_format is None
    assert attrs.text_font_size is None
    assert attrs.text_color is None
    assert attrs.text_background_color is None
    assert attrs.text_justification is None
    assert attrs.text_indent_first is None
    assert attrs.text_indent_left is None
    assert attrs.text_indent_right is None
    assert attrs.text_space is None
    assert attrs.text_space_before is None
    assert attrs.text_space_after is None
    assert attrs.text_hyphenation is None
    assert attrs.text_convert is None


def test_text_attributes_validation():
    """Test TextAttributes field validation."""
    # Test valid values
    attrs = TextAttributes(
        text_font=[1, 2],
        text_format=["", "bi"],
        text_font_size=[12, 14],
        text_justification=["l", "c"]
    )
    assert attrs.text_font == [1, 2]
    assert attrs.text_format == ["", "bi"]
    assert attrs.text_font_size == [12, 14]
    assert attrs.text_justification == ["l", "c"]

    # Test invalid font
    with pytest.raises(ValueError, match="Invalid font number"):
        TextAttributes(text_font=[999])

    # Test invalid format
    with pytest.raises(ValueError, match="Invalid text format"):
        TextAttributes(text_format=["invalid"])

    # Test invalid font size
    with pytest.raises(ValueError, match="Invalid font size"):
        TextAttributes(text_font_size=[-1])

    # Test invalid justification
    with pytest.raises(ValueError, match="Invalid text justification"):
        TextAttributes(text_justification=["invalid"])


def test_text_attributes_single_value_conversion():
    """Test conversion of single values to lists."""
    attrs = TextAttributes(
        text_font=1,
        text_format="b",
        text_font_size=12.0,
        text_justification="c"
    )
    assert attrs.text_font == [1]
    assert attrs.text_format == ["b"]
    assert attrs.text_font_size == [12.0]
    assert attrs.text_justification == ["c"]


def test_text_attributes_encode():
    """Test TextAttributes encoding functionality."""
    attrs = TextAttributes(
        text_font=1,
        text_format="b",
        text_font_size=12.0,
        text_color="red",
        text_justification="c",
        text_indent_first=10,
        text_indent_left=10,
        text_indent_right=10,
        text_space=1,
        text_space_before=1,
        text_space_after=1,
        text_hyphenation=True,
    )
    
    # Test paragraph encoding
    text = ["Test Title"]
    result = attrs._encode(text, method="paragraph")
    assert isinstance(result, list)
    assert len(result) == 1
    assert "\\b" in result[0]  # Bold format Red color
    assert "\\qc" in result[0]  # Center justification
    
    # Test line encoding
    text = ["Line 1", "Line 2"]
    result = attrs._encode(text, method="line")
    assert isinstance(result, str)
    assert "\\line" in result
    assert "\\b" in result
    assert "\\qc" in result

    # Test invalid method
    with pytest.raises(ValueError, match="Invalid method"):
        attrs._encode(text, method="invalid")
