import polars as pl

import rtflite as rtf


def test_nested_page_by_spanning_rows_long_text():
    """
    Test that multiple page_by columns create nested spanning rows
    and that long text in these rows uses the full table width for wrapping.
    """
    # Create data with 2 levels of grouping and long text
    long_text_1 = "Level 1 Grouping " * 20  # Should wrap if confined to column
    long_text_2 = "Level 2 Subgroup " * 20  # Should wrap if confined to column

    df = pl.DataFrame(
        {
            "Group1": [long_text_1, long_text_1, "Other Group", "Other Group"],
            "Group2": [long_text_2, "Other Subgroup", long_text_2, "Other Subgroup"],
            "ID": ["001", "002", "003", "004"],
            "Value": ["Val1", "Val2", "Val3", "Val4"],
        }
    )

    # Configure RTF document with 2 page_by columns
    # Use landscape to give more width
    document = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="landscape", nrow=20),
        rtf_body=rtf.RTFBody(
            page_by=["Group1", "Group2"],
            col_rel_width=[1, 1],  # Widths for ID and Value
            # Note: Group1 and Group2 are removed from table columns
        ),
    )

    # We need to access the internal pagination logic to verify row counts
    # directly, as parsing RTF for exact line counts is tricky.
    # We'll use the same logic as in document_service.py to setup the calculator

    from rtflite.pagination import PageBreakCalculator, RTFPagination
    from rtflite.row import Utils

    # Setup pagination
    pagination = RTFPagination(
        page_width=document.rtf_page.width,
        page_height=document.rtf_page.height,
        margin=document.rtf_page.margin,
        nrow=document.rtf_page.nrow,
        orientation=document.rtf_page.orientation,
    )

    calculator = PageBreakCalculator(pagination=pagination)

    # Calculate column widths
    col_total_width = document.rtf_page.col_width

    # We need to simulate what happens in the app.
    # We pass widths for ALL columns, including the spanning ones,
    # because the dataframe has them.
    col_widths_all = Utils._col_widths([1, 1, 1, 1], col_total_width)  # 4 columns

    # Calculate content rows WITH spanning columns (the fix)
    spanning_cols = document.rtf_body.page_by

    # Calculate rows with fix
    row_counts_fixed = calculator.calculate_content_rows(
        df,
        col_widths_all,
        table_attrs=document.rtf_body,
        spanning_columns=spanning_cols,
    )

    # Calculate rows WITHOUT fix (simulate by passing None for spanning_columns)
    row_counts_broken = calculator.calculate_content_rows(
        df, col_widths_all, table_attrs=document.rtf_body, spanning_columns=None
    )

    print(f"\nRow counts with fix: {row_counts_fixed}")
    print(f"Row counts without fix: {row_counts_broken}")

    # Verification
    # The spanning rows (indices 0 and 1 for the first group, etc.) should have
    # FEWER lines with the fix because they use the full width.

    # Check first row (Group1 long text)
    # With fix, it should be significantly smaller
    assert row_counts_fixed[0] < row_counts_broken[0], (
        f"Expected fewer rows for spanning column with fix. "
        f"Got {row_counts_fixed[0]} vs {row_counts_broken[0]}"
    )

    # Check second row (Group2 long text)
    assert row_counts_fixed[1] < row_counts_broken[1], (
        f"Expected fewer rows for spanning column with fix. "
        f"Got {row_counts_fixed[1]} vs {row_counts_broken[1]}"
    )


def test_nested_page_by_rtf_structure():
    """
    Test that nested page_by columns result in multiple spanning rows in the RTF output.
    """
    df = pl.DataFrame(
        {
            "Group1": ["G1", "G1"],
            "Group2": ["Sub1", "Sub2"],
            "ID": ["001", "002"],
            "Value": ["V1", "V2"],
        }
    )

    document = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait"),
        rtf_body=rtf.RTFBody(
            page_by=["Group1", "Group2"],
            col_rel_width=[1, 1],
        ),
    )

    rtf_output = document.rtf_encode()

    # We expect:
    # 1. Spanning row for "G1"
    # 2. Spanning row for "Sub1"
    # 3. Data row for "001"
    # 4. Spanning row for "Sub2" (since it changes)
    # 5. Data row for "002"

    # Check for "G1"
    assert "G1" in rtf_output

    # Check for "Sub1"
    assert "Sub1" in rtf_output

    # Check for "Sub2"
    assert "Sub2" in rtf_output

    # Check that "G1" and "Sub1" are NOT joined
    assert "G1 | Sub1" not in rtf_output
    assert "G1, Sub1" not in rtf_output

    # Check order
    g1_index = rtf_output.find("G1")
    sub1_index = rtf_output.find("Sub1")
    assert g1_index < sub1_index

    # And "Sub1" before "001"
    val1_index = rtf_output.find("001")
    assert sub1_index < val1_index

    # And "Sub2" after "001" (new group)
    sub2_index = rtf_output.find("Sub2")
    assert val1_index < sub2_index

    # CRITICAL CHECK: "G1" should NOT be repeated before "Sub2"
    # because "G1" value didn't change.
    # We search for "G1" AFTER "001". It should NOT be found
    # (or at least not as a header).
    # Note: "G1" might appear in the first header, so we need to be careful.
    # We can check the count. "G1" should appear ONCE (for the first group).
    # Unless it's a new page, but here it's a small table.
    assert rtf_output.count("G1") == 1, (
        "Group1 header should not be repeated when value is unchanged"
    )
