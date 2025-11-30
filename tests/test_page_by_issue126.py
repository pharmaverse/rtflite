"""
Tests for page_by feature (Issue #126).

Regression tests ensuring page_by works correctly for both single-page
and multi-page scenarios with new_page=True.
"""

import polars as pl

import rtflite as rtf


class TestPageByIssue126:
    """Test page_by feature with new_page for issue #126."""

    def create_test_data(self, groups: int = 2, rows_per_group: int = 10):
        """Create test data with specified groups and rows per group."""
        data = []
        for group_idx in range(1, groups + 1):
            group_name = f"Subject {group_idx}"
            for row_idx in range(1, rows_per_group + 1):
                global_idx = (group_idx - 1) * rows_per_group + row_idx
                data.append(
                    {
                        "__index__": group_name,
                        "ID": f"{global_idx:03d}",
                        "Event": f"AE{global_idx}",
                    }
                )
        return pl.DataFrame(data)

    def test_page_by_single_page_without_new_page(self):
        """
        Test page_by without new_page allows multiple groups on one page.

        After refactoring:
        - page_by creates spanning rows and removes columns (ALWAYS)
        - new_page=False allows natural pagination (NO forced breaks)
        - Multiple groups can appear on same page with spanning rows between them
        """
        df = self.create_test_data(groups=2, rows_per_group=5)

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape"),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=False,  # Natural pagination, no forced breaks
            ),
        )

        rtf_output = doc.rtf_encode()

        # With new_page=False and data that fits on one page:
        # Should have NO page breaks (all fits naturally)
        page_breaks = rtf_output.count(r"\page")
        assert page_breaks == 0, (
            f"Expected no page breaks with new_page=False and small data, found "
            f"{page_breaks}"
        )

        # Should have spanning rows for BOTH groups (on same page)
        # Subject values appear as spanning rows, not data columns
        assert "Subject 1" in rtf_output, "Subject 1 should appear as spanning row"
        assert "Subject 2" in rtf_output, "Subject 2 should appear as spanning row"

        # Verify columns removed: should have only 2 column headers (ID, Event)
        # not 3 (__index__, ID, Event)
        lines = rtf_output.split("\n")
        header_cols = sum(
            1 for line in lines[:50] if "\\clvertalb" in line and "\\cellx" in line
        )
        assert header_cols == 2, (
            f"Expected 2 columns after fix (ID, Event), found {header_cols}"
        )

    def test_page_by_single_page_with_new_page(self):
        """Test page_by on single page with new_page (spanning rows)."""
        df = self.create_test_data(groups=2, rows_per_group=5)

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape"),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",  # Creates spanning rows
            ),
        )

        rtf_output = doc.rtf_encode()

        # Should have 1 page break (forced break between groups)
        assert rtf_output.count(r"\page") == 1

        # Should have spanning rows for both groups
        # Each appears once as spanning row
        subject1_count = rtf_output.count("Subject 1")
        subject2_count = rtf_output.count("Subject 2")

        assert subject1_count == 1, "Subject 1 spanning row should appear once"
        assert subject2_count == 1, "Subject 2 spanning row should appear once"

    def test_page_by_multi_page_single_group_spanning(self):
        """
        Test page_by with single group spanning multiple pages.

        This is the CRITICAL test case for issue #126.
        A single group (Subject 1) with many rows should show the
        spanning row on ALL pages of that group.
        """
        df = self.create_test_data(groups=1, rows_per_group=50)

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape", nrow=15),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # Calculate expected pages
        # nrow=15 includes headers (2 rows) + spanning row (1 row) + data
        # So ~12 data rows per page
        # 50 rows / 12 is approximately 4-5 pages
        page_breaks = rtf_output.count(r"\page")
        total_pages = page_breaks + 1

        # Subject 1 should appear as spanning row on EVERY page
        subject1_count = rtf_output.count("Subject 1")

        assert subject1_count >= 4, (
            f"Subject 1 should appear on all {total_pages} pages, "
            f"but only found {subject1_count} times"
        )

        # Verify spanning rows have full width (12240 twips for landscape)
        # This is a characteristic of spanning rows
        assert r"\cellx12240" in rtf_output

    def test_page_by_multi_page_multiple_groups(self):
        """Test page_by with multiple groups across multiple pages."""
        df = self.create_test_data(groups=2, rows_per_group=30)

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape", nrow=15),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # Should have multiple page breaks
        page_breaks = rtf_output.count(r"\page")
        assert page_breaks >= 3, "Should have at least 3 page breaks for 60 rows"

        # Each group should appear multiple times (spanning rows repeated)
        subject1_count = rtf_output.count("Subject 1")
        subject2_count = rtf_output.count("Subject 2")

        # With 30 rows per group and ~12 rows per page:
        # Subject 1 should span ~3 pages -> 3 spanning rows
        # Subject 2 should span ~3 pages -> 3 spanning rows
        assert subject1_count >= 2, (
            f"Subject 1 should appear on multiple pages, found {subject1_count}"
        )
        assert subject2_count >= 2, (
            f"Subject 2 should appear on multiple pages, found {subject2_count}"
        )

    def test_page_by_with_sorting(self):
        """Test page_by with sorted data (common use case)."""
        # Create unsorted data
        data = []
        for i in range(20):
            subject = "Subject 2" if i % 2 == 0 else "Subject 1"
            data.append(
                {
                    "__index__": subject,
                    "ID": f"{i + 1:03d}",
                    "Event": f"AE{i + 1}",
                }
            )
        df = pl.DataFrame(data)

        # Sort by __index__ (groups together)
        df_sorted = df.sort("__index__")

        doc = rtf.RTFDocument(
            df=df_sorted,
            rtf_page=rtf.RTFPage(orientation="landscape"),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # Should have page break between groups
        assert rtf_output.count(r"\page") >= 1

        # Both groups should have spanning rows
        assert "Subject 1" in rtf_output
        assert "Subject 2" in rtf_output

    def test_page_by_columns_removed_when_new_page_true(self):
        """Verify page_by columns are removed from table when new_page=True."""
        df = self.create_test_data(groups=2, rows_per_group=10)

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape"),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # Verify that __index__ column header is NOT present
        # Only ID and Event should be in headers
        # Look for pattern: header row followed by column text

        # Simple check: Count "Event}\\cell" (should be 1 per page for last column)
        # and verify __index__ is not in header context
        lines = rtf_output.split("\n")

        # Find header section (before first data row)
        header_section = []
        found_header = False
        for line in lines:
            if "ID}\\cell" in line:
                found_header = True
                header_section.append(line)
            elif found_header and "Event}\\cell" in line:
                header_section.append(line)
                break

        header_text = "\n".join(header_section)

        # Verify ID and Event are present as headers
        assert "ID}\\cell" in header_text, "ID should be in headers"
        assert "Event}\\cell" in header_text, "Event should be in headers"

        # Verify __index__ is NOT in header row (it's been removed)
        # It will appear in spanning rows but not as a column header
        assert "__index__" not in header_text, (
            "__index__ should not appear as column header when new_page=True"
        )

    def test_page_by_landscape_orientation(self):
        """Test page_by with landscape orientation (common for wide tables)."""
        df = self.create_test_data(groups=2, rows_per_group=20)

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape", nrow=15),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # Verify landscape orientation
        assert "\\landscape" in rtf_output

        # Verify spanning rows use landscape page width
        # Landscape: 15840x12240 twips
        assert "\\paperw15840\\paperh12240" in rtf_output

        # Should have page breaks
        assert rtf_output.count(r"\page") >= 1


class TestPageByEdgeCases:
    """Test edge cases for page_by feature."""

    def test_page_by_empty_dataframe(self):
        """Test page_by with empty DataFrame."""
        df = pl.DataFrame({"__index__": [], "ID": [], "Event": []})

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape"),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        # Should not raise an error
        rtf_output = doc.rtf_encode()
        assert rtf_output is not None

    def test_page_by_single_row(self):
        """Test page_by with single row."""
        df = pl.DataFrame(
            {
                "__index__": ["Subject 1"],
                "ID": ["001"],
                "Event": ["AE1"],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape"),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # Single row, single group
        assert rtf_output.count(r"\page") == 0
        assert "Subject 1" in rtf_output

    def test_page_by_all_same_group(self):
        """Test page_by when all rows belong to same group."""
        df = pl.DataFrame(
            {
                "__index__": ["Subject 1"] * 20,
                "ID": [f"{i:03d}" for i in range(1, 21)],
                "Event": [f"AE{i}" for i in range(1, 21)],
            }
        )

        doc = rtf.RTFDocument(
            df=df,
            rtf_page=rtf.RTFPage(orientation="landscape", nrow=10),
            rtf_body=rtf.RTFBody(
                page_by=["__index__"],
                new_page=True,
                pageby_row="first_row",
            ),
        )

        rtf_output = doc.rtf_encode()

        # All same group, so should have natural pagination but no forced breaks
        # between groups (there's only one group)
        subject1_count = rtf_output.count("Subject 1")

        # Should appear on multiple pages (spanning row repeated)
        assert subject1_count >= 2, (
            "Spanning row should repeat on each page of the same group"
        )
