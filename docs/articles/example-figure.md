# Figure Embedding

rtflite supports embedding images (figures) in RTF documents, similar to the r2rtf package's `rtf_figure()` functionality. This feature allows you to include PNG, JPEG, and EMF images directly in your RTF reports.

## Supported Features

- **Multiple image formats**: PNG, JPEG, EMF
- **Flexible positioning**: Before or after table content
- **Custom sizing**: Individual dimensions for each figure
- **Alignment options**: Left, center, right alignment
- **Multiple figures**: Support for multiple images in a single document

## Basic Usage

### Reading Images

Use `rtf_read_figure()` to read image files:

```python
from rtflite import rtf_read_figure

# Single image
figures, formats = rtf_read_figure("chart.png")

# Multiple images
figures, formats = rtf_read_figure([
    "chart1.png", 
    "chart2.jpg", 
    "diagram.png"
])
```

### Creating RTFFigure Component

```python
from rtflite import RTFFigure

figure = RTFFigure(
    figures=figures,
    figure_formats=formats,
    fig_height=4.0,          # Height in inches
    fig_width=6.0,           # Width in inches
    fig_align="center",      # Alignment: "left", "center", "right"
    fig_pos="after"          # Position: "before" or "after" table
)
```

## Examples

### Single Figure After Table

```python
import polars as pl
from rtflite import RTFDocument, RTFTitle, RTFFigure, rtf_read_figure

# Sample data
data = pl.DataFrame({
    "Treatment": ["Placebo", "Drug A", "Drug B"],
    "Response Rate": ["45.0%", "62.3%", "55.0%"]
})

# Read image
figures, formats = rtf_read_figure("efficacy_chart.png")

# Create document
doc = RTFDocument(
    df=data,
    rtf_title=RTFTitle(text="Treatment Efficacy Results"),
    rtf_figure=RTFFigure(
        figures=figures,
        figure_formats=formats,
        fig_height=3.5,
        fig_width=5.0,
        fig_pos="after"
    )
)

doc.write_rtf("efficacy_report.rtf")
```

**Output**: [figure_single.rtf](rtf/figure_single.rtf) | [PDF](pdf/figure_single.pdf)

### Multiple Figures

```python
# Read multiple images
figures, formats = rtf_read_figure([
    "chart1.png",
    "chart2.jpg", 
    "diagram.png"
])

# Different sizes for each figure
doc = RTFDocument(
    df=data,
    rtf_figure=RTFFigure(
        figures=figures,
        figure_formats=formats,
        fig_height=[3.0, 3.0, 2.0],  # Individual heights
        fig_width=[4.5, 4.5, 6.0],   # Individual widths
        fig_pos="after"
    )
)
```

**Output**: [figure_multiple.rtf](rtf/figure_multiple.rtf) | [PDF](pdf/figure_multiple.pdf)

### Figure Before Table

```python
doc = RTFDocument(
    df=data,
    rtf_title=RTFTitle(text="Study Protocol"),
    rtf_figure=RTFFigure(
        figures=figures,
        figure_formats=formats,
        fig_height=2.5,
        fig_width=7.0,
        fig_pos="before"  # Position before table
    )
)
```

**Output**: [figure_before.rtf](rtf/figure_before.rtf) | [PDF](pdf/figure_before.pdf)

### Landscape with Figure

```python
from rtflite import RTFPage

doc = RTFDocument(
    df=data,
    rtf_page=RTFPage(orientation="landscape"),
    rtf_figure=RTFFigure(
        figures=figures,
        figure_formats=formats,
        fig_height=4.0,
        fig_width=8.0  # Wider for landscape
    )
)
```

**Output**: [figure_landscape.rtf](rtf/figure_landscape.rtf) | [PDF](pdf/figure_landscape.pdf)

## Technical Details

### Image Processing

- Images are automatically converted to hexadecimal format for RTF embedding
- Actual pixel dimensions are extracted from PNG and JPEG headers
- Display dimensions are specified in twips (1440 twips = 1 inch)

### RTF Syntax Generated

```rtf
{\pict\pngblip\picw600\pich400\picwgoal7200\pichgoal5040 89504e470d0a1a0a...}
```

- `\pict` - Picture group indicator
- `\pngblip`/`\jpegblip` - Image format
- `\picw\pich` - Actual pixel dimensions
- `\picwgoal\pichgoal` - Display dimensions in twips

### Compatibility

- Works with Microsoft Word, LibreOffice Writer
- Successfully converts to PDF via LibreOffice
- Self-contained RTF files (no external image dependencies)

## Migration from r2rtf

**r2rtf:**
```r
filename %>%
  rtf_read_figure() %>%
  rtf_figure(fig_height = 4.0, fig_width = 6.0) %>%
  rtf_encode(doc_type = "figure") %>%
  write_rtf("output.rtf")
```

**rtflite:**
```python
figures, formats = rtf_read_figure(filename)
doc = RTFDocument(
    df=data,
    rtf_figure=RTFFigure(
        figures=figures,
        figure_formats=formats,
        fig_height=4.0,
        fig_width=6.0
    )
)
doc.write_rtf("output.rtf")
```