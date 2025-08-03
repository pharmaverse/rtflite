#!/usr/bin/env python3
"""Test the border fix for footnote/source placement."""

import polars as pl
from src.rtflite import RTFDocument, RTFTitle, RTFFootnote, RTFSource, RTFPage

def test_border_placement():
    """Test that borders are applied correctly when footnotes/sources are on first page."""
    
    # Create test data that will require pagination
    df = pl.DataFrame({
        'col1': ['Row ' + str(i) for i in range(30)],
        'col2': [i for i in range(30)],
        'col3': ['Data ' + str(i) for i in range(30)]
    })
    
    print("Testing border placement with different component configurations...")
    
    # Test 1: Footnote on first page (as_table=True by default)
    print("\n1. Testing footnote on first page with as_table=True:")
    doc1 = RTFDocument(
        df=df,
        rtf_page=RTFPage(
            nrow=10, 
            page_footnote="first",  # Footnote only on first page
            border_last="double"    # Should apply to last data row
        ),
        rtf_title=RTFTitle(text='Test Title'),
        rtf_footnote=RTFFootnote(text='Test Footnote', as_table=True),
    )
    
    rtf1 = doc1.rtf_encode()
    footnote_count = rtf1.count('Test Footnote')
    border_count = rtf1.count('\\brdrdb')  # Double border
    
    print(f"   Footnote appears {footnote_count} time(s) - should be 1")
    print(f"   Double borders found: {border_count} - should be > 0")
    
    # Test 2: Source on first page with as_table=True  
    print("\n2. Testing source on first page with as_table=True:")
    doc2 = RTFDocument(
        df=df,
        rtf_page=RTFPage(
            nrow=10,
            page_source="first",    # Source only on first page  
            border_last="double"    # Should apply to last data row
        ),
        rtf_title=RTFTitle(text='Test Title'),
        rtf_source=RTFSource(text='Test Source', as_table=True),
    )
    
    rtf2 = doc2.rtf_encode()
    source_count = rtf2.count('Test Source')
    border_count2 = rtf2.count('\\brdrdb')  # Double border
    
    print(f"   Source appears {source_count} time(s) - should be 1")
    print(f"   Double borders found: {border_count2} - should be > 0")
    
    # Test 3: Both footnote and source on first page
    print("\n3. Testing both footnote and source on first page:")
    doc3 = RTFDocument(
        df=df,
        rtf_page=RTFPage(
            nrow=10,
            page_footnote="first",  # Both on first page
            page_source="first",    
            border_last="double"    # Should apply to last data row
        ),
        rtf_title=RTFTitle(text='Test Title'),
        rtf_footnote=RTFFootnote(text='Test Footnote', as_table=True),
        rtf_source=RTFSource(text='Test Source', as_table=True),
    )
    
    rtf3 = doc3.rtf_encode()
    footnote_count3 = rtf3.count('Test Footnote')
    source_count3 = rtf3.count('Test Source')
    border_count3 = rtf3.count('\\brdrdb')  # Double border
    
    print(f"   Footnote appears {footnote_count3} time(s) - should be 1")
    print(f"   Source appears {source_count3} time(s) - should be 1") 
    print(f"   Double borders found: {border_count3} - should be > 0")
    
    # Test 4: Control - footnote on last page (normal behavior)
    print("\n4. Control test - footnote on last page (normal):")
    doc4 = RTFDocument(
        df=df,
        rtf_page=RTFPage(
            nrow=10,
            page_footnote="last",   # Normal behavior
            border_last="double"    
        ),
        rtf_title=RTFTitle(text='Test Title'),
        rtf_footnote=RTFFootnote(text='Test Footnote', as_table=True),
    )
    
    rtf4 = doc4.rtf_encode()
    footnote_count4 = rtf4.count('Test Footnote')
    
    print(f"   Footnote appears {footnote_count4} time(s) - should be 1")
    
    print("\n✓ Border placement tests completed!")
    
    # Save test files for manual inspection
    doc1.write_rtf("test_footnote_first.rtf")
    doc2.write_rtf("test_source_first.rtf") 
    doc3.write_rtf("test_both_first.rtf")
    doc4.write_rtf("test_control.rtf")
    
    print("Test RTF files saved for manual inspection")

if __name__ == "__main__":
    test_border_placement()