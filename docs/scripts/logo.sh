#!/bin/bash

# Generate logo background
Rscript docs/scripts/logo.R
if [ -f "Rplots.pdf" ]; then
    rm Rplots.pdf
fi

# Generate text image and compose with background due to
# limited ligatures support in hexSticker and ImageMagick.
# Requires font: Playwrite Norge Guides, install via
# brew install font-playwrite-no-guides

alias chrome="/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"

chrome --headless \
    --disable-gpu \
    --no-margins \
    --no-pdf-header-footer \
    --print-to-pdf-no-header \
    --print-to-pdf=docs/scripts/logo-text.pdf \
    docs/scripts/logo-text.svg

pdfcrop --quiet \
    docs/scripts/logo-text.pdf docs/scripts/logo-text.pdf

magick -density 500 docs/scripts/logo-text.pdf \
    -transparent white \
    docs/scripts/logo-text.png

magick docs/assets/logo.png docs/scripts/logo-text.png \
    -gravity center \
    -composite docs/assets/logo.png

rm docs/scripts/logo-text.pdf docs/scripts/logo-text.png

# Optimize PNG
pngquant docs/assets/logo.png \
    --force \
    --output docs/assets/logo.png

# Pad the logo to get square favicon and resize
magick docs/assets/logo.png \
    -gravity center \
    -background none \
    -extent 640x640 \
    -resize 512x512 \
    docs/assets/favicon.png

# Optimize PNG
pngquant docs/assets/favicon.png \
    --force \
    --output docs/assets/favicon.png
