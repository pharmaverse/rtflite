import polars as pl
import pytest
import rtflite as rtf
import re

def test_page_by_column_alignment():
    """Test that column properties are correctly aligned when page_by is used."""
    df = pl.DataFrame({
        "section": ["-----", "Age", "Age"],
        "item": ["Participant in Population", "    <60", "    >=60"],
        "value": [55, 25, 30],
    })

    doc = rtf.RTFDocument(
        df=df,
        rtf_body=rtf.RTFBody(
            page_by="section",
            col_rel_width=[1],
            text_justification=["l", "l", "c"],
            border_top = ["single", "", ""],
            border_bottom = ["single", "", ""]
        ),
    )

    rtf_content = doc.rtf_encode()

    # We look for the row containing "55" (value column) and "Participant in Population"
    rows = rtf_content.split("\\row")
    row_with_55 = None
    for row in rows:
        if "55" in row and "Participant in Population" in row:
            row_with_55 = row
            break

    assert row_with_55 is not None, "Could not find the row with data"

    # Check alignment for "Participant in Population"
    idx_part = row_with_55.find("Participant in Population")
    pre_part = row_with_55[:idx_part]
    aligns_part = re.findall(r"\\q[lcrj]", pre_part)

    # Note: The table definition (\trowd...) also contains \trqc etc. but that's row alignment.
    # Cell content alignment is \ql, \qc etc. inside \pard.
    # Usually \pard resets, so we should see \ql inside the \pard block.
    # \trowd... contains \clvertalt etc. but not \ql/\qc usually (unless \clq...?)
    # The output shows: \pard\hyphpar0... \ql ... content.

    assert len(aligns_part) > 0, "No alignment found for Participant"
    last_align_part = aligns_part[-1]
    assert last_align_part == "\\ql", f"Expected \\ql for Participant, got {last_align_part}"

    # Check alignment for "55"
    idx_55 = row_with_55.find("55")
    pre_55 = row_with_55[:idx_55]
    aligns_55 = re.findall(r"\\q[lcrj]", pre_55)

    assert len(aligns_55) > 0, "No alignment found for 55"
    last_align_55 = aligns_55[-1]
    assert last_align_55 == "\\qc", f"Expected \\qc for 55, got {last_align_55}"
