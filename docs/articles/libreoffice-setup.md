# LibreOffice Setup for PDF Conversion

rtflite can convert RTF documents to PDF using LibreOffice. This guide helps you set up LibreOffice for PDF conversion functionality.

## Quick Start

### Check Installation Status

Run the provided utility script to check if LibreOffice is properly installed:

```bash
python scripts/check_libreoffice.py
```

This script will:
- Check if LibreOffice is installed
- Verify it's accessible to rtflite
- Provide platform-specific installation instructions if needed

## Installation Instructions

### macOS

**Option 1: Using Homebrew (recommended)**
```bash
brew install --cask libreoffice
```

**Option 2: Direct Download**
1. Visit [LibreOffice Download Page](https://www.libreoffice.org/download/download/)
2. Download the macOS version
3. Install the .dmg file
4. LibreOffice will be installed at `/Applications/LibreOffice.app`

### Linux

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libreoffice
```

**Fedora/RHEL/CentOS:**
```bash
sudo dnf install libreoffice
```

**Arch Linux:**
```bash
sudo pacman -S libreoffice-fresh
```

**Universal (Snap):**
```bash
sudo snap install libreoffice
```

### Windows

1. Visit [LibreOffice Download Page](https://www.libreoffice.org/download/download/)
2. Download the Windows version (64-bit recommended)
3. Run the installer (.msi file)
4. Follow the installation wizard
5. Default installation path: `C:\Program Files\LibreOffice`

## Verify Installation

After installation:

1. **Restart your terminal or IDE** to ensure PATH updates are loaded
2. Run the check script again:
   ```bash
   python scripts/check_libreoffice.py
   ```
3. You should see:
   ```
   ✓ LibreOffice is installed at: /path/to/soffice
   ✓ LibreOffice converter initialized successfully!
   ✓ PDF conversion is available.
   ```

## Using PDF Conversion

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

## Custom Installation Paths

If LibreOffice is installed in a non-standard location, you can specify the path:

```python
converter = rtf.LibreOfficeConverter(
    executable_path="/custom/path/to/soffice"
)
```

## Supported Output Formats

Besides PDF, LibreOffice can convert RTF to:
- `docx` - Microsoft Word format
- `html` - HTML format
- `odt` - OpenDocument Text format

Example:
```python
converter.convert(input_files="output.rtf", output_dir=".", format="docx")
```

## Troubleshooting

### "Can't find LibreOffice executable" Error

1. Ensure LibreOffice is installed
2. Restart your terminal/IDE
3. Check if `soffice` is in your PATH:
   - macOS/Linux: `which soffice`
   - Windows: `where soffice`
4. If not in PATH, specify the full path when creating the converter

### Version Requirements

rtflite requires LibreOffice version 7.1 or higher. Check your version:
```bash
soffice --version
```

### Permission Issues

On some systems, you may need to grant terminal/IDE permission to access LibreOffice:
- macOS: System Preferences → Security & Privacy → Privacy → Automation
- Linux: Ensure execute permissions on the soffice binary
- Windows: Run as administrator if needed

## Batch Conversion

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

## CI/CD Integration

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
FROM python:3.9
RUN apt-get update && apt-get install -y libreoffice
```

## Performance Tips

1. LibreOffice starts a background process for conversions
2. For batch conversions, reuse the same converter instance
3. The first conversion may be slower as LibreOffice initializes
4. Consider using parallel processing for large batches

## Next Steps

- Run the example scripts to test PDF conversion
- Check out the [pagination examples](example-pagination-basic.md) for multi-page documents
- Review the [API documentation](../reference/convert.md) for advanced options