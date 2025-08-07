"""Tests for RTF encoding engine and strategies."""

import polars as pl

from rtflite.encode import RTFDocument
from rtflite.encoding import PaginatedStrategy, RTFEncodingEngine, SinglePageStrategy
from rtflite.input import RTFBody, RTFPage
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
        rtf_body = RTFBody(page_by=["A"], new_page=True)
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
        rtf_body = RTFBody(page_by=["A"], new_page=True)
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
        rtf_body = RTFBody(page_by=["A"], new_page=True)
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
        rtf_body = RTFBody(page_by=["A"], new_page=True)
        document = RTFDocument(df=df, rtf_body=rtf_body)

        # Test successful paginated encoding
        result = strategy.encode(document)
        assert isinstance(result, str)
        assert len(result) > 100  # Meaningful content
        # Verify pagination markers are present
        assert "\\page" in result or "\\pagebb" in result  # Page breaks
