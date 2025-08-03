"""Example demonstrating RTF figure embedding functionality.

This example shows how to embed PNG and JPEG images in RTF documents
using rtflite's figure functionality.
"""

import polars as pl
from pathlib import Path
from rtflite import (
    RTFDocument, 
    RTFTitle, 
    RTFBody,
    RTFPage,
    RTFFigure,
    RTFFootnote,
    RTFSource,
    rtf_read_figure
)

# Create sample efficacy data
efficacy_data = pl.DataFrame({
    "Treatment": ["Placebo", "Drug A", "Drug B"],
    "N": [100, 101, 99],
    "Response Rate": ["45.0%", "62.3%", "55.0%"],
    "95% CI": ["(35.0, 55.0)", "(52.3, 72.3)", "(44.9, 65.1)"]
})

# Create sample time course data for landscape example
timecourse_data = pl.DataFrame({
    "Treatment": ["Placebo", "Drug A", "Drug B", "Drug C"],
    "N": [100, 101, 99, 102],
    "Baseline": ["5.2 (1.1)", "5.3 (1.2)", "5.1 (1.0)", "5.4 (1.3)"],
    "Week 4": ["5.0 (1.2)", "4.2 (1.1)", "4.5 (1.1)", "4.0 (1.0)"],
    "Week 8": ["4.8 (1.3)", "3.5 (1.0)", "3.9 (1.2)", "3.2 (0.9)"],
    "Week 12": ["4.7 (1.2)", "3.0 (0.9)", "3.5 (1.1)", "2.8 (0.8)"],
    "Change": ["-0.5", "-2.3", "-1.6", "-2.6"]
})

def example_single_figure():
    """Single figure after table example."""
    figures, formats = rtf_read_figure("docs/assets/images/figure_examples/efficacy_chart.png")
    
    doc = RTFDocument(
        df=efficacy_data,
        rtf_title=RTFTitle(text="Table 1: Treatment Efficacy Results"),
        rtf_body=RTFBody(
            col_rel_width=[2, 1, 2, 3],
            text_justification="l"
        ),
        rtf_figure=RTFFigure(
            figures=figures,
            figure_formats=formats,
            fig_height=3.5,
            fig_width=5.0,
            fig_align="center",
            fig_pos="after"
        ),
        rtf_footnote=RTFFootnote(text="CI = Confidence Interval"),
        rtf_source=RTFSource(text="Figure 1: Treatment efficacy by group")
    )
    
    doc.write_rtf("docs/articles/rtf/figure_single.rtf")
    return doc

def example_multiple_figures():
    """Multiple figures with different formats."""
    figures, formats = rtf_read_figure([
        "docs/assets/images/figure_examples/efficacy_chart.png",
        "docs/assets/images/figure_examples/response_graph.jpg",
        "docs/assets/images/figure_examples/study_design.png"
    ])
    
    doc = RTFDocument(
        df=efficacy_data,
        rtf_title=RTFTitle(text="Table 2: Clinical Trial Results Summary"),
        rtf_figure=RTFFigure(
            figures=figures,
            figure_formats=formats,
            fig_height=[3.0, 3.0, 2.0],
            fig_width=[4.5, 4.5, 6.0],
            fig_align="center",
            fig_pos="after"
        ),
        rtf_source=RTFSource(text=[
            "Figure 1: Treatment efficacy comparison",
            "Figure 2: Response over time", 
            "Figure 3: Study design overview"
        ])
    )
    
    doc.write_rtf("docs/articles/rtf/figure_multiple.rtf")
    return doc

def example_figure_before():
    """Figure positioned before table."""
    figures, formats = rtf_read_figure("docs/assets/images/figure_examples/study_design.png")
    
    doc = RTFDocument(
        df=efficacy_data,
        rtf_title=RTFTitle(text="Clinical Trial Protocol Summary"),
        rtf_figure=RTFFigure(
            figures=figures,
            figure_formats=formats,
            fig_height=2.5,
            fig_width=7.0,
            fig_align="center",
            fig_pos="before"
        ),
        rtf_body=RTFBody(
            col_rel_width=[2, 1, 2, 3],
            border_top="single",
            border_bottom="single"
        )
    )
    
    doc.write_rtf("docs/articles/rtf/figure_before.rtf")
    return doc

def example_landscape_figure():
    """Landscape orientation with figure."""
    figures, formats = rtf_read_figure("docs/assets/images/figure_examples/response_graph.png")
    
    doc = RTFDocument(
        df=timecourse_data,
        rtf_page=RTFPage(orientation="landscape"),
        rtf_title=RTFTitle(text="Table 3: Patient Response Over Time (Mean (SD))"),
        rtf_body=RTFBody(
            col_rel_width=[2, 1, 2, 2, 2, 2, 2]
        ),
        rtf_figure=RTFFigure(
            figures=figures,
            figure_formats=formats,
            fig_height=4.0,
            fig_width=8.0,
            fig_align="center",
            fig_pos="after"
        ),
        rtf_source=RTFSource(text="Figure: Mean response values over 12-week treatment period")
    )
    
    doc.write_rtf("docs/articles/rtf/figure_landscape.rtf")
    return doc

if __name__ == "__main__":
    # Create output directories
    Path("docs/articles/rtf").mkdir(parents=True, exist_ok=True)
    Path("docs/articles/pdf").mkdir(parents=True, exist_ok=True)
    
    # Generate examples
    example_single_figure()
    example_multiple_figures() 
    example_figure_before()
    example_landscape_figure()
    
    print("Figure examples generated in docs/articles/rtf/")