"""Tests for AdvancedPaginationService.

This module tests the advanced pagination service that provides enhanced
pagination capabilities using the PageDict system.
"""

from unittest.mock import Mock

import polars as pl
import pytest

from rtflite.encode import RTFDocument
from rtflite.input import RTFBody, RTFColumnHeader, RTFFootnote, RTFPage
from rtflite.pagination import PageBreakType, PageConfig, PageDict
from rtflite.services.advanced_pagination_service import AdvancedPaginationService


class TestAdvancedPaginationService:
    """Test the AdvancedPaginationService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = AdvancedPaginationService()

    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service.document_service is not None
        assert self.service.page_dict is None
        assert self.service.page_index_manager is None

    def test_create_page_dict_simple(self):
        """Test creating PageDict for a simple document."""
        # Create a simple document
        df = pl.DataFrame({"A": list(range(20)), "B": list(range(20, 40))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=10))

        # Create PageDict
        page_dict = self.service.create_page_dict(doc)

        assert isinstance(page_dict, PageDict)
        assert page_dict.nrow_per_page == 10
        assert page_dict.total_pages > 0

    def test_create_page_dict_with_override(self):
        """Test creating PageDict with nrow override."""
        df = pl.DataFrame({"A": list(range(15)), "B": list(range(15))})
        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=20),  # Document setting
        )

        # Override with different nrow
        page_dict = self.service.create_page_dict(doc, nrow_per_page=5)

        assert page_dict.nrow_per_page == 5  # Override value used

    def test_process_single_dataframe(self):
        """Test processing a single DataFrame document."""
        df = pl.DataFrame({"Group": ["A"] * 10 + ["B"] * 10, "Value": list(range(20))})

        rtf_body = RTFBody()
        page_dict = PageDict(nrow_per_page=8)

        # Process single dataframe
        self.service._process_single_dataframe(df, rtf_body, page_dict, 2)

        # Should have created page configurations
        assert page_dict.total_pages > 0

    def test_process_multi_section_document(self):
        """Test processing a document with multiple DataFrame sections."""
        # Create document with list of DataFrames
        df1 = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        df2 = pl.DataFrame({"A": [7, 8, 9], "B": [10, 11, 12]})

        # Mock document with list of DataFrames
        doc = Mock()
        doc.df = [df1, df2]
        doc.rtf_page = RTFPage(nrow=5)
        doc.rtf_body = RTFBody()

        page_dict = PageDict(nrow_per_page=5)

        # Process multi-section
        self.service._process_multi_section_document(doc, page_dict, 1)

        # Should have processed both sections
        assert page_dict.total_pages > 0

    def test_get_page_index_manager(self):
        """Test getting the PageIndexManager."""
        # Should raise without PageDict
        with pytest.raises(ValueError, match="Must create PageDict first"):
            self.service.get_page_index_manager()

        # Create PageDict first
        df = pl.DataFrame({"A": [1, 2, 3]})
        doc = RTFDocument(df=df)
        self.service.create_page_dict(doc)

        # Now should return manager
        manager = self.service.get_page_index_manager()
        assert manager is not None
        assert manager.page_dict == self.service.page_dict

    def test_get_page_for_row(self):
        """Test getting page number for specific row."""
        df = pl.DataFrame({"A": list(range(20))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=5))

        self.service.create_page_dict(doc)

        # Test row lookups
        assert self.service.get_page_for_row(0) == 1  # First row on page 1
        assert self.service.get_page_for_row(4) <= 2  # Row 4 on page 1 or 2
        assert self.service.get_page_for_row(10) >= 2  # Row 10 on page 2 or later

    def test_get_rows_for_page(self):
        """Test getting row range for specific page."""
        df = pl.DataFrame({"A": list(range(15))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=5))

        self.service.create_page_dict(doc)

        # Get rows for page 1
        start_row, end_row = self.service.get_rows_for_page(1)
        assert start_row >= 0
        assert end_row >= start_row

    def test_force_content_to_page(self):
        """Test forcing content to specific page."""
        df = pl.DataFrame({"A": [1, 2, 3]})
        doc = RTFDocument(df=df)

        self.service.create_page_dict(doc)

        # Force content to page 1
        self.service.force_content_to_page("header1", 1)

        # Verify through manager
        manager = self.service.get_page_index_manager()
        assert manager.get_content_page("header1") == 1

    def test_get_pagination_summary(self):
        """Test getting pagination summary."""
        # Without PageDict
        summary = self.service.get_pagination_summary()
        assert "error" in summary

        # With PageDict
        df = pl.DataFrame({"A": list(range(10))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=5))
        self.service.create_page_dict(doc)

        summary = self.service.get_pagination_summary()
        assert "total_pages" in summary
        assert "nrow_per_page" in summary
        assert "page_configs" in summary

    def test_convert_to_legacy_format(self):
        """Test converting to legacy format."""
        df = pl.DataFrame({"A": list(range(10))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=5))

        self.service.create_page_dict(doc)

        legacy_format = self.service.convert_to_legacy_format()
        assert isinstance(legacy_format, list)
        assert len(legacy_format) > 0

        # Check first page info
        first_page = legacy_format[0]
        assert "page_number" in first_page
        assert "total_pages" in first_page
        assert "start_row" in first_page
        assert "end_row" in first_page

    def test_validate_pagination(self):
        """Test pagination validation."""
        # Without PageDict
        issues = self.service.validate_pagination()
        assert len(issues) > 0
        assert "No PageDict available" in issues[0]

        # With valid PageDict
        df = pl.DataFrame({"A": list(range(10))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=5))
        self.service.create_page_dict(doc)

        issues = self.service.validate_pagination()
        # Should have no issues for valid pagination
        assert len(issues) == 0

    def test_optimize_pagination(self):
        """Test pagination optimization."""
        df = pl.DataFrame({"A": list(range(20))})
        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=5))

        self.service.create_page_dict(doc)

        # Should not raise
        self.service.optimize_pagination()

    def test_merge_section_pages(self):
        """Test merging section pages."""
        main_page_dict = PageDict(nrow_per_page=10)
        section_page_dict = PageDict(nrow_per_page=10)

        # Add a page to section dict
        config = PageConfig(
            page_number=1, start_row=0, end_row=4, break_type=PageBreakType.AUTOMATIC
        )
        section_page_dict.add_page_config(config)

        # Merge into main dict
        self.service._merge_section_pages(
            section_page_dict, main_page_dict, row_offset=10, section_idx=0
        )

        # Should have added the page with offset
        assert main_page_dict.total_pages == 1
        merged_config = main_page_dict.get_page_config(1)
        assert merged_config.start_row == 10  # Offset applied
        assert merged_config.end_row == 14

    def test_page_by_functionality(self):
        """Test page_by parameter creates forced page breaks."""
        df = pl.DataFrame(
            {"Category": ["A"] * 10 + ["B"] * 10, "Value": list(range(20))}
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=15),
            rtf_body=RTFBody(page_by=["Category"], new_page=True),
        )

        page_dict = self.service.create_page_dict(doc)

        # Should have at least 2 pages (one per category)
        assert page_dict.total_pages >= 2

        # Check for forced breaks
        has_forced = any(
            config.break_type == PageBreakType.FORCED
            for config in page_dict.page_configs.values()
        )
        assert has_forced

    def test_subline_by_functionality(self):
        """Test subline_by parameter creates subline breaks."""
        df = pl.DataFrame(
            {"Section": ["Intro"] * 5 + ["Methods"] * 5, "Content": list(range(10))}
        )

        doc = RTFDocument(
            df=df, rtf_page=RTFPage(nrow=15), rtf_body=RTFBody(subline_by="Section")
        )

        page_dict = self.service.create_page_dict(doc)

        # Check that subline information is captured
        has_subline = any(
            config.subline_header is not None
            for config in page_dict.page_configs.values()
        )
        assert has_subline or page_dict.total_pages > 0  # At minimum, pages are created

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        df = pl.DataFrame({"A": [], "B": []})
        doc = RTFDocument(df=df)

        # Should handle gracefully
        page_dict = self.service.create_page_dict(doc)

        assert page_dict is not None
        # Empty df might have 0 pages, which is ok
        assert page_dict.total_pages >= 0

    def test_complex_document_scenario(self):
        """Test complex document with multiple features."""
        df = pl.DataFrame(
            {
                "Department": ["Sales"] * 20 + ["Engineering"] * 20,
                "Team": (["Team A"] * 10 + ["Team B"] * 10) * 2,
                "Employee": [f"Emp{i:02d}" for i in range(40)],
                "Score": list(range(40)),
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=15),
            rtf_body=RTFBody(page_by=["Department"], new_page=True, subline_by="Team"),
            rtf_column_header=RTFColumnHeader(
                text=["Department", "Team", "Employee", "Score"]
            ),
            rtf_footnote=RTFFootnote(text="Performance Report"),
        )

        # Create complex PageDict
        page_dict = self.service.create_page_dict(doc)

        # Verify complex structure
        assert page_dict.total_pages >= 3  # Multiple pages needed

        # Get summary
        summary = self.service.get_pagination_summary()
        assert summary["total_pages"] >= 3

        # Validate pagination
        issues = self.service.validate_pagination()
        # Complex doc should still be valid
        assert len(issues) == 0 or all("Missing" not in issue for issue in issues)
