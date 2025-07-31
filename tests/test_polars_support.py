"""Test cases for polars DataFrame support in rtflite."""

import pandas as pd
import polars as pl

from rtflite import (
    RTFDocument,
    RTFTitle,
    RTFColumnHeader,
    RTFBody,
    RTFPageHeader,
    RTFPageFooter,
)
from rtflite.input import RTFSubline


class TestPolarsDataFrameSupport:
    """Test suite for polars DataFrame support."""

    def test_rtf_document_with_polars_dataframe(self):
        """Test RTFDocument accepts polars DataFrame."""
        # Create a polars DataFrame
        df_polars = pl.DataFrame(
            {
                "Name": ["Alice", "Bob", "Charlie"],
                "Age": [25, 30, 35],
                "City": ["New York", "London", "Paris"],
            }
        )

        # Create RTFDocument with polars DataFrame
        doc = RTFDocument(
            df=df_polars, rtf_title=RTFTitle(text=["Test Report with Polars"])
        )

        # Verify the document was created successfully
        assert doc is not None
        # The internal df should be converted to pandas
        assert isinstance(doc.df, pd.DataFrame)
        assert doc.df.shape == (3, 3)
        assert list(doc.df.columns) == ["Name", "Age", "City"]

    def test_rtf_column_header_with_polars_dataframe(self):
        """Test RTFColumnHeader accepts polars DataFrame."""
        # Create polars DataFrame for header
        header_polars = pl.DataFrame([["Column 1", "Column 2", "Column 3", "Total"]])

        # Create RTFColumnHeader with polars DataFrame
        header = RTFColumnHeader(df=header_polars, col_rel_width=[2, 2, 2, 1])

        # Verify the header was created successfully
        assert header is not None
        assert header.text is not None
        # The text field should contain a pandas DataFrame
        assert isinstance(header.text, pd.DataFrame)

    def test_rtf_document_with_complex_polars_data(self):
        """Test RTFDocument with more complex polars DataFrame."""
        # Create a more complex polars DataFrame
        df_polars = pl.DataFrame(
            {
                "Department": ["Sales", "Sales", "IT", "IT", "HR"],
                "Employee": ["John", "Jane", "Bob", "Alice", "Charlie"],
                "Salary": [50000, 55000, 60000, 65000, 45000],
                "Bonus": [5000, 5500, 6000, 6500, 4500],
                "Total": [55000, 60500, 66000, 71500, 49500],
            }
        )

        # Create RTFDocument with various components
        doc = RTFDocument(
            df=df_polars,
            rtf_title=RTFTitle(text=["Employee Compensation Report", "2024"]),
            rtf_page_header=RTFPageHeader(text=["Confidential"]),
            rtf_body=RTFBody(
                col_rel_width=[2, 2, 1.5, 1.5, 1.5],
                text_justification=["l", "l", "r", "r", "r"],
            ),
        )

        # Verify document creation
        assert doc is not None
        assert isinstance(doc.df, pd.DataFrame)
        assert doc.df.shape == (5, 5)

        # Test RTF encoding
        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0
        assert rtf_output.startswith("{\\rtf1")

    def test_multiple_column_headers_with_polars(self):
        """Test multiple RTFColumnHeaders with polars DataFrames."""
        # Create headers as polars DataFrames
        header1_polars = pl.DataFrame([["", "Q1", "Q2", "Q3", "Q4", "Total"]])
        header2_polars = pl.DataFrame(
            [["Product", "Sales", "Sales", "Sales", "Sales", "Annual"]]
        )

        # Create data as polars DataFrame
        data_polars = pl.DataFrame(
            {
                "Product": ["Product A", "Product B", "Product C"],
                "Q1": [100, 200, 150],
                "Q2": [120, 180, 160],
                "Q3": [130, 220, 140],
                "Q4": [140, 210, 170],
                "Total": [490, 810, 620],
            }
        )

        # Create RTFDocument with multiple headers
        doc = RTFDocument(
            df=data_polars,
            rtf_column_header=[
                RTFColumnHeader(df=header1_polars, col_rel_width=[2] + [1] * 5),
                RTFColumnHeader(df=header2_polars, col_rel_width=[2] + [1] * 5),
            ],
        )

        # Verify document creation
        assert doc is not None
        assert len(doc.rtf_column_header) == 2
        assert isinstance(doc.df, pd.DataFrame)

    def test_polars_dataframe_with_nulls(self):
        """Test handling of null values in polars DataFrame."""
        # Create polars DataFrame with null values
        df_polars = pl.DataFrame(
            {
                "Name": ["Alice", "Bob", None, "David"],
                "Score": [95, None, 87, 92],
                "Grade": ["A", "B", "B", None],
            }
        )

        # Create RTFDocument
        doc = RTFDocument(df=df_polars, rtf_title=RTFTitle(text=["Test Scores"]))

        # Verify null handling
        assert doc is not None
        assert isinstance(doc.df, pd.DataFrame)
        # Check that nulls are preserved
        assert doc.df.isna().sum().sum() == 3  # Total of 3 null values

    def test_polars_dataframe_type_preservation(self):
        """Test that data types are preserved when converting from polars."""
        # Create polars DataFrame with various types
        df_polars = pl.DataFrame(
            {
                "Integer": [1, 2, 3],
                "Float": [1.1, 2.2, 3.3],
                "String": ["a", "b", "c"],
                "Boolean": [True, False, True],
            }
        )

        # Create RTFDocument
        doc = RTFDocument(df=df_polars)

        # Verify type preservation
        assert doc.df["Integer"].dtype.kind == "i"  # integer
        assert doc.df["Float"].dtype.kind == "f"  # float
        assert doc.df["String"].dtype.kind == "O"  # object (string)
        assert doc.df["Boolean"].dtype.kind == "b"  # boolean

    def test_polars_dataframe_with_basic_rtf_components(self):
        """Test polars DataFrame with basic RTF components (excluding footnote/source due to existing bug)."""
        # Create sample data
        df_polars = pl.DataFrame(
            {
                "Metric": ["Revenue", "Expenses", "Profit"],
                "Value": [100000, 75000, 25000],
                "Percentage": ["100%", "75%", "25%"],
            }
        )

        # Create document with basic components (no footnote/source due to existing bug)
        doc = RTFDocument(
            df=df_polars,
            rtf_title=RTFTitle(text=["Financial Summary", "Q4 2024"]),
            rtf_subline=RTFSubline(text=["Preliminary Results"]),
            rtf_page_header=RTFPageHeader(text=["Confidential Report"]),
            rtf_page_footer=RTFPageFooter(text=["Page 1 of 1"]),
        )

        # Verify all components
        assert doc is not None
        assert isinstance(doc.df, pd.DataFrame)
        assert doc.rtf_title is not None
        assert doc.rtf_subline is not None
        assert doc.rtf_page_header is not None
        assert doc.rtf_page_footer is not None

        # Test RTF output
        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0
        assert rtf_output.startswith("{\\rtf1")

        # Test write functionality
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".rtf", delete=False) as tmp:
            doc.write_rtf(tmp.name)
            # Verify file was created
            import os

            assert os.path.exists(tmp.name)
            assert os.path.getsize(tmp.name) > 0
            os.unlink(tmp.name)

    def test_polars_to_pandas_conversion_equivalence(self):
        """Test that polars and pandas DataFrames produce equivalent results."""
        # Create identical data in both formats
        data = {"A": [1, 2, 3], "B": ["x", "y", "z"], "C": [10.5, 20.5, 30.5]}

        df_pandas = pd.DataFrame(data)
        df_polars = pl.DataFrame(data)

        # Create RTFDocuments with each
        doc_pandas = RTFDocument(df=df_pandas, rtf_title=RTFTitle(text=["Test"]))

        doc_polars = RTFDocument(df=df_polars, rtf_title=RTFTitle(text=["Test"]))

        # Compare the internal DataFrames
        pd.testing.assert_frame_equal(doc_pandas.df, doc_polars.df)

        # Compare RTF output
        rtf_pandas = doc_pandas.rtf_encode()
        rtf_polars = doc_polars.rtf_encode()

        # The RTF output should be identical
        assert rtf_pandas == rtf_polars
        assert isinstance(rtf_pandas, str)
        assert isinstance(rtf_polars, str)


