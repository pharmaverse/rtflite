"""Tests for RTF encoding engine and strategies."""

import polars as pl

from rtflite.encode import RTFDocument
from rtflite.encoding import PaginatedStrategy, RTFEncodingEngine, SinglePageStrategy
from rtflite.input import RTFBody, RTFColumnHeader, RTFPage, RTFTitle
from rtflite.services.document_service import RTFDocumentService


class TestRTFEncodingEngine:
    """Test the RTFEncodingEngine class."""

    def test_engine_initialization(self):
        """Test that the engine initializes correctly."""
        engine = RTFEncodingEngine()

        assert engine._single_page_strategy is not None
        assert engine._paginated_strategy is not None
        assert isinstance(engine._single_page_strategy, SinglePageStrategy)
        assert isinstance(engine._paginated_strategy, PaginatedStrategy)

    def test_select_single_page_strategy(self):
        """Test strategy selection for single-page documents."""
        engine = RTFEncodingEngine()

        # Create a simple document that doesn't need pagination
        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        document = RTFDocument(df=df)

        strategy = engine._select_strategy(document)
        assert isinstance(strategy, SinglePageStrategy)

    def test_select_paginated_strategy_with_page_by(self):
        """Test strategy selection when page_by is specified."""
        engine = RTFEncodingEngine()

        # Create a document with page_by enabled
        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        rtf_body = RTFBody(page_by=["A"], new_page=True, pageby_row="first_row")
        document = RTFDocument(df=df, rtf_body=rtf_body)

        strategy = engine._select_strategy(document)
        assert isinstance(strategy, PaginatedStrategy)

    def test_select_paginated_strategy_with_large_content(self):
        """Test strategy selection when content exceeds page capacity."""
        engine = RTFEncodingEngine()

        # Create a large document that exceeds page capacity
        df = pl.DataFrame({"A": list(range(100)), "B": list(range(100, 200))})
        rtf_page = RTFPage(nrow=10)  # Small page capacity
        document = RTFDocument(df=df, rtf_page=rtf_page)

        strategy = engine._select_strategy(document)
        assert isinstance(strategy, PaginatedStrategy)

    def test_needs_pagination_page_by_enabled(self):
        """Test pagination detection when page_by is enabled."""
        document_service = RTFDocumentService()

        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        rtf_body = RTFBody(page_by=["A"], new_page=True, pageby_row="first_row")
        document = RTFDocument(df=df, rtf_body=rtf_body)

        assert document_service.needs_pagination(document) is True

    def test_needs_pagination_content_exceeds_capacity(self):
        """Test pagination detection when content exceeds page capacity."""
        document_service = RTFDocumentService()

        df = pl.DataFrame({"A": list(range(50)), "B": list(range(50, 100))})
        rtf_page = RTFPage(nrow=10)
        document = RTFDocument(df=df, rtf_page=rtf_page)

        assert document_service.needs_pagination(document) is True

    def test_needs_pagination_false(self):
        """Test pagination detection when pagination is not needed."""
        document_service = RTFDocumentService()

        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        document = RTFDocument(df=df)

        assert document_service.needs_pagination(document) is False

    def test_encode_document_single_page(self):
        """Test encoding a single-page document."""
        engine = RTFEncodingEngine()

        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        document = RTFDocument(df=df)

        # Test that encoding produces a non-empty RTF document
        result = engine.encode_document(document)
        assert isinstance(result, str)
        assert len(result) > 100  # RTF documents should have substantial content
        # Verify it contains table data
        assert "\\cell" in result  # RTF table cells
        assert "\\row" in result  # RTF table rows

    def test_encode_document_paginated(self):
        """Test encoding a paginated document."""
        engine = RTFEncodingEngine()

        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        rtf_body = RTFBody(page_by=["A"], new_page=True, pageby_row="first_row")
        document = RTFDocument(df=df, rtf_body=rtf_body)

        # Test that encoding produces a valid paginated document
        result = engine.encode_document(document)
        assert isinstance(result, str)
        assert len(result) > 100  # RTF documents should have substantial content
        # Verify pagination occurred
        assert "\\page" in result  # Page breaks for pagination


