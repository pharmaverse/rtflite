# Converter setup

rtflite can convert RTF documents to PDF and other formats using a separately
installed LibreOffice.

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

!!! tip
    After installation, restart your shell to ensure `PATH` updates are loaded
    so that rtflite can find LibreOffice.

## Using the converter

Once LibreOffice is installed, convert RTF files to PDF in your code:

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
converter = rtf.LibreOfficeConverter(executable_path="/custom/path/to/soffice")
```

### Supported output formats

Besides PDF, LibreOffice can convert RTF to:

- `docx` - Microsoft Word format
- `doc` - Microsoft Word 97-2003 format
- `html` - HTML format
- `odt` - OpenDocument Text format
- `txt` - Plain text

Example:
```python
converter.convert(input_files="output.rtf", output_dir=".", format="docx")
```

For an explicit export filter, use LibreOffice's
`extension:filter[:options]` syntax. The returned filename uses only the extension:

```python
pdf_path = converter.convert(
    "output.rtf", output_dir="pdfs", format="pdf:writer_pdf_Export"
)
text_path = converter.convert(
    "output.rtf", output_dir="text", format="txt:Text (encoded):UTF8"
)
```

Filter names and options are passed through to LibreOffice unchanged. See
[LibreOffice's filter tables](https://help.libreoffice.org/latest/en-US/text/shared/guide/convertfilters.html)
for available filters. Availability depends on the installed LibreOffice version.

### Timeouts and isolated conversions

Each LibreOffice process has a 120 second timeout, including the version check.
For larger documents, increase the limit when creating the converter:

```python
converter = rtf.LibreOfficeConverter(timeout=300)
```

Use `timeout=None` to disable the limit. Failed conversions and timeouts raise
`RuntimeError`. Existing output files are preserved if conversion fails, even
with `overwrite=True`.

Each conversion uses a temporary LibreOffice user profile, independent of open
LibreOffice windows and other conversions. This also means personal settings
and extensions are not used. Output files and any HTML companion resources are
generated in a temporary directory and moved to the destination after conversion
succeeds. The temporary files and profile are then removed.

### Batch conversion

Convert multiple RTF files at once:

```python
files = ["file1.rtf", "file2.rtf", "file3.rtf"]
converter = rtf.LibreOfficeConverter()
converter.convert(input_files=files, output_dir="pdfs/", format="pdf", overwrite=True)
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
FROM python:3.14
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

!!! warning "Minimum version requirement"
    rtflite requires LibreOffice version 7.1 or higher. Check your version:

    ```bash
    soffice --version
    ```

## Performance tips

!!! tip "Optimization suggestions"
    1. Reuse a converter instance to avoid repeating executable discovery and
       version checks.
    2. Each input file starts a new LibreOffice process; batch inputs are processed
       sequentially. Reusing the converter does not keep LibreOffice running.
    3. Concurrent calls use separate profiles. Use distinct output filenames and
       limit concurrency to the memory available for LibreOffice processes.
