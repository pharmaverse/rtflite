#!/usr/bin/env Rscript
# Regenerate r2rtf outputs for pagination comparison tests with correct nrow behavior
# This script uses the correct understanding: nrow includes ALL rows (headers, data, footnotes, sources)

library(r2rtf)
library(dplyr)

# Helper function to convert rtf_encode output to string
rtf_to_string <- function(rtf_list) {
  paste(rtf_list$start, rtf_list$body, rtf_list$end, sep = "")
}

# Create test data to match Python tests
test_data <- data.frame(
  Col1 = c("Row1", "Row2", "Row3", "Row4", "Row5", "Row6"),
  Col2 = c("A", "B", "C", "D", "E", "F"),
  stringsAsFactors = FALSE
)

small_data <- data.frame(
  Col1 = c("Row1", "Row2"),
  Col2 = c("A", "B")
)

# Create output directory
dir.create("tests/fixtures/r_outputs", showWarnings = FALSE, recursive = TRUE)

# Test 1: Basic pagination with headers
# nrow=2 with headers means: 1 header + 1 data row per page = 6 pages
cat("Generating test_pagination_basic_with_headers.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%  # 2 total rows per page
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_basic_with_headers.txt")

# Test 2: No headers  
# nrow=2 with no headers means: 2 data rows per page = 3 pages
cat("Generating test_pagination_no_headers.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%  # 2 total rows per page
  rtf_body(
    col_rel_width = c(1, 1),
    as_colheader = FALSE
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_no_headers.txt")

# Test 3: With footnote
# nrow=2 with headers and footnote - need to see r2rtf behavior
cat("Generating test_pagination_with_footnote.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_footnote(
    footnote = "Note: This is a test footnote for pagination"
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_with_footnote.txt")

# Test 4: With source
cat("Generating test_pagination_with_source.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_source(
    source = "Source: Test data for pagination"
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_with_source.txt")

# Test 5: All components
cat("Generating test_pagination_all_components.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_footnote(
    footnote = "Note: This is a test footnote"
  ) %>%
  rtf_source(
    source = "Source: Test data"
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_all_components.txt")

# Test 6: Border styles - CRITICAL TEST
cat("Generating test_pagination_border_styles.txt\n")
rtf_content <- test_data %>%
  rtf_page(
    orientation = "portrait", 
    nrow = 2,
    border_first = "double",
    border_last = "double"
  ) %>%
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1),
    border_first = "single",
    border_last = "single"
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_border_styles.txt")

# Test 7: Single page
cat("Generating test_pagination_single_page.txt\n")
rtf_content <- small_data %>%
  rtf_page(orientation = "portrait", nrow = 10) %>%  # More than needed
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_footnote(
    footnote = "Single page test"
  ) %>%
  rtf_source(
    source = "Source: Small dataset"
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_single_page.txt")

# Test 8: Landscape
cat("Generating test_pagination_landscape.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "landscape", nrow = 2) %>%
  rtf_colheader(
    colheader = "Column 1 | Column 2",
    col_rel_width = c(1, 1)
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_landscape.txt")

# Test 9: Multirow headers
cat("Generating test_pagination_multirow_headers.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%
  rtf_colheader(
    colheader = "Main Header | Main Header",
    col_rel_width = c(1, 1),
    border_bottom = ""
  ) %>%
  rtf_colheader(
    colheader = "Column 1 | Column 2", 
    col_rel_width = c(1, 1),
    border_top = ""
  ) %>%
  rtf_body(
    col_rel_width = c(1, 1)
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_multirow_headers.txt")

# Test 10: No headers with footnote and source
cat("Generating test_pagination_no_headers_footnote_source.txt\n")
rtf_content <- test_data %>%
  rtf_page(orientation = "portrait", nrow = 2) %>%
  rtf_body(
    col_rel_width = c(1, 1),
    as_colheader = FALSE
  ) %>%
  rtf_footnote(
    footnote = "Note: No column headers test"
  ) %>%
  rtf_source(
    source = "Source: Test without headers"
  ) %>%
  rtf_encode() %>%
  rtf_to_string()
cat(rtf_content, file = "tests/fixtures/r_outputs/test_pagination_no_headers_footnote_source.txt")

cat("All R outputs regenerated successfully!\n")
cat("Files are saved in tests/fixtures/r_outputs/\n")
cat("You can now run the Python tests with updated R output comparisons.\n")