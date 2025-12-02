# Assemble

This article demonstrates how to assemble multiple RTF files into a single RTF or DOCX file using rtflite.

```python exec="on" session="default"
from rtflite import LibreOfficeConverter

converter = LibreOfficeConverter()
```

```python exec="on" source="above" session="default"
from pathlib import Path
from rtflite import assemble_rtf, assemble_docx
```

# Define input files

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
input_files = [
    "example-ae-summary.rtf",
    "example-efficacy.rtf",
]
```

# Assemble into RTF

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
assemble_rtf(input_files, "combined-rtf.rtf")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined-rtf.rtf", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined-rtf.pdf" style="width:100%; height:400px" type="application/pdf">

# Assemble into DOCX

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
assemble_docx(input_files, "combined-docx.docx")
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined-docx.docx", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined-docx.pdf" style="width:100%; height:400px" type="application/pdf">

# Assemble into DOCX with mixed orientation (portrait, landscape)

```python exec="on" source="above" session="default" workdir="docs/articles/rtf/"
assemble_docx(
    input_files,
    "combined-mixed.docx",
    landscape=[False, True]
)
```

```python exec="on" session="default" workdir="docs/articles/rtf/"
converter.convert("combined-mixed.docx", output_dir="../pdf/", format="pdf", overwrite=True)
```

<embed src="../pdf/combined-mixed.pdf" style="width:100%; height:400px" type="application/pdf">
