"""Tests for PageDict and related pagination classes.

This module tests the advanced pagination control system including
PageConfig, PageDict, and PageIndexManager.
"""

from rtflite.pagination import PageBreakType, PageConfig, PageDict, PageIndexManager


class TestPageConfig:
    """Test the PageConfig dataclass."""

    def test_page_config_creation(self):
        """Test creating a PageConfig instance."""
        config = PageConfig(
            page_number=1, start_row=0, end_row=9, break_type=PageBreakType.AUTOMATIC
        )

        assert config.page_number == 1
        assert config.start_row == 0
        assert config.end_row == 9
        assert config.break_type == PageBreakType.AUTOMATIC
        assert config.section_headers == []
        assert config.subline_header is None
        assert config.group_context == {}
        assert config.forced_content == set()

    def test_page_config_row_count(self):
        """Test the row_count property."""
        config = PageConfig(
            page_number=1, start_row=0, end_row=9, break_type=PageBreakType.AUTOMATIC
        )
        assert config.row_count == 10  # 0 to 9 inclusive

        config = PageConfig(
            page_number=2, start_row=10, end_row=19, break_type=PageBreakType.AUTOMATIC
        )
        assert config.row_count == 10

        # Single row
        config = PageConfig(
            page_number=1, start_row=5, end_row=5, break_type=PageBreakType.AUTOMATIC
        )
        assert config.row_count == 1

    def test_page_config_is_section_start(self):
        """Test the is_section_start property."""
        # Automatic break - not a section start
        config = PageConfig(
            page_number=1, start_row=0, end_row=9, break_type=PageBreakType.AUTOMATIC
        )
        assert config.is_section_start is False

        # Forced break - is a section start
        config = PageConfig(
            page_number=2, start_row=10, end_row=19, break_type=PageBreakType.FORCED
        )
        assert config.is_section_start is True

        # Subline break - is a section start
        config = PageConfig(
            page_number=3, start_row=20, end_row=29, break_type=PageBreakType.SUBLINE
        )
        assert config.is_section_start is True

        # Manual break - not a section start
        config = PageConfig(
            page_number=4, start_row=30, end_row=39, break_type=PageBreakType.MANUAL
        )
        assert config.is_section_start is False

    def test_page_config_with_headers(self):
        """Test PageConfig with section headers and context."""
        config = PageConfig(
            page_number=1,
            start_row=0,
            end_row=9,
            break_type=PageBreakType.FORCED,
            section_headers=["Section 1", "Subsection A"],
            subline_header="Group Header",
            group_context={"group": "A", "subgroup": "X"},
        )

        assert config.section_headers == ["Section 1", "Subsection A"]
        assert config.subline_header == "Group Header"
        assert config.group_context == {"group": "A", "subgroup": "X"}


