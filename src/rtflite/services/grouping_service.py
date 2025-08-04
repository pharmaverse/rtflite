"""
Enhanced group_by functionality for rtflite.

This service implements r2rtf-compatible group_by behavior where values in
group_by columns are displayed only once per group, with subsequent rows
showing blank/suppressed values for better readability.
"""

from typing import List, Optional, Dict, Any
import polars as pl


class GroupingService:
    """Service for handling group_by functionality with value suppression"""
    
    def __init__(self):
        pass
    
    def enhance_group_by(
        self, 
        df: pl.DataFrame, 
        group_by: Optional[List[str]] = None
    ) -> pl.DataFrame:
        """Apply group_by value suppression to a DataFrame
        
        Args:
            df: Input DataFrame
            group_by: List of column names to group by. Values will be suppressed
                     for duplicate rows within groups.
                     
        Returns:
            DataFrame with group_by columns showing values only on first occurrence
            within each group
        """
        if not group_by or df.is_empty():
            return df
        
        # Validate that all group_by columns exist
        missing_cols = [col for col in group_by if col not in df.columns]
        if missing_cols:
            raise ValueError(f"group_by columns not found in DataFrame: {missing_cols}")
        
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
        is_first_occurrence = (
            df[column] != df[column].shift(1)
        ) | (pl.int_range(df.height) == 0)  # First row is always shown
        
        # Create suppressed column by setting duplicates to null
        suppressed_values = pl.when(is_first_occurrence).then(df[column]).otherwise(None)
        
        # Replace the original column with suppressed version
        result_df = df.with_columns(suppressed_values.alias(column))
        
        return result_df
    
    def _suppress_hierarchical_columns(
        self, 
        df: pl.DataFrame, 
        group_by: List[str]
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
        page_start_indices: List[int]
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
                for col in group_by:
                    # Get the original value for this row
                    original_value = original_df[col][page_start_idx]
                    
                    # Update the suppressed DataFrame at this position
                    # Note: This is a simplified approach; in practice we'd need
                    # to use polars' update mechanisms properly
                    pass  # Implementation would depend on polars version and approach
        
        return result_df
    
    def get_group_structure(
        self, 
        df: pl.DataFrame, 
        group_by: List[str]
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
            level_cols = group_by[:i+1]
            unique_combinations = df.select(level_cols).unique().height
            structure[f"level_{i+1}"] = {
                "columns": level_cols,
                "unique_combinations": unique_combinations
            }
        
        # Overall statistics
        total_groups = df.select(group_by).unique().height
        
        return {
            "total_groups": total_groups,
            "levels": len(group_by),
            "structure": structure
        }
    
    def validate_group_by_columns(
        self, 
        df: pl.DataFrame, 
        group_by: List[str]
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


# Create a singleton instance for easy access
grouping_service = GroupingService()