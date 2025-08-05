"""
Enhanced group_by functionality for rtflite.

This service implements r2rtf-compatible group_by behavior where values in
group_by columns are displayed only once per group, with subsequent rows
showing blank/suppressed values for better readability.
"""

from typing import Any, Dict, List, Optional

import polars as pl


class GroupingService:
    """Service for handling group_by functionality with value suppression"""

    def __init__(self):
        pass

    def enhance_group_by(
        self, df: pl.DataFrame, group_by: Optional[List[str]] = None
    ) -> pl.DataFrame:
        """Apply group_by value suppression to a DataFrame

        Args:
            df: Input DataFrame
            group_by: List of column names to group by. Values will be suppressed
                     for duplicate rows within groups.

        Returns:
            DataFrame with group_by columns showing values only on first occurrence
            within each group

        Raises:
            ValueError: If data is not properly sorted by group_by columns
        """
        if not group_by or df.is_empty():
            return df

        # Validate that all group_by columns exist
        missing_cols = [col for col in group_by if col not in df.columns]
        if missing_cols:
            raise ValueError(f"group_by columns not found in DataFrame: {missing_cols}")

        # Validate data sorting for group_by columns
        self.validate_data_sorting(df, group_by=group_by)

        # Create a copy to avoid modifying original
        result_df = df.clone()

        # Apply grouping logic based on number of group columns
        if len(group_by) == 1:
            result_df = self._suppress_single_column(result_df, group_by[0])
        else:
            result_df = self._suppress_hierarchical_columns(result_df, group_by)

        return result_df

    def _suppress_single_column(self, df: pl.DataFrame, column: str) -> pl.DataFrame:
        """Suppress duplicate values in a single group column

        Args:
            df: Input DataFrame
            column: Column name to suppress duplicates

        Returns:
            DataFrame with duplicate values replaced with null
        """
        # Create a mask for rows where the value is different from the previous row
        is_first_occurrence = (df[column] != df[column].shift(1)) | (
            pl.int_range(df.height) == 0
        )  # First row is always shown

        # Create suppressed column by setting duplicates to null
        suppressed_values = (
            pl.when(is_first_occurrence).then(df[column]).otherwise(None)
        )

        # Replace the original column with suppressed version
        result_df = df.with_columns(suppressed_values.alias(column))

        return result_df

    def _suppress_hierarchical_columns(
        self, df: pl.DataFrame, group_by: List[str]
    ) -> pl.DataFrame:
        """Suppress duplicate values in hierarchical group columns

        For multiple group columns, values are suppressed hierarchically:
        - First column: only shows when it changes
        - Second column: shows when first column changes OR when it changes
        - And so on...

        Args:
            df: Input DataFrame
            group_by: List of column names in hierarchical order

        Returns:
            DataFrame with hierarchical value suppression
        """
        result_df = df.clone()

        for i, column in enumerate(group_by):
            # For hierarchical grouping, a value should be shown if:
            # 1. It's the first row, OR
            # 2. Any of the higher-level group columns have changed, OR
            # 3. This column's value has changed

            conditions = []

            # First row condition
            conditions.append(pl.int_range(df.height) == 0)

            # Higher-level columns changed condition
            for higher_col in group_by[:i]:
                conditions.append(df[higher_col] != df[higher_col].shift(1))

            # This column changed condition
            conditions.append(df[column] != df[column].shift(1))

            # Combine all conditions with OR
            should_show = conditions[0]
            for condition in conditions[1:]:
                should_show = should_show | condition

            # Apply suppression
            suppressed_values = pl.when(should_show).then(df[column]).otherwise(None)
            result_df = result_df.with_columns(suppressed_values.alias(column))

        return result_df

    def restore_page_context(
        self,
        suppressed_df: pl.DataFrame,
        original_df: pl.DataFrame,
        group_by: List[str],
        page_start_indices: List[int],
    ) -> pl.DataFrame:
        """Restore group context at the beginning of new pages

        When content spans multiple pages, the first row of each new page
        should show the group values for context, even if they were suppressed
        in the continuous flow.

        Args:
            suppressed_df: DataFrame with group_by suppression applied
            original_df: Original DataFrame with all values
            group_by: List of group columns
            page_start_indices: List of row indices where new pages start

        Returns:
            DataFrame with group context restored at page boundaries
        """
        if not group_by or not page_start_indices:
            return suppressed_df

        result_df = suppressed_df.clone()

        # For each page start, restore the group values from original data
        for page_start_idx in page_start_indices:
            if page_start_idx < len(original_df):
                # Create updates for each group column
                for col in group_by:
                    # Get the original value for this row
                    original_value = original_df[col][page_start_idx]

                    # Update the result DataFrame at this position
                    # Create a mask for this specific row
                    mask = pl.int_range(len(result_df)) == page_start_idx

                    # Update the column value where the mask is true
                    result_df = result_df.with_columns(
                        pl.when(mask)
                        .then(pl.lit(original_value))
                        .otherwise(pl.col(col))
                        .alias(col)
                    )

        return result_df

    def get_group_structure(
        self, df: pl.DataFrame, group_by: List[str]
    ) -> Dict[str, Any]:
        """Analyze the group structure of a DataFrame

        Args:
            df: Input DataFrame
            group_by: List of group columns

        Returns:
            Dictionary with group structure information
        """
        if not group_by or df.is_empty():
            return {"groups": 0, "structure": {}}

        # Count unique combinations at each level
        structure = {}

        for i, col in enumerate(group_by):
            level_cols = group_by[: i + 1]
            unique_combinations = df.select(level_cols).unique().height
            structure[f"level_{i + 1}"] = {
                "columns": level_cols,
                "unique_combinations": unique_combinations,
            }

        # Overall statistics
        total_groups = df.select(group_by).unique().height

        return {
            "total_groups": total_groups,
            "levels": len(group_by),
            "structure": structure,
        }

    def validate_group_by_columns(
        self, df: pl.DataFrame, group_by: List[str]
    ) -> List[str]:
        """Validate group_by columns and return any issues

        Args:
            df: Input DataFrame
            group_by: List of group columns to validate

        Returns:
            List of validation issues (empty if all valid)
        """
        issues = []

        if not group_by:
            return issues

        # Check if columns exist
        missing_cols = [col for col in group_by if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")

        # Check for empty DataFrame
        if df.is_empty():
            issues.append("DataFrame is empty")

        # Check for columns with all null values
        for col in group_by:
            if col in df.columns:
                null_count = df[col].null_count()
                if null_count == df.height:
                    issues.append(f"Column '{col}' contains only null values")

        return issues

    def validate_data_sorting(
        self,
        df: pl.DataFrame,
        group_by: Optional[List[str]] = None,
        page_by: Optional[List[str]] = None,
        subline_by: Optional[List[str]] = None,
    ) -> None:
        """Validate that data is properly sorted for grouping operations

        Based on r2rtf logic: ensures data is sorted by all grouping variables
        in the correct order for proper group_by, page_by, and subline_by functionality.

        Args:
            df: Input DataFrame to validate
            group_by: List of group_by columns (optional)
            page_by: List of page_by columns (optional)
            subline_by: List of subline_by columns (optional)

        Raises:
            ValueError: If data is not properly sorted or if there are overlapping columns
        """
        if df.is_empty():
            return

        # Collect all grouping variables
        all_grouping_vars = []

        # Add variables in priority order (page_by, subline_by, group_by)
        if page_by:
            all_grouping_vars.extend(page_by)
        if subline_by:
            all_grouping_vars.extend(subline_by)
        if group_by:
            all_grouping_vars.extend(group_by)

        if not all_grouping_vars:
            return  # No grouping variables to validate

        # Check for overlapping variables between different grouping types
        self._validate_no_overlapping_grouping_vars(group_by, page_by, subline_by)

        # Remove duplicates while preserving order
        unique_vars = []
        seen = set()
        for var in all_grouping_vars:
            if var not in seen:
                unique_vars.append(var)
                seen.add(var)

        # Validate all grouping columns exist
        missing_cols = [col for col in unique_vars if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Grouping columns not found in DataFrame: {missing_cols}")

        # Check if groups are contiguous (values in same group are together)
        # This ensures proper grouping behavior without requiring alphabetical sorting

        # For each grouping variable, check if its groups are contiguous
        for i, var in enumerate(unique_vars):
            # Get the values for this variable and all previous variables
            group_cols = unique_vars[: i + 1]

            # Create a key for each row based on grouping columns up to this level
            if i == 0:
                # For the first variable, just check if its values are contiguous
                values = df[var].to_list()
                current_value = values[0]
                seen_values = {current_value}

                for j in range(1, len(values)):
                    if values[j] != current_value:
                        if values[j] in seen_values:
                            # Found a value that appeared before but with different values in between
                            raise ValueError(
                                f"Data is not properly grouped by '{var}'. "
                                f"Values with the same '{var}' must be contiguous (together). "
                                f"Found '{values[j]}' at position {j} but it also appeared earlier. "
                                f"Please reorder your data so that all rows with the same '{var}' are together."
                            )
                        current_value = values[j]
                        seen_values.add(current_value)
            else:
                # For subsequent variables, check contiguity within parent groups
                # Create a composite key from all grouping variables up to this level
                # Handle null values by first converting to string with null handling
                df_with_key = df.with_columns(
                    [
                        pl.col(col)
                        .cast(pl.Utf8)
                        .fill_null("__NULL__")
                        .alias(f"_str_{col}")
                        for col in group_cols
                    ]
                )

                # Create the group key from the string columns
                str_cols = [f"_str_{col}" for col in group_cols]
                df_with_key = df_with_key.with_columns(
                    pl.concat_str(str_cols, separator="|").alias("_group_key")
                )

                group_keys = df_with_key["_group_key"].to_list()
                current_key = group_keys[0]
                seen_keys = {current_key}

                for j in range(1, len(group_keys)):
                    if group_keys[j] != current_key:
                        if group_keys[j] in seen_keys:
                            # Found a group that appeared before
                            group_values = df.row(j, named=True)
                            key_parts = [
                                f"{col}='{group_values[col]}'" for col in group_cols
                            ]
                            key_desc = ", ".join(key_parts)

                            raise ValueError(
                                f"Data is not properly grouped. "
                                f"Group with {key_desc} appears in multiple non-contiguous sections. "
                                f"Please reorder your data so that rows with the same grouping values are together."
                            )
                        current_key = group_keys[j]
                        seen_keys.add(current_key)

    def validate_subline_formatting_consistency(
        self, df: pl.DataFrame, subline_by: List[str], rtf_body
    ) -> List[str]:
        """Validate that formatting is consistent within each column after broadcasting

        When using subline_by, we need to ensure that after broadcasting formatting
        attributes, each remaining column (after removing subline_by columns) has
        consistent formatting values. Otherwise, different rows within a subline
        group would have different formatting.

        Args:
            df: Input DataFrame
            subline_by: List of subline_by columns
            rtf_body: RTFBody instance with formatting attributes

        Returns:
            List of warning messages
        """
        warnings = []

        if not subline_by or df.is_empty():
            return warnings

        # Get the columns that will remain after removing subline_by columns
        remaining_cols = [col for col in df.columns if col not in subline_by]
        if not remaining_cols:
            return warnings

        num_cols = len(remaining_cols)
        num_rows = df.height

        # Format attributes to check
        format_attributes = [
            "text_format",
            "text_justification",
            "text_font_size",
            "text_color",
            "border_top",
            "border_bottom",
            "border_left",
            "border_right",
            "border_color_top",
            "border_color_bottom",
            "border_color_left",
            "border_color_right",
        ]

        for attr_name in format_attributes:
            if hasattr(rtf_body, attr_name):
                attr_value = getattr(rtf_body, attr_name)
                if attr_value is None:
                    continue

                # Use BroadcastValue to expand the attribute to full matrix
                from ..attributes import BroadcastValue

                try:
                    broadcast_obj = BroadcastValue(
                        value=attr_value, dimension=(num_rows, num_cols)
                    )
                    broadcasted = broadcast_obj.to_list()
                except:
                    # If broadcasting fails, skip this attribute
                    continue

                # Check each column for consistency
                for col_idx in range(num_cols):
                    # Get all values for this column
                    col_values = [
                        broadcasted[row_idx][col_idx] for row_idx in range(num_rows)
                    ]

                    # Filter out None and empty string values
                    meaningful_values = [v for v in col_values if v not in [None, ""]]
                    if not meaningful_values:
                        continue

                    # Check if all values in this column are the same
                    unique_values = set(meaningful_values)
                    if len(unique_values) > 1:
                        col_name = remaining_cols[col_idx]
                        warnings.append(
                            f"Column '{col_name}' has inconsistent {attr_name} values {list(unique_values)} "
                            f"after broadcasting. When using subline_by, formatting should be consistent "
                            f"within each column to ensure uniform appearance within subline groups."
                        )

        return warnings

    def _validate_no_overlapping_grouping_vars(
        self,
        group_by: Optional[List[str]] = None,
        page_by: Optional[List[str]] = None,
        subline_by: Optional[List[str]] = None,
    ) -> None:
        """Validate that grouping variables don't overlap between different types

        Based on r2rtf validation logic to prevent conflicts between
        group_by, page_by, and subline_by parameters.

        Args:
            group_by: List of group_by columns (optional)
            page_by: List of page_by columns (optional)
            subline_by: List of subline_by columns (optional)

        Raises:
            ValueError: If there are overlapping variables between grouping types
        """
        # Convert None to empty lists for easier processing
        group_by = group_by or []
        page_by = page_by or []
        subline_by = subline_by or []

        # Check for overlaps between each pair
        overlaps = []

        # group_by vs page_by
        group_page_overlap = set(group_by) & set(page_by)
        if group_page_overlap:
            overlaps.append(f"group_by and page_by: {sorted(group_page_overlap)}")

        # group_by vs subline_by
        group_subline_overlap = set(group_by) & set(subline_by)
        if group_subline_overlap:
            overlaps.append(f"group_by and subline_by: {sorted(group_subline_overlap)}")

        # page_by vs subline_by
        page_subline_overlap = set(page_by) & set(subline_by)
        if page_subline_overlap:
            overlaps.append(f"page_by and subline_by: {sorted(page_subline_overlap)}")

        if overlaps:
            overlap_details = "; ".join(overlaps)
            raise ValueError(
                f"Overlapping variables found between grouping parameters: {overlap_details}. "
                f"Each variable can only be used in one grouping parameter (group_by, page_by, or subline_by)."
            )


# Create a singleton instance for easy access
grouping_service = GroupingService()
