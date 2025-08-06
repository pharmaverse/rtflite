"""
Advanced pagination control system for rtflite.

This module implements a PageDict equivalent to r2rtf's advanced pagination features,
providing page_index-like functionality while maintaining rtflite's existing architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import polars as pl
from pydantic import BaseModel, ConfigDict, Field


class PageBreakType(Enum):
    """Types of page breaks that can occur"""

    AUTOMATIC = "automatic"  # Based on nrow limit
    FORCED = "forced"  # Based on page_by with new_page=True
    SUBLINE = "subline"  # Based on subline_by changes
    MANUAL = "manual"  # Manually specified via PageIndexManager


@dataclass
class PageConfig:
    """Configuration for a specific page"""

    page_number: int
    start_row: int
    end_row: int
    break_type: PageBreakType
    section_headers: List[str] = field(default_factory=list)
    subline_header: Optional[str] = None
    group_context: Dict[str, Any] = field(default_factory=dict)
    forced_content: Set[str] = field(
        default_factory=set
    )  # Content IDs forced to this page

    @property
    def row_count(self) -> int:
        """Number of data rows on this page"""
        return self.end_row - self.start_row + 1

    @property
    def is_section_start(self) -> bool:
        """True if this page starts a new section"""
        return self.break_type in {PageBreakType.FORCED, PageBreakType.SUBLINE}


@dataclass
class PageBreakRule:
    """Rule for determining when page breaks should occur"""

    column: str
    break_on_change: bool = True
    force_new_page: bool = False
    priority: int = 0  # Higher priority rules are processed first

    def applies_to_row(
        self, df: pl.DataFrame, row_idx: int, prev_row_idx: Optional[int] = None
    ) -> bool:
        """Check if this rule should trigger a page break for the given row"""
        if prev_row_idx is None:
            return False

        if self.column not in df.columns:
            return False

        current_value = df[self.column][row_idx]
        previous_value = df[self.column][prev_row_idx]

        return self.break_on_change and current_value != previous_value


class PageDict(BaseModel):
    """Advanced pagination control structure (r2rtf PageDict equivalent)

    This class provides sophisticated pagination control similar to r2rtf's page_dict,
    enabling page_index-like functionality while maintaining compatibility with
    rtflite's existing row-based pagination system.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    page_configs: Dict[int, PageConfig] = Field(
        default_factory=dict, description="Configuration for each page"
    )
    break_rules: List[PageBreakRule] = Field(
        default_factory=list, description="Rules determining where page breaks occur"
    )
    content_index: Dict[str, List[int]] = Field(
        default_factory=dict, description="Maps content identifiers to page numbers"
    )
    total_pages: int = Field(default=0, description="Total number of pages")
    nrow_per_page: int = Field(default=40, description="Base rows per page")

    def add_page_config(self, config: PageConfig) -> None:
        """Add a page configuration"""
        self.page_configs[config.page_number] = config
        self.total_pages = max(self.total_pages, config.page_number)

    def get_page_config(self, page_num: int) -> Optional[PageConfig]:
        """Get configuration for a specific page"""
        return self.page_configs.get(page_num)

    def add_break_rule(self, rule: PageBreakRule) -> None:
        """Add a page break rule"""
        self.break_rules.append(rule)
        # Sort rules by priority (highest first)
        self.break_rules.sort(key=lambda r: r.priority, reverse=True)

    def get_page_for_content(self, content_id: str) -> int:
        """Get the page number where specific content appears (page_index equivalent)"""
        pages = self.content_index.get(content_id, [])
        return pages[0] if pages else 1  # Default to page 1

    def get_pages_for_content(self, content_id: str) -> List[int]:
        """Get all page numbers where specific content appears"""
        return self.content_index.get(content_id, [])

    def add_content_to_page(self, content_id: str, page_num: int) -> None:
        """Add content to a specific page"""
        if content_id not in self.content_index:
            self.content_index[content_id] = []
        if page_num not in self.content_index[content_id]:
            self.content_index[content_id].append(page_num)
            self.content_index[content_id].sort()

    def get_section_pages(self, section_header: str) -> List[int]:
        """Get all pages that belong to a specific section"""
        section_pages = []
        for page_num, config in self.page_configs.items():
            if section_header in config.section_headers:
                section_pages.append(page_num)
        return sorted(section_pages)

    def get_page_break_summary(self) -> Dict[str, int]:
        """Get summary of page break types"""
        summary = {}
        for config in self.page_configs.values():
            break_type = config.break_type.value
            summary[break_type] = summary.get(break_type, 0) + 1
        return summary

    def calculate_pages_from_dataframe(
        self,
        df: pl.DataFrame,
        page_by: Optional[List[str]] = None,
        subline_by: Optional[str] = None,
        new_page: bool = False,
        additional_rows_per_page: int = 0,
    ) -> None:
        """Calculate page configurations from a DataFrame

        This method implements the core pagination algorithm inspired by r2rtf's approach.
        """
        if df.is_empty():
            return

        # Clear existing configurations
        self.page_configs.clear()
        self.content_index.clear()

        # Calculate effective rows per page (accounting for headers, footers, etc.)
        effective_nrow = max(1, self.nrow_per_page - additional_rows_per_page)

        # Add break rules based on parameters
        if page_by and new_page:
            for col in page_by:
                self.add_break_rule(
                    PageBreakRule(
                        column=col,
                        break_on_change=True,
                        force_new_page=True,
                        priority=10,
                    )
                )

        if subline_by:
            self.add_break_rule(
                PageBreakRule(
                    column=subline_by,
                    break_on_change=True,
                    force_new_page=True,
                    priority=20,  # Higher priority than page_by
                )
            )

        # Calculate page boundaries
        page_boundaries = self._calculate_page_boundaries(df, effective_nrow)

        # Create page configurations
        for page_num, (start_row, end_row, break_type) in enumerate(page_boundaries, 1):
            config = PageConfig(
                page_number=page_num,
                start_row=start_row,
                end_row=end_row,
                break_type=break_type,
            )

            # Add section headers for page_by columns
            if page_by and start_row < df.height:
                for col in page_by:
                    if col in df.columns:
                        header_value = str(df[col][start_row])
                        config.section_headers.append(f"{col}: {header_value}")

            # Add subline header
            if subline_by and subline_by in df.columns and start_row < df.height:
                subline_value = str(df[subline_by][start_row])
                config.subline_header = f"{subline_by}: {subline_value}"

            self.add_page_config(config)

        self.total_pages = len(page_boundaries)

    def _calculate_page_boundaries(
        self, df: pl.DataFrame, effective_nrow: int
    ) -> List[Tuple[int, int, PageBreakType]]:
        """Calculate where page boundaries should occur"""
        boundaries = []
        current_start = 0

        for row_idx in range(df.height):
            # Check if any break rules apply
            forced_break = False
            break_type = PageBreakType.AUTOMATIC

            if row_idx > 0:  # Don't break on first row
                for rule in self.break_rules:
                    if rule.applies_to_row(df, row_idx, row_idx - 1):
                        if rule.force_new_page:
                            forced_break = True
                            break_type = PageBreakType.FORCED
                            if rule.column and "subline" in rule.column.lower():
                                break_type = PageBreakType.SUBLINE
                            break

            # Check if we need to break due to row limit or forced break
            rows_on_current_page = row_idx - current_start
            if forced_break or (rows_on_current_page >= effective_nrow and row_idx > 0):
                # End current page
                boundaries.append((current_start, row_idx - 1, break_type))
                current_start = row_idx

        # Add final page
        if current_start < df.height:
            boundaries.append((current_start, df.height - 1, PageBreakType.AUTOMATIC))

        return boundaries

    def to_legacy_page_info(self) -> List[Dict[str, Any]]:
        """Convert to legacy page info format for backward compatibility"""
        page_info_list = []

        for page_num in sorted(self.page_configs.keys()):
            config = self.page_configs[page_num]
            page_info = {
                "page_number": page_num,
                "total_pages": self.total_pages,
                "start_row": config.start_row,
                "end_row": config.end_row,
                "is_first_page": page_num == 1,
                "is_last_page": page_num == self.total_pages,
                "break_type": config.break_type.value,
                "section_headers": config.section_headers,
                "subline_header": config.subline_header,
            }
            page_info_list.append(page_info)

        return page_info_list


