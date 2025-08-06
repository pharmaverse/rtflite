import polars as pl
import pytest

import rtflite as rtf

from .utils import ROutputReader
from .utils_snapshot import assert_rtf_equals_semantic

r_output = ROutputReader("test_pagination")


class TestPaginationData:
    """Test data for comprehensive pagination tests."""

    @staticmethod
    def df_6_rows():
        """DataFrame with 6 rows for testing pagination with nrow=2 (3 pages)"""
        return pl.DataFrame(
            {
                "Col1": ["Row1", "Row2", "Row3", "Row4", "Row5", "Row6"],
                "Col2": ["A", "B", "C", "D", "E", "F"],
            }
        )

    @staticmethod
    def df_2_rows():
        """DataFrame with 2 rows for testing single page scenarios"""
        return pl.DataFrame({"Col1": ["Row1", "Row2"], "Col2": ["A", "B"]})


def test_pagination_basic_with_headers():
    """Test basic pagination with column headers, no footnote/source."""
    df = TestPaginationData.df_6_rows()

    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait", nrow=3),
        rtf_column_header=[
            rtf.RTFColumnHeader(text=["Column 1", "Column 2"], col_rel_width=[1, 1])
        ],
        rtf_body=rtf.RTFBody(col_rel_width=[1, 1]),
    )

    # ```{r, basic_with_headers}
    # library(r2rtf)
    # test_data <- data.frame(
    #   Col1 = c("Row1", "Row2", "Row3", "Row4", "Row5", "Row6"),
    #   Col2 = c("A", "B", "C", "D", "E", "F"),
    #   stringsAsFactors = FALSE
    # )
    #
    # test_data |>
    #   rtf_page(orientation = "portrait", nrow = 3) |>
    #   rtf_colheader(
    #     colheader = "Column 1 | Column 2",
    #     col_rel_width = c(1, 1)
    #   ) |>
    #   rtf_body(
    #     col_rel_width = c(1, 1)
    #   ) |>
    #   rtf_encode() |>
    #   write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```

    rtf_output = doc.rtf_encode()
    expected = r_output.read("basic_with_headers")

    # Use exact assertion with semantic normalization (handles font tables, page breaks, border styles, etc.)
    assert_rtf_equals_semantic(
        rtf_output, expected, "test_pagination_basic_with_headers"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
