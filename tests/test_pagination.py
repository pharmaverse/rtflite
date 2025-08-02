import pytest
import polars as pl

import rtflite as rtf
from .utils import ROutputReader, TestData

r_output = ROutputReader("test_pagination")


class TestPaginationData:
    """Test data for comprehensive pagination tests."""
    
    @staticmethod
    def df_6_rows():
        """DataFrame with 6 rows for testing pagination with nrow=2 (3 pages)"""
        return pl.DataFrame({
            'Col1': ['Row1', 'Row2', 'Row3', 'Row4', 'Row5', 'Row6'],
            'Col2': ['A', 'B', 'C', 'D', 'E', 'F']
        })
    
    @staticmethod
    def df_2_rows():
        """DataFrame with 2 rows for testing single page scenarios"""
        return pl.DataFrame({
            'Col1': ['Row1', 'Row2'],
            'Col2': ['A', 'B']
        })


def test_pagination_basic_with_headers():
    """Test basic pagination with column headers, no footnote/source."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    # ```{r, basic_with_headers}
    # library(r2rtf)
    # test_data <- data.frame(
    #   Col1 = c("Row1", "Row2", "Row3", "Row4", "Row5", "Row6"),
    #   Col2 = c("A", "B", "C", "D", "E", "F"),
    #   stringsAsFactors = FALSE
    # )
    # 
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    
    # rtflite now matches r2rtf behavior exactly:
    # nrow=2 means 2 total rows per page (including headers, footnotes, sources)
    # With 1 header per page, this leaves 1 data row per page
    # 6 data rows = 6 pages with 1 data row each = 5 page breaks
    
    # Verify rtflite pagination behavior matches r2rtf
    assert rtf_output.count("\\page") == 5  # 5 page breaks for 6 pages (6 data rows × 1 row per page)
    assert "Column 1" in rtf_output  # Column headers present
    assert "Row6" in rtf_output  # All data present
    
    # Verify page structure: each section should have 1 header + 1 data row = 2 total rows
    sections = rtf_output.split("\\page")
    assert len(sections) == 6  # 6 pages
    
    for i, section in enumerate(sections):
        assert "Column 1" in section  # Headers on each page
        row_count = section.count("Row")
        assert row_count == 1, f"Page {i+1} should have 1 data row, got {row_count}"


def test_pagination_no_headers():
    """Test pagination without column headers."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[],  # No headers
        rtf_body=rtf.RTFBody(
            col_rel_width=[1, 1],
            as_colheader=False
        )
    )
    
    # ```{r, no_headers}
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1),
    #     as_colheader = FALSE
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    
    # Verify pagination without headers (r2rtf compatible)
    # nrow=2 with no headers means 2 data rows per page
    # 6 data rows = 3 pages with 2 data rows each = 2 page breaks
    assert rtf_output.count("\\page") == 2  # 2 page breaks for 3 pages
    assert "Column" not in rtf_output  # No column headers
    assert "Row6" in rtf_output  # All data present
    
    # Verify page structure: each section should have 2 data rows
    sections = rtf_output.split("\\page")
    assert len(sections) == 3  # 3 pages
    
    for i, section in enumerate(sections):
        row_count = section.count("Row")
        assert row_count == 2, f"Page {i+1} should have 2 data rows, got {row_count}"