class PageIndexManager:
    """Provides page_index-like functionality for advanced page control

    This class enables explicit control over which content appears on which pages,
    similar to how a page_index parameter would work in other pagination systems.
    """

    def __init__(self, page_dict: PageDict):
        self.page_dict = page_dict
        self._content_assignments: Dict[str, int] = {}
        self._page_content_map: Dict[int, Set[str]] = {}

    def assign_content_to_page(self, content_id: str, page_num: int) -> None:
        """Assign specific content to a specific page (explicit page_index control)"""
        self._content_assignments[content_id] = page_num

        if page_num not in self._page_content_map:
            self._page_content_map[page_num] = set()
        self._page_content_map[page_num].add(content_id)

        # Update the PageDict
        self.page_dict.add_content_to_page(content_id, page_num)

        # Mark content as forced on the target page
        if page_num in self.page_dict.page_configs:
            self.page_dict.page_configs[page_num].forced_content.add(content_id)

    def get_content_page(self, content_id: str) -> Optional[int]:
        """Get the assigned page for specific content"""
        return self._content_assignments.get(content_id)

    def get_page_content(self, page_num: int) -> Set[str]:
        """Get all content assigned to a specific page"""
        return self._page_content_map.get(page_num, set())

    def force_page_break_before_content(self, content_id: str) -> None:
        """Force a page break before specific content appears"""
        # This would require integration with the DataFrame processing
        # to identify where the content appears and insert a break rule
        pass

    def get_content_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all content assignments"""
        summary = {}
        for content_id, page_num in self._content_assignments.items():
            summary[content_id] = {
                "assigned_page": page_num,
                "is_forced": content_id
                in self.page_dict.page_configs.get(
                    page_num, PageConfig(0, 0, 0, PageBreakType.AUTOMATIC)
                ).forced_content,
            }
        return summary

    def optimize_page_distribution(self) -> None:
        """Optimize content distribution across pages to balance page lengths"""
        # Advanced algorithm to redistribute content for better balance
        # This could implement sophisticated optimization based on content weight,
        # page capacity, and user constraints
        pass
