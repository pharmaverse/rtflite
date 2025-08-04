#!/usr/bin/env python3
"""
Test script for Phase 1 pagination features.

This script demonstrates the new PageDict and PageIndexManager functionality.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import polars as pl
import rtflite as rtf
from rtflite.services.advanced_pagination_service import AdvancedPaginationService
from rtflite.pagination import PageDict, PageIndexManager, PageBreakType


def create_sample_data():
    """Create sample clinical data for testing"""
    return pl.DataFrame({
        'USUBJID': [f'01-001-{i:03d}' for i in range(1, 51)],  # 50 subjects
        'TRTA': ['Placebo'] * 25 + ['Active Drug'] * 25,
        'AEDECOD': [f'Adverse Event {(i-1) % 10 + 1}' for i in range(1, 51)],
        'AESEV': ['Mild', 'Moderate', 'Severe'] * 16 + ['Mild', 'Moderate'],
        'SUBLINEBY': [f'Study Site {((i-1) // 10) + 1}' for i in range(1, 51)],
    })


def test_basic_pagedict_functionality():
    """Test basic PageDict creation and functionality"""
    print("=== Testing Basic PageDict Functionality ===")
    
    # Create sample data
    df = create_sample_data()
    print(f"Created sample data with {df.height} rows")
    
    # Create PageDict
    page_dict = PageDict(nrow_per_page=15)
    page_dict.calculate_pages_from_dataframe(
        df=df,
        page_by=['TRTA'],
        new_page=True,
        additional_rows_per_page=5  # Account for headers/footers
    )
    
    print(f"\nPageDict Summary:")
    print(f"  Total pages: {page_dict.total_pages}")
    print(f"  Break types: {page_dict.get_page_break_summary()}")
    
    # Show page configurations
    for page_num in sorted(page_dict.page_configs.keys()):
        config = page_dict.page_configs[page_num]
        print(f"  Page {page_num}: rows {config.start_row}-{config.end_row} ({config.row_count} rows)")
        print(f"    Break type: {config.break_type.value}")
        if config.section_headers:
            print(f"    Section headers: {config.section_headers}")
        if config.subline_header:
            print(f"    Subline header: {config.subline_header}")
    
    # Test completed successfully
    assert page_dict.total_pages > 0
    assert len(page_dict.page_configs) > 0


def test_page_index_manager():
    """Test PageIndexManager functionality"""
    print("\n=== Testing PageIndexManager Functionality ===")
    
    # Create sample data and PageDict
    df = create_sample_data()
    page_dict = PageDict(nrow_per_page=12)
    page_dict.calculate_pages_from_dataframe(df, additional_rows_per_page=3)
    
    # Create PageIndexManager
    manager = PageIndexManager(page_dict)
    
    # Test content assignment (page_index-like functionality)
    manager.assign_content_to_page("adverse_event_summary", 1)
    manager.assign_content_to_page("demographic_table", 2)
    manager.assign_content_to_page("safety_analysis", 3)
    
    print("Content assignments:")
    for content_id in ["adverse_event_summary", "demographic_table", "safety_analysis"]:
        page_num = manager.get_content_page(content_id)
        print(f"  {content_id}: Page {page_num}")
    
    # Test page content lookup
    print("\nPage content:")
    for page_num in range(1, min(4, page_dict.total_pages + 1)):
        content = manager.get_page_content(page_num)
        print(f"  Page {page_num}: {content}")
    
    # Get content summary
    summary = manager.get_content_summary()
    print(f"\nContent summary: {summary}")
    
    # Test completed successfully
    assert len(summary) > 0
    assert manager.get_content_page("adverse_event_summary") == 1


def test_advanced_pagination_service():
    """Test AdvancedPaginationService integration"""
    print("\n=== Testing AdvancedPaginationService Integration ===")
    
    # Create sample data
    df = create_sample_data()
    
    # Create RTF document
    doc = rtf.RTFDocument(
        df=df,
        rtf_page=rtf.RTFPage(nrow=12),
        rtf_body=rtf.RTFBody(
            page_by=['TRTA'],
            new_page=True
        ),
        rtf_title=rtf.RTFTitle(text="Advanced Pagination Test"),
        rtf_footnote=rtf.RTFFootnote(text="Generated using Phase 1 pagination features")
    )
    
    # Create advanced pagination service
    service = AdvancedPaginationService()
    
    # Create PageDict for the document
    page_dict = service.create_page_dict(doc)
    print(f"Created PageDict with {page_dict.total_pages} pages")
    
    # Get pagination summary
    summary = service.get_pagination_summary()
    print(f"\nPagination Summary:")
    print(f"  Total pages: {summary['total_pages']}")
    print(f"  Rows per page: {summary['nrow_per_page']}")
    print(f"  Break types: {summary['break_types']}")
    
    # Show detailed page info
    for page_num, config in summary['page_configs'].items():
        print(f"  Page {page_num}:")
        print(f"    Rows: {config['rows']} ({config['row_count']} rows)")
        print(f"    Break type: {config['break_type']}")
        print(f"    Section start: {config['is_section_start']}")
        if config['section_headers']:
            print(f"    Headers: {config['section_headers']}")
    
    # Test page_index-like functionality
    service.force_content_to_page("title_content", 1)
    service.force_content_to_page("summary_table", 2)
    
    print(f"\nForced content assignments:")
    manager = service.get_page_index_manager()
    print(f"  title_content: Page {manager.get_content_page('title_content')}")
    print(f"  summary_table: Page {manager.get_content_page('summary_table')}")
    
    # Validate pagination
    issues = service.validate_pagination()
    if issues:
        print(f"\nPagination issues found: {issues}")
    else:
        print(f"\n✅ Pagination validation passed!")
    
    # Test completed successfully
    assert service.page_dict.total_pages > 0
    assert len(service.get_pagination_summary()["page_configs"]) > 0


def test_subline_by_functionality():
    """Test subline_by functionality"""
    print("\n=== Testing subline_by Functionality ===")
    
    # Create data with subline groupings
    df = create_sample_data()
    
    # Create PageDict with subline_by
    page_dict = PageDict(nrow_per_page=10)
    page_dict.calculate_pages_from_dataframe(
        df=df,
        subline_by='SUBLINEBY',  # Group by study site
        additional_rows_per_page=4
    )
    
    print(f"Created {page_dict.total_pages} pages with subline_by grouping")
    
    # Show page configurations with subline headers
    for page_num in sorted(page_dict.page_configs.keys()):
        config = page_dict.page_configs[page_num]
        print(f"Page {page_num}: rows {config.start_row}-{config.end_row}")
        if config.subline_header:
            print(f"  Subline: {config.subline_header}")
        print(f"  Break type: {config.break_type.value}")
    
    # Test completed successfully
    assert page_dict.total_pages > 0
    assert any(config.break_type.value == "subline" for config in page_dict.page_configs.values())


def test_backward_compatibility():
    """Test backward compatibility with existing pagination"""
    print("\n=== Testing Backward Compatibility ===")
    
    # Create PageDict
    df = create_sample_data()
    page_dict = PageDict(nrow_per_page=15)
    page_dict.calculate_pages_from_dataframe(df, additional_rows_per_page=3)
    
    # Convert to legacy format
    legacy_format = page_dict.to_legacy_page_info()
    
    print(f"Converted to legacy format: {len(legacy_format)} pages")
    for page_info in legacy_format[:3]:  # Show first 3 pages
        print(f"  Page {page_info['page_number']}: {page_info['start_row']}-{page_info['end_row']}")
        print(f"    First page: {page_info['is_first_page']}")
        print(f"    Last page: {page_info['is_last_page']}")
    
    # Test completed successfully
    assert len(legacy_format) > 0
    assert all("page_number" in page for page in legacy_format)


if __name__ == "__main__":
    print("🚀 Phase 1 Pagination Features Demo")
    print("=" * 50)
    
    try:
        # Run all tests
        test_basic_pagedict_functionality()
        test_page_index_manager()
        test_advanced_pagination_service()
        test_subline_by_functionality()
        test_backward_compatibility()
        
        print("\n" + "=" * 50)
        print("✅ Phase 1 implementation completed successfully!")
        print("\nKey features demonstrated:")
        print("  ✅ PageDict for advanced pagination control")
        print("  ✅ PageIndexManager for page_index-like functionality")
        print("  ✅ AdvancedPaginationService integration")
        print("  ✅ subline_by support with subheader generation")
        print("  ✅ Backward compatibility with existing pagination")
        print("  ✅ Multi-level page break support (automatic, forced, subline)")
        print("  ✅ Content assignment to specific pages")
        print("  ✅ Comprehensive pagination validation")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)