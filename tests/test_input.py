import polars as pl
import pytest

from rtflite.encode import RTFDocument
from rtflite.input import (
    RTFBody,
    RTFFootnote,
    RTFPage,
    RTFSource,
    RTFTitle,
    TextAttributes,
)

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
    """Test RTF document creation with title - legacy encoding methods removed during refactoring."""
    # Test text_font_size as a list conversion
    rtf_doc = RTFDocument(
        df=TestData.df1(),
        rtf_title=RTFTitle(text=["title 1", "title 2"], text_font_size=[1, 2]),
    )
    assert rtf_doc.rtf_title.text_font_size == (1.0, 2.0)

    # Test that document encodes successfully with title
    rtf_output = rtf_doc.rtf_encode()
    assert isinstance(rtf_output, str)
    assert len(rtf_output) > 0


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
    assert attrs.text_convert == [True]


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
    result = attrs._encode_text(text, method="paragraph")
    assert isinstance(result, list)
    assert len(result) == 1
    assert "\\b" in result[0]  # Bold format Red color
    assert "\\qc" in result[0]  # Center justification

    # Test line encoding
    text = ["Line 1", "Line 2"]
    result = attrs._encode_text(text, method="line")
    assert isinstance(result, str)
    assert "\\line" in result
    assert "\\b" in result
    assert "\\qc" in result

    # Test invalid method
    with pytest.raises(ValueError, match="Invalid method"):
        attrs._encode_text(text, method="invalid")


@pytest.mark.parametrize(
    "component_type,as_table,text_content,fixture_name",
    [
        ("footnote", True, "Footnote as table", "footnote_as_table_true"),
        ("footnote", False, "Footnote as plain text", "footnote_as_table_false"),
        ("source", True, "Source as table", "source_as_table_true"),
        ("source", False, "Source as plain text", "source_as_table_false"),
    ],
)
def test_rtf_footnote_source_as_table(
    component_type, as_table, text_content, fixture_name
):
    """Test RTFFootnote and RTFSource with as_table parameter.

    This parameterized test consolidates 4 similar tests into one,
    testing both footnote and source components with as_table True/False.

    R code fixtures are generated for each combination:
    - footnote with as_table=TRUE
    - footnote with as_table=FALSE
    - source with as_table=TRUE
    - source with as_table=FALSE
    """
    # Test data common to all cases
    df = pl.DataFrame(
        {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
    )

    # Create document with appropriate component
    if component_type == "footnote":
        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_footnote=RTFFootnote(text=[text_content], as_table=as_table),
        )
    else:  # source
        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_source=RTFSource(text=[text_content], as_table=as_table),
        )

    rtf_output = doc.rtf_encode()
    expected = r_output.read(fixture_name)

    # Use semantic RTF comparison
    test_name = f"test_rtf_{component_type}_as_table_{as_table}"
    assert_rtf_equals_semantic(rtf_output, expected, test_name)


def test_rtf_footnote_as_table_boolean_storage():
    """Test RTFFootnote with as_table=True explicitly set."""
    footnote = RTFFootnote(text=["Footnote text"], as_table=True)
    assert footnote.as_table is True

    # Test that it has table borders when as_table=True
    assert footnote.border_left == [["single"]]
    assert footnote.border_right == [["single"]]
    assert footnote.border_top == [["single"]]
    assert footnote.border_bottom == [[""]]


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


def test_rtf_footnote_pagination():
    """Test that footnotes appear correctly on paginated documents."""
    # Create dataset that will span multiple pages
    df = pl.DataFrame(
        {
            "Column1": [f"Row {i + 1}" for i in range(24)],
            "Column2": [f"Data {i + 1}" for i in range(24)],
        }
    )

    doc = RTFDocument(
        df=df,
        rtf_page=RTFPage(nrow=10),  # Force pagination
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(text=["Test footnote"]),
    )

    rtf_output = doc.rtf_encode()

    # Verify pagination occurred
    assert "\\page" in rtf_output
    # Verify footnote text appears
    assert "Test footnote" in rtf_output


def test_rtf_footnote_as_table_borders():
    """Test that as_table=True adds borders to footnotes."""
    df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})

    # Document with table-style footnote
    doc_table = RTFDocument(
        df=df,
        rtf_footnote=RTFFootnote(text=["Table footnote"], as_table=True),
    )

    # Document with plain footnote
    doc_plain = RTFDocument(
        df=df,
        rtf_footnote=RTFFootnote(text=["Plain footnote"], as_table=False),
    )

    rtf_table = doc_table.rtf_encode()
    rtf_plain = doc_plain.rtf_encode()

    # Table footnote should have border commands
    assert "\\brdr" in rtf_table
    # Outputs should differ due to formatting
    assert rtf_table != rtf_plain


def test_rtf_source_pagination():
    """Test that sources appear correctly on paginated documents."""
    # Create dataset that will span multiple pages
    df = pl.DataFrame(
        {
            "Column1": [f"Item {i + 1}" for i in range(24)],
            "Column2": [f"Desc {i + 1}" for i in range(24)],
        }
    )

    doc = RTFDocument(
        df=df,
        rtf_page=RTFPage(nrow=10),  # Force pagination
        rtf_body=RTFBody(),
        rtf_source=RTFSource(text=["Test source"]),
    )

    rtf_output = doc.rtf_encode()

    # Verify pagination occurred
    assert "\\page" in rtf_output
    # Verify source text appears
    assert "Test source" in rtf_output