def test_pagination_with_footnote():
    """Test pagination with column headers and footnote."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1]),
        rtf_footnote=rtf.RTFFootnote(
            text="Note: This is a test footnote for pagination",
            col_rel_width=[1]
        )
    )
    
    # ```{r, with_footnote}
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_footnote(
    #     footnote = "Note: This is a test footnote for pagination",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("with_footnote")
    
    assert "test footnote" in rtf_output


def test_pagination_with_source():
    """Test pagination with column headers and source."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1]),
        rtf_source=rtf.RTFSource(
            text="Source: Test data for pagination",
            col_rel_width=[1]
        )
    )
    
    # ```{r, with_source}
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_source(
    #     source = "Source: Test data for pagination",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("with_source")
    
    assert "Source: Test data" in rtf_output


def test_pagination_all_components():
    """Test pagination with all components (headers, footnote, source)."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1]),
        rtf_footnote=rtf.RTFFootnote(
            text="Note: This is a test footnote",
            col_rel_width=[1]
        ),
        rtf_source=rtf.RTFSource(
            text="Source: Test data",
            col_rel_width=[1]
        )
    )
    
    # ```{r, all_components}
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_footnote(
    #     footnote = "Note: This is a test footnote",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_source(
    #     source = "Source: Test data",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("all_components")
    
    assert "test footnote" in rtf_output
    assert "Source: Test data" in rtf_output


def test_pagination_multirow_headers():
    """Test multi-row column headers with pagination."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Main Header", "Main Header"],
                col_rel_width=[1, 1],
                border_bottom=[[""]]
            ),
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1],
                border_top=[[""]]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    # ```{r, multirow_headers}
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_colheader(
    #     colheader = "Main Header | Main Header",
    #     col_rel_width = c(1, 1),
    #     border_bottom = ""
    #   ) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2", 
    #     col_rel_width = c(1, 1),
    #     border_top = ""
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("multirow_headers")
    
    assert "Main Header" in rtf_output
    assert "Column 1" in rtf_output


def test_pagination_border_styles():
    """Test different border styles with pagination - critical test for double border issue."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(
            orientation="portrait",
            nrow=2,
            border_first="double",
            border_last="double"
        ),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(
            col_rel_width=[1, 1],
            border_first=[["single"]],
            border_last=[["single"]]
        )
    )
    
    # ```{r, border_styles}
    # test_data %>%
    #   rtf_page(
    #     orientation = "portrait", 
    #     nrow = 2,
    #     border_first = "double",
    #     border_last = "double"
    #   ) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1),
    #     border_first = "single",
    #     border_last = "single"
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # # expected = r_output.read("border_styles")  # TODO: Generate R outputs
    
    # Critical test: Verify correct double border placement
    double_border_count = rtf_output.count('brdrdb')
    assert double_border_count == 4, f"Expected 4 double borders, got {double_border_count}"
    
    # Verify double borders are only on first column header and last row
    lines = rtf_output.split('\n')
    double_border_lines = [i for i, line in enumerate(lines) if 'brdrdb' in line]
    
    # Should have exactly 4 lines with double borders (2 columns × 2 locations)
    assert len(double_border_lines) == 4
    
    # Check that only the last data row (Row6) has double bottom borders
    row6_lines = [i for i, line in enumerate(lines) if 'Row6' in line]
    assert len(row6_lines) == 1
    row6_line = row6_lines[0]
    
    # Check that the border definitions before Row6 contain double borders
    found_double_before_row6 = any(
        'brdrdb' in lines[i] and 'brdrb' in lines[i] 
        for i in range(max(0, row6_line - 5), row6_line)
    )
    assert found_double_before_row6, "Row6 should have double bottom borders"
    
    # Check that Row5 does NOT have double bottom borders
    row5_lines = [i for i, line in enumerate(lines) if 'Row5' in line]
    if row5_lines:
        row5_line = row5_lines[0]
        found_double_before_row5 = any(
            'brdrdb' in lines[i] and 'brdrb' in lines[i] 
            for i in range(max(0, row5_line - 5), row5_line)
        )
        assert not found_double_before_row5, "Row5 should NOT have double bottom borders"


def test_pagination_single_page():
    """Test single page (no pagination needed) with all components."""
    df = TestPaginationData.df_2_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=10),  # nrow > data rows
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1]),
        rtf_footnote=rtf.RTFFootnote(
            text="Single page test",
            col_rel_width=[1]
        ),
        rtf_source=rtf.RTFSource(
            text="Source: Small dataset",
            col_rel_width=[1]
        )
    )
    
    # ```{r, single_page}
    # small_data <- data.frame(
    #   Col1 = c("Row1", "Row2"),
    #   Col2 = c("A", "B")
    # )
    # 
    # small_data %>%
    #   rtf_page(orientation = "portrait", nrow = 10) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_footnote(
    #     footnote = "Single page test",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_source(
    #     source = "Source: Small dataset",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("single_page")
    
    # Should NOT have page breaks
    assert "\\page" not in rtf_output
    assert "Single page test" in rtf_output
    assert "Small dataset" in rtf_output


def test_pagination_landscape():
    """Test landscape orientation with pagination."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="landscape", nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    # ```{r, landscape}
    # test_data %>%
    #   rtf_page(orientation = "landscape", nrow = 2) %>%
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("landscape")
    
    assert "\\landscape" in rtf_output
    assert "\\page" in rtf_output


def test_pagination_needs_detection():
    """Test that pagination is correctly detected when needed."""
    df = TestPaginationData.df_6_rows()
    
    # Document that needs pagination
    doc_paginated = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(nrow=2),  # Force pagination
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    # Document that doesn't need pagination
    doc_single = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(nrow=10),  # More than data rows
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    assert doc_paginated._needs_pagination() == True
    assert doc_single._needs_pagination() == False


def test_pagination_page_break_format():
    """Test that page breaks follow the correct RTF format."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(nrow=2),
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    rtf_output = doc.rtf_encode()
    
    # Test page break format matches r2rtf
    expected_page_break = "{\\pard\\fs2\\par}\\page{\\pard\\fs2\\par}"
    assert expected_page_break in rtf_output
    
    # Test that page setup follows page breaks
    lines = rtf_output.split('\n')
    for i, line in enumerate(lines):
        if expected_page_break in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Next line should contain paper dimensions
            assert "\\paperw" in next_line and "\\paperh" in next_line


def test_pagination_column_header_repetition():
    """Test that column headers repeat on each page."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(nrow=2),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1])
    )
    
    rtf_output = doc.rtf_encode()
    
    # Count occurrences of column headers - should appear on each page
    column_header_count = rtf_output.count("Column 1")
    page_count = rtf_output.count("\\page") + 1  # +1 for first page
    
    assert column_header_count == page_count, f"Column headers should appear {page_count} times, got {column_header_count}"


