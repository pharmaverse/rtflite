"""Test that font information is properly passed through pagination system."""

import polars as pl

from rtflite.input import RTFBody
from rtflite.pagination import PageBreakCalculator, RTFPagination


class TestPaginationFont:
    """Test font handling in pagination calculations."""

    def test_font_passed_to_string_width_calculation(self):
        """Test that font from RTFBody is used in content row calculations."""
        # Create test data with text that will wrap differently based on font
        df = pl.DataFrame(
            {
                "col1": [
                    "Short",
                    "This is a much, much, much, much, much, much, much, much, much, much longer piece of text that wraps differently with fonts",
                ],
                "col2": ["Val1", "Another value that demonstrates font differences"],
            }
        )

        # Create pagination configuration
        pagination = RTFPagination(
            page_width=8.5,
            page_height=11,
            margin=[1, 1, 1, 1, 0.5, 0.5],
            nrow=10,
            orientation="portrait",
        )

        calculator = PageBreakCalculator(pagination=pagination)

        # Test with Times New Roman (proportional font)
        body_times = RTFBody(
            text_font=[[1, 1]],  # Font 1: Times New Roman
            text_font_size=[[12, 12]],
            col_rel_width=[1, 1],
        )

        # Test with Courier New (monospace font)
        body_courier = RTFBody(
            text_font=[[9, 9]],  # Font 9: Courier New
            text_font_size=[[12, 12]],
            col_rel_width=[1, 1],
        )

        # Use narrow columns to force text wrapping
        col_widths = [1.5, 1.5]

        rows_times = calculator.calculate_content_rows(
            df, col_widths, body_times, font_size=12
        )

        rows_courier = calculator.calculate_content_rows(
            df, col_widths, body_courier, font_size=12
        )

        # Different fonts should produce different row calculations for long text
        assert rows_times != rows_courier, (
            "Different fonts should produce different row counts"
        )

        # Monospace font should generally need more rows for the same text
        assert rows_courier[1] >= rows_times[1], (
            "Courier New should need at least as many rows as Times New Roman"
        )

    def test_font_broadcast_in_mixed_table(self):
        """Test that different fonts in different cells are handled correctly."""
        df = pl.DataFrame(
            {
                "col1": ["Text in Times", "Text in Courier"],
                "col2": ["Text in Arial", "Text in Georgia"],
            }
        )

        pagination = RTFPagination(
            page_width=8.5,
            page_height=11,
            margin=[1, 1, 1, 1, 0.5, 0.5],
            nrow=10,
            orientation="portrait",
        )

        calculator = PageBreakCalculator(pagination=pagination)

        # Different font for each cell
        body_mixed = RTFBody(
            text_font=[[1, 4], [9, 7]],  # Times, Arial; Courier, Georgia
            text_font_size=[[12, 12], [12, 12]],
            col_rel_width=[1, 1],
        )

        col_widths = [2.0, 2.0]

        # Should complete without errors and use correct fonts for each cell
        rows = calculator.calculate_content_rows(
            df, col_widths, body_mixed, font_size=12
        )

        assert len(rows) == 2, "Should calculate rows for each data row"
        assert all(r >= 1 for r in rows), "Each row should need at least 1 line"

    def test_default_font_when_no_table_attrs(self):
        """Test that default font (1) is used when no table attributes provided."""
        df = pl.DataFrame({"col1": ["Text"], "col2": ["Value"]})

        pagination = RTFPagination(
            page_width=8.5,
            page_height=11,
            margin=[1, 1, 1, 1, 0.5, 0.5],
            nrow=10,
            orientation="portrait",
        )

        calculator = PageBreakCalculator(pagination=pagination)
        col_widths = [2.0, 2.0]

        # Call without table_attrs - should use default font 1
        rows = calculator.calculate_content_rows(df, col_widths, None, font_size=12)

        assert len(rows) == 1, "Should calculate rows"
        assert rows[0] >= 1, "Should need at least 1 line"

    def test_font_size_and_font_both_respected(self):
        """Test that both font and font size from table attrs are used."""
        df = pl.DataFrame(
            {"col1": ["Same text repeated"], "col2": ["Same text repeated"]}
        )

        pagination = RTFPagination(
            page_width=8.5,
            page_height=11,
            margin=[1, 1, 1, 1, 0.5, 0.5],
            nrow=10,
            orientation="portrait",
        )

        calculator = PageBreakCalculator(pagination=pagination)

        # Small font size with Times
        body_small = RTFBody(
            text_font=[[1, 1]], text_font_size=[[8, 8]], col_rel_width=[1, 1]
        )

        # Large font size with Times
        body_large = RTFBody(
            text_font=[[1, 1]], text_font_size=[[16, 16]], col_rel_width=[1, 1]
        )

        col_widths = [1.0, 1.0]  # Narrow columns

        rows_small = calculator.calculate_content_rows(
            df, col_widths, body_small, font_size=12
        )

        rows_large = calculator.calculate_content_rows(
            df, col_widths, body_large, font_size=12
        )

        # Larger font size should need more rows
        assert rows_large[0] > rows_small[0], (
            "Larger font size should need more rows for same text"
        )
