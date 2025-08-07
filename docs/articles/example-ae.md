# AE summary

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

This example shows how to create a simplified adverse events summary table.

## Imports

```python exec="on" source="above" session="default"
from importlib.resources import files

import polars as pl

import rtflite as rtf
```

## Create data for RTF table

Load adverse events data from parquet file:

```python exec="on" source="above" session="default"
data_path = files("rtflite.data").joinpath("adae.parquet")
df = pl.read_parquet(data_path)
```

Process the data to create summary statistics:

```python exec="on" source="above" session="default" result="text"
# First, get the total number of subjects per treatment group
subjects_per_trt = df.group_by("TRTA").agg(pl.col("USUBJID").n_unique().alias("n_subj"))

# Count subjects with each AE by treatment group and calculate percentages
ae_t1 = (
    df.group_by(["TRTA", "AEDECOD"])
    .agg(pl.col("USUBJID").n_unique().alias("n_ae"))
    .join(subjects_per_trt, on="TRTA")
    .with_columns((pl.col("n_ae") / pl.col("n_subj") * 100).round(2).alias("pct"))
    # Only show AE terms with at least 5 subjects in one treatment group
    .filter(pl.col("n_ae") > 5)
)

# Pivot the data to create wide format with n and pct for each treatment
# First, melt the n_ae and pct columns
ae_long = ae_t1.select(["TRTA", "AEDECOD", "n_ae", "pct"]).unpivot(
    index=["TRTA", "AEDECOD"],
    on=["n_ae", "pct"],
    variable_name="var",
    value_name="value",
)

# Create combined column names for pivoting
ae_long = ae_long.with_columns((pl.col("TRTA") + "_" + pl.col("var")).alias("temp"))

# Pivot to wide format
ae_wide = ae_long.pivot(values="value", index="AEDECOD", on="temp").fill_null(0)

# Ensure columns are in the correct order
col_order = [
    "AEDECOD",
    "Placebo_n_ae",
    "Placebo_pct",
    "Xanomeline High Dose_n_ae",
    "Xanomeline High Dose_pct",
    "Xanomeline Low Dose_n_ae",
    "Xanomeline Low Dose_pct",
]

ae_t1_final = (
    ae_wide.select(col_order)
    .with_columns(pl.col(pl.Float64).cast(pl.String))
    .sort("AEDECOD")
)

print(ae_t1_final.head(10))
```

## Define table format

Prepare the data for RTF output:

```python exec="on" source="above" session="default"
# Define column headers
header1 = [" ", "Placebo", "Drug High Dose", "Drug Low Dose"]
header2 = [" ", "n", "(%)", "n", "(%)", "n", "(%)"]

# Create RTF components
col_header1 = rtf.RTFColumnHeader(
    text=header1, col_rel_width=[4, 2, 2, 2], text_justification=["l", "c", "c", "c"]
)

col_header2 = rtf.RTFColumnHeader(
    text=header2,
    col_rel_width=[4] + [1] * 6,
    text_justification=["l", "c", "c", "c", "c", "c", "c"],
    border_top=[""] + ["single"] * 6,
    border_left=["single"] + ["single", ""] * 3,
)

# Create table body
tbl_body = rtf.RTFBody(
    col_rel_width=[4] + [1] * 6,
    text_justification=["l"] + ["c"] * 6,
    border_left=["single"] + ["single", ""] * 3,
)
```

Create the RTF document with formatting:

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Create RTF document
doc = rtf.RTFDocument(
    df=ae_t1_final,
    rtf_title=rtf.RTFTitle(
        text=[
            "Analysis of Subjects With Specific Adverse Events",
            "(Incidence > 5 Subjects in One or More Treatment Groups)",
            "ASaT",
        ]
    ),
    rtf_column_header=[col_header1, col_header2],
    rtf_body=tbl_body,
    rtf_footnote=rtf.RTFFootnote(
        text=["{^\\dagger}This is footnote 1", "This is footnote 2"],
        text_convert=[[True]],  # Enable LaTeX symbol conversion
    ),
    rtf_source=rtf.RTFSource(text=["Source: xxx"]),
)

# Output .rtf file
doc.write_rtf("example-ae-summary.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("example-ae-summary.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/example-ae-summary.pdf" style="width:100%; height:400px" type="application/pdf">