def test_pagination_no_headers_footnote_source():
    """Test pagination without headers but with footnote and source."""
    df = TestPaginationData.df_6_rows()
    
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=2),
        rtf_column_header=[],  # No headers
        rtf_body=rtf.RTFBody(
            col_rel_width=[1, 1],
            as_colheader=False
        ),
        rtf_footnote=rtf.RTFFootnote(
            text="Note: No column headers test",
            col_rel_width=[1]
        ),
        rtf_source=rtf.RTFSource(
            text="Source: Test without headers",
            col_rel_width=[1]
        )
    )
    
    # ```{r, no_headers_footnote_source}
    # test_data %>%
    #   rtf_page(orientation = "portrait", nrow = 2) %>%
    #   rtf_body(
    #     col_rel_width = c(1, 1),
    #     as_colheader = FALSE
    #   ) %>%
    #   rtf_footnote(
    #     footnote = "Note: No column headers test",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_source(
    #     source = "Source: Test without headers",
    #     col_rel_width = c(1)
    #   ) %>%
    #   rtf_encode() %>%
    #   cat()
    # ```
    
    rtf_output = doc.rtf_encode()
    # expected = r_output.read("no_headers_footnote_source")
    
    assert "No column headers test" in rtf_output
    assert "Test without headers" in rtf_output
    assert "Column" not in rtf_output  # No column headers


def test_pagination_border_fix_regression():
    """Regression test for the border reference bug that was fixed.
    
    The bug was in _apply_border_to_row where we were appending references
    to the same list object instead of copies, causing all rows to share
    the same border settings.
    """
    df = TestPaginationData.df_6_rows()
    
    # Use the same setup as test_pagination_border_styles which was failing before the fix
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(
            orientation="portrait",
            nrow=2,
            border_first="double",
            border_last="double"
        ),
        rtf_column_header=[
            rtf.RTFColumnHeader(
                text=["Column 1", "Column 2"],
                col_rel_width=[1, 1]
            )
        ],
        rtf_body=rtf.RTFBody(
            col_rel_width=[1, 1],
            border_first=[["single"]],
            border_last=[["single"]]
        )
    )
    
    rtf_output = doc.rtf_encode()
    
    # The specific bug: Row5 was getting double bottom borders when only Row6 should
    lines = rtf_output.split('\n')
    
    # Find lines mentioning Row5 and Row6
    row5_lines = [i for i, line in enumerate(lines) if 'Row5' in line]
    row6_lines = [i for i, line in enumerate(lines) if 'Row6' in line]
    
    # Both should exist
    assert len(row5_lines) == 1
    assert len(row6_lines) == 1
    
    # Check borders before each row (RTF borders are defined before the content)
    row5_line = row5_lines[0]
    row6_line = row6_lines[0]
    
    # Row5 should NOT have double bottom borders
    row5_has_double_bottom = any(
        'brdrdb' in lines[i] and 'brdrb' in lines[i]
        for i in range(max(0, row5_line - 5), row5_line)
    )
    assert not row5_has_double_bottom, "Row5 should not have double bottom borders (this was the bug)"
    
    # Row6 should have double bottom borders
    row6_has_double_bottom = any(
        'brdrdb' in lines[i] and 'brdrb' in lines[i]
        for i in range(max(0, row6_line - 5), row6_line)
    )
    assert row6_has_double_bottom, "Row6 should have double bottom borders"
    
    # Verify the fix: exactly 4 double borders total
    double_border_count = rtf_output.count('brdrdb')
    assert double_border_count == 4, f"Expected exactly 4 double borders, got {double_border_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])