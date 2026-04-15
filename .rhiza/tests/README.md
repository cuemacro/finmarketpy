# Rhiza Test Suite

This directory contains the comprehensive test suite for the Rhiza project.

## Test Organization

Tests are organized into purpose-driven subdirectories:

### `structure/`
Static assertions about file and directory presence. These tests verify that the repository contains the expected files, directories, and configuration structure without executing any subprocesses.

- `test_project_layout.py` — Validates root-level files and directories
- `test_requirements.py` — Validates `.rhiza/requirements/` structure

### `api/`
Makefile target validation via dry-runs. These tests verify that Makefile targets are properly defined and would execute the expected commands.

- `test_makefile_targets.py` — Core Makefile targets (install, test, fmt, etc.)
- `test_makefile_api.py` — Makefile API (delegation, extension, hooks, overrides)
- `test_github_targets.py` — GitHub-specific Makefile targets

### `integration/`
Tests requiring sandboxed git repositories or subprocess execution. These tests verify end-to-end workflows.

- `test_release.py` — Release script functionality
- `test_book_targets.py` — Documentation book build targets

### `sync/`
Template sync, workflows, versioning, and content validation tests. These tests ensure that template synchronization and content validation work correctly.

- `test_rhiza_version.py` — Version reading and workflow validation
- `test_readme_validation.py` — README code block execution and validation
- `test_docstrings.py` — Doctest validation across source modules

#### Skipping README code blocks with `+RHIZA_SKIP`

By default, every `python` and `bash` code block in `README.md` is executed or
syntax-checked by `test_readme_validation.py`. To mark a block as intentionally
non-runnable (e.g. illustrative snippets or environment-specific commands), add
`+RHIZA_SKIP` to the opening fence line:

~~~markdown
```python +RHIZA_SKIP
# This block will NOT be executed or syntax-checked
from my_env import some_function
some_function()
```

```bash +RHIZA_SKIP
# This bash block will NOT be syntax-checked
run-something --only-on-ci
```
~~~

Markdown renderers (including GitHub) ignore everything after the first word on
a fence line, so the block still renders as a normal highlighted code block.
Blocks without `+RHIZA_SKIP` continue to be validated as before.

### `utils/`
Tests for utility code and test infrastructure. These tests validate the testing framework itself and utility scripts.

- `test_git_repo_fixture.py` — Validates the `git_repo` fixture

### `deps/`
Dependency validation tests. These tests ensure that project dependencies are correctly specified and healthy.

- `test_dependency_health.py` — Validates pyproject.toml and requirements files

### `stress/`
Stress tests that verify Rhiza's stability under heavy load. These tests execute Rhiza-specific operations under concurrent load and repeated execution to detect race conditions, resource leaks, and performance degradation.

- `test_makefile_stress.py` — Makefile operations under concurrent/repeated load
- `test_git_stress.py` — Git operations under concurrent load

See [stress/README.md](stress/README.md) for detailed documentation.

## Running Tests

### Run all tests
```bash
uv run pytest .rhiza/tests/
# or
make test
```

### Run tests from a specific category
```bash
uv run pytest .rhiza/tests/structure/
uv run pytest .rhiza/tests/api/
uv run pytest .rhiza/tests/integration/
uv run pytest .rhiza/tests/sync/
uv run pytest .rhiza/tests/utils/
uv run pytest .rhiza/tests/deps/
uv run pytest .rhiza/tests/stress/
```

### Run stress tests with custom parameters
```bash
# Run all stress tests (default: 100 iterations, 10 workers)
uv run pytest .rhiza/tests/stress/ -v

# Run with fewer iterations (faster)
uv run pytest .rhiza/tests/stress/ -v --iterations=10

# Skip stress tests when running full test suite
uv run pytest .rhiza/tests/ -v -m "not stress"
```

### Run a specific test file
```bash
uv run pytest .rhiza/tests/structure/test_project_layout.py
```

### Run with verbose output
```bash
uv run pytest .rhiza/tests/ -v
```

### Run with coverage
```bash
uv run pytest .rhiza/tests/ --cov
```

## Fixtures

### Root-level fixtures (`conftest.py`)
- `root` — Repository root path (session-scoped)
- `logger` — Configured logger instance (session-scoped)
- `git_repo` — Sandboxed git repository (function-scoped)

### Category-specific fixtures
- `api/conftest.py` — `setup_tmp_makefile`, `run_make`, `setup_rhiza_git_repo`
- `sync/conftest.py` — `setup_sync_env`

## Writing Tests

### Conventions
- Use descriptive test names that explain what is being tested
- Group related tests in classes when appropriate
- Use appropriate fixtures for setup/teardown
- Add docstrings to test modules and complex test functions
- Use `pytest.mark.skip` for tests that depend on optional features

### Import Patterns
```python
# Import shared helpers from test_utils
from test_utils import strip_ansi, run_make, setup_rhiza_git_repo

# Import from local category conftest (for fixtures and category-specific helpers)
from api.conftest import SPLIT_MAKEFILES, setup_tmp_makefile

# Note: Fixtures defined in conftest.py are automatically available in tests
# and don't need to be explicitly imported
```

## Test Coverage

The test suite aims for high coverage across:
- Configuration validation (structure, dependencies)
- Makefile target correctness (api)
- End-to-end workflows (integration)
- Template synchronization (sync)
- Utility code (utils)

## Notes

- Benchmarks are located in `tests/benchmarks/` and run via `make benchmark`
- Integration tests use sandboxed git repositories to avoid affecting the working tree
- All Makefile tests use dry-run mode (`make -n`) to avoid side effects
