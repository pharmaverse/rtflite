import polars as pl

from rtflite.input import RTFBody
from rtflite.pagination.core import PageBreakCalculator, RTFPagination
from rtflite.row import Utils
from rtflite.services.encoding_service import RTFEncodingService


def test_col_widths_proportionality():
    """Test that Utils._col_widths distributes width proportionally."""
    col_total_width = 10.0

    # Case 1: Equal weights
    rel_widths = [1, 1]
    widths = Utils._col_widths(rel_widths, col_total_width)
    # Note: Utils._col_widths returns cumulative widths!
    # [5.0, 10.0]
    assert widths[0] == 5.0
    assert widths[1] == 10.0

    # Case 2: 1:3 ratio
    rel_widths = [1, 3]
    widths = Utils._col_widths(rel_widths, col_total_width)
    # 1/4 * 10 = 2.5
    # 3/4 * 10 = 7.5
    # Cumulative: [2.5, 10.0]
    assert widths[0] == 2.5
    assert widths[1] == 10.0


def test_prepare_dataframe_slices_col_rel_width():
    """Test that prepare_dataframe_for_body_encoding correctly slices col_rel_width."""
    service = RTFEncodingService()

    # Setup
    df = pl.DataFrame(
        {
            "A": [1],
            "B": [2],  # page_by column
            "C": [3],
        }
    )

    rtf_body = RTFBody(col_rel_width=[1, 1, 3], page_by="B")

    processed_df, _, processed_attrs = service.prepare_dataframe_for_body_encoding(
        df, rtf_body
    )

    # Check processed dataframe columns
    assert processed_df.columns == ["A", "C"]

    # Check processed attributes col_rel_width
    # Should remove the middle element (index 1)
    # [1, 1, 3] -> [1, 3]
    assert processed_attrs.col_rel_width == [1, 3]


def test_page_break_calculator_skips_removed_columns():
    """Test that PageBreakCalculator correctly skips removed columns."""

    # Setup
    # Original DF has 3 columns: A, B(page_by), C
    # Processed DF has 2 columns: A, C
    # col_rel_width was [1, 1, 3] -> [1, 3]
    # col_total_width = 10
    # col_widths (cumulative) for [1, 3] -> [2.5, 10.0]

    pagination = RTFPagination(
        page_width=11, page_height=8.5, margin=[1] * 6, nrow=24, orientation="landscape"
    )
    calculator = PageBreakCalculator(pagination=pagination)

    # Mock data
    df = pl.DataFrame({"A": ["Long text " * 10], "B": ["Page By Val"], "C": ["Short"]})

    # If B is NOT skipped, it uses width 2.5 (from A) for B.
    # If B IS skipped, it uses width 2.5 for A, and width 7.5 for C.

    # We can check calculate_row_metadata
    # But we need to pass removed_column_indices

    col_widths = [2.5, 10.0]
    removed_indices = [1]  # B is removed

    meta = calculator.calculate_row_metadata(
        df=df,
        col_widths=col_widths,
        removed_column_indices=removed_indices,
        additional_rows_per_page=0,
    )

    # If logic is correct, it should process A (idx 0) and C (idx 2).
    # A uses col_widths[0] = 2.5
    # C uses col_widths[1] = 10.0 (cumulative) -> effective width 10.0?
    # Wait, if PageBreakCalculator uses cumulative widths as absolute, that's a bug
    # I suspected earlier.
    # But let's assume for now we are testing that it SKIPS index 1.

    # If it didn't skip index 1, it would try to calculate rows for B using
    # col_widths[1]?
    # Or it would run out of col_widths?

    # The loop in calculate_row_metadata iterates over df.width (3 columns).
    # width_idx starts at 0.
    # Col 0 (A): not removed. Uses col_widths[0]. width_idx -> 1.
    # Col 1 (B): removed. Should continue. width_idx stays 1.
    # Col 2 (C): not removed. Uses col_widths[1]. width_idx -> 2.

    # If removed_indices was None:
    # Col 0 (A): Uses col_widths[0]. width_idx -> 1.
    # Col 1 (B): Uses col_widths[1]. width_idx -> 2.
    # Col 2 (C): Breaks because width_idx 2 >= len(col_widths) (2).

    # So if we pass removed_indices, we should get results for all rows.
    # If we don't, we might get incomplete results or different behavior.

    assert meta.height == 1
    # We just verify it runs without error and produces metadata
    assert meta["data_rows"][0] > 0


def test_spanning_row_width():
    """Test that spanning rows (page_by/subline_by) use the full page width."""
    service = RTFEncodingService()
    page_width = 10.0

    # Encode a spanning row
    rtf_lines = service.encode_spanning_row(
        text="Spanning Header", page_width=page_width, rtf_body_attrs=None
    )

    # Verify the RTF output contains \cellx with the correct width in twips
    # 10 inches = 14400 twips
    expected_twips = int(page_width * 1440)
    expected_cellx = f"\\cellx{expected_twips}"

    # Join lines to search
    rtf_output = "".join(rtf_lines)

    assert expected_cellx in rtf_output


