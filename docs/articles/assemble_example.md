# Assemble

This example demonstrates how to assemble multiple RTF files into a single RTF or DOCX file using `rtflite`.

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

```python exec="on" source="above" session="default"
from pathlib import Path
from rtflite import assemble_rtf, assemble_docx
```

# Define input files

```python exec="on" source="above" session="default"
docs_dir = Path("./rtf")
input_files = [
    str(docs_dir / "example-ae-summary.rtf"),
    str(docs_dir / "example-efficacy.rtf"),
]
```

# Assemble into RTF

```python exec="on" session="default" workdir="docs/articles/rtf/"
assemble_rtf(input_files, "combined.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined.pdf" style="width:100%; height:400px" type="application/pdf">

# Assemble into DOCX

```python exec="on" session="default" workdir="docs/articles/rtf/"
assemble_docx(input_files, "combined.docx")
```

# Assemble into DOCX with mixed orientation (Portrait, Landscape)

```python exec="on" session="default" workdir="docs/articles/rtf/"
assemble_docx(
    input_files,
    "combined_mixed.docx",
    landscape=[False, True]
)
```
