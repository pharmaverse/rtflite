"""
CRITICAL BUG TEST: page_by should create spanning rows, not keep column as data.

Current WRONG behavior:
- page_by=['__index__'] creates a 3-column table: __index__ | ID | Event
- Subject values appear in EVERY row as data

Expected CORRECT behavior:
- page_by=['__index__'] creates a 2-column table: ID | Event
- Subject values appear as SPANNING ROWS (one cell across full width)
- Subject 1 (spanning row)
- 001 | AE1
- 003 | AE3
- ...
- Subject 2 (spanning row)
- 002 | AE2
- ...
"""

import polars as pl

import rtflite as rtf


def test_page_by_should_create_spanning_rows_not_data_column():
    """
    CRITICAL BUG: page_by should always create spanning rows.

    Currently, page_by without new_page=True keeps the column as data.
    This test verifies the CORRECT behavior: spanning rows regardless of new_page.
    """
    # Exact user data
    df = pl.DataFrame(
        {
            "__index__": ["Subject 1", "Subject 1", "Subject 2", "Subject 2"],
            "ID": ["001", "002", "003", "004"],
            "Event": ["AE1", "AE2", "AE3", "AE4"],
        }
    )
    df = pl.concat([df] * 25)
    df = df.with_columns(
        pl.when(pl.int_range(0, pl.len()) % 2 == 0)
        .then(pl.lit("Subject 1"))
        .otherwise(pl.lit("Subject 2"))
        .alias("__index__")
    )
    df = df.with_columns(
        (pl.int_range(0, pl.len()) + 1).map_elements(lambda x: f"{x:03d}").alias("ID")
    )
    df = df.with_columns(
        (pl.int_range(0, pl.len()) + 1).map_elements(lambda x: f"AE{x}").alias("Event")
    )

    df_sorted = df.sort("__index__")

    document = rtf.RTFDocument(
        df=df_sorted,
        rtf_page=rtf.RTFPage(orientation="landscape"),
        rtf_body=rtf.RTFBody(
            page_by=["__index__"],
            # NOTE: new_page NOT set!
        ),
    )

    rtf_output = document.rtf_encode()

    # CRITICAL TEST: Check table structure
    lines = rtf_output.split("\n")

    # Find header row - should have ONLY 2 columns (ID, Event)
    # NOT 3 columns (__index__, ID, Event)

    # Method: Count column definitions in first table row
    # Look for \cellx definitions before first \cell
    header_col_defs = []
    data_col_defs = []
    in_header = False
    in_data = False
    for _i, line in enumerate(lines):
        # Find header row (has \clvertalb - vertical align bottom)
        if "\\clvertalb" in line and "\\cellx" in line and not in_header:
            in_header = True

        if in_header and "\\cellx" in line and "cellx" in line:
            # Extract cellx value
            header_col_defs.append(line)

        if in_header and "\\intbl\\row" in line:
            in_header = False
            # Next table row will be data
            in_data = True
            continue

        # Find first data row (has \clvertalt - vertical align top)
        if in_data and "\\clvertalt" in line and "\\cellx" in line:
            data_col_defs.append(line)

        if in_data and "\\intbl\\row" in line:
            break  # Got first data row

    print(f"\nHeader column definitions found: {len(header_col_defs)}")
    print(f"Data column definitions found: {len(data_col_defs)}")

    # CRITICAL ASSERTION 1: Should have only 2 columns, not 3
    assert len(header_col_defs) == 2, (
        f"Expected 2 columns (ID, Event), but found {len(header_col_defs)} columns. "
        "Bug: page_by column '__index__' should be removed from table, not kept as "
        "data column."
    )

    # CRITICAL ASSERTION 2: Data rows should also have only 2 columns
    # (unless there's a spanning row, which would have 1 column spanning full width)
    # For first data row after header, check if it's a spanning row

    # Look for spanning row pattern: single cell with full page width
    # In landscape: full width is 12240 twips, but for spanning row it should be
    # the ONLY cellx in that row

    # Actually, let's check differently: find the first data row and count cells
    first_data_row_cells = []
    found_header_end = False
    cell_count = 0

    for _i, line in enumerate(lines):
        if "\\intbl\\row" in line:
            if not found_header_end:
                found_header_end = True
                continue
            else:
                # Found end of first data row
                break

        if found_header_end and "}\\cell" in line:
            cell_count += 1
            first_data_row_cells.append(line.strip()[:80])  # Truncate for readability

    print(f"\nFirst data row has {cell_count} cells:")
    for cell in first_data_row_cells:
        print(f"  {cell}")

    # CRITICAL ASSERTION 3: First data row after header should either:
    # Option A: Be a spanning row (1 cell with group value)
    # Option B: Be a data row with 2 cells (ID, Event)
    #
    # It should NOT be 3 cells (Subject 1, ID, Event)

    assert cell_count != 3, (
        "First data row has 3 cells, which indicates page_by column is in the table "
        "as data. Expected: spanning row (1 cell) or data row (2 cells). "
        "Bug: page_by should create spanning rows, not keep column as data."
    )

    # ASSERTION 4: Check if spanning row exists
    # A spanning row should have "Subject 1" or "Subject 2" as sole content
    # followed by data rows with only ID and Event

    # Simpler check: The table should NOT have __index__ as a column header
    has_index_header = False
    for line in lines[:100]:  # Check first 100 lines
        if "__index__" in line and "\\cell" in line:
            # Check if it's in a header context (has \\clvertalb nearby)
            # Find this line index and check nearby lines
            line_idx = lines.index(line) if line in lines else -1
            if line_idx > 0:
                nearby_lines = lines[max(0, line_idx - 5) : line_idx + 1]
                if any("\\clvertalb" in line_check for line_check in nearby_lines):
                    has_index_header = True
                    break

    assert not has_index_header, (
        "Found '__index__' as a column header. "
        "Bug: page_by column should be removed from headers, not displayed as a column."
    )