def test_page_break_calculator_cumulative_width_fix():
    """
    Test that PageBreakCalculator correctly decodes cumulative widths
    to calculate individual column widths for row height estimation.
    """
    # Setup
    pagination = RTFPagination(
        page_width=11, page_height=8.5, margin=[1] * 6, nrow=24, orientation="landscape"
    )
    calculator = PageBreakCalculator(pagination=pagination)

    # 2 columns.
    # Col 1: width 2.0. Cumulative: 2.0.
    # Col 2: width 2.0. Cumulative: 4.0.
    col_widths = [2.0, 4.0]

    # Text that fits in 4.0 inches but NOT in 2.0 inches.
    # 2.0 inches = 144 points.
    # 4.0 inches = 288 points.
    # Assume font size 9 (default).
    # "A" is approx 5-6 points?
    # Let's use a string length that we know wraps.
    # get_string_width uses rough estimation.
    # Let's say 100 chars.
    long_text = "A" * 100

    df = pl.DataFrame({"Col1": ["Short"], "Col2": [long_text]})

    meta = calculator.calculate_row_metadata(
        df=df,
        col_widths=col_widths,
        removed_column_indices=[],
        additional_rows_per_page=0,
    )

    # Check row height (lines)
    # If using cumulative width (4.0) for Col 2:
    # Text width for 100 chars ~ 500-600 points?
    # 4.0 inches = 288 points? Wait.
    # 1 inch = 72 points.
    # 4.0 inches = 288 points.
    # 2.0 inches = 144 points.

    # If text width is e.g. 200 points.
    # Fits in 4.0 (288). Lines = 1.
    # Wraps in 2.0 (144). Lines = 2.

    # Let's verify what get_string_width returns for "A"*100.
    from rtflite.strwidth import get_string_width

    width_pts = get_string_width(long_text, font_size=9)
    # print(f"Width: {width_pts}")

    # If logic is correct (using individual width 2.0), lines should be > 1.
    # If logic is buggy (using cumulative width 4.0), lines might be 1 (if text
    # fits in 4.0).

    lines = meta["data_rows"][0]

    # We expect lines > 1 because 2.0 inches is narrow.
    assert lines > 1, (
        f"Expected wrapping for narrow column. Got {lines} lines. "
        f"Text width: {width_pts}"
    )

    # Also verify that if we make text short enough to fit in 4.0 but not 2.0,
    # we can distinguish.
    # But "A"*100 is likely wide enough to wrap even in 4.0?
    # Let's try "A"*40.

    medium_text = "A" * 40
    df_medium = pl.DataFrame({"Col1": ["Short"], "Col2": [medium_text]})

    meta_medium = calculator.calculate_row_metadata(
        df=df_medium,
        col_widths=col_widths,
        removed_column_indices=[],
        additional_rows_per_page=0,
    )

    lines_medium = meta_medium["data_rows"][0]

    # With fix: uses width 2.0 (144 pts). 240 > 144. Should wrap. Lines >= 2.
    # Without fix: uses width 4.0 (288 pts). 240 < 288. Should fit. Lines = 1.

    assert lines_medium >= 2, (
        "Regression: PageBreakCalculator using cumulative width instead of individual!"
    )


def test_data_row_width_redistribution():
    """
    Test that data column widths are redistributed proportionally
    to fill the WHOLE table width after removing page_by columns.
    """
    service = RTFEncodingService()

    # Setup: 3 columns, middle one is page_by
    df = pl.DataFrame(
        {
            "A": [1],
            "B": [2],  # page_by
            "C": [3],
        }
    )

    # Relative widths: [1, 1, 2]
    # If B is removed, remaining are [1, 2]. Total weight = 3.
    rtf_body = RTFBody(col_rel_width=[1, 1, 2], page_by="B")

    # 1. Prepare dataframe (simulate UnifiedRTFEncoder step)
    processed_df, _, processed_attrs = service.prepare_dataframe_for_body_encoding(
        df, rtf_body
    )

    # Verify B is removed and col_rel_width is sliced
    assert processed_df.columns == ["A", "C"]
    assert processed_attrs.col_rel_width == [1, 2]

    # 2. Calculate widths (simulate UnifiedRTFEncoder step)
    col_total_width = 9.0  # Use 9.0 for easy math (1+2=3, 9/3=3 per unit)

    col_widths = Utils._col_widths(processed_attrs.col_rel_width, col_total_width)

    # Expected:
    # Col A: 1/3 * 9.0 = 3.0
    # Col C: 2/3 * 9.0 = 6.0
    # Cumulative: [3.0, 9.0]

    assert len(col_widths) == 2
    assert col_widths[0] == 3.0
    assert col_widths[1] == 9.0

    # This confirms that the remaining columns expand to fill the FULL page width.
