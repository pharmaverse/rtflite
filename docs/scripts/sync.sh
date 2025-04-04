#!/bin/zsh

# Render .qmd to .md and convert to .py
sync_article() {
    local article_name=$1
    local article_path="docs/articles/$article_name.qmd"
    local example_output="examples/$article_name.py"

    # Render .qmd to .md
    quarto render "$article_path" --quiet

    # Convert .qmd to .ipynb
    quarto convert "$article_path"

    # Convert .ipynb to .py using nbconvert from venv
    python -m nbconvert --to python "docs/articles/$article_name.ipynb" --output "../../$example_output"

    # Remove all comments
    awk '!/^#/' "$example_output" >temp && mv temp "$example_output"

    # Consolidate consecutive blank lines into a single blank line
    awk 'NF {p = 0} !NF {p++} p < 2' "$example_output" >temp && mv temp "$example_output"

    # Clean up
    rm "docs/articles/$article_name.ipynb"

    # Format .py using ruff from venv
    python -m ruff format "$example_output"
}

# Sync articles
for article in example-baseline; do
    sync_article "$article"
done

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/pharmaverse/rtflite/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md

# Sync CONTRIBUTING.md with docs/contributing.md
cp CONTRIBUTING.md docs/contributing.md
