#!/bin/bash

echo "Sync root-level docs into mkdocs..."

# Sync README.md with modified image path for docs/index.md
awk '{gsub("https://github.com/pharmaverse/rtflite/raw/main/docs/assets/logo.png", "assets/logo.png"); print}' README.md >docs/index.md

# Sync CHANGELOG.md with docs/changelog.md
cp CHANGELOG.md docs/changelog.md

# Sync CONTRIBUTING.md with docs/contributing.md
cp CONTRIBUTING.md docs/contributing.md

echo "Done."
