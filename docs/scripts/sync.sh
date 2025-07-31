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
    for py_file in docs/articles/py/*.py; do
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


# Generate RTF files by running Python scripts
generate_rtf_files

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/pharmaverse/rtflite/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md

# Sync CONTRIBUTING.md with docs/contributing.md
cp CONTRIBUTING.md docs/contributing.md

