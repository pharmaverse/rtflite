# R test fixtures

This directory contains output fixtures generated from R code for
testing Python implementations.

To update the fixtures, run the Python script to extract and execute the R code
locally (assuming R exists):

```bash
python tests/fixtures/run_r_tests.py
```

The outputs will be available in `tests/fixtures/r_outputs/`.

Note: This step is only needed when updating the expected outputs from R,
not for running the Python tests.
