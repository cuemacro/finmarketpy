# Development Workflows

This guide covers recommended day-to-day development workflows for Rhiza projects.

## Dependency Management

Rhiza uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python dependency management.

> 📚 **For detailed information about dependency version constraints and rationale**, see [docs/DEPENDENCIES.md](../../docs/DEPENDENCIES.md)

### Adding Dependencies

**Recommended: Use `uv add`** — handles everything in one step:

```bash
# Add a runtime dependency
uv add requests

# Add a development dependency
uv add --dev pytest-xdist

# Add with version constraint
uv add "pandas>=2.0"
```

This command:
1. Updates `pyproject.toml`
2. Resolves and updates `uv.lock`
3. Installs the package into your active venv

### Manual Editing

If you prefer to edit `pyproject.toml` directly:

```bash
# After editing pyproject.toml, sync your environment
uv sync
```

> ⚠️ **Important:** Editing `pyproject.toml` alone does **not** update `uv.lock` or your venv. You must run `uv sync` afterward.

**Safety nets:**
- `make install` checks if `uv.lock` is in sync with `pyproject.toml` and fails with a helpful message if not
- A pre-commit hook runs `uv lock` to ensure the lock file is updated before committing
- CI will fail if you forget to update the lock file

### Removing Dependencies

```bash
uv remove requests
```

### Command Reference

| Goal | Command |
|------|---------|
| Add a runtime dependency | `uv add <package>` |
| Add a dev dependency | `uv add --dev <package>` |
| Remove a dependency | `uv remove <package>` |
| Sync after manual edits | `uv sync` |
| Update lock file only | `uv lock` |
| Upgrade a package | `uv lock --upgrade-package <package>` |
| Upgrade all packages | `uv lock --upgrade` |

## Development Cycle

### Starting Work

```bash
# Ensure your environment is up to date
make install

# Create a feature branch
git checkout -b feature/my-feature
```

### Making Changes

1. **Write code** in `src/`
2. **Write tests** in `tests/`
3. **Run tests frequently:**
   ```bash
   make test
   ```
4. **Format before committing:**
   ```bash
   make fmt
   ```

### Pre-Commit Checklist

Before committing, run these checks:

```bash
make fmt      # Format and lint
make test     # Run all tests
make deptry   # Check for dependency issues
```

Or run all pre-commit hooks at once:

```bash
make pre-commit
```

### Committing Changes

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```bash
git commit -m "feat: add new widget component"
git commit -m "fix: resolve null pointer in parser"
git commit -m "docs: update API reference"
git commit -m "chore: update dependencies"
```

Common prefixes:
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `test:` — Adding/updating tests
- `chore:` — Maintenance tasks
- `refactor:` — Code refactoring

### Skipping CI

For documentation-only or trivial changes:

```bash
git commit -m "docs: fix typo [skip ci]"
```

## Running Python Code

Always use `uv run` to ensure the correct environment:

```bash
# Run a script
uv run python scripts/my_script.py

# Run a module
uv run python -m mymodule

# Run tests directly
uv run pytest tests/test_specific.py -v

# Interactive Python
uv run python
```

## Testing Workflows

### Run All Tests

```bash
make test
```

### Run Specific Tests

```bash
# Single file
uv run pytest tests/test_rhiza/test_makefile.py -v

# Single test function
uv run pytest tests/test_rhiza/test_makefile.py::test_specific_function -v

# Tests matching a pattern
uv run pytest -k "test_pattern" -v

# With print output
uv run pytest -v -s
```

### Run with Coverage

```bash
make test  # Coverage is included by default
```

## Releasing

See [RELEASING.md](RELEASING.md) for the complete release workflow.

Quick reference:

```bash
# Bump version and release in one step (recommended)
make publish

# Bump version (interactive)
make bump

# Bump specific version
make bump BUMP=patch  # 1.0.0 → 1.0.1
make bump BUMP=minor  # 1.0.0 → 1.1.0
make bump BUMP=major  # 1.0.0 → 2.0.0

# Create and push release tag (without bump)
make release

# Check release workflow status and latest release
make release-status
```

## Template Synchronization

Keep your project in sync with upstream Rhiza templates:

```bash
make sync
```

This updates shared configurations while preserving your customizations in `local.mk`.

## Troubleshooting

### Environment Out of Sync

If your environment seems broken or out of date:

```bash
# Full reinstall
rm -rf .venv
make install
```

### Lock File Conflicts

If `uv.lock` has merge conflicts:

```bash
# Accept current pyproject.toml as source of truth
git checkout --theirs uv.lock  # or --ours depending on your situation
uv lock
```

### Dependency Check Failures

If `make deptry` reports issues:

```bash
# Missing dependencies — add them
uv add <missing-package>

# Unused dependencies — remove them
uv remove <unused-package>
```
