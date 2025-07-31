
# Function to convert all RTF files to PDF in batch
convert_rtf_to_pdf() {
    echo ""
    echo "=== Converting RTF files to PDF ==="

    # Create pdf directory if it doesn't exist
    mkdir -p docs/articles/pdf

    # Find all RTF files in the rtf directory
    if ls docs/articles/rtf/*.rtf 1> /dev/null 2>&1; then
        echo "Converting RTF files to PDF using rtflite converter..."

        # Use Python to batch convert RTF files
        cat > temp_convert.py << 'EOF'
import os
import glob
import rtflite as rtf

rtf_dir = "docs/articles/rtf"
pdf_dir = "docs/articles/pdf"

# Ensure PDF directory exists
os.makedirs(pdf_dir, exist_ok=True)

# Find all RTF files and convert them
rtf_files = glob.glob(os.path.join(rtf_dir, "*.rtf"))

if rtf_files:
    print(f"Found {len(rtf_files)} RTF files to convert:")
    try:
        converter = rtf.LibreOfficeConverter()
        for rtf_file in rtf_files:
            rtf_name = os.path.basename(rtf_file)
            pdf_name = os.path.splitext(rtf_name)[0] + ".pdf"

            print(f"  Converting: {rtf_name} -> {pdf_name}")
            try:
                converter.convert(
                    input_files=rtf_file,
                    output_dir=pdf_dir,
                    format="pdf",
                    overwrite=True
                )
                print(f"    ✓ Success")
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
    except FileNotFoundError as e:
        print(f"LibreOffice not found: {e}")
        print("Please install LibreOffice to enable PDF conversion")
else:
    print("No RTF files found to convert")
EOF

        # Run the conversion script
        python temp_convert.py

        # Clean up
        rm temp_convert.py
    else
        echo "No RTF files found in docs/articles/rtf/"
    fi
}

# Main execution flow
echo ""
echo "=== Step 1: Syncing QMD to MD and PY files ==="
for qmd_file in docs/articles/quarto/*.qmd; do
    if [[ -f "$qmd_file" ]]; then
        article=$(basename "$qmd_file" .qmd)
        sync_article "$article"
    fi
done

# Convert all RTF files to PDF in batch
convert_rtf_to_pdf