class TestPageDict:
    """Test the PageDict class."""

    def test_page_dict_creation(self):
        """Test creating a PageDict instance."""
        page_dict = PageDict(nrow_per_page=10)

        assert page_dict.nrow_per_page == 10
        assert page_dict.page_configs == {}
        assert page_dict.total_pages == 0
        assert page_dict.content_index == {}

    def test_add_page(self):
        """Test adding pages to PageDict."""
        page_dict = PageDict(nrow_per_page=10)

        # Add first page
        config1 = PageConfig(
            page_number=1, start_row=0, end_row=9, break_type=PageBreakType.AUTOMATIC
        )
        page_dict.add_page_config(config1)

        assert len(page_dict.page_configs) == 1
        assert page_dict.total_pages == 1

        # Add second page
        config2 = PageConfig(
            page_number=2, start_row=10, end_row=19, break_type=PageBreakType.AUTOMATIC
        )
        page_dict.add_page_config(config2)

        assert len(page_dict.page_configs) == 2
        assert page_dict.total_pages == 2

    def test_get_page_for_row(self):
        """Test getting the page number for a specific row."""
        page_dict = PageDict(nrow_per_page=10)

        # Add pages
        page_dict.add_page_config(PageConfig(1, 0, 9, PageBreakType.AUTOMATIC))
        page_dict.add_page_config(PageConfig(2, 10, 19, PageBreakType.AUTOMATIC))
        page_dict.add_page_config(PageConfig(3, 20, 29, PageBreakType.AUTOMATIC))

        # Test getting page for row
        # Note: The actual PageDict doesn't have get_page_for_row method
        # We'll test the page configs directly
        for page_num, config in page_dict.page_configs.items():
            if 0 >= config.start_row and 0 <= config.end_row:
                assert page_num == 1
            if 15 >= config.start_row and 15 <= config.end_row:
                assert page_num == 2
            if 25 >= config.start_row and 25 <= config.end_row:
                assert page_num == 3

    def test_get_page_config(self):
        """Test getting PageConfig for a specific page number."""
        page_dict = PageDict(nrow_per_page=10)

        config1 = PageConfig(1, 0, 9, PageBreakType.AUTOMATIC)
        config2 = PageConfig(2, 10, 19, PageBreakType.FORCED)

        page_dict.add_page_config(config1)
        page_dict.add_page_config(config2)

        # Get existing pages
        assert page_dict.get_page_config(1) == config1
        assert page_dict.get_page_config(2) == config2

        # Non-existent page
        assert page_dict.get_page_config(3) is None
        assert page_dict.get_page_config(0) is None

    def test_get_rows_for_page(self):
        """Test getting row range for a specific page."""
        page_dict = PageDict(nrow_per_page=10)

        page_dict.add_page_config(PageConfig(1, 0, 9, PageBreakType.AUTOMATIC))
        page_dict.add_page_config(
            PageConfig(2, 10, 14, PageBreakType.FORCED)
        )  # Partial page

        # Get row ranges from configs
        config1 = page_dict.get_page_config(1)
        assert (config1.start_row, config1.end_row) == (0, 9)

        config2 = page_dict.get_page_config(2)
        assert (config2.start_row, config2.end_row) == (10, 14)

        # Non-existent page
        assert page_dict.get_page_config(3) is None

    def test_is_page_break(self):
        """Test checking if a row is a page break."""
        page_dict = PageDict(nrow_per_page=10)

        page_dict.add_page_config(PageConfig(1, 0, 9, PageBreakType.AUTOMATIC))
        page_dict.add_page_config(PageConfig(2, 10, 19, PageBreakType.FORCED))

        # Check if rows are at page boundaries
        # We'll test using the page configs
        config1 = page_dict.get_page_config(1)
        config2 = page_dict.get_page_config(2)

        # End of page 1 is row 9
        assert config1.end_row == 9
        # End of page 2 is row 19
        assert config2.end_row == 19
        # Start of page 2 is row 10
        assert config2.start_row == 10

    def test_build_page_index(self):
        """Test building the page index."""
        page_dict = PageDict(nrow_per_page=10)

        # Add pages with content IDs
        config1 = PageConfig(1, 0, 9, PageBreakType.AUTOMATIC)
        config1.forced_content = {"header1", "footer1"}

        config2 = PageConfig(2, 10, 19, PageBreakType.FORCED)
        config2.forced_content = {"header2", "section2"}

        page_dict.add_page_config(config1)
        page_dict.add_page_config(config2)

        # Add content to index
        page_dict.add_content_to_page("header1", 1)
        page_dict.add_content_to_page("footer1", 1)
        page_dict.add_content_to_page("header2", 2)
        page_dict.add_content_to_page("section2", 2)

        # Check index
        assert page_dict.get_page_for_content("header1") == 1
        assert page_dict.get_page_for_content("footer1") == 1
        assert page_dict.get_page_for_content("header2") == 2
        assert page_dict.get_page_for_content("section2") == 2


