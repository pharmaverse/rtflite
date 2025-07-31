# Converter setup

rtflite can convert RTF documents to PDF using LibreOffice.
This guide helps you set up LibreOffice for PDF conversion functionality.

## Install LibreOffice

On macOS (using Homebrew):

```bash
brew install --cask libreoffice
```

On Ubuntu/Debian:

```bash
sudo apt-get install libreoffice
```

On Windows (using Chocolatey):

```bash
choco install libreoffice
```

After installation, restart your shell to ensure `PATH` updates are loaded
so that rtflite can find LibreOffice.

## Using the converter

Once LibreOffice is installed, you can convert RTF files to PDF in your code:

```python
import rtflite as rtf

# Create your RTF document
doc = rtf.RTFDocument(df=df, ...)
doc.write_rtf("output.rtf")

# Convert to PDF
try:
    converter = rtf.LibreOfficeConverter()
    converter.convert(
        input_files="output.rtf",
        output_dir=".",
        format="pdf",
        overwrite=True
    )
    print("PDF created successfully!")
except FileNotFoundError:
    print("LibreOffice not found. Please install it for PDF conversion.")
```

### Custom installation paths

If LibreOffice is installed in a non-standard location, you can specify the path:

```python
converter = rtf.LibreOfficeConverter(
    executable_path="/custom/path/to/soffice"
)
```

### Supported output formats

Besides PDF, LibreOffice can convert RTF to:

- `docx` - Microsoft Word format
- `html` - HTML format
- `odt` - OpenDocument Text format

Example:
```python
converter.convert(input_files="output.rtf", output_dir=".", format="docx")
```

### Batch conversion

Convert multiple RTF files at once:

```python
files = ["file1.rtf", "file2.rtf", "file3.rtf"]
converter = rtf.LibreOfficeConverter()
converter.convert(
    input_files=files,
    output_dir="pdfs/",
    format="pdf",
    overwrite=True
)
```

## CI/CD integration

For automated workflows:

### GitHub Actions

```yaml
- name: Install LibreOffice
  run: |
    sudo apt-get update
    sudo apt-get install -y libreoffice
```

### Docker

```dockerfile
FROM python:3.13
RUN apt-get update && apt-get install -y libreoffice
```

## Troubleshooting

### "Can't find LibreOffice executable" error

1. Ensure LibreOffice is installed
2. Restart your terminal/IDE
3. Check if `soffice` is in your PATH:
   - macOS/Linux: `which soffice`
   - Windows: `where soffice`
4. If not in PATH, specify the full path when creating the converter

### Version requirements

rtflite requires LibreOffice version 7.1 or higher. Check your version:

```bash
soffice --version
```

## Performance tips

1. LibreOffice starts a background process for conversions.
2. For batch conversions, reuse the same converter instance.
3. The first conversion may be slower as LibreOffice initializes.
4. Consider using thread-based parallel processing for large batches.
