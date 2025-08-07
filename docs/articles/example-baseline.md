# Baseline characteristics

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

## Imports

```python exec="on" source="above" session="default"
from importlib.resources import files

import polars as pl

import rtflite as rtf
```

## Ingest data

Load data from parquet file:

```python exec="on" source="above" session="default" result="text"
data_path = files("rtflite.data").joinpath("baseline.parquet")
df = pl.read_parquet(data_path)
print(df)
```

Create header data frames:

```python exec="on" source="above" session="default"
header1 = ["", "Placebo", "Drug Low Dose", "Drug High Dose", "Total"]
header2 = ["", "n", "(%)", "n", "(%)", "n", "(%)", "n", "(%)"]
```

## Compose RTF

Create RTF document:

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
doc = rtf.RTFDocument(
    df=df,
    rtf_title=rtf.RTFTitle(
        text=["Demographic and Anthropometric Characteristics", "ITT Subjects"]
    ),
    rtf_column_header=[
        rtf.RTFColumnHeader(text=header1, col_rel_width=[3] + [2] * 4),
        rtf.RTFColumnHeader(
            text=header2,
            col_rel_width=[3] + [1.2, 0.8] * 4,
            border_top=[""] + ["single"] * 8,
            border_left=["single"] + ["single", ""] * 4,
        ),
    ],
    rtf_body=rtf.RTFBody(
        page_by=["var_label"],
        col_rel_width=[3] + [1.2, 0.8] * 4 + [3],
        text_justification=["l"] + ["c"] * 8 + ["l"],
        text_format=[""] * 9 + ["b"],
        border_left=["single"] + ["single", ""] * 4 + ["single"],
        border_top=[""] * 9 + ["single"],
        border_bottom=[""] * 9 + ["single"],
    ),
)

doc.write_rtf("example-baseline-char.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("example-baseline-char.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/example-baseline-char.pdf" style="width:100%; height:400px" type="application/pdf">
