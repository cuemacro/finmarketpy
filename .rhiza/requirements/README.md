# Requirements Folder

This folder contains the development dependencies for the Rhiza project, organized by purpose.

## Files

- **tests.txt** - Testing dependencies (pytest, pytest-cov, pytest-html)
- **marimo.txt** - Marimo notebook dependencies
- **docs.txt** - Documentation generation dependencies (pdoc)
- **tools.txt** - Development tools (pre-commit, python-dotenv)

## Usage

These requirements files are automatically installed by the `make install` command.

To install specific requirement files manually:

```bash
uv pip install -r .rhiza/requirements/tests.txt
uv pip install -r .rhiza/requirements/marimo.txt
uv pip install -r .rhiza/requirements/docs.txt
uv pip install -r .rhiza/requirements/tools.txt
```

## CI/CD

GitHub Actions workflows automatically install these requirements as needed.
