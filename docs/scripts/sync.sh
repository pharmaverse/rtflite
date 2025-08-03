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

    # Convert .qmd to .ipynb (in the same directory as the qmd file)
    echo "  - Converting QMD to IPYNB..."
    cd docs/articles/quarto || exit 1
    quarto convert "$article_name.qmd"
    cd - > /dev/null || exit 1

    # Convert .ipynb to .py using nbconvert
    echo "  - Converting IPYNB to PY..."
    source .venv/bin/activate
    python -m nbconvert --to python "docs/articles/quarto/$article_name.ipynb" --output "../../../$example_output"

    # Remove all comments
    awk '!/^#/' "$example_output" >temp && mv temp "$example_output"

    # Consolidate consecutive blank lines into a single blank line
    awk 'NF {p = 0} !NF {p++} p < 2' "$example_output" >temp && mv temp "$example_output"

    # Clean up
    rm "docs/articles/quarto/$article_name.ipynb"

    # Format .py using ruff
    echo "  - Formatting PY file with ruff..."
    ruff format "$example_output"
}

# Function to run Python files and generate RTF files
generate_rtf_files() {
    echo ""
    echo "=== Generating RTF files from Python scripts ==="

    # Create rtf directory if it doesn't exist
    mkdir -p docs/articles/rtf

    # Run each Python file to generate RTF
    for py_file in docs/articles/py/*.py; do
        if [[ -f "$py_file" ]]; then
            py_name=$(basename "$py_file" .py)
            echo "Running: $py_name.py"

            # Change to py directory to run the script with proper relative paths
            cd docs/articles/py || exit 1
            source ../../../.venv/bin/activate
            python "$py_name.py"
            cd - > /dev/null || exit 1
        fi
    done
}

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate virtual environment first
source "$PROJECT_ROOT/.venv/bin/activate"

# Sync all articles in the quarto folder
for qmd_file in docs/articles/quarto/*.qmd; do
    if [[ -f "$qmd_file" ]]; then
        article_name=$(basename "$qmd_file" .qmd)
        sync_article "$article_name"
    fi
done

# Generate RTF files by running Python scripts
generate_rtf_files
sh docs/scripts/rtf_to_pdf.sh

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/pharmaverse/rtflite/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md

# Sync CONTRIBUTING.md with docs/contributing.md
cp CONTRIBUTING.md docs/contributing.md