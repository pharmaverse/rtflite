import polars as pl

from rtflite import RTFBody, RTFDocument, RTFPage
from rtflite.encoding.unified_encoder import UnifiedRTFEncoder


def test_multi_section_encoding_success():
    """
    Test that multi-section encoding works correctly without hanging or crashing.
    This regression test ensures that the fix for the 'list object has no attribute
    subline_by' error (caused by incorrect temp_document creation) is working.
    """
    # Create simple dataframes
    df1 = pl.DataFrame({"col1": ["A", "B"], "col2": [1, 2]})
    df2 = pl.DataFrame({"col1": ["C", "D"], "col2": [3, 4]})

    # Create document components
    page = RTFPage(width=8.5, height=11, margin=(1, 1, 1, 1, 0.5, 0.5))
    body = RTFBody()

    # Create multi-section document
    doc = RTFDocument(
        df=[df1, df2],
        rtf_page=page,
        rtf_body=[body, body],  # Reuse body for simplicity
        rtf_column_header=[],  # Empty list to avoid validation errors
    )

    encoder = UnifiedRTFEncoder()

    # This should not raise an exception or hang
    rtf = encoder.encode(doc)

    assert isinstance(rtf, str)
    assert len(rtf) > 0
    assert "{\\rtf1" in rtf
    # Basic check that content from both sections is present
    assert "A" in rtf
    assert "C" in rtf
