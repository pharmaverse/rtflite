#!/bin/zsh

echo "=== RTF Lite Document Sync Script ==="
echo "This script converts QMD files to MD and PY, runs PY files to generate RTF, and converts RTF to PDF"

# Function to render .qmd to .md and convert to .py
sync_article() {
    local article_name=$1
    local article_path="docs/articles/quarto/$article_name.qmd"
    local example_output="docs/articles/py/$article_name.py"

    echo "Processing: $article_name"
    
    # Render .qmd to .md
    echo "  - Rendering QMD to MD..."
    quarto render "$article_path" --output-dir ".." --quiet

    # Convert .qmd to .ipynb
    echo "  - Converting QMD to IPYNB..."
    quarto convert "$article_path"

    # Convert .ipynb to .py using nbconvert from venv
    echo "  - Converting IPYNB to PY..."
    uv run python -m nbconvert --to python "docs/articles/quarto/$article_name.ipynb" --output "../../../$example_output"

    # Remove all comments
    awk '!/^#/' "$example_output" >temp && mv temp "$example_output"

    # Consolidate consecutive blank lines into a single blank line
    awk 'NF {p = 0} !NF {p++} p < 2' "$example_output" >temp && mv temp "$example_output"

    # Clean up
    rm "docs/articles/quarto/$article_name.ipynb"

    # Format .py using ruff from venv
    echo "  - Formatting PY file with ruff..."
    uv run ruff format "$example_output"
}

# Function to run Python files and generate RTF files
generate_rtf_files() {
    echo ""
    echo "=== Generating RTF files from Python scripts ==="
    
    # Create rtf directory if it doesn't exist
    mkdir -p docs/articles/rtf
    
    # Run each Python file to generate RTF
    for py_file in docs/articles/py/example-*.py; do
        if [[ -f "$py_file" ]]; then
            py_name=$(basename "$py_file" .py)
            echo "Running: $py_name.py"
            
            # Change to py directory to run the script with proper relative paths
            cd docs/articles/py || exit 1
            uv run python "$py_name.py"
            cd - > /dev/null || exit 1
        fi
    done
}

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
        uv run python temp_convert.py
        
        # Clean up
        rm temp_convert.py
    else
        echo "No RTF files found in docs/articles/rtf/"
    fi
}

# Main execution flow
echo ""
echo "=== Step 1: Syncing QMD to MD and PY files ==="
for qmd_file in docs/articles/quarto/example-*.qmd; do
    if [[ -f "$qmd_file" ]]; then
        article=$(basename "$qmd_file" .qmd)
        sync_article "$article"
    fi
done

# Generate RTF files by running Python scripts
generate_rtf_files

# Convert all RTF files to PDF in batch
convert_rtf_to_pdf

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/pharmaverse/rtflite/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md

# Sync CONTRIBUTING.md with docs/contributing.md
cp CONTRIBUTING.md docs/contributing.md

