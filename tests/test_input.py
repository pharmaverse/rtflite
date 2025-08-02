from rtflite.encode import RTFDocument
from rtflite.input import (
    RTFTitle,
    RTFFootnote,
    RTFSource,
    RTFBody,
    TextAttributes,
)
import polars as pl
import pytest

from .utils import ROutputReader, TestData
from .utils_snapshot import assert_rtf_equals_semantic

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

    rtf_output = rtf_doc.rtf_encode()
    expected = r_output.read("rtf_minimal")

    # Use semantic RTF comparison (handles font tables, borders, whitespace, page breaks)
    assert_rtf_equals_semantic(rtf_output, expected, "test_rtf_encode_minimal")


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
        text_justification=["l", "c"],
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
        text_font=1, text_format="b", text_font_size=12.0, text_justification="c"
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


def test_rtf_footnote_as_table_true():
    """Test RTFFootnote with as_table=True generates RTF matching R2RTF output."""
    # ```{r, footnote_as_table_true}
    # library(r2rtf)
    #
    # # Create a simple data frame
    # tbl <- data.frame(
    #   Column1 = c("Data 1.1", "Data 2.1"),
    #   Column2 = c("Data 1.2", "Data 2.2")
    # )
    #
    # # Test footnote with as_table = TRUE (default)
    # tbl_footnote_table <- tbl |>
    #   r2rtf::rtf_body() |>
    #   r2rtf::rtf_footnote(text = "Footnote as table", as_table = TRUE) |>
    #   r2rtf::rtf_encode(verbose = FALSE)
    #
    # # Output RTF content
    # tbl_footnote_table |>
    #   r2rtf::write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```

    # Test data matching R fixture
    df = pl.DataFrame(
        {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
    )

    # Create document with footnote as_table=True (default)
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Footnote as table"], as_table=True),
    )

    rtf_output = doc.rtf_encode()
    expected = r_output.read("footnote_as_table_true")

    # Use semantic RTF comparison
    assert_rtf_equals_semantic(rtf_output, expected, "test_rtf_footnote_as_table_true")


def test_rtf_footnote_as_table_false():
    """Test RTFFootnote with as_table=False generates RTF matching R2RTF output."""
    # ```{r, footnote_as_table_false}
    # library(r2rtf)
    #
    # # Test footnote with as_table = FALSE
    # tbl_footnote_plain <- tbl |>
    #   r2rtf::rtf_body() |>
    #   r2rtf::rtf_footnote(text = "Footnote as plain text", as_table = FALSE) |>
    #   r2rtf::rtf_encode(verbose = FALSE)
    #
    # tbl_footnote_plain |>
    #   r2rtf::write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```

    # Test data matching R fixture
    df = pl.DataFrame(
        {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
    )

    # Create document with footnote as_table=False
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Footnote as plain text"], as_table=False),
    )

    rtf_output = doc.rtf_encode()
    expected = r_output.read("footnote_as_table_false")

    # Use semantic RTF comparison
    assert_rtf_equals_semantic(rtf_output, expected, "test_rtf_footnote_as_table_false")


def test_rtf_source_as_table_true():
    """Test RTFSource with as_table=True generates RTF matching R2RTF output."""
    # ```{r, source_as_table_true}
    # library(r2rtf)
    #
    # # Test source with as_table = TRUE
    # tbl_source_table <- tbl |>
    #   r2rtf::rtf_body() |>
    #   r2rtf::rtf_source(text = "Source as table", as_table = TRUE) |>
    #   r2rtf::rtf_encode(verbose = FALSE)
    #
    # tbl_source_table |>
    #   r2rtf::write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```

    # Test data matching R fixture
    df = pl.DataFrame(
        {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
    )

    # Create document with source as_table=True
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_source=RTFSource(text=["Source as table"], as_table=True),
    )

    rtf_output = doc.rtf_encode()
    expected = r_output.read("source_as_table_true")

    # Use semantic RTF comparison
    assert_rtf_equals_semantic(rtf_output, expected, "test_rtf_source_as_table_true")


