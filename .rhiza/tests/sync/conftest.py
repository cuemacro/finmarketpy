"""Shared fixtures and helpers for sync tests.

Provides environment setup for template sync, workflow versioning,
and content validation tests.

Security Notes:
- S101 (assert usage): Asserts are used in pytest tests to validate conditions
- S603/S607 (subprocess usage): Any subprocess calls are for testing sync targets
  in isolated environments with controlled inputs
- Test code operates in a controlled environment with trusted inputs
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

tests_root = Path(__file__).resolve().parents[1]
if str(tests_root) not in sys.path:
    sys.path.insert(0, str(tests_root))

from test_utils import run_make, setup_rhiza_git_repo, strip_ansi  # noqa: E402, F401


@pytest.fixture(autouse=True)
def setup_sync_env(logger, root, tmp_path: Path):
    """Set up a temporary environment for sync tests with Makefile, templates, and git.

    This fixture creates a complete test environment with:
    - Makefile and rhiza.mk configuration
    - .rhiza-version file and .env configuration
    - template.yml and pyproject.toml
    - Initialized git repository (configured as rhiza origin)
    - src/ and tests/ directories to satisfy validate target
    """
    logger.debug("Setting up sync test environment: %s", tmp_path)

    # Copy the main Makefile into the temporary working directory
    shutil.copy(root / "Makefile", tmp_path / "Makefile")

    # Copy core Rhiza Makefiles and version file
    (tmp_path / ".rhiza").mkdir(exist_ok=True)
    shutil.copy(root / ".rhiza" / "rhiza.mk", tmp_path / ".rhiza" / "rhiza.mk")

    # Copy split Makefiles from make.d directory
    split_makefiles = [
        "bootstrap.mk",
        "quality.mk",
        "releasing.mk",
        "test.mk",
        "book.mk",
        "marimo.mk",
        "presentation.mk",
        "github.mk",
        "agentic.mk",
        "docker.mk",
    ]
    (tmp_path / ".rhiza" / "make.d").mkdir(parents=True, exist_ok=True)
    for mk_file in split_makefiles:
        source_path = root / ".rhiza" / "make.d" / mk_file
        if source_path.exists():
            shutil.copy(source_path, tmp_path / ".rhiza" / "make.d" / mk_file)

    # Copy .rhiza-version if it exists
    if (root / ".rhiza" / ".rhiza-version").exists():
        shutil.copy(root / ".rhiza" / ".rhiza-version", tmp_path / ".rhiza" / ".rhiza-version")

    # Create a minimal, deterministic .rhiza/.env for tests
    env_content = "CUSTOM_SCRIPTS_FOLDER=.rhiza/customisations/scripts\n"
    (tmp_path / ".rhiza" / ".env").write_text(env_content)

    logger.debug("Copied Makefile from %s to %s", root / "Makefile", tmp_path / "Makefile")

    # Create a minimal .rhiza/template.yml
    (tmp_path / ".rhiza" / "template.yml").write_text("repository: Jebel-Quant/rhiza\nref: v0.7.1\n")

    # Sort out pyproject.toml
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    # Move into tmp directory for isolation
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    logger.debug("Changed working directory to %s", tmp_path)

    # Initialize a git repo so that commands checking for it (like sync) don't fail validation
    setup_rhiza_git_repo()

    # Create src and tests directories to satisfy validate
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)

    try:
        yield
    finally:
        os.chdir(old_cwd)
        logger.debug("Restored working directory to %s", old_cwd)
