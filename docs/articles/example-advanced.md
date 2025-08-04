# Advanced Features: group_by


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

This example demonstrates advanced table formatting features in rtflite,
focusing on the `group_by` functionality that provides enhanced
readability by suppressing duplicate values within groups.

## Overview

The `group_by` feature is particularly useful for clinical trial
listings where multiple rows belong to the same subject or treatment
group. Instead of repeating identical values in every row, `group_by`
displays the value only once per group, leaving subsequent rows blank
for better visual organization.

Key benefits: - **Improved readability**: Reduces visual clutter by
eliminating redundant information - **Clinical standards compliance**:
Follows pharmaceutical industry conventions for listing formats -
**Hierarchical grouping**: Supports multiple columns with nested group
relationships

## Imports

``` python
from importlib.resources import files
import polars as pl
import rtflite as rtf
```

## Step 1: Load and prepare adverse events data

Load the adverse events dataset and create a subset for demonstration:

``` python
# Load adverse events data from parquet file
data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)

# Take a subset of the data for this example (rows 200-260)
ae_subset = df.slice(200, 60)

# Display the raw data structure
print("Raw adverse events data:")
print(ae_subset.select(['USUBJID', 'TRTA', 'AEDECOD', 'AESEV', 'ASTDY']).head(10))
```

Create additional columns for a more comprehensive listing format:

``` python
# Create formatted columns for the listing
ae_t1 = ae_subset.with_columns([
    # Create subline header with study and site information
    (pl.lit('Trial Number: ') + pl.col('STUDYID') + pl.lit(', Site Number: ') + pl.col('SITEID').cast(pl.String)).alias('SUBLINEBY'),
    
    # Create subject line with demographic information
    (pl.lit('Subject ID = ') + pl.col('USUBJID') + 
     pl.lit(', Gender = ') + pl.col('SEX') + 
     pl.lit(', Race = ') + pl.col('RACE') + 
     pl.lit(', AGE = ') + pl.col('AGE').cast(pl.String) + pl.lit(' Years') + 
     pl.lit(', TRT = ') + pl.col('TRTA')).alias('SUBJLINE'),
    
    # Format adverse event term (title case)
    pl.col('AEDECOD').str.to_titlecase().alias('AEDECD1'),
    
    # Create duration string
    (pl.col('ADURN').cast(pl.String) + pl.lit(' ') + pl.col('ADURU')).alias('DUR')
]).select([
    'SUBLINEBY', 'TRTA', 'SUBJLINE', 'USUBJID', 'ASTDY', 
    'AEDECD1', 'DUR', 'AESEV', 'AESER', 'AEREL', 'AEACN', 'AEOUT'
])

# Sort by key variables to group related events together
ae_t1 = ae_t1.sort(['SUBLINEBY', 'TRTA', 'SUBJLINE', 'USUBJID', 'ASTDY'])

print("Processed adverse events data:")
print(ae_t1.select(['USUBJID', 'ASTDY', 'AEDECD1', 'AESEV']).head(10))
```

## Step 2: Demonstrate single column group_by

Start with a simple example using a single column for grouping:

``` python
# Create RTF document with single column group_by
doc_single = rtf.RTFDocument(
    df=ae_t1.select(['USUBJID', 'AEDECD1', 'AESEV', 'AESER']).head(15),
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 1: Single Column group_by"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        group_by=['USUBJID', "AEDECD1"],  # Group by subject ID only
        col_rel_width=[3, 4, 2, 2],
        text_justification=['l', 'l', 'c', 'c'],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Subject ID values are shown only once per subject for better readability",
        text_convert=False,
    ),
)

# Generate the RTF file
doc_single.write_rtf("../rtf/example_advance_single.rtf")
```

## Step 3: Demonstrate hierarchical group_by

Show the power of multi-column grouping with hierarchical value
suppression:

``` python
# Create RTF document with hierarchical group_by
doc_group = rtf.RTFDocument(
    df=ae_t1.select(['USUBJID', 'ASTDY', 'AEDECD1', 'AESEV', 'AESER']),
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 2: Hierarchical group_by Usage"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Study Day", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        group_by=['USUBJID', 'ASTDY'],  # Hierarchical grouping
        col_rel_width=[3, 1, 4, 2, 2],
        text_justification=['l', 'c', 'l', 'c', 'c'],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Note: group_by feature provides hierarchical value suppression:",
            "• Subject ID: shown once per subject",
            "• Study Day: shown once per subject-day combination",
            "• Blank cells indicate values suppressed for readability"
        ],
        text_convert=False,
    ),
)

# Generate the RTF file
doc_group.write_rtf("../rtf/example_advance_group.rtf")
```

## Step 4: Multi-page example with group context

Demonstrate how group_by works with pagination, including context
restoration:

``` python
# Create larger dataset for multi-page demonstration
ae_large = ae_t1.head(100)  # Use more rows to trigger pagination

doc_multipage = rtf.RTFDocument(
    df=ae_large.select(['USUBJID', 'ASTDY', 'AEDECD1', 'AESEV', 'AESER']),
    rtf_page=rtf.RTFPage(nrow=25),  # Force pagination
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 3: Multi-page with group_by"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Study Day", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        group_by=['USUBJID', 'ASTDY'],
        col_rel_width=[3, 1, 4, 2, 2],
        text_justification=['l', 'c', 'l', 'c', 'c'],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Note: In multi-page listings, group context is automatically restored",
            "at the beginning of each new page for better readability."
        ],
        text_convert=False,
    ),
)

# Generate the RTF file
doc_multipage.write_rtf("../rtf/example_advance_multipage.rtf")
```

## Step 5: Comparison without group_by

For comparison, create the same table without group_by to show the
difference:

``` python
# Create the same table without group_by for comparison
doc_no_group = rtf.RTFDocument(
    df=ae_t1.select(['USUBJID', 'ASTDY', 'AEDECD1', 'AESEV', 'AESER']).head(20),
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 4: Without group_by (for comparison)"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Subject ID", "Study Day", "Adverse Event", "Severity", "Serious"],
        text_format="b",
        text_justification=["l", "c", "l", "c", "c"],
    ),
    rtf_body=rtf.RTFBody(
        # No group_by specified - all values will be displayed
        col_rel_width=[3, 1, 4, 2, 2],
        text_justification=['l', 'c', 'l', 'c', 'c'],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Without group_by, all values are displayed in every row",
        text_convert=False,
    ),
)

# Generate the RTF file
doc_no_group.write_rtf("../rtf/example_advance_no_group.rtf")
```

## Summary

The `group_by` feature in rtflite provides:

1.  **Single column grouping**: Suppress duplicates in one column (e.g.,
    Subject ID)
2.  **Hierarchical grouping**: Multi-level value suppression with nested
    relationships
3.  **Pagination support**: Automatic context restoration at page
    boundaries
4.  **Clinical compliance**: Follows pharmaceutical industry standards
    for listing formats

This feature is particularly valuable for: - Subject-level adverse event
listings - Medical history summaries - Concomitant medication listings -
Any tabular data with natural grouping relationships

The group_by functionality enhances readability while maintaining all
the original data integrity, making it an essential tool for creating
professional clinical trial documentation.
