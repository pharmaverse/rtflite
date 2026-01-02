#!/bin/bash

zensical build --clean
cp site/articles/rtf/*.rtf tests/fixtures/mkdocs_outputs