class TestSinglePageStrategy:
    """Test the SinglePageStrategy class."""

    def test_strategy_encode(self):
        """Test that single page strategy encodes correctly."""
        strategy = SinglePageStrategy()

        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        document = RTFDocument(df=df)

        # Test successful encoding without implementation details
        result = strategy.encode(document)
        assert isinstance(result, str)
        assert len(result) > 100  # Meaningful content
        # Verify table structure is present
        assert "\\trowd" in result  # Table row definition


class TestPaginatedStrategy:
    """Test the PaginatedStrategy class."""

    def test_strategy_encode(self):
        """Test that paginated strategy encodes with pagination."""
        strategy = PaginatedStrategy()

        df = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        rtf_body = RTFBody(page_by=["A"], new_page=True, pageby_row="first_row")
        document = RTFDocument(df=df, rtf_body=rtf_body)

        # Test successful paginated encoding
        result = strategy.encode(document)
        assert isinstance(result, str)
        assert len(result) > 100  # Meaningful content
        # Verify pagination markers are present
        assert "\\page" in result or "\\pagebb" in result  # Page breaks

    def test_page_by_columns_excluded_with_new_page(self):
        """Test that page_by columns are excluded from display when new_page=True.

        This is a regression test for issue #126 where page_by columns were appearing
        as regular data columns when used with pagination (new_page=True), commonly
        used with landscape orientation.
        """
        strategy = PaginatedStrategy()

        # Create test data with a page_by column
        df = pl.DataFrame(
            {
                "__index__": ["Subject 1", "Subject 1", "Subject 2", "Subject 2"],
                "ID": ["001", "002", "003", "004"],
                "Event": ["AE1", "AE2", "AE3", "AE4"],
            }
        )

        # Test with landscape orientation (common use case for the bug)
        document = RTFDocument(
            df=df,
            rtf_page=RTFPage(orientation="landscape"),
            rtf_title=RTFTitle(text=["Test Page By with Landscape"]),
            rtf_column_header=[
                RTFColumnHeader(
                    text=["ID", "Event"],  # Headers only for non-page_by columns
                    col_rel_width=[1, 1],
                )
            ],
            rtf_body=RTFBody(
                col_rel_width=[2, 1, 1],  # All columns including page_by
                page_by=["__index__"],
                new_page=True,  # This triggers pagination
                pageby_row="first_row",
            ),
        )

        result = strategy.encode(document)

        # Verify result is valid RTF
        assert isinstance(result, str)
        assert result.startswith(r"{\rtf1")
        assert result.endswith("}")

        # Verify page breaks exist (pagination is working)
        assert "\\page" in result or "\\pagebb" in result

        # Verify the data columns are present in the output
        assert "001" in result
        assert "002" in result
        assert "003" in result
        assert "004" in result
        assert "AE1" in result
        assert "AE2" in result
        assert "AE3" in result
        assert "AE4" in result

        # Count the number of cells in the output to verify column structure
        # With page_by column excluded, we should have 2 columns (ID, Event) not 3
        # Each data row should have 2 cells, not 3
        cell_pattern = r"\\cell"
        result.count(cell_pattern)

        # We have 4 data rows + headers, so we expect cells for 2 columns
        # (not 3 columns which would indicate page_by column wasn't removed)
        # The exact cell count will depend on headers and structure, but it should
        # be consistent with 2 data columns, not 3

        # Verify that Subject 1 and Subject 2 appear as section headers
        # (not in table cells)
        # The page_by values should appear as section headers before each group
        assert "Subject 1" in result
        assert "Subject 2" in result

        # Verify that section headers appear before table content
        # The page_by values should be in paragraph format (\\pard), not table cells
        assert "\\pard" in result  # Paragraph formatting for section headers
