import polars as pl

from rtflite import RTFBody, RTFDocument, RTFPageFooter, RTFPageHeader


class TestPageHeadersFooters:
    """Test cases for RTF page headers and footers functionality"""

    def test_page_header_default(self):
        """Test page header with default values"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(df=df, rtf_body=RTFBody(), rtf_page_header=RTFPageHeader())

        rtf_output = doc.rtf_encode()

        # Check that header is included with default text
        assert "\\header" in rtf_output
        assert "chpgn" in rtf_output  # r2rtf-style page number field
        assert "NUMPAGES" in rtf_output  # r2rtf-style total pages field
        assert "\\qr" in rtf_output  # Right alignment (default)
        assert "\\fs24" in rtf_output  # r2rtf default font size (12pt)

    def test_page_footer_basic(self):
        """Test page footer with custom text"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_page_footer=RTFPageFooter(text=["Custom Footer Text"]),
        )

        rtf_output = doc.rtf_encode()

        # Check that footer is included
        assert "\\footer" in rtf_output
        assert "Custom Footer Text" in rtf_output
        assert "\\qc" in rtf_output  # Center alignment (default for footer)

    def test_both_header_and_footer(self):
        """Test document with both header and footer"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_page_header=RTFPageHeader(text=["Study Report"]),
            rtf_page_footer=RTFPageFooter(text=["Confidential"]),
        )

        rtf_output = doc.rtf_encode()

        # Check that both header and footer are included
        assert "\\header" in rtf_output
        assert "\\footer" in rtf_output
        assert "Study Report" in rtf_output
        assert "Confidential" in rtf_output

    def test_custom_formatting(self):
        """Test custom formatting for headers and footers"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_page_header=RTFPageHeader(
                text=["Header Text"],
                text_font_size=[12],  # 12pt
                text_justification=["c"],  # Center aligned
            ),
            rtf_page_footer=RTFPageFooter(
                text=["Footer Text"],
                text_font_size=[8],  # 8pt
                text_justification=["l"],  # Left aligned
            ),
        )

        rtf_output = doc.rtf_encode()

        # Check custom formatting is applied
        assert "Header Text" in rtf_output
        assert "Footer Text" in rtf_output

        # Check for custom font sizes (RTF uses half-points, so 12pt = 24, 8pt = 16)
        assert "\\fs24" in rtf_output  # Header 12pt
        assert "\\fs16" in rtf_output  # Footer 8pt

    def test_multiline_header_footer(self):
        """Test multi-line headers and footers"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_page_header=RTFPageHeader(
                text=["Line 1 of Header", "Line 2 of Header"]
            ),
            rtf_page_footer=RTFPageFooter(
                text=["Line 1 of Footer", "Line 2 of Footer"]
            ),
        )

        rtf_output = doc.rtf_encode()

        # Check that multiline text is handled
        assert "Line 1 of Header" in rtf_output
        assert "Line 2 of Header" in rtf_output
        assert "Line 1 of Footer" in rtf_output
        assert "Line 2 of Footer" in rtf_output

    def test_no_header_footer(self):
        """Test document without headers or footers"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(df=df, rtf_body=RTFBody())

        rtf_output = doc.rtf_encode()

        # Check that no header or footer content blocks are included
        # Note: \headery and \footery are margin settings, not content
        assert "{\\header" not in rtf_output
        assert "{\\footer" not in rtf_output

    def test_empty_footer_text(self):
        """Test footer with empty/None text should not be included"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        doc = RTFDocument(
            df=df, rtf_body=RTFBody(), rtf_page_footer=RTFPageFooter(text=None)
        )

        rtf_output = doc.rtf_encode()

        # Footer with no text should not be included
        assert "{\\footer" not in rtf_output

    def test_page_header_text_validation(self):
        """Test text validation for page headers"""
        # String should be converted to list then tuple (internal processing)
        header = RTFPageHeader(text="Single string header")
        assert header.text == ("Single string header",)

        # List should be converted to tuple (internal processing)
        header = RTFPageHeader(text=["List", "header"])
        assert header.text == ("List", "header")

    def test_rtf_field_codes(self):
        """Test that RTF field codes are preserved"""
        df = pl.DataFrame(
            {"Column1": ["Data 1.1", "Data 2.1"], "Column2": ["Data 1.2", "Data 2.2"]}
        )

        # Test various RTF field codes
        doc = RTFDocument(
            df=df,
            rtf_body=RTFBody(),
            rtf_page_header=RTFPageHeader(
                text=["Page \\pagenumber of \\pagefield - \\date"]
            ),
        )

        rtf_output = doc.rtf_encode()

        # Check that field codes are preserved (conversion not yet implemented)
        assert "pagenumber" in rtf_output  # Custom field codes should still work
        assert "pagefield" in rtf_output
        assert "date" in rtf_output
