import polars as pl

from rtflite.input import RTFBody, RTFPage
from rtflite.pagination.strategies.base import PaginationContext
from rtflite.pagination.strategies.grouping import SublineStrategy


class TestCombinedGrouping:
    def test_combined_page_by_and_subline_by(self):
        """Test that SublineStrategy handles both page_by and subline_by."""
        # Create sample data
        data = pl.DataFrame(
            {
                "study": ["A", "A", "A", "B", "B"],
                "site": ["1", "1", "2", "3", "3"],
                "subject": ["001", "002", "003", "004", "005"],
                "val": [1, 2, 3, 4, 5],
            }
        )

        # Configure attributes
        rtf_page = RTFPage(
            width=11.0,
            height=8.5,
            margin=[1.0, 1.0, 1.0, 1.0, 0.5, 0.5],
            nrow=10,
            orientation="landscape",
        )
        rtf_page._set_default()

        rtf_body = RTFBody(
            page_by=["study"],
            subline_by=["site"],
            new_page=True,  # subline_by implies new_page usually
        )

        # Create context
        context = PaginationContext(
            df=data,
            rtf_body=rtf_body,
            rtf_page=rtf_page,
            col_widths=[1.0, 2.0, 3.0, 4.0],
            table_attrs=rtf_body,
            additional_rows_per_page=0,
        )

        # Run strategy
        strategy = SublineStrategy()
        pages = strategy.paginate(context)

        # Verify results
        # We expect 3 pages: (A, 1), (A, 2), (B, 3)
        assert len(pages) == 3

        # Page 1: Study A, Site 1
        p1 = pages[0]
        assert p1.subline_header is not None
        assert p1.subline_header["group_values"]["site"] == "1"
        assert p1.pageby_header_info is not None
        assert p1.pageby_header_info["group_values"]["study"] == "A"

        # Page 2: Study A, Site 2
        p2 = pages[1]
        assert p2.subline_header is not None
        assert p2.subline_header["group_values"]["site"] == "2"
        assert p2.pageby_header_info is not None
        assert p2.pageby_header_info["group_values"]["study"] == "A"

        # Page 3: Study B, Site 3
        p3 = pages[2]
        assert p3.subline_header is not None
        assert p3.subline_header["group_values"]["site"] == "3"
        assert p3.pageby_header_info is not None
        assert p3.pageby_header_info["group_values"]["study"] == "B"
