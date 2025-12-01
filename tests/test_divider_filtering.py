"""Tests for divider row filtering functionality in page_by.

Tests the feature that removes "-----" divider rows from page_by output
while preserving the associated data.
"""

import polars as pl

from rtflite import RTFBody, RTFDocument
from rtflite.services.document_service import RTFDocumentService


class TestDividerFiltering:
    """Test divider row filtering in page_by functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.document_service = RTFDocumentService()

    def test_rtf_output_integration(self):
        """Test full RTF generation with divider filtering."""
        df = pl.DataFrame(
            {
                "Section": ["-----", "-----", "Results", "Results"],
                "Item": ["A", ">=B", "<C", "D"],
                "Value": [1, 2, 3, 4],
            }
        )

        doc = RTFDocument(
            df=df, rtf_body=RTFBody(page_by=["Section"], col_rel_width=[1, 1])
        )

        # Generate RTF output
        rtf_output = doc.rtf_encode()

        # Verify RTF contains all data
        assert "A" in rtf_output
        assert r"\uc1\u8805* B" in rtf_output  # >=B converted
        assert "<C" in rtf_output
        assert "D" in rtf_output
        assert "Results" in rtf_output

        # Verify "-----" doesn't appear as header content
        # (It might appear in other RTF formatting, but not as cell content)
        assert "-----" not in rtf_output or rtf_output.count("-----") == 0

        # Should be a valid RTF document
        assert rtf_output.startswith(r"{\rtf1\ansi")
        assert rtf_output.endswith("}")
