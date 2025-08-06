import pytest

from rtflite.attributes import TextAttributes
from rtflite.input import RTFBody, RTFTitle


class TestLineCalculation:
    """Test cases for enhanced line calculation functionality"""

    def test_calculate_lines_basic_with_title(self):
        """Test basic line calculation with RTFTitle"""
        title = RTFTitle(text_font=[1], text_font_size=[12])

        # Text should fit in one line with wide available width
        lines = title.calculate_lines("Short text", available_width=5.0)
        assert lines == 1

        # Text should need multiple lines with narrow available width
        lines = title.calculate_lines(
            "This is a much longer text that will definitely need multiple lines",
            available_width=1.0,
        )
        assert lines > 1

    def test_calculate_lines_different_fonts(self):
        """Test line calculation with different fonts"""
        title1 = RTFTitle(text_font=[1], text_font_size=[12])  # Times New Roman
        title2 = RTFTitle(text_font=[2], text_font_size=[12])  # Arial

        lines1 = title1.calculate_lines("Sample text", available_width=2.0)
        lines2 = title2.calculate_lines("Sample text", available_width=2.0)

        # Both should return positive line counts
        assert lines1 >= 1
        assert lines2 >= 1

    def test_calculate_lines_different_sizes(self):
        """Test line calculation with different font sizes"""
        title_small = RTFTitle(text_font=[1], text_font_size=[8])
        title_large = RTFTitle(text_font=[1], text_font_size=[16])

        # Same text, same available width, different sizes
        lines_small = title_small.calculate_lines("Sample text", available_width=1.0)
        lines_large = title_large.calculate_lines("Sample text", available_width=1.0)

        # Larger font should need more lines (or at least same number)
        assert lines_large >= lines_small

    def test_calculate_lines_error_cases(self):
        """Test error handling for missing font attributes"""
        # Test with missing text_font
        attrs = TextAttributes()
        attrs.text_font = None
        attrs.text_font_size = [12]

        with pytest.raises(ValueError, match="text_font must be set"):
            attrs.calculate_lines("test", available_width=2.0)

        # Test with missing text_font_size
        attrs2 = TextAttributes()
        attrs2.text_font = [1]
        attrs2.text_font_size = None

        with pytest.raises(ValueError, match="text_font_size must be set"):
            attrs2.calculate_lines("test", available_width=2.0)

    def test_calculate_lines_edge_cases(self):
        """Test edge cases for line calculation"""
        title = RTFTitle(text_font=[1], text_font_size=[12])

        # Empty text should return 1 line
        lines = title.calculate_lines("", available_width=2.0)
        assert lines == 1

        # Zero or negative available width should return 1 line
        lines = title.calculate_lines("test", available_width=0)
        assert lines == 1

        lines = title.calculate_lines("test", available_width=-1.0)
        assert lines == 1

    def test_rtf_body_line_calculation_integration(self):
        """Test that RTFBody can use line calculation"""
        import polars as pl

        # Create sample data
        pl.DataFrame(
            {
                "col1": ["Short", "This is a much longer text that needs wrapping"],
                "col2": ["Text", "More content here"],
            }
        )

        body = RTFBody(text_font=[[1, 1]], text_font_size=[[12, 12]])

        # Test that we can calculate lines for specific cells
        lines1 = body.calculate_lines(
            "Short", available_width=2.0, row_idx=0, col_idx=0
        )
        lines2 = body.calculate_lines(
            "This is a much longer text that needs wrapping",
            available_width=2.0,
            row_idx=1,
            col_idx=0,
        )

        assert lines1 >= 1
        assert lines2 > lines1  # Longer text should need more lines

    def test_rtf_title_line_calculation(self):
        """Test line calculation with RTFTitle"""
        title = RTFTitle(text=["Sample Title"], text_font=[1], text_font_size=[14])

        # Calculate lines for title text
        lines_short = title.calculate_lines("Short Title", available_width=5.0)
        lines_long = title.calculate_lines(
            "This is a very long title that spans multiple lines", available_width=2.0
        )

        assert lines_short == 1
        assert lines_long > 1

    def test_calculate_lines_approximation_accuracy(self):
        """Test that line calculation approximation is reasonable"""
        from rtflite.strwidth import get_string_width

        title = RTFTitle(text_font=[1], text_font_size=[12])
        test_text = "Test text for approximation"

        # Get string width for comparison
        text_width = get_string_width(test_text, font=1, font_size=12)

        # Calculate lines with available width equal to text width
        lines_exact = title.calculate_lines(test_text, available_width=text_width)
        assert lines_exact == 1

        # Calculate lines with half the available width
        lines_half = title.calculate_lines(test_text, available_width=text_width / 2)
        assert lines_half == 2

        # Calculate lines with quarter available width
        lines_quarter = title.calculate_lines(test_text, available_width=text_width / 4)
        assert lines_quarter == 4

    def test_broadcast_value_integration(self):
        """Test line calculation with broadcast values for different positions"""
        # Create a TextAttributes object directly for testing broadcast values
        from rtflite.attributes import TextAttributes

        text_attrs = TextAttributes()
        text_attrs.text_font = [[1, 2], [1, 2]]
        text_attrs.text_font_size = [[12, 14], [12, 14]]

        # Test different positions use correct font attributes
        lines_pos1 = text_attrs.calculate_lines(
            "Sample text", available_width=2.0, row_idx=0, col_idx=0
        )
        lines_pos2 = text_attrs.calculate_lines(
            "Sample text", available_width=2.0, row_idx=0, col_idx=1
        )
        lines_pos3 = text_attrs.calculate_lines(
            "Sample text", available_width=2.0, row_idx=1, col_idx=0
        )
        lines_pos4 = text_attrs.calculate_lines(
            "Sample text", available_width=2.0, row_idx=1, col_idx=1
        )

        # All should return positive line counts
        assert all(
            lines >= 1 for lines in [lines_pos1, lines_pos2, lines_pos3, lines_pos4]
        )

    def test_enhanced_cell_nrow_calculation(self):
        """Test that enhanced cell_nrow calculation works with table data"""
        import polars as pl

        # Create sample data with varying text lengths
        df = pl.DataFrame(
            {
                "short": ["A", "B"],
                "long": ["This is long text", "Another long text entry"],
            }
        )

        body = RTFBody(text_font=[[1, 1]], text_font_size=[[12, 12]])

        # Set narrow column widths to force line wrapping
        col_widths = [0.5, 1.0]  # Very narrow columns

        # Test the _encode method which calculates cell_nrow
        try:
            rtf_output = body._encode(df, col_widths)
            # If no error is raised, the enhanced calculation worked
            assert isinstance(rtf_output, list)
        except Exception as e:
            pytest.fail(f"Enhanced cell_nrow calculation failed: {e}")
