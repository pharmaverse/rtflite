"""Tests for RTFPage component placement settings."""

import polars as pl
import pytest

from src.rtflite import RTFDocument, RTFFootnote, RTFPage, RTFSource, RTFTitle


class TestRTFPageComponentPlacement:
    """Test the RTFPage settings for controlling component placement in multi-page documents."""

    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset that will require pagination."""
        return pl.DataFrame(
            {
                "col1": ["Row " + str(i) for i in range(100)],
                "col2": [i for i in range(100)],
                "col3": ["Data " + str(i) for i in range(100)],
            }
        )

    def test_default_parameters_work(self, large_dataset):
        """Test that default parameters don't break existing functionality."""
        doc = RTFDocument(df=large_dataset)
        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0

    def test_rtfpage_validation(self, large_dataset):
        """Test that invalid RTFPage parameter values raise ValueError."""
        with pytest.raises(ValueError, match="Invalid page placement option"):
            RTFDocument(df=large_dataset, rtf_page=RTFPage(page_title="invalid"))

        with pytest.raises(ValueError, match="Invalid page placement option"):
            RTFDocument(df=large_dataset, rtf_page=RTFPage(page_footnote="invalid"))

        with pytest.raises(ValueError, match="Invalid page placement option"):
            RTFDocument(df=large_dataset, rtf_page=RTFPage(page_source="invalid"))

    def test_all_valid_combinations(self, large_dataset):
        """Test that all valid RTFPage parameter combinations work without errors."""
        for page_title in ["first", "last", "all"]:
            for page_footnote in ["first", "last", "all"]:
                for page_source in ["first", "last", "all"]:
                    doc = RTFDocument(
                        df=large_dataset,
                        rtf_page=RTFPage(
                            page_title=page_title,
                            page_footnote=page_footnote,
                            page_source=page_source,
                        ),
                    )
                    rtf_output = doc.rtf_encode()
                    assert isinstance(rtf_output, str)
                    assert len(rtf_output) > 0

    def test_page_title_first(self, large_dataset):
        """Test that page_title='first' shows title only on first page."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_title="first"),
            rtf_title=RTFTitle(text="Test Title"),
        )
        rtf_output = doc.rtf_encode()
        title_count = rtf_output.count("Test Title")
        assert title_count == 1, f"Expected title to appear 1 time, got {title_count}"

    def test_page_title_all(self, large_dataset):
        """Test that page_title='all' shows title on all pages."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_title="all"),
            rtf_title=RTFTitle(text="Test Title"),
        )
        rtf_output = doc.rtf_encode()
        title_count = rtf_output.count("Test Title")
        assert title_count > 1, (
            f"Expected title to appear multiple times, got {title_count}"
        )

    def test_page_title_last(self, large_dataset):
        """Test that page_title='last' shows title only on last page."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_title="last"),
            rtf_title=RTFTitle(text="Test Title"),
        )
        rtf_output = doc.rtf_encode()
        title_count = rtf_output.count("Test Title")
        assert title_count == 1, f"Expected title to appear 1 time, got {title_count}"

    def test_page_footnote_first(self, large_dataset):
        """Test that page_footnote='first' shows footnote only on first page."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_footnote="first"),
            rtf_footnote=RTFFootnote(text="Test Footnote"),
        )
        rtf_output = doc.rtf_encode()
        footnote_count = rtf_output.count("Test Footnote")
        assert footnote_count == 1, (
            f"Expected footnote to appear 1 time, got {footnote_count}"
        )

    def test_page_footnote_last_default(self, large_dataset):
        """Test that page_footnote='last' (default) shows footnote only on last page."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_footnote="last"),
            rtf_footnote=RTFFootnote(text="Test Footnote"),
        )
        rtf_output = doc.rtf_encode()
        footnote_count = rtf_output.count("Test Footnote")
        assert footnote_count == 1, (
            f"Expected footnote to appear 1 time, got {footnote_count}"
        )

    def test_page_footnote_all(self, large_dataset):
        """Test that page_footnote='all' shows footnote on all pages."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_footnote="all"),
            rtf_footnote=RTFFootnote(text="Test Footnote"),
        )
        rtf_output = doc.rtf_encode()
        footnote_count = rtf_output.count("Test Footnote")
        assert footnote_count > 1, (
            f"Expected footnote to appear multiple times, got {footnote_count}"
        )

    def test_page_source_first(self, large_dataset):
        """Test that page_source='first' shows source only on first page."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_source="first"),
            rtf_source=RTFSource(text="Test Source"),
        )
        rtf_output = doc.rtf_encode()
        source_count = rtf_output.count("Test Source")
        assert source_count == 1, (
            f"Expected source to appear 1 time, got {source_count}"
        )

    def test_page_source_last_default(self, large_dataset):
        """Test that page_source='last' (default) shows source only on last page."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_source="last"),
            rtf_source=RTFSource(text="Test Source"),
        )
        rtf_output = doc.rtf_encode()
        source_count = rtf_output.count("Test Source")
        assert source_count == 1, (
            f"Expected source to appear 1 time, got {source_count}"
        )

    def test_page_source_all(self, large_dataset):
        """Test that page_source='all' shows source on all pages."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10, page_source="all"),
            rtf_source=RTFSource(text="Test Source"),
        )
        rtf_output = doc.rtf_encode()
        source_count = rtf_output.count("Test Source")
        assert source_count > 1, (
            f"Expected source to appear multiple times, got {source_count}"
        )

    def test_single_page_document_uses_all_components(self, large_dataset):
        """Test that single-page documents show all components regardless of settings."""
        # Create a document that won't be paginated
        small_df = large_dataset.head(5)

        # Test with different settings - all should show components once (single page)
        for page_title in ["first", "last", "all"]:
            for page_footnote in ["first", "last", "all"]:
                for page_source in ["first", "last", "all"]:
                    doc = RTFDocument(
                        df=small_df,
                        rtf_page=RTFPage(
                            nrow=50,  # Large enough to fit all data
                            page_title=page_title,
                            page_footnote=page_footnote,
                            page_source=page_source,
                        ),
                        rtf_title=RTFTitle(text="Test Title"),
                        rtf_footnote=RTFFootnote(text="Test Footnote"),
                        rtf_source=RTFSource(text="Test Source"),
                    )

                    rtf_output = doc.rtf_encode()

                    # All should contain the components once (single page)
                    assert rtf_output.count("Test Title") == 1
                    assert rtf_output.count("Test Footnote") == 1
                    assert rtf_output.count("Test Source") == 1

    def test_combined_settings(self, large_dataset):
        """Test combinations of different RTFPage settings."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(
                nrow=10, page_title="all", page_footnote="first", page_source="last"
            ),
            rtf_title=RTFTitle(text="Test Title"),
            rtf_footnote=RTFFootnote(text="Test Footnote"),
            rtf_source=RTFSource(text="Test Source"),
        )

        rtf_output = doc.rtf_encode()

        title_count = rtf_output.count("Test Title")
        footnote_count = rtf_output.count("Test Footnote")
        source_count = rtf_output.count("Test Source")

        assert title_count > 1, "Title should appear on all pages"
        assert footnote_count == 1, "Footnote should appear only on first page"
        assert source_count == 1, "Source should appear only on last page"

    def test_no_components_no_error(self, large_dataset):
        """Test that documents without title/footnote/source work normally."""
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(
                nrow=10, page_title="all", page_footnote="all", page_source="all"
            ),
        )

        # Should work without errors even with component placement settings
        rtf_output = doc.rtf_encode()

        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0
        # No components should appear
        assert "Test Title" not in rtf_output
        assert "Test Footnote" not in rtf_output
        assert "Test Source" not in rtf_output

    def test_default_values(self, large_dataset):
        """Test that RTFPage has correct default values."""
        page = RTFPage()
        assert page.page_title == "all"
        assert page.page_footnote == "last"
        assert page.page_source == "last"

        # Test with document using defaults
        doc = RTFDocument(
            df=large_dataset,
            rtf_page=RTFPage(nrow=10),  # Just set pagination
            rtf_title=RTFTitle(text="Test Title"),
            rtf_footnote=RTFFootnote(text="Test Footnote"),
            rtf_source=RTFSource(text="Test Source"),
        )

        rtf_output = doc.rtf_encode()

        # Should follow default behavior
        title_count = rtf_output.count("Test Title")
        footnote_count = rtf_output.count("Test Footnote")
        source_count = rtf_output.count("Test Source")

        assert title_count > 1, "Title should appear on all pages (default)"
        assert footnote_count == 1, "Footnote should appear on last page only (default)"
        assert source_count == 1, "Source should appear on last page only (default)"