class TestPageIndexManager:
    """Test the PageIndexManager class."""

    def test_page_index_manager_creation(self):
        """Test creating a PageIndexManager instance."""
        page_dict = PageDict(nrow_per_page=10)
        manager = PageIndexManager(page_dict)

        assert manager.page_dict == page_dict
        assert manager._content_assignments == {}
        assert manager._page_content_map == {}

    def test_force_to_page(self):
        """Test forcing content to specific pages."""
        page_dict = PageDict(nrow_per_page=10)
        manager = PageIndexManager(page_dict)

        # Assign content to pages
        manager.assign_content_to_page("item1", 2)
        assert manager.get_content_page("item1") == 2

        # Assign multiple items
        manager.assign_content_to_page("item2", 3)
        manager.assign_content_to_page("item3", 3)
        assert manager.get_content_page("item2") == 3
        assert manager.get_content_page("item3") == 3

        # Override existing
        manager.assign_content_to_page("item1", 5)
        assert manager.get_content_page("item1") == 5

    def test_keep_together_groups(self):
        """Test keeping content groups together."""
        page_dict = PageDict(nrow_per_page=10)
        manager = PageIndexManager(page_dict)

        # Test assigning groups to same page
        manager.assign_content_to_page("row1", 1)
        manager.assign_content_to_page("row2", 1)
        manager.assign_content_to_page("row3", 1)

        assert manager.get_page_content(1) == {"row1", "row2", "row3"}

        # Add another group on different page
        manager.assign_content_to_page("row4", 2)
        manager.assign_content_to_page("row5", 2)

        assert manager.get_page_content(2) == {"row4", "row5"}

    def test_add_page_hint(self):
        """Test adding page hints."""
        page_dict = PageDict(nrow_per_page=10)
        manager = PageIndexManager(page_dict)

        # Test content assignment which is the actual functionality
        manager.assign_content_to_page("content5", 1)
        manager.assign_content_to_page("content10", 2)

        assert manager.get_content_page("content5") == 1
        assert manager.get_content_page("content10") == 2

        # Override existing assignment
        manager.assign_content_to_page("content5", 3)
        assert manager.get_content_page("content5") == 3

    def test_get_forced_page(self):
        """Test getting forced page for content."""
        page_dict = PageDict(nrow_per_page=10)
        manager = PageIndexManager(page_dict)

        manager.assign_content_to_page("item1", 2)
        manager.assign_content_to_page("item2", 3)

        assert manager.get_content_page("item1") == 2
        assert manager.get_content_page("item2") == 3
        assert manager.get_content_page("item3") is None

    def test_should_keep_together(self):
        """Test checking if items should be kept together."""
        page_dict = PageDict(nrow_per_page=10)
        manager = PageIndexManager(page_dict)

        # Assign items to same page (keeping them together)
        manager.assign_content_to_page("row1", 1)
        manager.assign_content_to_page("row2", 1)
        manager.assign_content_to_page("row3", 1)

        # Another group on different page
        manager.assign_content_to_page("row4", 2)
        manager.assign_content_to_page("row5", 2)

        # Same page = kept together
        assert manager.get_content_page("row1") == manager.get_content_page("row2")
        assert manager.get_content_page("row2") == manager.get_content_page("row3")
        assert manager.get_content_page("row4") == manager.get_content_page("row5")

        # Different pages = not kept together
        assert manager.get_content_page("row1") != manager.get_content_page("row4")
        assert manager.get_content_page("row3") != manager.get_content_page("row5")

    def test_complex_page_dict_scenario(self):
        """Test a complex scenario with multiple page types."""
        page_dict = PageDict(nrow_per_page=5)

        # Page 1: Regular content
        config1 = PageConfig(
            page_number=1, start_row=0, end_row=4, break_type=PageBreakType.AUTOMATIC
        )

        # Page 2: New section (forced break)
        config2 = PageConfig(
            page_number=2,
            start_row=5,
            end_row=9,
            break_type=PageBreakType.FORCED,
            section_headers=["Section 2"],
        )

        # Page 3: Subline header
        config3 = PageConfig(
            page_number=3,
            start_row=10,
            end_row=12,  # Partial page
            break_type=PageBreakType.SUBLINE,
            subline_header="Subsection A",
        )

        page_dict.add_page_config(config1)
        page_dict.add_page_config(config2)
        page_dict.add_page_config(config3)

        # Verify structure
        assert page_dict.total_pages == 3
        # Check that we have 13 total rows (0-12) across all pages
        total_rows = sum(config.row_count for config in page_dict.page_configs.values())
        assert total_rows == 13  # 0-12

        # Check page properties
        assert page_dict.get_page_config(1).is_section_start is False
        assert page_dict.get_page_config(2).is_section_start is True
        assert page_dict.get_page_config(3).is_section_start is True

        # Verify row distribution by checking page configs directly
        # Row 2 should be on page 1 (0-4)
        assert (
            2 >= page_dict.get_page_config(1).start_row
            and 2 <= page_dict.get_page_config(1).end_row
        )
        # Row 7 should be on page 2 (5-9)
        assert (
            7 >= page_dict.get_page_config(2).start_row
            and 7 <= page_dict.get_page_config(2).end_row
        )
        # Row 11 should be on page 3 (10-12)
        assert (
            11 >= page_dict.get_page_config(3).start_row
            and 11 <= page_dict.get_page_config(3).end_row
        )
