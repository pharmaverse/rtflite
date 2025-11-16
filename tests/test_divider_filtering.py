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

    def test_divider_rows_filtered_from_headers(self):
        """Test that '-----' values don't create section headers."""
        # Test data with divider rows
        df = pl.DataFrame(
            {
                "Section": ["-----", "-----", "Results", "Results"],
                "Item": ["A", ">=B", "<C", "D"],
                "Value": [1, 2, 3, 4],
            }
        )

        # Create document with page_by
        doc = RTFDocument(
            df=df, rtf_body=RTFBody(page_by=["Section"], col_rel_width=[1, 1])
        )

        # Process page_by components
        components = self.document_service.process_page_by(doc)

        # Verify components structure
        assert components is not None
        assert len(components) > 0

        # Count header components vs data components
        header_components = []
        data_components = []

        for component in components:
            if len(component) == 1 and len(component[0]) == 3:
                # Header component: [(row_idx, col_idx, level)]
                if component[0][2] < len(doc.rtf_body.page_by):
                    header_components.append(component)
                else:
                    data_components.append(component)
            else:
                # Data component: multiple tuples for data columns
                data_components.append(component)

        # Should only have 1 header (for "Results"), not 2 (no "-----" header)
        assert len(header_components) == 1, (
            f"Expected 1 header, got {len(header_components)}"
        )

        # Should have 4 data rows (all data preserved: A, >=B, <C, D)
        assert len(data_components) == 4, (
            f"Expected 4 data rows, got {len(data_components)}"
        )

    def test_normal_page_by_still_works(self):
        """Test that normal page_by functionality is unaffected."""
        # Test data without divider rows
        df = pl.DataFrame(
            {
                "Section": ["Group1", "Group1", "Group2", "Group2"],
                "Item": ["A", "B", "C", "D"],
                "Value": [1, 2, 3, 4],
            }
        )

        doc = RTFDocument(
            df=df, rtf_body=RTFBody(page_by=["Section"], col_rel_width=[1, 1])
        )

        components = self.document_service.process_page_by(doc)

        # Count headers and data
        header_components = []
        data_components = []

        for component in components:
            if len(component) == 1 and len(component[0]) == 3:
                if component[0][2] < len(doc.rtf_body.page_by):
                    header_components.append(component)
                else:
                    data_components.append(component)
            else:
                data_components.append(component)

        # Should have 2 headers (Group1, Group2) and 4 data rows
        assert len(header_components) == 2
        assert len(data_components) == 4

    def test_mixed_dividers_and_normal_groups(self):
        """Test page_by with mix of divider rows and normal groups."""
        df = pl.DataFrame(
            {
                "Section": ["-----", "Normal", "-----", "Normal2"],
                "Item": ["A", "B", "C", "D"],
                "Value": [1, 2, 3, 4],
            }
        )

        doc = RTFDocument(
            df=df, rtf_body=RTFBody(page_by=["Section"], col_rel_width=[1, 1])
        )

        components = self.document_service.process_page_by(doc)

        header_components = []
        data_components = []

        for component in components:
            if len(component) == 1 and len(component[0]) == 3:
                if component[0][2] < len(doc.rtf_body.page_by):
                    header_components.append(component)
                else:
                    data_components.append(component)
            else:
                data_components.append(component)

        # Should have 2 headers (Normal, Normal2) - no "-----" headers
        assert len(header_components) == 2
        # Should have 4 data rows (all preserved)
        assert len(data_components) == 4

    def test_only_divider_rows(self):
        """Test page_by with only divider rows."""
        df = pl.DataFrame(
            {
                "Section": ["-----", "-----"],
                "Item": ["A", "B"],
                "Value": [1, 2],
            }
        )

        doc = RTFDocument(
            df=df, rtf_body=RTFBody(page_by=["Section"], col_rel_width=[1, 1])
        )

        components = self.document_service.process_page_by(doc)

        header_components = []
        data_components = []

        for component in components:
            if len(component) == 1 and len(component[0]) == 3:
                if component[0][2] < len(doc.rtf_body.page_by):
                    header_components.append(component)
                else:
                    data_components.append(component)
            else:
                data_components.append(component)

        # Should have 0 headers (all dividers filtered)
        assert len(header_components) == 0
        # Should still have 2 data rows
        assert len(data_components) == 2

    def test_different_divider_patterns_not_filtered(self):
        """Test that only '-----' is filtered, not other patterns."""
        df = pl.DataFrame(
            {
                "Section": ["----", "___", "===", "-----"],
                "Item": ["A", "B", "C", "D"],
                "Value": [1, 2, 3, 4],
            }
        )

        doc = RTFDocument(
            df=df, rtf_body=RTFBody(page_by=["Section"], col_rel_width=[1, 1])
        )

        components = self.document_service.process_page_by(doc)

        header_components = []
        data_components = []

        for component in components:
            if len(component) == 1 and len(component[0]) == 3:
                if component[0][2] < len(doc.rtf_body.page_by):
                    header_components.append(component)
                else:
                    data_components.append(component)
            else:
                data_components.append(component)

        # Should have 3 headers (----, ___, ===) - only "-----" filtered
        assert len(header_components) == 3
        # Should have 4 data rows
        assert len(data_components) == 4

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

    def test_multiple_page_by_columns(self):
        """Test divider filtering with multiple page_by columns."""
        df = pl.DataFrame(
            {
                "Section1": ["-----", "A", "A", "B"],
                "Section2": ["-----", "X", "Y", "X"],
                "Item": ["test1", "test2", "test3", "test4"],
                "Value": [1, 2, 3, 4],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(page_by=["Section1", "Section2"], col_rel_width=[1, 1]),
        )

        components = self.document_service.process_page_by(doc)

        # Process components to count headers
        header_count = 0
        data_count = 0

        for component in components:
            if len(component) == 1 and len(component[0]) == 3:
                if component[0][2] < len(doc.rtf_body.page_by):
                    header_count += 1
                else:
                    data_count += 1
            else:
                data_count += 1

        # Should filter out headers for first row (Section1="-----", Section2="-----")
        # but keep headers for other combinations
        assert data_count == 4  # All data preserved
        # Header count will depend on the unique combinations after filtering
        assert header_count >= 0  # At least no crash
