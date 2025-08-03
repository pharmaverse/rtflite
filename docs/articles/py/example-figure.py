from importlib.resources import files
import polars as pl
from plotnine import *
import rtflite as rtf

data_path = files("rtflite.data").joinpath("adsl.parquet")
df = pl.read_parquet(data_path)

age_plot = (
    ggplot(df, aes(x="AGE"))
    + geom_histogram(bins=20, fill="#4472C4", color="black", alpha=0.7)
    + labs(x="Age (years)", y="Number of Subjects")
    + theme_minimal()
    + theme(figure_size=(8, 6))
)

age_plot.save("../image/age_histogram.png", dpi=300, width=8, height=6)

sex_counts = df.group_by("SEX").agg(pl.len()).sort("SEX")

sex_plot = (
    ggplot(sex_counts, aes(x="SEX", y="len"))
    + geom_col(fill="#4472C4", color="black", alpha=0.7)
    + labs(x="Sex", y="Number of Subjects")
    + theme_minimal()
    + theme(figure_size=(6, 6))
)

sex_plot.save("../image/sex_histogram.png", dpi=300, width=6, height=6)

doc_age = rtf.RTFDocument(
    rtf_title=rtf.RTFTitle(text=["Study Population Demographics", "Age Distribution"]),
    rtf_figure=rtf.RTFFigure(
        figures="../image/age_histogram.png", fig_width=6, fig_height=4
    ),
    rtf_footnote=rtf.RTFFootnote(
        text=["Analysis population: All randomized subjects (N=254)"]
    ),
    rtf_source=rtf.RTFSource(text=["Source: ADSL dataset"]),
)

doc_both = rtf.RTFDocument(
    rtf_title=rtf.RTFTitle(
        text=["Study Population Demographics", "Age and Sex Distribution"]
    ),
    rtf_figure=rtf.RTFFigure(
        figures=["../image/age_histogram.png", "../image/sex_histogram.png"],
        fig_width=6,
        fig_height=4,
    ),
    rtf_footnote=rtf.RTFFootnote(text=["A footnote"]),
    rtf_source=rtf.RTFSource(text=["Source: ADSL dataset analysis"]),
)
