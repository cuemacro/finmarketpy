# Rhiza Copilot Instructions

You are working in a project that utilises the `rhiza` framework. Rhiza is a collection of reusable
configuration templates and tooling designed to standardise and streamline modern Python development.

As a Rhiza-based project, this workspace adheres to specific conventions for structure, dependency management, and automation.

## Development Environment

The project uses `make` and `uv` for development tasks. UV handles all dependency and Python version management automatically.

### Prerequisites

- **Git**: Required for version control
- **Make**: Command runner for all development tasks
- **curl**: Required for installing uv (usually pre-installed on most systems)

**Note**: Python is NOT a prerequisite. UV will automatically download and install the correct Python version (specified in `.python-version`) when you run `make install`.

### Environment Setup

Setting up your environment is simple:

```bash
make install
```

This single command handles everything:
1. Installs `uv` package manager (to `./bin/uv` if not already in PATH)
2. Downloads and installs the correct Python version from `.python-version` (currently 3.13)
3. Creates a `.venv` virtual environment with that Python version
4. Installs all project dependencies from `pyproject.toml`

### Verifying Installation

After installation completes, verify everything works:

```bash
make test  # Should run successfully
```

### Environment Variables

UV automatically uses these environment variables (set by the bootstrap process):
- `UV_LINK_MODE=copy`: Ensures proper dependency linking across filesystems
- `UV_VENV_CLEAR=1`: Clears existing venv on reinstall to avoid conflicts

### Common Development Commands

- **Install Dependencies**: `make install` (full setup: uv, Python, venv, dependencies)
- **Run Tests**: `make test` (runs `pytest` with coverage)
- **Format Code**: `make fmt` (runs `ruff format` and `ruff check --fix`)
- **Check Dependencies**: `make deptry` (checks for missing/unused dependencies)
- **Marimo Notebooks**: `make marimo` (starts the Marimo notebook server)
- **Build Documentation**: `make book` (builds the documentation book)
- **Clean Environment**: `make clean` (removes build artifacts and stale branches)

### Troubleshooting

- **Installation fails**: Check internet connectivity (UV needs to download Python and packages)
- **Python version issues**: The `.python-version` file is the single source of truth. UV uses this automatically.
- **Pre-commit failures**: Run `make fmt` to auto-fix most formatting issues
- **Stale environment**: Run `make clean` followed by `make install` to start fresh

### Important Notes for Agents

- **Virtual Environment Activation**: Most `make` commands automatically handle virtual environment activation. Manual activation is rarely needed.
- **Python Version**: The repository specifies Python 3.13 in `.python-version`. UV installs this automatically.
- **All Commands Through Make**: Always use `make` targets rather than running tools directly to ensure consistency.
- **When a `make` target exists, use it**: Do not replace `make test`, `make fmt`, `make deptry`, etc. with direct tool commands.
- **For Python commands without a `make` target, use `uv run`**: Run Python and Python tooling via `uv run <command>`.
- **Never call the interpreter directly from `.venv`**: Do **not** use `.venv/bin/python`, `.venv/bin/pytest`, etc.

### Command Execution Policy (Strict)

Use these rules in order:

1. If there is an appropriate `make` target, use the `make` target.
2. If no `make` target exists and you must run Python code/tooling, use `uv run ...`.
3. Do not invoke binaries from `.venv/bin` directly.

Examples:

- ✅ `make test`
- ✅ `make fmt`
- ✅ `uv run pytest`
- ✅ `uv run python -m pytest tests/property/test_makefile_properties.py`
- ✅ `uv run python scripts/some_script.py`
- ❌ `.venv/bin/python -m pytest`
- ❌ `.venv/bin/pytest`

### Customizing Setup with Hooks

The Makefile provides hooks for customizing the setup process. Add these to the root `Makefile`:

```makefile
# Run before make install
pre-install::
	@echo "Installing system dependencies..."
	@command -v graphviz || brew install graphviz

# Run after make install
post-install::
	@echo "Running custom setup..."
	@./scripts/custom-setup.sh
```

**Available hooks:**
- `pre-install` / `post-install`: Runs around `make install`
- `pre-sync` / `post-sync`: Runs around template synchronization
- `pre-validate` / `post-validate`: Runs around validation
- `pre-release` / `post-release`: Runs around releases

**Note**: Use double-colon syntax (`::`) for hooks to allow multiple definitions. See `.rhiza/make.d/README.md` for more details.

### Cloud/CI Environment Setup

The Copilot coding agent environment is automatically configured via official GitHub mechanisms:

- **`.github/workflows/copilot-setup-steps.yml`**: Runs before the agent starts. Installs uv, configures git auth for private packages, and runs `make install` to set up a deterministic environment.
- **`.github/hooks/hooks.json`**: Defines session lifecycle hooks:
  - `sessionStart`: Validates the environment is correctly set up (uv available, .venv exists)
  - `sessionEnd`: Runs `make fmt` and `make test` as quality gates after the agent finishes work

These files must exist on the default branch. The agent does not need to run any setup commands manually.

For DevContainers and Codespaces, the `.devcontainer/` configuration and `bootstrap.sh` handle setup automatically. See `docs/DEVCONTAINER.md` for details.

## Project Structure

- `src/`: Source code
- `tests/`: Tests (pytest)
- `assets/`: Static assets
- `book/`: Documentation source
- `docker/`: Docker configuration
- `presentation/`: Presentation slides
- `.rhiza/`: Rhiza-specific scripts and configurations

## Coding Standards

- **Style**: Follow PEP 8. Use `make fmt` to enforce style.
- **Testing**: Write tests in `tests/` using `pytest`. Ensure high coverage.
- **Documentation**: Document code using docstrings.
- **Dependencies**: Manage dependencies in `pyproject.toml`. Use `uv add` to add dependencies.

## Workflow

1.  **Setup**: Run `make install` to set up the environment.
2.  **Develop**: Write code in `src/` and tests in `tests/`.
3.  **Test**: Run `make test` to verify changes.
4.  **Format**: Run `make fmt` before committing.
5.  **Verify**: Run `make deptry` to check dependencies.

## GitHub Agentic Workflows (gh-aw)

This repository uses GitHub Agentic Workflows for AI-driven automation.
Agentic workflow files are Markdown files in `.github/workflows/` with
`.lock.yml` compiled counterparts.

**Key Commands:**
- `make gh-aw-compile` or `gh aw compile` — Compile workflow `.md` files to `.lock.yml`
- `make gh-aw-run WORKFLOW=<name>` or `gh aw run <name>` — Run a specific workflow locally
- `make gh-aw-status` — Check status of all agentic workflows
- `make gh-aw-setup` — Configure secrets and engine for first-time setup

**Important Rules:**
- **Never edit `.lock.yml` files directly** — Always edit the `.md` source and recompile
- Workflows must be compiled before they can run in GitHub Actions
- After editing any `.md` workflow, always run `make gh-aw-compile` and commit both files

**Available Starter Workflows:**
- `daily-repo-status.md` — Daily repository health reports
- `ci-doctor.md` — Automatic CI failure diagnosis
- `issue-triage.md` — Automatic issue classification and labeling

For more details, see `docs/GH_AW.md`.

## Key Files

- `Makefile`: Main entry point for tasks.
- `pyproject.toml`: Project configuration and dependencies.
- `.devcontainer/bootstrap.sh`: Bootstrap script for dev containers.
- `.github/workflows/copilot-setup-steps.yml`: Agent environment setup (runs before agent starts).
- `.github/hooks/hooks.json`: Agent session hooks (quality gates).
