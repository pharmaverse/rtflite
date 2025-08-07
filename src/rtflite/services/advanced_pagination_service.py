"""Advanced Pagination Service for rtflite.

This service provides enhanced pagination capabilities using the PageDict system,
enabling page_index-like functionality while maintaining backward compatibility.
"""

from typing import Any, Dict, List, Optional, Tuple

import polars as pl

from ..pagination import PageBreakType, PageConfig, PageDict, PageIndexManager
from .document_service import RTFDocumentService


class AdvancedPaginationService:
    """Service for advanced pagination features using PageDict system"""

    def __init__(self):
        self.document_service = RTFDocumentService()
        self.page_dict: Optional[PageDict] = None
        self.page_index_manager: Optional[PageIndexManager] = None

    def create_page_dict(
        self, document, nrow_per_page: Optional[int] = None
    ) -> PageDict:
        """Create a PageDict for the given document

        Args:
            document: RTF document to create PageDict for
            nrow_per_page: Override the document's nrow setting

        Returns:
            PageDict instance with calculated page configurations
        """
        # Use document's nrow or provided override
        nrow = nrow_per_page or document.rtf_page.nrow

        # Calculate additional rows needed for headers, footnotes, etc.
        additional_rows = self.document_service.calculate_additional_rows_per_page(
            document
        )

        # Create PageDict instance
        page_dict = PageDict(nrow_per_page=nrow)

        # Handle multi-section documents (list of DataFrames)
        if isinstance(document.df, list):
            self._process_multi_section_document(document, page_dict, additional_rows)
        else:
            # Single DataFrame
            self._process_single_dataframe(
                document.df, document.rtf_body, page_dict, additional_rows
            )

        self.page_dict = page_dict
        return page_dict

    def get_page_index_manager(self) -> PageIndexManager:
        """Get or create a PageIndexManager for the current PageDict"""
        if self.page_dict is None:
            raise ValueError("Must create PageDict first using create_page_dict()")

        if self.page_index_manager is None:
            self.page_index_manager = PageIndexManager(self.page_dict)

        return self.page_index_manager

    def _process_single_dataframe(
        self, df: pl.DataFrame, rtf_body, page_dict: PageDict, additional_rows: int
    ) -> None:
        """Process a single DataFrame for pagination"""
        # Extract pagination parameters from rtf_body
        page_by = getattr(rtf_body, "page_by", None)
        subline_by = getattr(rtf_body, "subline_by", None)
        new_page = getattr(rtf_body, "new_page", False)

        # Calculate page configurations
        page_dict.calculate_pages_from_dataframe(
            df=df,
            page_by=page_by,
            subline_by=subline_by,
            new_page=new_page,
            additional_rows_per_page=additional_rows,
        )

    def _process_multi_section_document(
        self, document, page_dict: PageDict, additional_rows: int
    ) -> None:
        """Process a multi-section document (list of DataFrames)"""
        current_row_offset = 0

        for section_idx, df in enumerate(document.df):
            rtf_body = (
                document.rtf_body[section_idx]
                if isinstance(document.rtf_body, list)
                else document.rtf_body
            )

            # Create a temporary PageDict for this section
            section_page_dict = PageDict(nrow_per_page=page_dict.nrow_per_page)
            self._process_single_dataframe(
                df, rtf_body, section_page_dict, additional_rows
            )

            # Merge section pages into main PageDict with offset
            self._merge_section_pages(
                section_page_dict, page_dict, current_row_offset, section_idx
            )

            current_row_offset += df.height

    def _merge_section_pages(
        self,
        section_page_dict: PageDict,
        main_page_dict: PageDict,
        row_offset: int,
        section_idx: int,
    ) -> None:
        """Merge section pages into the main PageDict"""
        # Calculate the page number offset
        page_offset = main_page_dict.total_pages

        for page_num, config in section_page_dict.page_configs.items():
            # Create new config with adjusted page number and row indices
            new_config = PageConfig(
                page_number=page_num + page_offset,
                start_row=config.start_row + row_offset,
                end_row=config.end_row + row_offset,
                break_type=config.break_type,
                section_headers=config.section_headers + [f"Section {section_idx + 1}"],
                subline_header=config.subline_header,
                group_context=config.group_context.copy(),
                forced_content=config.forced_content.copy(),
            )

            main_page_dict.add_page_config(new_config)

    def get_page_for_row(self, row_index: int) -> int:
        """Get the page number where a specific row appears"""
        if self.page_dict is None:
            return 1

        for page_num, config in self.page_dict.page_configs.items():
            if config.start_row <= row_index <= config.end_row:
                return page_num

        return 1  # Default to first page

    def get_rows_for_page(self, page_num: int) -> Tuple[int, int]:
        """Get the row range for a specific page"""
        if self.page_dict is None:
            return (0, 0)

        config = self.page_dict.get_page_config(page_num)
        if config:
            return (config.start_row, config.end_row)

        return (0, 0)

    def force_content_to_page(self, content_id: str, page_num: int) -> None:
        """Force specific content to appear on a specific page (page_index functionality)"""
        manager = self.get_page_index_manager()
        manager.assign_content_to_page(content_id, page_num)

    def get_pagination_summary(self) -> Dict[str, Any]:
        """Get a summary of the pagination configuration"""
        if self.page_dict is None:
            return {"error": "No PageDict available"}

        summary = {
            "total_pages": self.page_dict.total_pages,
            "nrow_per_page": self.page_dict.nrow_per_page,
            "break_types": self.page_dict.get_page_break_summary(),
            "page_configs": {},
        }

        for page_num, config in self.page_dict.page_configs.items():
            summary["page_configs"][page_num] = {
                "rows": f"{config.start_row}-{config.end_row}",
                "row_count": config.row_count,
                "break_type": config.break_type.value,
                "is_section_start": config.is_section_start,
                "section_headers": config.section_headers,
                "subline_header": config.subline_header,
                "forced_content_count": len(config.forced_content),
            }

        return summary

    def convert_to_legacy_format(self) -> List[Dict[str, Any]]:
        """Convert PageDict to legacy page info format for backward compatibility"""
        if self.page_dict is None:
            return []

        return self.page_dict.to_legacy_page_info()

    def optimize_pagination(self) -> None:
        """Optimize pagination for better balance and readability"""
        if self.page_index_manager:
            self.page_index_manager.optimize_page_distribution()

    def validate_pagination(self) -> List[str]:
        """Validate the pagination configuration and return any issues"""
        issues = []

        if self.page_dict is None:
            issues.append("No PageDict available")
            return issues

        # Check for empty pages
        for page_num, config in self.page_dict.page_configs.items():
            if config.row_count <= 0:
                issues.append(f"Page {page_num} has no content rows")

        # Check for overlapping page ranges
        sorted_pages = sorted(self.page_dict.page_configs.items())
        for i in range(len(sorted_pages) - 1):
            current_page = sorted_pages[i][1]
            next_page = sorted_pages[i + 1][1]

            if current_page.end_row >= next_page.start_row:
                issues.append(
                    f"Pages {current_page.page_number} and {next_page.page_number} have overlapping row ranges"
                )

        # Check for missing row coverage
        if sorted_pages:
            total_expected_rows = sorted_pages[-1][1].end_row + 1
            covered_rows = set()

            for _, config in sorted_pages:
                for row in range(config.start_row, config.end_row + 1):
                    covered_rows.add(row)

            missing_rows = set(range(total_expected_rows)) - covered_rows
            if missing_rows:
                issues.append(f"Missing row coverage for rows: {sorted(missing_rows)}")

        return issues
