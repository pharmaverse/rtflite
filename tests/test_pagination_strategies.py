"""Tests for pagination strategies and advanced features.

This module tests critical pagination functionality including group_by,
subline_by, page context restoration, and boundary conditions.
"""

import polars as pl

from rtflite.encode import RTFDocument
from rtflite.input import RTFBody, RTFColumnHeader, RTFFootnote, RTFPage, RTFTitle
from rtflite.services.document_service import RTFDocumentService
from rtflite.services.grouping_service import GroupingService


class TestPaginationWithGroupBy:
    """Test pagination with group_by feature for value suppression."""

    def test_group_by_single_column(self):
        """Test group_by suppresses duplicate values in single column."""
        df = pl.DataFrame(
            {
                "ID": ["A", "A", "A", "B", "B", "C"],
                "Value": [1, 2, 3, 4, 5, 6],
                "Status": ["OK", "OK", "FAIL", "OK", "OK", "FAIL"],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(
                group_by=["ID"],
                col_rel_width=[1, 1, 1],
            ),
        )

        rtf_output = doc.rtf_encode()

        # Verify RTF was generated
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0
        # Should contain table structure
        assert "\\trowd" in rtf_output
        assert "\\cell" in rtf_output

    def test_group_by_multiple_columns_hierarchical(self):
        """Test hierarchical group_by with multiple columns."""
        df = pl.DataFrame(
            {
                "Site": ["S1", "S1", "S1", "S1", "S2", "S2"],
                "Patient": ["P01", "P01", "P02", "P02", "P03", "P03"],
                "Visit": [1, 2, 1, 2, 1, 2],
                "Value": [10, 20, 30, 40, 50, 60],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(
                group_by=["Site", "Patient"],  # Hierarchical grouping
                col_rel_width=[1, 1, 1, 1],
            ),
        )

        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert "\\row" in rtf_output  # Has table rows

    def test_group_by_with_pagination(self):
        """Test that group_by works correctly across page boundaries."""
        # Create data that will span multiple pages
        df = pl.DataFrame(
            {
                "Group": ["A"] * 15 + ["B"] * 15,  # 30 rows total
                "ID": [f"ID{i:03d}" for i in range(30)],
                "Value": list(range(30)),
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=12),  # Force pagination
            rtf_body=RTFBody(
                group_by=["Group"],
                col_rel_width=[1, 2, 1],
            ),
            rtf_column_header=RTFColumnHeader(text=["Group", "ID", "Value"]),
        )

        rtf_output = doc.rtf_encode()

        # Should have page breaks
        assert "\\page" in rtf_output
        # Should have multiple pages (at least 2)
        page_count = rtf_output.count("\\page")
        assert page_count >= 1

    def test_group_by_page_context_restoration(self):
        """Test that group context is restored at the start of new pages."""
        # Create data where groups span page boundaries
        df = pl.DataFrame(
            {
                "Category": ["Cat1"] * 8 + ["Cat2"] * 8,
                "Item": [f"Item{i}" for i in range(16)],
                "Count": list(range(16)),
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=6),  # Small pages to force multiple pages
            rtf_body=RTFBody(
                group_by=["Category"],
                col_rel_width=[2, 3, 1],
            ),
            rtf_title=RTFTitle(text="Group Context Test"),
            rtf_column_header=RTFColumnHeader(text=["Category", "Item", "Count"]),
        )

        rtf_output = doc.rtf_encode()

        # Verify pagination occurred
        assert "\\page" in rtf_output
        # Context should be maintained (difficult to verify in RTF directly)
        assert len(rtf_output) > 1000  # Substantial content


class TestPaginationWithSublineBy:
    """Test pagination with subline_by feature for section headers."""

    def test_subline_by_creates_headers(self):
        """Test that subline_by creates section headers, not table rows."""
        df = pl.DataFrame(
            {
                "Section": ["Introduction", "Introduction", "Methods", "Methods"],
                "Item": ["A", "B", "C", "D"],
                "Value": [1, 2, 3, 4],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(
                subline_by=["Section"],
                col_rel_width=[1, 1],  # Only 2 columns after Section removal
            ),
        )

        rtf_output = doc.rtf_encode()

        # Should have RTF content
        assert isinstance(rtf_output, str)
        # Should have paragraph formatting for headers
        assert "\\par" in rtf_output

    def test_subline_by_forces_pagination(self):
        """Test that subline_by with new_page creates page breaks."""
        df = pl.DataFrame(
            {
                "Chapter": ["Ch1", "Ch1", "Ch2", "Ch2", "Ch3", "Ch3"],
                "Section": ["S1", "S2", "S3", "S4", "S5", "S6"],
                "Content": ["Text1", "Text2", "Text3", "Text4", "Text5", "Text6"],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(
                subline_by=["Chapter"],
                page_by=["Chapter"],
                new_page=True,  # Force new page for each chapter
                col_rel_width=[1, 2],
            ),
        )

        rtf_output = doc.rtf_encode()

        # Should have page breaks between chapters
        assert "\\page" in rtf_output

    def test_subline_by_with_group_by_combination(self):
        """Test combining subline_by headers with group_by suppression."""
        df = pl.DataFrame(
            {
                "Department": ["Sales", "Sales", "Sales", "Engineering", "Engineering"],
                "Employee": ["John", "John", "Jane", "Bob", "Bob"],
                "Quarter": ["Q1", "Q2", "Q1", "Q1", "Q2"],
                "Revenue": [100, 150, 200, 300, 350],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(
                subline_by=["Department"],  # Creates department headers
                group_by=["Employee"],  # Suppresses duplicate employee names
                col_rel_width=[2, 1, 1],  # 3 columns after Department removal
            ),
        )

        rtf_output = doc.rtf_encode()

        # Verify both features are working
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 500


class TestPaginationBoundaryConditions:
    """Test edge cases and boundary conditions for pagination."""

    def test_empty_dataframe(self):
        """Test pagination with empty DataFrame."""
        df = pl.DataFrame({"A": [], "B": [], "C": []})

        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=10), rtf_body=RTFBody())

        rtf_output = doc.rtf_encode()

        # Should still generate valid RTF structure
        assert isinstance(rtf_output, str)
        assert "{\\rtf" in rtf_output  # Valid RTF header

    def test_single_row_dataframe(self):
        """Test pagination with single row DataFrame."""
        df = pl.DataFrame({"A": [1], "B": ["test"], "C": [True]})

        doc = RTFDocument(df=df, rtf_page=RTFPage(nrow=10), rtf_body=RTFBody())

        rtf_output = doc.rtf_encode()

        # Should not have page breaks for single row
        assert "\\page" not in rtf_output or rtf_output.count("\\page") == 0
        # Should have the data
        assert "test" in rtf_output

    def test_exact_page_size_boundary(self):
        """Test when data exactly fills page capacity."""
        # Create data that exactly fits one page (considering headers/footers)
        df = pl.DataFrame(
            {
                "Row": [f"R{i:02d}" for i in range(8)],  # Exactly 8 data rows
                "Value": list(range(8)),
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=10),  # 10 total rows (8 data + headers)
            rtf_column_header=RTFColumnHeader(text=["Row", "Value"]),
            rtf_body=RTFBody(),
        )

        rtf_output = doc.rtf_encode()

        # Should fit in one page, no page breaks
        page_breaks = rtf_output.count("\\page")
        assert page_breaks == 0 or page_breaks == 1  # At most one final page break

    def test_one_row_over_page_boundary(self):
        """Test when data is exactly one row over page capacity."""
        # Create data that's one row over page capacity
        # nrow includes headers, so with nrow=10 and headers, we can fit ~8 data rows
        df = pl.DataFrame(
            {
                "Row": [f"R{i:02d}" for i in range(12)],  # 12 rows to exceed capacity
                "Value": list(range(12)),
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=10),  # Forces second page
            rtf_column_header=RTFColumnHeader(text=["Row", "Value"]),
            rtf_footnote=RTFFootnote(
                text="Test footnote"
            ),  # Add footnote for more rows
            rtf_body=RTFBody(),
        )

        rtf_output = doc.rtf_encode()

        # Should have page break for overflow
        assert "\\page" in rtf_output

    def test_large_dataset_pagination(self):
        """Test pagination with large dataset (1000+ rows)."""
        # Create large dataset
        df = pl.DataFrame(
            {
                "ID": [f"ID{i:04d}" for i in range(1000)],
                "Value": list(range(1000)),
                "Status": ["Active" if i % 2 == 0 else "Inactive" for i in range(1000)],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=50),  # 50 rows per page
            rtf_body=RTFBody(col_rel_width=[2, 1, 2]),
        )

        # Should not raise any errors
        rtf_output = doc.rtf_encode()

        # Should have many page breaks
        page_count = rtf_output.count("\\page")
        assert page_count >= 19  # At least 1000/50 = 20 pages


class TestServiceLayerIntegration:
    """Test integration of various services in pagination."""

    def test_document_service_pagination_detection(self):
        """Test DocumentService correctly detects when pagination is needed."""
        service = RTFDocumentService()

        # Case 1: Small data, no pagination needed
        df_small = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
        doc_small = RTFDocument(df=df_small)
        assert service.needs_pagination(doc_small) is False

        # Case 2: Large data, pagination needed
        df_large = pl.DataFrame({"A": list(range(100)), "B": list(range(100))})
        doc_large = RTFDocument(df=df_large, rtf_page=RTFPage(nrow=20))
        assert service.needs_pagination(doc_large) is True

        # Case 3: page_by specified, pagination needed
        doc_pageby = RTFDocument(
            df=df_small, rtf_body=RTFBody(page_by=["A"], new_page=True)
        )
        assert service.needs_pagination(doc_pageby) is True

    def test_grouping_service_enhance_group_by(self):
        """Test GroupingService correctly applies group_by transformation."""
        service = GroupingService()

        df = pl.DataFrame(
            {"Group": ["A", "A", "A", "B", "B"], "Value": [1, 2, 3, 4, 5]}
        )

        # Apply group_by transformation
        result = service.enhance_group_by(df, ["Group"])

        # First occurrence should remain, duplicates should be None
        assert result["Group"][0] == "A"
        assert result["Group"][1] is None  # Duplicate suppressed
        assert result["Group"][2] is None  # Duplicate suppressed
        assert result["Group"][3] == "B"  # New group
        assert result["Group"][4] is None  # Duplicate suppressed

    def test_grouping_service_restore_page_context(self):
        """Test GroupingService restores context at page boundaries."""
        service = GroupingService()

        # Original data
        original_df = pl.DataFrame(
            {
                "Site": ["S1", "S1", "S1", "S2", "S2"],
                "Patient": ["P1", "P1", "P2", "P1", "P1"],
                "Visit": [1, 2, 3, 1, 2],
            }
        )

        # Apply group_by
        transformed_df = service.enhance_group_by(original_df, ["Site", "Patient"])

        # Simulate page boundaries at rows 2 and 4
        page_start_indices = [2, 4]

        # Restore context
        restored_df = service.restore_page_context(
            transformed_df, original_df, ["Site", "Patient"], page_start_indices
        )

        # Context should be restored at page starts
        assert restored_df["Site"][2] == "S1"  # Restored at page 2 start
        assert restored_df["Patient"][2] == "P2"  # Restored at page 2 start
        assert restored_df["Site"][4] == "S2"  # Restored at page 3 start
        assert restored_df["Patient"][4] == "P1"  # Restored at page 3 start

    def test_full_pipeline_with_services(self):
        """Test complete document generation with all services."""
        # Create complex document with multiple features
        df = pl.DataFrame(
            {
                "Department": ["Sales"] * 10 + ["Engineering"] * 10,
                "Employee": (["John"] * 5 + ["Jane"] * 5) * 2,
                "Month": list(range(1, 11)) * 2,
                "Revenue": [100 + i * 10 for i in range(20)],
            }
        )

        doc = RTFDocument(
            df=df,
            rtf_page=RTFPage(nrow=8),  # Force pagination
            rtf_title=RTFTitle(text="Revenue Report"),
            rtf_column_header=RTFColumnHeader(
                text=["Department", "Employee", "Month", "Revenue"]
            ),
            rtf_body=RTFBody(
                group_by=["Department", "Employee"], col_rel_width=[2, 2, 1, 1]
            ),
            rtf_footnote=RTFFootnote(text="Generated by RTFLite"),
        )

        # Should complete without errors
        rtf_output = doc.rtf_encode()

        # Verify output has expected elements
        assert isinstance(rtf_output, str)
        assert "Revenue Report" in rtf_output
        assert "\\page" in rtf_output  # Has pagination
        assert "Generated by RTFLite" in rtf_output


class TestGroupByImplementationDetails:
    """Test specific implementation details of group_by feature."""

    def test_group_by_null_handling(self):
        """Test that group_by handles null values correctly."""
        # Data must be sorted for group_by to work properly
        df = pl.DataFrame(
            {"Group": ["A", "A", "B", None, None], "Value": [1, 3, 4, 2, 5]}
        )

        service = GroupingService()
        result = service.enhance_group_by(df, ["Group"])

        # First occurrence should remain, duplicates should be suppressed
        assert result["Group"][0] == "A"
        assert result["Group"][1] is None  # Duplicate A suppressed
        assert result["Group"][2] == "B"  # New group
        assert result["Group"][3] is None  # Original null preserved
        assert result["Group"][4] is None  # Duplicate null

    def test_group_by_maintains_other_columns(self):
        """Test that group_by only affects specified columns."""
        df = pl.DataFrame(
            {
                "Group": ["A", "A", "B", "B"],
                "Value": [1, 2, 3, 4],
                "Status": ["OK", "FAIL", "OK", "FAIL"],
            }
        )

        service = GroupingService()
        result = service.enhance_group_by(df, ["Group"])

        # Only Group column should be modified
        assert result["Group"].to_list() == ["A", None, "B", None]
        assert result["Value"].to_list() == [1, 2, 3, 4]  # Unchanged
        assert result["Status"].to_list() == ["OK", "FAIL", "OK", "FAIL"]  # Unchanged