def test_page_by_correct_spanning_row_structure():
    """
    Test what the CORRECT structure should look like.

    This test describes the expected behavior based on Image #3.
    """
    df = pl.DataFrame(
        {
            "Subject": ["S1", "S1", "S1", "S2", "S2", "S2"],
            "ID": ["001", "002", "003", "004", "005", "006"],
            "Value": ["V1", "V2", "V3", "V4", "V5", "V6"],
        }
    )

    # With new_page=True, it currently works
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(orientation="portrait"),
        rtf_body=rtf.RTFBody(
            page_by=["Subject"],
            new_page=True,  # This makes it work
        ),
    )

    rtf_output = doc.rtf_encode()

    # This should have correct structure:
    # - Only 2 column headers (ID, Value)
    # - Spanning rows for S1 and S2

    # Verify NOT 3 columns
    lines = rtf_output.split("\n")
    header_cols = sum(
        1 for line in lines[:50] if "\\clvertalb" in line and "\\cellx" in line
    )

    # Should be 2 columns, not 3
    assert header_cols == 2, (
        f"Even with new_page=True, expected 2 columns but found {header_cols}"
    )


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING: page_by spanning row bug")
    print("=" * 80)

    try:
        test_page_by_should_create_spanning_rows_not_data_column()
        print("\n✓ TEST PASSED - Bug does not exist (spanning rows working correctly)")
    except AssertionError as e:
        print("\n✗ TEST FAILED - Bug confirmed!")
        print(f"\nError:\n{e}")

    print("\n" + "=" * 80)
    print("TESTING: page_by with new_page=True (should work)")
    print("=" * 80)

    try:
        test_page_by_correct_spanning_row_structure()
        print("\n✓ TEST PASSED - new_page=True creates correct structure")
    except AssertionError as e:
        print("\n✗ TEST FAILED")
        print(f"\nError:\n{e}")
