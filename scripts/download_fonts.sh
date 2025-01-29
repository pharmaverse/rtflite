#!/bin/bash

ROOT_DIR="$(pwd)"
mkdir -p src/rtflite/fonts/liberation
mkdir -p src/rtflite/fonts/cros

TEMP_DIR=$(mktemp -d)
pushd "$TEMP_DIR" >/dev/null

curl -s -S -L -o liberation-fonts.tar.gz https://github.com/liberationfonts/liberation-fonts/files/7261482/liberation-fonts-ttf-2.1.5.tar.gz
tar xf liberation-fonts.tar.gz

mv -f liberation-fonts-ttf-2.1.5/LiberationMono-Regular.ttf "$ROOT_DIR/src/rtflite/fonts/liberation/"
mv -f liberation-fonts-ttf-2.1.5/LiberationSans-Regular.ttf "$ROOT_DIR/src/rtflite/fonts/liberation/"
mv -f liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf "$ROOT_DIR/src/rtflite/fonts/liberation/"

curl -s -S -L -o "$ROOT_DIR/src/rtflite/fonts/cros/Caladea-Regular.ttf" https://github.com/huertatipografica/Caladea/raw/refs/heads/master/fonts/ttf/Caladea-Regular.ttf
curl -s -S -L -o "$ROOT_DIR/src/rtflite/fonts/cros/Carlito-Regular.ttf" https://github.com/googlefonts/carlito/raw/refs/heads/main/fonts/ttf/Carlito-Regular.ttf
curl -s -S -L -o "$ROOT_DIR/src/rtflite/fonts/cros/Gelasio-Regular.ttf" https://github.com/SorkinType/Gelasio/raw/refs/heads/main/fonts/ttf/Gelasio-Regular.ttf

popd >/dev/null
rm -rf "$TEMP_DIR"
