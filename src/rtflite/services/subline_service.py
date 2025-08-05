"""
Service for handling subline_by functionality in rtflite.

The subline_by feature creates subheader rows in the table to group related data.
When subline_by columns are specified, unique combinations of values from these
columns are used to create visually distinct subheader rows that span the entire
table width, providing clear visual separation between groups.
"""

from typing import List, Optional, Dict, Any, Tuple
import polars as pl


class SublineService:
    """Service for handling subline_by functionality with subheader generation"""
    
    def __init__(self):
        pass
    
    def process_subline_by(
        self,
        df: pl.DataFrame,
        subline_by: Optional[List[str]] = None,
        col_widths: Optional[List[float]] = None,
        text_format: Optional[str] = None,
        text_justification: Optional[str] = None,
        text_font_size: Optional[float] = None,
        text_color: Optional[str] = None,
        border_top: Optional[str] = None,
        border_bottom: Optional[str] = None,
    ) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
        """Process DataFrame with subline_by to generate subheader rows
        
        Args:
            df: Input DataFrame
            subline_by: List of column names to create sublines by
            col_widths: Column widths for the table
            text_format: Format for subheader text (e.g., 'b' for bold)
            text_justification: Justification for subheader text ('l', 'c', 'r')
            text_font_size: Font size for subheader text
            text_color: Color for subheader text
            border_top: Top border style for subheader rows
            border_bottom: Bottom border style for subheader rows
            
        Returns:
            Tuple of:
            - Modified DataFrame with subline_by columns removed
            - List of subheader definitions with row indices
        """
        if not subline_by or df.is_empty():
            return df, []
        
        # Validate subline_by columns exist
        missing_cols = [col for col in subline_by if col not in df.columns]
        if missing_cols:
            raise ValueError(f"subline_by columns not found in DataFrame: {missing_cols}")
        
        # Get unique combinations of subline_by values
        subline_groups = df.select(subline_by).unique().sort(subline_by)
        
        # Create subheader definitions
        subheaders = []
        
        # Process each group
        for group_idx, group_row in enumerate(subline_groups.iter_rows()):
            # Create filter condition for this group
            conditions = []
            for col_idx, col_name in enumerate(subline_by):
                conditions.append(pl.col(col_name) == group_row[col_idx])
            
            # Combine conditions
            filter_condition = conditions[0]
            for condition in conditions[1:]:
                filter_condition = filter_condition & condition
            
            # Find rows belonging to this group
            group_mask = df.select(filter_condition).to_series(0)
            group_indices = [i for i, val in enumerate(group_mask) if val]
            
            if group_indices:
                # Create subheader text from subline_by values
                subheader_text = self._create_subheader_text(subline_by, group_row)
                
                # Create subheader definition
                subheader = {
                    'insert_before_row': group_indices[0],  # Insert before first row of group
                    'text': subheader_text,
                    'text_format': text_format or 'b',  # Default to bold
                    'text_justification': text_justification or 'l',  # Default to left
                    'text_font_size': text_font_size,
                    'text_color': text_color,
                    'border_top': border_top or 'single',
                    'border_bottom': border_bottom or 'single',
                    'span_all_columns': True,  # Subheader spans all columns
                    'group_values': dict(zip(subline_by, group_row)),
                    'group_indices': group_indices,
                }
                subheaders.append(subheader)
        
        # Remove subline_by columns from DataFrame as they're now in subheaders
        result_df = df.drop(subline_by)
        
        return result_df, subheaders
    
    def _create_subheader_text(
        self, 
        column_names: List[str], 
        values: Tuple[Any, ...]
    ) -> str:
        """Create formatted subheader text from column names and values
        
        Args:
            column_names: List of column names
            values: Tuple of corresponding values
            
        Returns:
            Formatted subheader text
        """
        # Create key-value pairs
        parts = []
        for col_name, value in zip(column_names, values):
            # Convert column name to title case and add value
            formatted_name = col_name.replace('_', ' ').title()
            parts.append(f"{formatted_name}: {value}")
        
        # Join with comma and space
        return ", ".join(parts)
    
    def integrate_subheaders_with_data(
        self,
        df: pl.DataFrame,
        subheaders: List[Dict[str, Any]],
        num_columns: int
    ) -> pl.DataFrame:
        """Integrate subheader rows into the DataFrame for rendering
        
        This method is used when the rendering engine needs subheaders
        as actual rows in the DataFrame rather than separate metadata.
        
        Args:
            df: DataFrame without subline_by columns
            subheaders: List of subheader definitions
            num_columns: Number of columns in the table
            
        Returns:
            DataFrame with subheader rows inserted
        """
        if not subheaders:
            return df
        
        # Convert to list of rows for easier manipulation
        rows = df.to_dicts()
        
        # Sort subheaders by insertion position (reverse order for correct insertion)
        sorted_subheaders = sorted(subheaders, key=lambda x: x['insert_before_row'], reverse=True)
        
        # Track row offset due to insertions
        offset = 0
        
        # Insert subheader rows
        for subheader in sorted_subheaders:
            insert_pos = subheader['insert_before_row'] + offset
            
            # Create subheader row
            subheader_row = {}
            
            # For subheader rows, we typically put the text in the first column
            # and leave other columns empty (they will be merged/spanned)
            column_names = df.columns
            if column_names:
                subheader_row[column_names[0]] = subheader['text']
                for col in column_names[1:]:
                    subheader_row[col] = None
            
            # Mark this as a subheader row with special metadata
            subheader_row['_is_subheader'] = True
            subheader_row['_subheader_metadata'] = subheader
            
            # Insert the subheader row
            rows.insert(insert_pos, subheader_row)
            offset += 1
        
        # Convert back to DataFrame
        result_df = pl.DataFrame(rows)
        
        return result_df
    
    def validate_subline_by_with_pagination(
        self,
        subline_by: Optional[List[str]],
        page_by: Optional[List[str]],
        subheaders: List[Dict[str, Any]],
        page_breaks: List[int]
    ) -> List[Dict[str, Any]]:
        """Validate and adjust subheaders for pagination
        
        When subline_by is used with pagination, ensure subheaders
        are repeated at the start of new pages when a group spans pages.
        
        Args:
            subline_by: List of subline_by columns
            page_by: List of page_by columns (if any)
            subheaders: List of subheader definitions
            page_breaks: List of row indices where pages break
            
        Returns:
            Updated list of subheader definitions with pagination adjustments
        """
        if not subline_by or not page_breaks:
            return subheaders
        
        additional_subheaders = []
        
        for subheader in subheaders:
            group_indices = subheader['group_indices']
            
            # Check if this group spans multiple pages
            for page_break in page_breaks:
                # Find indices in this group that appear after the page break
                indices_after_break = [idx for idx in group_indices if idx >= page_break]
                
                if indices_after_break:
                    # First index of group on the new page
                    first_on_new_page = min(indices_after_break)
                    
                    # Only add if it's not already the start of the group
                    if first_on_new_page != subheader['insert_before_row']:
                        # Create a duplicate subheader for the new page
                        new_subheader = subheader.copy()
                        new_subheader['insert_before_row'] = first_on_new_page
                        new_subheader['is_continuation'] = True
                        additional_subheaders.append(new_subheader)
        
        # Combine original and additional subheaders
        all_subheaders = subheaders + additional_subheaders
        
        # Sort by insertion position
        all_subheaders.sort(key=lambda x: x['insert_before_row'])
        
        return all_subheaders
    
    def get_subline_metadata(
        self,
        df: pl.DataFrame,
        subline_by: List[str]
    ) -> Dict[str, Any]:
        """Get metadata about subline groups for reporting
        
        Args:
            df: Input DataFrame
            subline_by: List of subline_by columns
            
        Returns:
            Dictionary with subline metadata
        """
        if not subline_by:
            return {"groups": 0, "columns": []}
        
        # Get unique groups
        unique_groups = df.select(subline_by).unique()
        
        return {
            "groups": len(unique_groups),
            "columns": subline_by,
            "unique_values": unique_groups.to_dicts(),
            "rows_per_group": df.group_by(subline_by).len().to_dicts()
        }


# Create a singleton instance for easy access
subline_service = SublineService()