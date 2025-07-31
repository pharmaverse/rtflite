"""
Comprehensive tests for pagination functionality
"""

import polars as pl
import pytest
from rtflite import RTFDocument, RTFTitle, RTFFootnote, RTFSource, RTFPage, RTFBody
from rtflite.pagination import RTFPagination, PageBreakCalculator, ContentDistributor


class TestRTFPagination:
    """Test RTFPagination class"""

    def test_pagination_creation(self):
        """Test basic pagination instance creation"""
        pagination = RTFPagination(
            page_width=8.5,
            page_height=11.0,
            margin=[1.25, 1, 1.75, 1.25, 1.75, 1.00625],
            nrow=40,
            orientation="portrait",
        )

        assert pagination.page_width == 8.5
        assert pagination.page_height == 11.0
        assert pagination.nrow == 40
        assert pagination.orientation == "portrait"

    def test_available_space_calculation(self):
        """Test available space calculation"""
        pagination = RTFPagination(
            page_width=8.5,
            page_height=11.0,
            margin=[1.25, 1, 1.75, 1.25, 1.75, 1.00625],
            nrow=40,
            orientation="portrait",
        )

        space = pagination.calculate_available_space()

        assert space["content_width"] == 8.5 - 1.25 - 1  # page_width - left - right
        assert (
            space["content_height"] == 11.0 - 1.75 - 1.25
        )  # page_height - top - bottom
        assert space["header_space"] == 1.75
        assert space["footer_space"] == 1.00625