class TestPolarsEdgeCases:
    """Test edge cases for polars DataFrame support."""

    def test_empty_polars_dataframe(self):
        """Test handling of empty polars DataFrame."""
        # Create empty DataFrame with columns but no data
        df_empty = pl.DataFrame({"A": [], "B": []})

        # Create document - should work with empty data
        doc = RTFDocument(df=df_empty)
        assert doc is not None
        assert doc.df.shape == (0, 2)

    def test_single_row_polars_dataframe(self):
        """Test polars DataFrame with single row."""
        df_single = pl.DataFrame({"A": [1], "B": ["test"]})

        doc = RTFDocument(df=df_single)
        assert doc is not None
        assert doc.df.shape == (1, 2)

    def test_single_column_polars_dataframe(self):
        """Test polars DataFrame with single column."""
        df_single_col = pl.DataFrame({"Values": [1, 2, 3, 4, 5]})

        doc = RTFDocument(df=df_single_col)
        assert doc is not None
        assert doc.df.shape == (5, 1)

    def test_large_polars_dataframe(self):
        """Test handling of larger polars DataFrame."""
        # Create a larger DataFrame
        n_rows = 1000
        df_large = pl.DataFrame(
            {
                "ID": range(n_rows),
                "Value": [i * 2 for i in range(n_rows)],
                "Category": ["A" if i % 2 == 0 else "B" for i in range(n_rows)],
            }
        )

        doc = RTFDocument(
            df=df_large,
            rtf_title=RTFTitle(text=["Large Dataset Report"]),
            rtf_body=RTFBody(col_rel_width=[1, 2, 1]),
        )

        assert doc is not None
        assert doc.df.shape == (n_rows, 3)

        # Test RTF encoding works with large dataset
        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0
        assert rtf_output.startswith("{\\rtf1")
