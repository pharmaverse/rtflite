# Figures

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

This example shows how to create RTF documents with embedded figures using rtflite.

## Imports

```python exec="on" source="above" session="default"
from importlib.resources import files

# Set matplotlib backend for headless environments (GitHub Actions)
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import polars as pl

import rtflite as rtf
```

## Create age histogram by treatment

```python exec="on" source="above" session="default"
# Load ADSL data
data_path = files("rtflite.data").joinpath("adsl.parquet")
df = pl.read_parquet(data_path)
```

```python exec="on" source="above" session="default" workdir="docs/articles/images/"
# Create multiple age group histograms for different treatments
treatment_groups = df["TRT01A"].unique().sort()

for i, treatment in enumerate(treatment_groups):
    treatment_df = df.filter(pl.col("TRT01A") == treatment)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(6, 4))

    # Plot histogram
    ages = treatment_df["AGE"].to_list()
    ax.hist(ages, bins=15, color="#70AD47", edgecolor="black", alpha=0.7)

    # Set labels
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("Number of Subjects")

    # Apply minimal theme styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)
    ax.set_axisbelow(True)

    # Save figure
    plt.savefig(
        f"../images/age-histogram-treatment-{i}.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()
```

## Single figure

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
doc_age = rtf.RTFDocument(
    rtf_title=rtf.RTFTitle(text=["Study Population Demographics", "Age Distribution"]),
    rtf_figure=rtf.RTFFigure(
        figures="../images/age-histogram-treatment-0.png", fig_width=6, fig_height=4
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=["Analysis population: All randomized subjects (N=254)"],
        as_table=False,  # Required when using RTFFigure
    ),
    rtf_source=rtf.RTFSource(text=["Source: ADSL dataset"]),
)

# Write RTF
doc_age.write_rtf("example-figure-age.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("example-figure-age.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/example-figure-age.pdf" style="width:100%; height:400px" type="application/pdf">

## Multiple figures with elements on every page

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
# Create RTF document with multiple figures and elements on every page
doc_multi_page = rtf.RTFDocument(
    rtf_page=rtf.RTFPage(
        page_title="all",  # Show title on all pages
        page_footnote="all",  # Show footnote on all pages
        page_source="all",  # Show source on all pages
    ),
    rtf_title=rtf.RTFTitle(
        text=["Clinical Study XYZ-123", "Age Distribution by Treatment Group"]
    ),
    rtf_figure=rtf.RTFFigure(
        figures=[
            "../images/age-histogram-treatment-0.png",
            "../images/age-histogram-treatment-1.png",
            "../images/age-histogram-treatment-2.png",
        ],
        fig_width=6,
        fig_height=4,
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=[
            "Note: Each histogram represents age distribution for one treatment group"
        ],
        as_table=False,  # Required when using RTFFigure
    ),
    rtf_source=rtf.RTFSource(
        text=["Source: ADSL dataset, Clinical Database Lock Date: 2023-12-31"]
    ),
)

# Write RTF
doc_multi_page.write_rtf("example-figure-multipage.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("example-figure-multipage.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/example-figure-multipage.pdf" style="width:100%; height:400px" type="application/pdf">
