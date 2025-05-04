import pandas as pd
import polars as pl
import pytest

from rtflite.input import BroadcastValue


def test_table_attributes_list():
    # List represent each column
    table = BroadcastValue(value=[1, 2, 3, 4], dimension=(3, 4))

    assert table.iloc(0, 0) == 1
    assert table.iloc(0, 1) == 2
    assert table.iloc(0, 4) == 1
    assert table.iloc(0, 5) == 2
    assert table.iloc(0, 6) == 3
    assert table.iloc(0, 7) == 4
    # Test to_dataframe
    df = table.to_dataframe()
    expected_df = pd.DataFrame([[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]])
    pd.testing.assert_frame_equal(df, expected_df)

    # Test with smaller dimensions for a list
    table_small = BroadcastValue(value=[1, 2, 3, 4], dimension=(2, 2))
    df_small = table_small.to_dataframe()
    expected_df_small = pd.DataFrame([[1, 2], [1, 2]])
    pd.testing.assert_frame_equal(df_small, expected_df_small)

    # Test with larger dimensions for a list
    table_large = BroadcastValue(value=[1, 2, 3, 4], dimension=(3, 6))
    df_large = table_large.to_dataframe()
    expected_df_large = pd.DataFrame(
        [[1, 2, 3, 4, 1, 2], [1, 2, 3, 4, 1, 2], [1, 2, 3, 4, 1, 2]]
    )
    pd.testing.assert_frame_equal(df_large, expected_df_large)


def test_table_attributes_tuple():
    # Dictionary representation
    table = BroadcastValue(value=("A", "B", "C"), dimension=(3, 3))

    assert table.iloc(0, 0) == "A"
    assert table.iloc(1, 0) == "B"
    assert table.iloc(2, 0) == "C"
    assert table.iloc(0, 3) == "A"
    assert table.iloc(1, 4) == "B"
    assert table.iloc(2, 5) == "C"
    # Test to_dataframe
    df = table.to_dataframe()
    expected_df = pd.DataFrame([["A", "A", "A"], ["B", "B", "B"], ["C", "C", "C"]])
    pd.testing.assert_frame_equal(df, expected_df)

    # Test with smaller dimensions for a tuple
    table_small = BroadcastValue(value=("A", "B", "C"), dimension=(2, 2))
    df_small = table_small.to_dataframe()
    expected_df_small = pd.DataFrame([["A", "A"], ["B", "B"]])
    pd.testing.assert_frame_equal(df_small, expected_df_small)

    # Test with larger dimensions for a tuple
    table_large = BroadcastValue(value=("A", "B", "C"), dimension=(6, 6))
    df_large = table_large.to_dataframe()
    expected_df_large = pd.DataFrame(
        [
            ["A", "A", "A", "A", "A", "A"],
            ["B", "B", "B", "B", "B", "B"],
            ["C", "C", "C", "C", "C", "C"],
            ["A", "A", "A", "A", "A", "A"],
            ["B", "B", "B", "B", "B", "B"],
            ["C", "C", "C", "C", "C", "C"],
        ]
    )
    pd.testing.assert_frame_equal(df_large, expected_df_large)


def test_table_attributes_string():
    # String representation
    table = BroadcastValue(value="Test String", dimension=(3, 3))

    assert table.iloc(0, 0) == "Test String"
    assert table.iloc(1, 3) == "Test String"
    assert table.iloc(2, 2) == "Test String"

    # Test to_dataframe
    df = table.to_dataframe()
    expected_df = pd.DataFrame(
        [
            ["Test String", "Test String", "Test String"],
            ["Test String", "Test String", "Test String"],
            ["Test String", "Test String", "Test String"],
        ]
    )
    pd.testing.assert_frame_equal(df, expected_df)


