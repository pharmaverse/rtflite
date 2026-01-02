#!/bin/bash

zensical build --clean
cp site/articles/rtf/*.rtf tests/fixtures/docs_outputs
