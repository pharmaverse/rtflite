#!/bin/zsh

# Render .qmd to .md and convert to .py
sync_article() {
    local article_name=$1
    local article_path="docs/articles/quarto/$article_name.qmd"
    local example_output="docs/articles/py/$article_name.py"

    # Render .qmd to .md
    quarto render "$article_path" --output-dir ".." --quiet

    # Convert .qmd to .ipynb
    quarto convert "$article_path"

    # Convert .ipynb to .py using nbconvert from venv
    uv run python -m nbconvert --to python "docs/articles/quarto/$article_name.ipynb" --output "../../../$example_output"

    # Remove all comments
    awk '!/^#/' "$example_output" >temp && mv temp "$example_output"

    # Consolidate consecutive blank lines into a single blank line
    awk 'NF {p = 0} !NF {p++} p < 2' "$example_output" >temp && mv temp "$example_output"

    # Clean up
    rm "docs/articles/quarto/$article_name.ipynb"

    # Format .py using ruff from venv
    uv run ruff format "$example_output"
}

# Sync articles
for qmd_file in docs/articles/quarto/example-*.qmd; do
    if [[ -f "$qmd_file" ]]; then
        article=$(basename "$qmd_file" .qmd)
        sync_article "$article"
    fi
done

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/pharmaverse/rtflite/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md

# Sync CONTRIBUTING.md with docs/contributing.md
cp CONTRIBUTING.md docs/contributing.md