def test_table_attributes_dataframe():
    table = BroadcastValue(
        value=pd.DataFrame({"Column 1": [1, 2], "Column 2": [3, 4]}), dimension=(2, 2)
    )

    assert table.iloc(0, 0) == 1
    assert table.iloc(0, 1) == 3
    assert table.iloc(1, 0) == 2
    assert table.iloc(1, 1) == 4
    assert table.iloc(2, 0) == 1
    assert table.iloc(2, 1) == 3
    assert table.iloc(3, 0) == 2
    assert table.iloc(3, 1) == 4
    # Test to_dataframe
    df = table.to_dataframe()
    expected_df = pd.DataFrame({"Column 1": [1, 2], "Column 2": [3, 4]})
    pd.testing.assert_frame_equal(df, expected_df)
    # Test with smaller dimensions for a DataFrame
    table_small_df = BroadcastValue(
        value=pd.DataFrame([[1, 2, 3], [7, 8, 9]]), dimension=(2, 1)
    )
    df_small_df = table_small_df.to_dataframe()
    expected_df_small_df = pd.DataFrame([[1], [7]])
    pd.testing.assert_frame_equal(df_small_df, expected_df_small_df)

    # Test with larger dimensions for a DataFrame
    table_large_df = BroadcastValue(
        value=pd.DataFrame([["A", "B", "C"], ["D", "E", "F"]]), dimension=(6, 6)
    )
    df_large_df = table_large_df.to_dataframe()
    expected_df_large_df = pd.DataFrame(
        [
            ["A", "B", "C", "A", "B", "C"],
            ["D", "E", "F", "D", "E", "F"],
            ["A", "B", "C", "A", "B", "C"],
            ["D", "E", "F", "D", "E", "F"],
            ["A", "B", "C", "A", "B", "C"],
            ["D", "E", "F", "D", "E", "F"],
        ]
    )
    assert (df_large_df.to_numpy() == expected_df_large_df.to_numpy()).all()


def test_table_attributes_none():
    """Test handling of None values."""
    # Test with None value
    table = BroadcastValue(value=None, dimension=(2, 2))
    with pytest.raises(ValueError):
        df = table.to_dataframe()

    # Test with None in list
    table = BroadcastValue(value=[1, None, 3], dimension=(2, 3))
    df = table.to_dataframe()
    expected_df = pd.DataFrame([[1, None, 3], [1, None, 3]])
    assert (df.to_numpy() == expected_df.to_numpy()).all()


def test_table_attributes_invalid_dimensions():
    """Test handling of invalid dimensions."""
    # Test with negative dimensions
    with pytest.raises(ValueError):
        BroadcastValue(value=[1, 2, 3], dimension=(-1, 2))

    # # Test with zero dimensions
    with pytest.raises(ValueError):
        BroadcastValue(value=[1, 2, 3], dimension=(0, 2))

    # # Test with non-integer dimensions
    with pytest.raises(ValueError):
        BroadcastValue(value=[1, 2, 3], dimension=(2.5, 2))


def test_table_attributes_update():
    """Test updating table attributes."""
    table = BroadcastValue(value=[1, 2, 3], dimension=(2, 3))
    
    # Test updating value
    table.value = [4, 5, 6]
    df = table.to_dataframe()
    expected_df = pd.DataFrame([[4, 5, 6], [4, 5, 6]])
    assert (df.to_numpy() == expected_df.to_numpy()).all()
    
    # Test updating dimension
    table.dimension = (3, 2)
    df = table.to_dataframe()
    expected_df = pd.DataFrame([[4, 5], [4, 5], [4, 5]])
    assert (df.to_numpy() == expected_df.to_numpy()).all()


def test_table_attributes_edge_cases():
    """Test edge cases for table attributes."""
    # Test with single value
    table = BroadcastValue(value=[1], dimension=(1, 1))
    df = table.to_dataframe()
    expected_df = pd.DataFrame([[1]])
    assert (df.to_numpy() == expected_df.to_numpy()).all()
    
    # Test with very large dimensions
    table = BroadcastValue(value=["A"], dimension=(1000, 1000))
    assert table.iloc(999, 999) == "A"
