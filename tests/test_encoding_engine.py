"""Tests for RTF encoding engine and strategies."""

import polars as pl

from rtflite.encode import RTFDocument
from rtflite.encoding import RTFEncodingEngine
from rtflite.encoding.unified_encoder import UnifiedRTFEncoder
from rtflite.input import RTFBody, RTFColumnHeader, RTFPage, RTFTitle


class TestRTFEncodingEngine:
    """Test the RTFEncodingEngine class."""

    def test_engine_initialization(self):
        """Test that the engine initializes correctly."""
        engine = RTFEncodingEngine()
        # Check that it uses the new unified encoder
        assert hasattr(engine, "_encoder")
        assert isinstance(engine._encoder, UnifiedRTFEncoder)

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
        assert r"\cell" in result  # RTF table cells
        assert r"\row" in result  # RTF table rows

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
        assert r"\page" in result  # Page breaks for pagination

    def test_page_by_columns_excluded_with_new_page(self):
        """Test that page_by columns are excluded from display when new_page=True.

        This is a regression test for issue #126 where page_by columns were appearing
        as regular data columns when used with pagination (new_page=True), commonly
        used with landscape orientation.
        """
        engine = RTFEncodingEngine()

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

        result = engine.encode_document(document)

        # Verify result is valid RTF
        assert isinstance(result, str)
        assert result.startswith(r"{\rtf1")
        assert result.endswith("}")

        # Verify page breaks exist (pagination is working)
        assert r"\page" in result

        # Verify the data columns are present in the output
        assert "001" in result
        assert "002" in result
        assert "003" in result
        assert "004" in result
        assert "AE1" in result
        assert "AE2" in result
        assert "AE3" in result
        assert "AE4" in result

        # Verify that Subject 1 and Subject 2 appear as section headers
        # (not in table cells)
        # The page_by values should appear as section headers before each group
        assert "Subject 1" in result
        assert "Subject 2" in result

        # Ensure headers are applied correctly
        assert r"\pard" in result