class TestPageBreakCalculator:
    """Test PageBreakCalculator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.pagination = RTFPagination(
            page_width=8.5,
            page_height=11.0,
            margin=[1.25, 1, 1.75, 1.25, 1.75, 1.00625],
            nrow=5,  # Small page limit for testing
            orientation="portrait",
        )
        self.calculator = PageBreakCalculator(pagination=self.pagination)

    def test_calculate_content_rows_simple(self):
        """Test content row calculation with simple data"""
        df = pl.DataFrame(
            {"col1": ["short", "text", "here"], "col2": ["more", "short", "text"]}
        )
        col_widths = [2.0, 2.0]

        row_counts = self.calculator.calculate_content_rows(df, col_widths)

        assert len(row_counts) == 3
        assert all(count >= 1 for count in row_counts)

    def test_calculate_content_rows_long_text(self):
        """Test content row calculation with long text that should wrap"""
        df = pl.DataFrame(
            {
                "col1": ["This is a very long text that should wrap to multiple lines"],
                "col2": ["Short"],
            }
        )
        col_widths = [1.0, 2.0]  # Narrow first column

        row_counts = self.calculator.calculate_content_rows(df, col_widths)

        assert len(row_counts) == 1
        # Long text should require multiple lines
        assert row_counts[0] > 1

    def test_find_page_breaks_no_pagination_needed(self):
        """Test page breaks when no pagination is needed"""
        df = pl.DataFrame({"col1": ["A", "B"], "col2": ["1", "2"]})
        col_widths = [2.0, 2.0]

        breaks = self.calculator.find_page_breaks(df, col_widths)

        # Should have one page with all data
        assert len(breaks) == 1
        assert breaks[0] == (0, 1)  # start_row=0, end_row=1

    def test_find_page_breaks_pagination_needed(self):
        """Test page breaks when pagination is needed"""
        # Create data that exceeds page limit (nrow=5)
        df = pl.DataFrame(
            {
                "col1": [f"Row {i}" for i in range(10)],
                "col2": [f"Data {i}" for i in range(10)],
            }
        )
        col_widths = [2.0, 2.0]

        breaks = self.calculator.find_page_breaks(df, col_widths)

        # Should have multiple pages
        assert len(breaks) > 1

        # Check that page breaks are valid
        for i, (start, end) in enumerate(breaks):
            assert start <= end
            assert start >= 0
            assert end < df.height
            if i > 0:
                prev_end = breaks[i - 1][1]
                assert start == prev_end + 1  # No gaps or overlaps

    def test_find_page_breaks_with_grouping(self):
        """Test page breaks with group-based pagination"""
        df = pl.DataFrame({"group": ["A", "A", "B", "B", "C"], "data": [1, 2, 3, 4, 5]})
        col_widths = [1.0, 1.0]

        breaks = self.calculator.find_page_breaks(
            df, col_widths, page_by=["group"], new_page=True
        )

        # Should have breaks at group boundaries
        assert len(breaks) == 3  # One page per group

    def test_find_page_breaks_empty_dataframe(self):
        """Test page breaks with empty DataFrame"""
        df = pl.DataFrame(
            {"col1": [], "col2": []}, schema={"col1": pl.Utf8, "col2": pl.Utf8}
        )
        col_widths = [2.0, 2.0]

        breaks = self.calculator.find_page_breaks(df, col_widths)

        assert breaks == []

    def test_find_page_breaks_single_row(self):
        """Test page breaks with single row DataFrame"""
        df = pl.DataFrame({"col1": ["A"], "col2": ["1"]})
        col_widths = [2.0, 2.0]

        breaks = self.calculator.find_page_breaks(df, col_widths)

        assert len(breaks) == 1
        assert breaks[0] == (0, 0)


class TestContentDistributor:
    """Test ContentDistributor class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.pagination = RTFPagination(
            page_width=8.5,
            page_height=11.0,
            margin=[1.25, 1, 1.75, 1.25, 1.75, 1.00625],
            nrow=3,  # Very small page limit for testing
            orientation="portrait",
        )
        self.calculator = PageBreakCalculator(pagination=self.pagination)
        self.distributor = ContentDistributor(
            pagination=self.pagination, calculator=self.calculator
        )

    def test_distribute_content_single_page(self):
        """Test content distribution for single page"""
        df = pl.DataFrame({"col1": ["A", "B"], "col2": ["1", "2"]})
        col_widths = [2.0, 2.0]

        pages = self.distributor.distribute_content(df, col_widths)

        assert len(pages) == 1
        page = pages[0]
        assert page["page_number"] == 1
        assert page["total_pages"] == 1
        assert page["is_first_page"]
        assert page["is_last_page"]
        assert page["needs_header"]
        assert page["data"].height == 2

    def test_distribute_content_multiple_pages(self):
        """Test content distribution for multiple pages"""
        df = pl.DataFrame(
            {
                "col1": [f"Row {i}" for i in range(8)],
                "col2": [f"Data {i}" for i in range(8)],
            }
        )
        col_widths = [2.0, 2.0]

        pages = self.distributor.distribute_content(df, col_widths)

        assert len(pages) > 1

        # Check first page
        first_page = pages[0]
        assert first_page["page_number"] == 1
        assert first_page["is_first_page"]
        assert not first_page["is_last_page"]

        # Check last page
        last_page = pages[-1]
        assert last_page["page_number"] == len(pages)
        assert not last_page["is_first_page"]
        assert last_page["is_last_page"]

        # Check total pages consistency
        for page in pages:
            assert page["total_pages"] == len(pages)

    def test_distribute_content_with_grouping(self):
        """Test content distribution with grouping"""
        df = pl.DataFrame({"group": ["A", "A", "B", "B"], "data": [1, 2, 3, 4]})
        col_widths = [1.0, 1.0]

        pages = self.distributor.distribute_content(
            df, col_widths, page_by=["group"], new_page=True
        )

        assert len(pages) == 2  # One page per group

    def test_get_group_headers(self):
        """Test group header generation"""
        df = pl.DataFrame(
            {"group1": ["A", "A", "B"], "group2": ["X", "Y", "X"], "data": [1, 2, 3]}
        )

        headers = self.distributor.get_group_headers(df, ["group1", "group2"], 0)

        assert headers["group_by_columns"] == ["group1", "group2"]
        assert headers["group_values"] == {"group1": "A", "group2": "X"}
        assert "group1: A | group2: X" in headers["header_text"]

    def test_get_group_headers_empty(self):
        """Test group headers with no grouping columns"""
        df = pl.DataFrame({"data": [1, 2, 3]})

        headers = self.distributor.get_group_headers(df, [], 0)

        assert headers == {}


