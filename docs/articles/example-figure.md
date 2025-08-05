# Figures


<!-- `.md` and `.py` files are generated from the `.qmd` file. Please edit that file. -->

This example shows how to create RTF documents with embedded figures
using rtflite.

## Imports

``` python
from importlib.resources import files

import polars as pl
from plotnine import ggplot, aes, geom_histogram, labs, theme_minimal, theme

import rtflite as rtf
```

## Create Age Histogram by Treatment

``` python
# Load ADSL data
data_path = files("rtflite.data").joinpath("adsl.parquet")
df = pl.read_parquet(data_path)
```

``` python
# Create multiple age group histograms for different treatments
treatment_groups = df["TRT01A"].unique().sort()

for i, treatment in enumerate(treatment_groups):
    treatment_df = df.filter(pl.col("TRT01A") == treatment)

    treatment_plot = (
        ggplot(treatment_df, aes(x="AGE"))
        + geom_histogram(bins=15, fill="#70AD47", color="black", alpha=0.7)
        + labs(x="Age (years)", y="Number of Subjects")
        + theme_minimal()
        + theme(figure_size=(6, 4))
    )

    treatment_plot.save(
        f"../image/age_histogram_treatment_{i}.png",
        dpi=300,
        width=6,
        height=4,
        verbose=False,
    )
```

## Single Figure

``` python
doc_age = rtf.RTFDocument(
    rtf_title=rtf.RTFTitle(text=["Study Population Demographics", "Age Distribution"]),
    rtf_figure=rtf.RTFFigure(
        figures="../image/age_histogram_treatment_0.png", fig_width=6, fig_height=4
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=["Analysis population: All randomized subjects (N=254)"],
        as_table=False,  # Required when using RTFFigure
    ),
    rtf_source=rtf.RTFSource(text=["Source: ADSL dataset"]),
)

# Write RTF
doc_age.write_rtf("../rtf/example_figure_age.rtf")
```

<embed src="../pdf/example_figure_age.pdf" style="width:100%; height:400px" type="application/pdf">

## Multiple Figures with Elements on Every Page

``` python
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
            "../image/age_histogram_treatment_0.png",
            "../image/age_histogram_treatment_1.png",
            "../image/age_histogram_treatment_2.png",
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
doc_multi_page.write_rtf("../rtf/example_figure_multipage.rtf")
```

<embed src="../pdf/example_figure_multipage.pdf" style="width:100%; height:400px" type="application/pdf">
