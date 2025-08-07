# Contributing to rtflite

## Developer workflow

### Setup

First off, [install uv](https://docs.astral.sh/uv/getting-started/installation/).
rtflite uses uv to manage the Python package development environment.

If you have trouble installing the exact Python version pinned in the project, run

```bash
uv self update
```

to update your uv installation.

### Branching

Clone the repository (if you have no direct access, replace the address with
your forked repository address):

```bash
git clone https://github.com/pharmaverse/rtflite.git
```

Create a dedicated branch:

```bash
cd rtflite
git checkout -b my-branch
```

### Dependencies

Restore the environment using
[uv sync](https://docs.astral.sh/uv/concepts/projects/sync/).
This will restore the exact versions of Python and dependency packages
under the project's `.venv/` directory:

```bash
uv sync
```

### Development

Open the project in VS Code:

```bash
code rtflite
```

Make changes to the codebase.

We use pytest for unit testing. To run tests and get an HTML preview of
code coverage, open the
[VS Code terminal](https://code.visualstudio.com/docs/terminal/basics):

```bash
pytest
pytest tests/specific_test.py
pytest --cov=rtflite --cov-report=html:docs/coverage/
```

If your terminal did not activate the virtual environment for some reason
(with symptoms like not finding pytest commands), activate it manually:

```bash
source .venv/bin/activate
```

### Documentation

To preview the mkdocs website locally:

```bash
mkdocs serve
```

To build the mkdocs website locally into `site/`, run:

```bash
mkdocs build
```

rtflite renders vignette-like articles under `docs/articles `using markdown-exec.
This allows mkdocs to render Python code chunks and their outputs when building the site.
Check the [markdown-exec documentation](https://pawamoy.github.io/markdown-exec/usage/)
for possible code chunk options.

If you made changes to the `.md` files in the root directory,
make sure to synchronize them to the mkdocs website:

```bash
sh docs/scripts/sync.sh
```

### Formatting

Use isort and ruff to sort imports and format Python code:

```bash
isort .
ruff format
```

### Pull request

Add, commit, and push to remote, then send a pull request:

```bash
git add -A
git commit -m "Your commit message"
git push origin my-branch
```

## Maintainer workflow

### Updates

Update local uv version:

```bash
uv self update
```

Update `uv.lock` file regularly:

```bash
uv sync --quiet
uv lock --upgrade
uv sync
```

### Python version

Pin a newer Python version in `.python-version` when appropriate:

```bash
uv python pin x.y.z
```

The latest Python release versions are often promptly supported by uv.

### Publishing

Publish on PyPI (maintainer token required):

```bash
uv build
uv publish
```