def test_rtf_source_as_table_borders():
    """Test that as_table=True adds borders to sources."""
    df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})

    # Document with table-style source
    doc_table = RTFDocument(
        df=df,
        rtf_source=RTFSource(text=["Table source"], as_table=True),
    )

    # Document with plain source
    doc_plain = RTFDocument(
        df=df,
        rtf_source=RTFSource(text=["Plain source"], as_table=False),
    )

    rtf_table = doc_table.rtf_encode()
    rtf_plain = doc_plain.rtf_encode()

    # Table source should have border commands
    assert "\\brdr" in rtf_table
    # Outputs should differ due to formatting
    assert rtf_table != rtf_plain


def test_rtf_footnote_and_source_multipage_mixed():
    """Test document with both footnote and source with different as_table settings across 3 pages."""
    # Create dataset for 3 pages
    data_for_3_pages = {
        "Patient ID": [f"P{str(i + 1).zfill(3)}" for i in range(24)],
        "Treatment": [f"Treatment {'A' if i % 2 == 0 else 'B'}" for i in range(24)],
        "Response": [f"{80 + i % 20}%" for i in range(24)],
        "Status": ["Complete" if i % 3 == 0 else "Ongoing" for i in range(24)],
    }
    df_large = pl.DataFrame(data_for_3_pages)

    # Create document with footnote as table and source as plain text
    doc_mixed = RTFDocument(
        df=df_large,
        rtf_page=RTFPage(nrow=10),  # Force 3 pages
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(
            text=[
                "Note: Treatment assignment was randomized",
                "Response rates are preliminary",
            ],
            as_table=True,  # Footnote with borders
        ),
        rtf_source=RTFSource(
            text=["Data collected from Jan 2024 to Mar 2024"],
            as_table=False,  # Source as plain text
        ),
    )

    rtf_output = doc_mixed.rtf_encode()

    # Verify 3 pages
    assert rtf_output.count("\\page") == 2

    # Create opposite configuration for comparison
    doc_mixed_opposite = RTFDocument(
        df=df_large,
        rtf_page=RTFPage(nrow=10),
        rtf_body=RTFBody(),
        rtf_footnote=RTFFootnote(
            text=[
                "Note: Treatment assignment was randomized",
                "Response rates are preliminary",
            ],
            as_table=False,  # Footnote as plain text
        ),
        rtf_source=RTFSource(
            text=["Data collected from Jan 2024 to Mar 2024"],
            as_table=True,  # Source with borders
        ),
    )

    rtf_output_opposite = doc_mixed_opposite.rtf_encode()

    # Outputs should be different due to different formatting
    assert rtf_output != rtf_output_opposite

    # Both should have 3 pages
    assert rtf_output_opposite.count("\\page") == 2


def test_rtf_multipage_pagination_with_as_table():
    """Test that as_table behavior works correctly with pagination across 3 pages."""
    # Create dataset that spans exactly 3 pages
    df_large = pl.DataFrame(
        {
            "Patient": [f"P{str(i + 1).zfill(3)}" for i in range(24)],  # 24 patients
            "Age": [25 + (i % 50) for i in range(24)],  # Ages 25-74
            "Treatment": ["A" if i % 2 == 0 else "B" for i in range(24)],
            "Response": [
                f"{70 + (i % 30)}%" for i in range(24)
            ],  # Response rates 70-99%
        }
    )

    # Test all combinations across multiple pages
    test_cases = [
        ("footnote_table_source_plain", True, False),
        ("footnote_plain_source_table", False, True),
        ("both_table", True, True),
        ("both_plain", False, False),
    ]

    results = {}

    for case_name, footnote_as_table, source_as_table in test_cases:
        doc = RTFDocument(
            df=df_large,
            rtf_page=RTFPage(nrow=8),  # 8 rows per page = 3 pages (24/8 = 3)
            rtf_body=RTFBody(),
            rtf_footnote=RTFFootnote(
                text=[
                    f"Multi-line footnote for {case_name}",
                    "Additional footnote information",
                ],
                as_table=footnote_as_table,
            ),
            rtf_source=RTFSource(
                text=[f"Source data for {case_name} test"], as_table=source_as_table
            ),
        )

        rtf_output = doc.rtf_encode()
        results[case_name] = rtf_output

        # Verify multiple pages (at least 2 page breaks for 3+ pages)
        page_breaks = rtf_output.count("\\page")
        assert page_breaks >= 2, (
            f"Expected at least 2 page breaks for {case_name}, got {page_breaks}"
        )

        # Verify footnote and source text appear
        # Note: underscores in case names get converted to RTF subscript (\sub)
        rtf_case_name = case_name.replace("_", "\\sub ")
        assert rtf_case_name in rtf_output, (
            f"Case name should appear in RTF for {case_name} (looking for: {rtf_case_name})"
        )

    # Compare different combinations to ensure they produce different outputs
    assert (
        results["footnote_table_source_plain"] != results["footnote_plain_source_table"]
    )
    assert results["both_table"] != results["both_plain"]
    assert results["footnote_table_source_plain"] != results["both_table"]

    # Verify table borders appear more frequently when as_table=True
    border_count_both_table = results["both_table"].count("\\clbrdrl\\brdrs\\brdrw15")
    border_count_both_plain = results["both_plain"].count("\\clbrdrl\\brdrs\\brdrw15")

    # Both table should have more borders than both plain
    assert border_count_both_table > border_count_both_plain
