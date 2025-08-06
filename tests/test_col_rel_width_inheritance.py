import polars as pl

from rtflite.encode import RTFDocument
from rtflite.input import RTFBody, RTFColumnHeader


def test_col_rel_width_inheritance_from_body():
    """Test that rtf_column_header inherits col_rel_width from rtf_body when not specified"""
    df = pl.DataFrame(
        {"Treatment": ["Placebo", "Drug A"], "N": [50, 48], "Response": ["75%", "92%"]}
    )

    # Custom column width ratios
    custom_widths = [3.0, 1.2, 0.8]

    # Create document with custom body col_rel_width but no explicit header col_rel_width
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(col_rel_width=custom_widths),
        # rtf_column_header not explicitly specified - should use default and inherit
    )

    # Verify inheritance occurred
    assert doc.rtf_column_header[0].col_rel_width == custom_widths
    assert doc.rtf_body.col_rel_width == custom_widths


def test_col_rel_width_no_inheritance_when_header_specified():
    """Test that rtf_column_header does NOT inherit when it has its own col_rel_width"""
    df = pl.DataFrame(
        {"Treatment": ["Placebo", "Drug A"], "N": [50, 48], "Response": ["75%", "92%"]}
    )

    body_widths = [3.0, 1.2, 0.8]
    header_widths = [2.0, 1.5, 1.0]

    # Create document with different widths for body and header
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(col_rel_width=body_widths),
        rtf_column_header=[RTFColumnHeader(col_rel_width=header_widths)],
    )

    # Verify no inheritance - each keeps its own values
    assert doc.rtf_column_header[0].col_rel_width == header_widths
    assert doc.rtf_body.col_rel_width == body_widths


def test_col_rel_width_inheritance_multiple_headers():
    """Test inheritance works with multiple column headers"""
    df = pl.DataFrame(
        {"Treatment": ["Placebo", "Drug A"], "N": [50, 48], "Response": ["75%", "92%"]}
    )

    custom_widths = [3.0, 1.2, 0.8]

    # Create document with multiple headers, none with explicit col_rel_width
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(col_rel_width=custom_widths),
        rtf_column_header=[RTFColumnHeader(), RTFColumnHeader()],
    )

    # Verify all headers inherited the width
    assert doc.rtf_column_header[0].col_rel_width == custom_widths
    assert doc.rtf_column_header[1].col_rel_width == custom_widths
    assert doc.rtf_body.col_rel_width == custom_widths


def test_col_rel_width_inheritance_partial():
    """Test inheritance works when some headers have widths and others don't"""
    df = pl.DataFrame(
        {"Treatment": ["Placebo", "Drug A"], "N": [50, 48], "Response": ["75%", "92%"]}
    )

    body_widths = [3.0, 1.2, 0.8]
    header1_widths = [2.0, 1.5, 1.0]

    # Create document with mixed header configurations
    doc = RTFDocument(
        df=df,
        rtf_body=RTFBody(col_rel_width=body_widths),
        rtf_column_header=[
            RTFColumnHeader(col_rel_width=header1_widths),  # Has its own
            RTFColumnHeader(),  # Should inherit
        ],
    )

    # Verify selective inheritance
    assert doc.rtf_column_header[0].col_rel_width == header1_widths  # Keeps its own
    assert doc.rtf_column_header[1].col_rel_width == body_widths  # Inherits
    assert doc.rtf_body.col_rel_width == body_widths


def test_col_rel_width_default_behavior_unchanged():
    """Test that default behavior is unchanged when no custom widths are specified"""
    df = pl.DataFrame(
        {"Treatment": ["Placebo", "Drug A"], "N": [50, 48], "Response": ["75%", "92%"]}
    )

    # Create document with no custom widths
    doc = RTFDocument(df=df)

    # Both should have default widths [1, 1, 1]
    expected_defaults = [1, 1, 1]  # One for each column
    assert doc.rtf_column_header[0].col_rel_width == expected_defaults
    assert doc.rtf_body.col_rel_width == expected_defaults
