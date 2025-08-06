"""
Tests for data sorting validation in RTF document generation.

This module tests the data sorting validation functionality that ensures
data is properly sorted for group_by, page_by, and subline_by operations,
following r2rtf compatibility requirements.
"""

import polars as pl
import pytest

from src.rtflite.encode import RTFDocument
from src.rtflite.services.grouping_service import grouping_service


class TestDataSortingValidation:
    """Test class for data sorting validation functionality"""

    def test_enhance_group_by_with_sorted_data(self):
        """Test that properly sorted data passes validation"""
        df = pl.DataFrame(
            {
                "USUBJID": ["01-701-1015", "01-701-1015", "01-701-1023", "01-701-1023"],
                "ASTDY": [1, 3, 1, 2],
                "AEDECOD": ["Headache", "Fatigue", "Dizziness", "Headache"],
                "AESEV": ["MILD", "MILD", "SEVERE", "MILD"],
            }
        )

        # Should not raise any exception
        result = grouping_service.enhance_group_by(df, group_by=["USUBJID", "ASTDY"])

        # Check that suppression worked correctly
        assert result["USUBJID"][0] == "01-701-1015"  # First occurrence shown
        assert result["USUBJID"][1] is None  # Suppressed
        assert result["USUBJID"][2] == "01-701-1023"  # New group shown
        assert result["USUBJID"][3] is None  # Suppressed

        assert result["ASTDY"][0] == 1  # First occurrence shown
        assert result["ASTDY"][1] == 3  # Different value shown
        assert result["ASTDY"][2] == 1  # New group shown
        assert result["ASTDY"][3] == 2  # Different value shown

    def test_enhance_group_by_with_unsorted_data(self):
        """Test that improperly sorted data raises ValueError"""
        df = pl.DataFrame(
            {
                "USUBJID": ["01-701-1023", "01-701-1015", "01-701-1015", "01-701-1023"],
                "ASTDY": [1, 1, 3, 2],
                "AEDECOD": ["Dizziness", "Headache", "Fatigue", "Headache"],
            }
        )

        with pytest.raises(ValueError, match="Data is not properly grouped"):
            grouping_service.enhance_group_by(df, group_by=["USUBJID", "ASTDY"])

    def test_validate_data_sorting_overlapping_variables(self):
        """Test validation of overlapping grouping variables"""
        df = pl.DataFrame(
            {
                "USUBJID": ["01-701-1015", "01-701-1023"],
                "ASTDY": [1, 1],
                "TRTA": ["Placebo", "Active"],
            }
        )

        with pytest.raises(ValueError, match="Overlapping variables found"):
            grouping_service.validate_data_sorting(
                df, group_by=["USUBJID"], page_by=["USUBJID", "TRTA"]
            )

    def test_validate_data_sorting_missing_columns(self):
        """Test validation with missing columns"""
        df = pl.DataFrame({"USUBJID": ["01-701-1015", "01-701-1023"], "ASTDY": [1, 1]})

        with pytest.raises(ValueError, match="Grouping columns not found"):
            grouping_service.validate_data_sorting(
                df, group_by=["USUBJID", "NONEXISTENT"]
            )

    def test_validate_data_sorting_multiple_grouping_types(self):
        """Test validation with multiple grouping types (properly sorted)"""
        df = pl.DataFrame(
            {
                "TRTA": ["Active", "Active", "Placebo", "Placebo"],
                "USUBJID": ["01-701-1015", "01-701-1023", "01-701-1015", "01-701-1023"],
                "ASTDY": [1, 1, 1, 1],
            }
        )

        # Should not raise any exception - data is properly sorted
        grouping_service.validate_data_sorting(
            df, page_by=["TRTA"], group_by=["USUBJID"]
        )

    def test_validate_data_sorting_complex_hierarchy(self):
        """Test validation with complex grouping hierarchy"""
        df = pl.DataFrame(
            {
                "STUDY": ["Study1", "Study1", "Study1", "Study2", "Study2"],
                "TRTA": ["Active", "Active", "Placebo", "Active", "Placebo"],
                "USUBJID": ["001", "002", "003", "004", "005"],
                "ASTDY": [1, 1, 1, 1, 1],
            }
        )

        # Should not raise exception - properly sorted
        grouping_service.validate_data_sorting(
            df, page_by=["STUDY"], subline_by=["TRTA"], group_by=["USUBJID"]
        )

    def test_rtf_document_integration(self):
        """Test that RTF document generation works with sorting validation"""
        df = pl.DataFrame(
            {
                "USUBJID": ["01-701-1015", "01-701-1015", "01-701-1023"],
                "AEDECOD": ["Headache", "Nausea", "Dizziness"],
                "AESEV": ["MILD", "MODERATE", "SEVERE"],
            }
        )

        # This should work without raising an exception
        doc = RTFDocument(df=df, rtf_body={"group_by": ["USUBJID"]})

        # Should be able to encode without errors
        rtf_output = doc.rtf_encode()
        assert isinstance(rtf_output, str)
        assert len(rtf_output) > 0

    def test_empty_dataframe(self):
        """Test validation with empty DataFrame"""
        df = pl.DataFrame(
            {"USUBJID": [], "ASTDY": [], "AEDECOD": []},
            schema={"USUBJID": pl.String, "ASTDY": pl.Int64, "AEDECOD": pl.String},
        )

        # Should not raise exception for empty DataFrame
        result = grouping_service.enhance_group_by(df, group_by=["USUBJID", "ASTDY"])
        assert result.is_empty()

    def test_single_row_dataframe(self):
        """Test validation with single row DataFrame"""
        df = pl.DataFrame(
            {"USUBJID": ["01-701-1015"], "ASTDY": [1], "AEDECOD": ["Headache"]}
        )

        # Should not raise exception for single row
        result = grouping_service.enhance_group_by(df, group_by=["USUBJID", "ASTDY"])
        assert len(result) == 1
        assert result["USUBJID"][0] == "01-701-1015"

    def test_validate_no_overlapping_grouping_vars_success(self):
        """Test that non-overlapping grouping variables pass validation"""
        # Should not raise exception
        grouping_service._validate_no_overlapping_grouping_vars(
            group_by=["USUBJID", "ASTDY"], page_by=["TRTA"], subline_by=["STUDYID"]
        )

    def test_validate_no_overlapping_grouping_vars_with_none(self):
        """Test overlapping validation with None values"""
        # Should not raise exception when some parameters are None
        grouping_service._validate_no_overlapping_grouping_vars(
            group_by=["USUBJID"], page_by=None, subline_by=["TRTA"]
        )
