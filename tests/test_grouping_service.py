"""Tests for GroupingService functionality.

Direct unit tests for the GroupingService to ensure proper coverage tracking.
"""

import polars as pl
import pytest

from rtflite.services.grouping_service import GroupingService


class TestGroupingService:
    """Test the GroupingService class directly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GroupingService()

    def test_enhance_group_by_single_column(self):
        """Test group_by with a single column."""
        df = pl.DataFrame(
            {"Group": ["A", "A", "A", "B", "B", "C"], "Value": [1, 2, 3, 4, 5, 6]}
        )

        result = self.service.enhance_group_by(df, ["Group"])

        # First occurrence kept, duplicates suppressed
        assert result["Group"][0] == "A"
        assert result["Group"][1] is None
        assert result["Group"][2] is None
        assert result["Group"][3] == "B"
        assert result["Group"][4] is None
        assert result["Group"][5] == "C"
        # Other columns unchanged
        assert result["Value"].to_list() == [1, 2, 3, 4, 5, 6]

    def test_enhance_group_by_multiple_columns(self):
        """Test hierarchical group_by with multiple columns."""
        df = pl.DataFrame(
            {
                "Level1": ["A", "A", "A", "B", "B"],
                "Level2": ["X", "X", "Y", "X", "X"],
                "Value": [1, 2, 3, 4, 5],
            }
        )

        result = self.service.enhance_group_by(df, ["Level1", "Level2"])

        # Hierarchical suppression
        assert result["Level1"][0] == "A"
        assert result["Level1"][1] is None  # Same Level1, same Level2
        assert result["Level1"][2] is None  # Same Level1, different Level2
        assert result["Level2"][0] == "X"
        assert result["Level2"][1] is None  # Duplicate suppressed
        assert result["Level2"][2] == "Y"  # New Level2 value
        assert result["Level1"][3] == "B"  # New Level1 value
        assert result["Level2"][3] == "X"  # Level2 shown for new Level1

    def test_enhance_group_by_with_nulls(self):
        """Test group_by handles null values correctly."""
        # Test with cleaner data where nulls don't interfere with group boundaries
        df = pl.DataFrame(
            {"Group": ["A", "A", "B", "B", None, None], "Value": [1, 2, 3, 4, 5, 6]}
        )

        result = self.service.enhance_group_by(df, ["Group"])

        # The service suppresses consecutive duplicates within groups
        assert result["Group"][0] == "A"
        assert result["Group"][1] is None  # Duplicate A suppressed
        assert result["Group"][2] == "B"  # New group B shown
        assert result["Group"][3] is None  # Duplicate B suppressed
        assert result["Group"][4] is None  # Null stays null
        assert result["Group"][5] is None  # Another null stays null

    def test_enhance_group_by_empty_dataframe(self):
        """Test group_by with empty DataFrame."""
        df = pl.DataFrame({"Group": [], "Value": []})

        result = self.service.enhance_group_by(df, ["Group"])

        assert len(result) == 0
        assert result.columns == ["Group", "Value"]

    def test_enhance_group_by_no_groups(self):
        """Test group_by with None or empty group list."""
        df = pl.DataFrame({"Group": ["A", "B", "C"], "Value": [1, 2, 3]})

        # No group_by specified
        result = self.service.enhance_group_by(df, None)
        assert result.equals(df)

        # Empty group list
        result = self.service.enhance_group_by(df, [])
        assert result.equals(df)

    def test_validate_data_sorting_properly_sorted(self):
        """Test validation passes for properly sorted data."""
        df = pl.DataFrame({"Group": ["A", "A", "B", "B"], "Value": [1, 2, 3, 4]})

        # Should not raise
        self.service.validate_data_sorting(df, group_by=["Group"])

    def test_validate_data_sorting_not_contiguous(self):
        """Test validation fails when groups are not contiguous."""
        df = pl.DataFrame(
            {
                "Group": ["A", "B", "A"],  # A appears twice with B in between
                "Value": [1, 2, 3],
            }
        )

        with pytest.raises(ValueError, match="not properly grouped"):
            self.service.validate_data_sorting(df, group_by=["Group"])

    def test_validate_data_sorting_missing_column(self):
        """Test validation fails for missing columns."""
        df = pl.DataFrame({"Group": ["A", "B"], "Value": [1, 2]})

        with pytest.raises(ValueError, match="not found in DataFrame"):
            self.service.validate_data_sorting(df, group_by=["NonExistent"])

    def test_validate_data_sorting_with_page_by(self):
        """Test validation with page_by columns."""
        df = pl.DataFrame(
            {
                "Page": ["P1", "P1", "P2", "P2"],
                "Group": ["A", "B", "A", "B"],
                "Value": [1, 2, 3, 4],
            }
        )

        # Should validate page_by takes precedence
        self.service.validate_data_sorting(df, group_by=["Group"], page_by=["Page"])

    def test_validate_data_sorting_overlapping_columns(self):
        """Test validation fails with overlapping grouping columns."""
        df = pl.DataFrame({"Col1": ["A", "B"], "Col2": ["X", "Y"], "Value": [1, 2]})

        with pytest.raises(ValueError, match="Overlapping variables found"):
            self.service.validate_data_sorting(
                df,
                group_by=["Col1"],
                page_by=["Col1"],  # Same column in both
            )

    def test_restore_page_context(self):
        """Test page context restoration at page boundaries."""
        original_df = pl.DataFrame(
            {
                "Group": ["A", "A", "A", "B", "B"],
                "Subgroup": ["X", "X", "Y", "X", "X"],
                "Value": [1, 2, 3, 4, 5],
            }
        )

        # Apply group_by transformation
        transformed_df = self.service.enhance_group_by(
            original_df, ["Group", "Subgroup"]
        )

        # Restore context at page boundaries (rows 2 and 4)
        page_start_indices = [2, 4]
        restored_df = self.service.restore_page_context(
            transformed_df, original_df, ["Group", "Subgroup"], page_start_indices
        )

        # Context should be restored at page starts
        assert restored_df["Group"][2] == "A"  # Restored
        assert restored_df["Subgroup"][2] == "Y"  # Different subgroup shown
        assert restored_df["Group"][4] == "B"  # Restored
        assert restored_df["Subgroup"][4] == "X"  # Restored

    def test_restore_page_context_empty_indices(self):
        """Test page context restoration with no page breaks."""
        df = pl.DataFrame({"Group": ["A", "A", "B"], "Value": [1, 2, 3]})

        transformed_df = self.service.enhance_group_by(df, ["Group"])

        # No page breaks
        restored_df = self.service.restore_page_context(
            transformed_df, df, ["Group"], []
        )

        # Should be unchanged from transformed
        assert restored_df.equals(transformed_df)

    def test_validate_no_overlapping_grouping_vars(self):
        """Test the overlapping validation method directly."""
        # Valid case - no overlaps
        self.service._validate_no_overlapping_grouping_vars(
            group_by=["A", "B"], page_by=["C", "D"], subline_by=["E"]
        )

        # Invalid - group_by and page_by overlap
        with pytest.raises(ValueError, match="Overlapping variables found"):
            self.service._validate_no_overlapping_grouping_vars(
                group_by=["A", "B"], page_by=["B", "C"], subline_by=None
            )

        # Invalid - all three overlap
        with pytest.raises(ValueError, match="Overlapping variables found"):
            self.service._validate_no_overlapping_grouping_vars(
                group_by=["A"], page_by=["A"], subline_by=["A"]
            )

    def test_complex_hierarchical_grouping(self):
        """Test complex hierarchical grouping scenario."""
        df = pl.DataFrame(
            {
                "Country": ["USA", "USA", "USA", "USA", "UK", "UK"],
                "State": ["CA", "CA", "NY", "NY", "ENG", "ENG"],
                "City": ["LA", "SF", "NYC", "BUF", "LON", "MAN"],
                "Sales": [100, 200, 300, 400, 500, 600],
            }
        )

        result = self.service.enhance_group_by(df, ["Country", "State", "City"])

        # Country level
        assert result["Country"][0] == "USA"
        assert all(result["Country"][i] is None for i in range(1, 4))
        assert result["Country"][4] == "UK"
        assert result["Country"][5] is None

        # State level
        assert result["State"][0] == "CA"
        assert result["State"][1] is None
        assert result["State"][2] == "NY"
        assert result["State"][3] is None
        assert result["State"][4] == "ENG"
        assert result["State"][5] is None

        # City level (never suppressed as it's unique)
        assert result["City"].to_list() == ["LA", "SF", "NYC", "BUF", "LON", "MAN"]
