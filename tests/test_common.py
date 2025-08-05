"""Clean tests for BroadcastValue functionality without legacy pandas dependencies."""

import polars as pl
import pytest
from pydantic import ValidationError

from rtflite.attributes import BroadcastValue


def test_broadcast_value_list():
    """Test BroadcastValue with list input."""
    table = BroadcastValue(value=[[1]], dimension=(3, 3))

    # Test iloc access
    assert table.iloc(0, 0) == 1
    assert table.iloc(1, 1) == 1
    assert table.iloc(2, 2) == 1

    # Test to_list conversion
    result = table.to_list()
    expected = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    assert result == expected


def test_broadcast_value_tuple():
    """Test BroadcastValue with tuple input."""
    table = BroadcastValue(value=("A", "B", "C"), dimension=(3, 3))

    # Test iloc access
    assert table.iloc(0, 0) == "A"
    assert table.iloc(1, 0) == "B"
    assert table.iloc(2, 0) == "C"

    # Test to_list conversion
    result = table.to_list()
    expected = [["A", "A", "A"], ["B", "B", "B"], ["C", "C", "C"]]
    assert result == expected


def test_broadcast_value_string():
    """Test BroadcastValue with string input."""
    table = BroadcastValue(value="Test String", dimension=(3, 3))

    # Test iloc access
    assert table.iloc(0, 0) == "Test String"
    assert table.iloc(1, 1) == "Test String"
    assert table.iloc(2, 2) == "Test String"

    # Test to_list conversion
    result = table.to_list()
    expected = [
        ["Test String", "Test String", "Test String"],
        ["Test String", "Test String", "Test String"],
        ["Test String", "Test String", "Test String"],
    ]
    assert result == expected


def test_broadcast_value_dataframe():
    """Test BroadcastValue with DataFrame input."""
    df = pl.DataFrame({"Column 1": [1, 2], "Column 2": [3, 4]})
    table = BroadcastValue(value=df, dimension=(2, 2))

    # Test iloc access
    assert table.iloc(0, 0) == 1
    assert table.iloc(0, 1) == 3
    assert table.iloc(1, 0) == 2
    assert table.iloc(1, 1) == 4

    # Test to_list conversion
    result = table.to_list()
    expected = [[1, 3], [2, 4]]
    assert result == expected


def test_broadcast_value_none():
    """Test BroadcastValue with None input."""
    table = BroadcastValue(value=None, dimension=(2, 2))

    # Test to_list conversion
    result = table.to_list()
    assert result is None


def test_broadcast_value_invalid_dimensions():
    """Test BroadcastValue with invalid dimensions."""
    with pytest.raises((TypeError, ValueError, ValidationError)):
        BroadcastValue(value=[[1]], dimension=(2,))  # Wrong tuple length

    with pytest.raises((TypeError, ValueError, ValidationError)):
        BroadcastValue(value=[[1]], dimension=("invalid", 2))  # Non-integer


def test_broadcast_value_update():
    """Test BroadcastValue update functionality."""
    table = BroadcastValue(value=[[1]], dimension=(2, 2))

    # Update a cell
    table.update_cell(0, 1, 99)

    # Test updated value
    assert table.iloc(0, 1) == 99
    assert table.iloc(0, 0) == 1  # Other values unchanged


def test_broadcast_value_edge_cases():
    """Test BroadcastValue edge cases."""
    # Single value broadcast to single dimension
    table = BroadcastValue(value=[[42]], dimension=(1, 1))
    result = table.to_list()
    expected = [[42]]
    assert result == expected

    # Test with single row, multiple columns
    table_single_row = BroadcastValue(value=[["A", "B"]], dimension=(1, 2))
    result_single_row = table_single_row.to_list()
    expected_single_row = [["A", "B"]]
    assert result_single_row == expected_single_row