def test_rtf_source_as_table_false():
    """Test RTFSource with as_table=False generates RTF matching R2RTF output."""
    # ```{r, source_as_table_false}
    # library(r2rtf)
    #
    # # Test source with as_table = FALSE (default)
    # tbl_source_plain <- tbl |>
    #   r2rtf::rtf_body() |>
    #   r2rtf::rtf_source(text = "Source as plain text", as_table = FALSE) |>
    #   r2rtf::rtf_encode(verbose = FALSE)
    #
    # tbl_source_plain |>
    #   r2rtf::write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```

    # Test data matching R fixture
    df = pl.DataFrame(
        {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
    )

    # Create document with source as_table=False (default)
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_source=RTFSource(text=["Source as plain text"], as_table=False),
    )

    rtf_output = doc.rtf_encode()
    expected = r_output.read("source_as_table_false")

    # Use semantic RTF comparison
    assert_rtf_equals_semantic(rtf_output, expected, "test_rtf_source_as_table_false")


def test_rtf_footnote_as_table_boolean_storage():
    """Test RTFFootnote with as_table=True explicitly set."""
    footnote = RTFFootnote(text=["Footnote text"], as_table=True)
    assert footnote.as_table is True

    # Test that it has table borders when as_table=True
    assert footnote.border_left == [["single"]]
    assert footnote.border_right == [["single"]]
    assert footnote.border_top == [["single"]]
    assert footnote.border_bottom == [[""]]


def test_rtf_footnote_as_table_false():
    """Test RTFFootnote with as_table=False."""
    footnote = RTFFootnote(text=["Footnote text"], as_table=False)
    assert footnote.as_table is False

    # Test that it has no borders when as_table=False
    assert footnote.border_left == [[""]]
    assert footnote.border_right == [[""]]
    assert footnote.border_top == [[""]]
    assert footnote.border_bottom == [[""]]


def test_rtf_source_as_table_true():
    """Test RTFSource with as_table=True."""
    source = RTFSource(text=["Source text"], as_table=True)
    assert source.as_table is True

    # Test that it has table borders when as_table=True
    assert source.border_left == [["single"]]
    assert source.border_right == [["single"]]
    assert source.border_top == [["single"]]
    assert source.border_bottom == [[""]]


def test_rtf_source_as_table_false():
    """Test RTFSource with as_table=False explicitly set."""
    source = RTFSource(text=["Source text"], as_table=False)
    assert source.as_table is False

    # Test that it has no borders when as_table=False
    assert source.border_left == [[""]]
    assert source.border_right == [[""]]
    assert source.border_top == [[""]]
    assert source.border_bottom == [[""]]


def test_rtf_footnote_as_table_with_multiple_lines():
    """Test RTFFootnote as_table behavior with multiple text lines."""
    # Test as_table=True with multiple lines
    footnote_table = RTFFootnote(text=["Line 1", "Line 2", "Line 3"], as_table=True)
    assert footnote_table.as_table is True
    assert footnote_table.border_left == [["single"]]

    # Test as_table=False with multiple lines
    footnote_plain = RTFFootnote(text=["Line 1", "Line 2", "Line 3"], as_table=False)
    assert footnote_plain.as_table is False
    assert footnote_plain.border_left == [[""]]


def test_rtf_source_as_table_with_multiple_lines():
    """Test RTFSource as_table behavior with multiple text lines."""
    # Test as_table=True with multiple lines
    source_table = RTFSource(text=["Line 1", "Line 2", "Line 3"], as_table=True)
    assert source_table.as_table is True
    assert source_table.border_left == [["single"]]

    # Test as_table=False with multiple lines
    source_plain = RTFSource(text=["Line 1", "Line 2", "Line 3"], as_table=False)
    assert source_plain.as_table is False
    assert source_plain.border_left == [[""]]


def test_rtf_footnote_as_table_validation():
    """Test that as_table accepts only boolean values."""
    # Valid boolean values
    RTFFootnote(text=["Test"], as_table=True)
    RTFFootnote(text=["Test"], as_table=False)

    # Test with invalid types - should raise validation error
    with pytest.raises(ValueError):
        RTFFootnote(text=["Test"], as_table="true")

    with pytest.raises(ValueError):
        RTFFootnote(text=["Test"], as_table=1)

    with pytest.raises(ValueError):
        RTFFootnote(text=["Test"], as_table=None)


def test_rtf_source_as_table_validation():
    """Test that as_table accepts only boolean values."""
    # Valid boolean values
    RTFSource(text=["Test"], as_table=True)
    RTFSource(text=["Test"], as_table=False)

    # Test with invalid types - should raise validation error
    with pytest.raises(ValueError):
        RTFSource(text=["Test"], as_table="false")

    with pytest.raises(ValueError):
        RTFSource(text=["Test"], as_table=0)

    with pytest.raises(ValueError):
        RTFSource(text=["Test"], as_table=None)


