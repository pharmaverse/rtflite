#!/bin/bash

mkdocs build 
cp site/articles/rtf/*.rtf tests/fixtures/mkdocs_outputs 