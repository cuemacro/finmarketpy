# Rhiza Quick Reference Card

A concise reference for common Rhiza operations.

## Essential Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies and set up environment |
| `make test` | Run pytest with coverage |
| `make fmt` | Format and lint code with ruff |
| `make help` | Show all available targets |

## Version & Release

| Command | Description |
|---------|-------------|
| `make publish` | Bump version, create tag and push in one step |
| `make bump` | Bump version (prompts for major/minor/patch) |
| `make bump BUMP=patch` | Bump patch version directly |
| `make bump BUMP=minor` | Bump minor version directly |
| `make bump BUMP=major` | Bump major version directly |
| `make release` | Create and push release tag |
| `make release-status` | Show release workflow status and latest release |

## Code Quality

| Command | Description |
|---------|-------------|
| `make fmt` | Format + lint with auto-fix |
| `make deptry` | Check for unused/missing dependencies |
| `make pre-commit` | Run all pre-commit hooks |

## Template Sync

| Command | Description |
|---------|-------------|
| `make sync` | Sync templates from upstream Rhiza |

## GitHub Agentic Workflows (gh-aw)

| Command | Description |
|---------|-------------|
| `make install-gh-aw` | Install the gh-aw CLI extension |
| `make gh-aw-init` | Initialize repository for gh-aw |
| `make gh-aw-setup` | Guided setup for secrets and engine configuration |
| `make gh-aw-compile` | Compile workflow `.md` files into `.lock.yml` GitHub Actions |
| `make gh-aw-validate` | Validate that `.lock.yml` files are up-to-date |
| `make gh-aw-status` | Show status of all agentic workflows |
| `make gh-aw-run WORKFLOW=<name>` | Run a specific agentic workflow locally |
| `make gh-aw-logs` | Show logs for recent agentic workflow runs |

## Running Tests

```bash
# All tests
make test

# Specific file
uv run pytest tests/path/to/test.py -v

# Specific test function
uv run pytest tests/path/to/test.py::test_name -v

# With output
uv run pytest -v -s
```

## Directory Structure

```text
.rhiza/
├── rhiza.mk          # Core Makefile logic
├── make.d/           # Modular extensions (auto-loaded)
│   ├── 00-19*.mk     # Configuration
│   ├── 20-79*.mk     # Task definitions
│   └── 80-99*.mk     # Hook implementations
├── utils/            # Python utilities
└── template.yml      # Sync configuration
```

## Hook Targets

Extend these with `::` syntax in `local.mk` or `.rhiza/make.d/`:

| Hook | When it runs |
|------|--------------|
| `pre-install::` | Before dependency installation |
| `post-install::` | After dependency installation |
| `pre-sync::` | Before template sync |
| `post-sync::` | After template sync |
| `pre-validate::` | Before project validation |
| `post-validate::` | After project validation |
| `pre-release::` | Before release creation |
| `post-release::` | After release creation |
| `pre-bump::` | Before version bump |
| `post-bump::` | After version bump |

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, version |
| `uv.lock` | Locked dependency versions |
| `.python-version` | Default Python version |
| `ruff.toml` | Linter/formatter configuration |
| `local.mk` | Local Makefile customizations (not synced) |

## Python Execution

Always use `uv` for Python operations:

```bash
uv run python script.py    # Run Python script
uv run pytest              # Run tests
uv build                   # Build distribution packages
```

## Version Format

- Source of truth: `version` field in `pyproject.toml`
- Git tags: `v` prefix (e.g., `v1.2.3`)
- Semantic versioning: `MAJOR.MINOR.PATCH`

## CI Workflows

| Workflow | Trigger |
|----------|---------|
| CI | Push, Pull Request |
| Release | Tag `v*` |
| Security | Schedule, Push |
| Sync | Manual |

## Common Patterns

### Add a custom make target

Create `.rhiza/make.d/50-custom.mk`:
```makefile
my-target:
	@echo "Custom target"
```

### Extend a hook

Add to `local.mk`:
```makefile
post-install::
	@echo "Additional setup after install"
```

### Skip CI on commit

```bash
git commit -m "docs: update readme [skip ci]"
```