def test_rtf_document_with_footnote_as_table():
    """Test RTF document generation with footnote as_table settings."""
    df = TestData.df1()

    # Test with footnote as table (default)
    doc_with_table_footnote = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Footnote as table"], as_table=True),
    )

    rtf_output_table = doc_with_table_footnote.rtf_encode()

    # Test with footnote as plain text
    doc_with_plain_footnote = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Footnote as plain text"], as_table=False),
    )

    rtf_output_plain = doc_with_plain_footnote.rtf_encode()

    # The outputs should be different due to different border handling
    assert rtf_output_table != rtf_output_plain

    # Table footnote should contain border RTF codes
    assert "\\clbrdrl\\brdrs\\brdrw15" in rtf_output_table

    # Plain text footnote should not contain table border codes for footnote
    # Note: It might still contain border codes for the main table body


def test_rtf_document_with_source_as_table():
    """Test RTF document generation with source as_table settings."""
    df = TestData.df1()

    # Test with source as table
    doc_with_table_source = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_source=RTFSource(text=["Source as table"], as_table=True),
    )

    rtf_output_table = doc_with_table_source.rtf_encode()

    # Test with source as plain text (default)
    doc_with_plain_source = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_source=RTFSource(text=["Source as plain text"], as_table=False),
    )

    rtf_output_plain = doc_with_plain_source.rtf_encode()

    # The outputs should be different due to different border handling
    assert rtf_output_table != rtf_output_plain


def test_rtf_document_with_both_footnote_and_source():
    """Test RTF document with both footnote and source with different as_table settings."""
    df = TestData.df1()

    # Test default configuration (footnote as table, source as plain text)
    doc_default = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Footnote text"]),  # as_table=True by default
        rtf_source=RTFSource(text=["Source text"]),  # as_table=False by default
    )

    rtf_output_default = doc_default.rtf_encode()

    # Test reversed configuration (footnote as plain text, source as table)
    doc_reversed = RTFDocument(
        df=df,
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Footnote text"], as_table=False),
        rtf_source=RTFSource(text=["Source text"], as_table=True),
    )

    rtf_output_reversed = doc_reversed.rtf_encode()

    # The outputs should be different
    assert rtf_output_default != rtf_output_reversed


def test_rtf_footnote_empty_text():
    """Test RTFFootnote with empty or None text."""
    # Test with None text
    footnote_none = RTFFootnote(text=None, as_table=True)
    assert footnote_none.as_table is True
    assert footnote_none.text is None

    # Test with empty list
    footnote_empty = RTFFootnote(text=[], as_table=False)
    assert footnote_empty.as_table is False
    assert footnote_empty.text == []


def test_rtf_source_empty_text():
    """Test RTFSource with empty or None text."""
    # Test with None text
    source_none = RTFSource(text=None, as_table=True)
    assert source_none.as_table is True
    assert source_none.text is None

    # Test with empty list
    source_empty = RTFSource(text=[], as_table=False)
    assert source_empty.as_table is False
    assert source_empty.text == []


def test_rtf_as_table_border_inheritance():
    """Test that as_table setting correctly sets border defaults without overriding explicit borders."""
    # Test footnote with explicit borders should not be overridden by as_table
    footnote_custom = RTFFootnote(
        text=["Test"],
        as_table=True,
        border_left=["double"],  # Explicit border
        border_right=["thick"],  # Explicit border
    )

    # Explicit borders should be preserved
    assert footnote_custom.border_left == [["double"]]
    assert footnote_custom.border_right == [["thick"]]
    # But defaults from as_table=True should still apply to unspecified borders
    assert footnote_custom.border_top == [["single"]]
    assert footnote_custom.border_bottom == [[""]]

    # Test source with explicit borders
    source_custom = RTFSource(
        text=["Test"],
        as_table=False,
        border_left=["single"],  # Explicit border (overriding as_table=False default)
    )

    # Explicit border should be preserved
    assert source_custom.border_left == [["single"]]
    # Defaults from as_table=False should apply to unspecified borders
    assert source_custom.border_right == [[""]]
    assert source_custom.border_top == [[""]]
    assert source_custom.border_bottom == [[""]]
