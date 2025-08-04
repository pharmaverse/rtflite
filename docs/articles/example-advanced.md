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
```

## Step 2: Demonstrate single column group_by

Start with a simple example using a single column for grouping:

``` python
# Create RTF document with single column group_by
doc_single = rtf.RTFDocument(
    df=ae_t1.select(['USUBJID', 'AEDECD1', 'AESEV', 'AESER']).head(15).sort(['USUBJID', 'AEDECD1']),
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
        group_by=['USUBJID', 'AEDECD1'],  # Group by subject ID and adverse event
        col_rel_width=[3, 4, 2, 2],
        text_justification=['l', 'l', 'c', 'c'],
    ),
    rtf_footnote=rtf.RTFFootnote(
        text="Note: Subject ID and Adverse Event values are shown only once per group for better readability",
        text_convert=False,
    ),
)

# Generate the RTF file
doc_single.write_rtf("../rtf/example_advance_single.rtf")
```

## Step 3: Multi-page example with group context

Demonstrate how group_by works with pagination, including context
restoration:

``` python
# Create larger dataset for multi-page demonstration
ae_large = ae_t1.head(100)  # Use more rows to trigger pagination

doc_multipage = rtf.RTFDocument(
    df=ae_large.select(['USUBJID', 'ASTDY', 'AEDECD1', 'AESEV', 'AESER']).sort(['USUBJID', 'ASTDY']),
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

## Step 6: Combining group_by with new_page (treatment separation)

Demonstrate the powerful combination of `group_by` and `new_page` for
clinical trial reporting:

``` python
# Create treatment-separated document with group_by within each page
# Filter data to have multiple treatment groups
ae_with_treatments = (
    ae_t1.
    filter(pl.col('TRTA').is_in(['Placebo', 'Xanomeline High Dose'])).
    select(['TRTA', 'USUBJID', 'ASTDY', 'AEDECD1', 'AESEV']).
    head(40).
    sort(['TRTA', 'USUBJID', 'ASTDY'])
)

doc_treatment_separated = rtf.RTFDocument(
    df=ae_with_treatments,
    rtf_title=rtf.RTFTitle(
        text=["Adverse Events Listing", "Example 5: group_by + new_page (Treatment Separation)"],
        text_convert=False,
    ),
    rtf_column_header=rtf.RTFColumnHeader(
        text=["Treatment", "Subject ID", "Study Day", "Adverse Event", "Severity"],
        text_format="b",
        text_justification=["l", "l", "c", "l", "c"],
    ),
    rtf_body=rtf.RTFBody(
        page_by=["TRTA"],           # Separate pages by treatment
        new_page=True,              # Force new page for each treatment
        group_by=["TRTA", "USUBJID", "ASTDY"],  # Suppress duplicates within each treatment page
        col_rel_width=[2, 3, 1, 4, 2],
        text_justification=["l", "l", "c", "l", "c"],
        pageby_header=True,         # Repeat headers on each treatment page
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Example of group_by + new_page combination:",
            "- Each treatment group gets its own page(s) (new_page=True)",
            "- Within each treatment, USUBJID and ASTDY are suppressed when duplicate (group_by)",
            "- Headers are repeated on each treatment page (pageby_header=True)"
        ],
        text_convert=False,
    ),
)

# Generate the RTF file
doc_treatment_separated.write_rtf("../rtf/example_advance_group_newpage.rtf")
```