class TestRTFDocumentPagination:
    """Test pagination integration with RTFDocument"""

    def test_needs_pagination_small_data(self):
        """Test pagination detection with small dataset"""
        df = pl.DataFrame({"col1": ["A", "B"], "col2": ["1", "2"]})

        doc = RTFDocument(df=df)

        assert not doc._needs_pagination()

    def test_needs_pagination_large_data(self):
        """Test pagination detection with large dataset"""
        # Create data that exceeds default page limit (40 rows)
        df = pl.DataFrame(
            {
                "col1": [f"Row {i}" for i in range(50)],
                "col2": [f"Data {i}" for i in range(50)],
            }
        )

        doc = RTFDocument(df=df)

        assert doc._needs_pagination()

    def test_needs_pagination_with_forced_page_breaks(self):
        """Test pagination detection with forced page breaks"""
        df = pl.DataFrame({"group": ["A", "B"], "data": [1, 2]})

        doc = RTFDocument(df=df, rtf_body=RTFBody(page_by=["group"], new_page=True))

        assert doc._needs_pagination()

    def test_paginated_encoding_basic(self):
        """Test basic paginated RTF encoding"""
        # Create data that needs pagination
        df = pl.DataFrame(
            {
                "col1": [f"Row {i}" for i in range(50)],
                "col2": [f"Data {i}" for i in range(50)],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_title=RTFTitle(text=["Test Title"]),
            rtf_footnote=RTFFootnote(text="Test footnote"),
            rtf_source=RTFSource(text="Test source"),
        )

        rtf_content = doc.rtf_encode()

        # Should contain page breaks
        assert "\\page" in rtf_content
        # Should contain RTF structure
        assert rtf_content.startswith("{\\rtf1\\ansi")
        assert rtf_content.endswith("}")

    def test_page_element_location_first(self):
        """Test page element appearing only on first page"""
        df = pl.DataFrame(
            {
                "col1": [f"Row {i}" for i in range(50)],
                "col2": [f"Data {i}" for i in range(50)],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_title=RTFTitle(text=["First Page Title"]),
            rtf_page=RTFPage(page_title_location="first"),
        )

        rtf_content = doc.rtf_encode()

        # Title should appear, but not be repeated after page breaks
        assert "First Page Title" in rtf_content
        title_count = rtf_content.count("First Page Title")
        page_break_count = rtf_content.count("\\page")

        # Title should appear once despite multiple pages
        assert title_count == 1
        assert page_break_count > 0

    def test_page_element_location_last(self):
        """Test page element appearing only on last page"""
        df = pl.DataFrame(
            {
                "col1": [f"Row {i}" for i in range(50)],
                "col2": [f"Data {i}" for i in range(50)],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_footnote=RTFFootnote(text="Last page footnote"),
            rtf_page=RTFPage(page_footnote_location="last"),
        )

        rtf_content = doc.rtf_encode()

        # Footnote should appear only once
        assert "Last page footnote" in rtf_content
        footnote_count = rtf_content.count("Last page footnote")
        assert footnote_count == 1


class TestPaginationEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_dataframe(self):
        """Test pagination with empty DataFrame"""
        df = pl.DataFrame(
            {"col1": [], "col2": []}, schema={"col1": pl.Utf8, "col2": pl.Utf8}
        )

        doc = RTFDocument(df=df)

        # Should not need pagination
        assert not doc._needs_pagination()

        # Should still generate valid RTF
        rtf_content = doc.rtf_encode()
        assert rtf_content.startswith("{\\rtf1\\ansi")
        assert rtf_content.endswith("}")

    def test_single_row_dataframe(self):
        """Test pagination with single row DataFrame"""
        df = pl.DataFrame({"col1": ["A"], "col2": ["1"]})

        doc = RTFDocument(df=df)

        assert not doc._needs_pagination()

        rtf_content = doc.rtf_encode()
        assert "\\page" not in rtf_content

    def test_very_small_page_limit(self):
        """Test pagination with very small page limit"""
        df = pl.DataFrame({"col1": ["A", "B", "C"], "col2": ["1", "2", "3"]})

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=1),  # One row per page
        )

        assert doc._needs_pagination()

        rtf_content = doc.rtf_encode()
        page_breaks = rtf_content.count("\\page")
        assert page_breaks == 2  # 3 rows = 3 pages = 2 page breaks

    def test_invalid_page_by_column(self):
        """Test pagination with invalid page_by column"""
        df = pl.DataFrame({"col1": ["A"], "col2": ["1"]})

        with pytest.raises(ValueError, match="not found in"):
            RTFDocument(df=df, rtf_body=RTFBody(page_by=["nonexistent_column"]))

    def test_all_same_group_values(self):
        """Test pagination with all same group values"""
        df = pl.DataFrame({"group": ["A", "A", "A"], "data": [1, 2, 3]})

        doc = RTFDocument(df=df, rtf_body=RTFBody(page_by=["group"], new_page=True))

        # Should still work, just one group
        assert doc._needs_pagination()

        rtf_content = doc.rtf_encode()
        # Should not have page breaks since all rows are same group
        assert "\\page" not in rtf_content

    def test_all_different_group_values(self):
        """Test pagination with all different group values"""
        df = pl.DataFrame({"group": ["A", "B", "C"], "data": [1, 2, 3]})

        doc = RTFDocument(df=df, rtf_body=RTFBody(page_by=["group"], new_page=True))

        assert doc._needs_pagination()

        rtf_content = doc.rtf_encode()
        # Should have page breaks between each group
        page_breaks = rtf_content.count("\\page")
        assert page_breaks == 2  # 3 groups = 3 pages = 2 page breaks

    def test_unicode_and_special_characters(self):
        """Test pagination with Unicode and special characters"""
        df = pl.DataFrame(
            {"col1": ["αβγ", "café", "日本語"], "col2": ["δεζ", "naïve", "中文"]}
        )

        doc = RTFDocument(df=df)

        # Should handle Unicode without errors
        rtf_content = doc.rtf_encode()
        assert rtf_content.startswith("{\\rtf1\\ansi")
        assert rtf_content.endswith("}")

    def test_very_long_cell_content(self):
        """Test pagination with very long cell content"""
        long_text = "This is a very long text " * 100  # Very long content

        df = pl.DataFrame({"col1": [long_text], "col2": ["Short"]})

        doc = RTFDocument(df=df)

        # Should handle long content without errors
        rtf_content = doc.rtf_encode()
        assert long_text[:50] in rtf_content  # Check part of long text is present

    def test_mixed_data_types(self):
        """Test pagination with mixed data types"""
        df = pl.DataFrame(
            {
                "strings": ["A", "B", "C"],
                "integers": [1, 2, 3],
                "floats": [1.1, 2.2, 3.3],
                "booleans": [True, False, True],
            }
        )

        doc = RTFDocument(df=df)

        # Should handle mixed types
        rtf_content = doc.rtf_encode()
        assert "1.1" in rtf_content
        assert "True" in rtf_content or "true" in rtf_content.lower()

    def test_null_values(self):
        """Test pagination with null/None values"""
        df = pl.DataFrame({"col1": ["A", None, "C"], "col2": [None, "2", None]})

        doc = RTFDocument(df=df)

        # Should handle null values without errors
        rtf_content = doc.rtf_encode()
        assert rtf_content.startswith("{\\rtf1\\ansi")
        assert rtf_content.endswith("}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
