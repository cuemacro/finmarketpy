"""Shared fixtures for Makefile API tests.

This conftest provides:
- setup_tmp_makefile: Copies Makefile and split files to temp dir for isolated testing
- run_make: Helper to execute make commands with dry-run support (imported from test_utils)
- setup_rhiza_git_repo: Initialize a git repo configured as rhiza origin (imported from test_utils)
- SPLIT_MAKEFILES: List of split Makefile paths

Security Notes:
- S101 (assert usage): Asserts are used in pytest tests to validate conditions
- S603/S607 (subprocess usage): Any subprocess calls (via run_make) are for testing
  Makefile targets in isolated environments with controlled inputs
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

# Split Makefile paths that are included in the main Makefile
# These are now located in .rhiza/make.d/ directory
SPLIT_MAKEFILES = [
    ".rhiza/rhiza.mk",
    ".rhiza/make.d/bootstrap.mk",
    ".rhiza/make.d/quality.mk",
    ".rhiza/make.d/releasing.mk",
    ".rhiza/make.d/test.mk",
    ".rhiza/make.d/book.mk",
    ".rhiza/make.d/marimo.mk",
    ".rhiza/make.d/presentation.mk",
    ".rhiza/make.d/github.mk",
    ".rhiza/make.d/agentic.mk",
    ".rhiza/make.d/gh-aw.mk",
    ".rhiza/make.d/docker.mk",
]


@pytest.fixture(autouse=True)
def setup_tmp_makefile(logger, root, tmp_path: Path):
    """Copy the Makefile and split Makefiles into a temp directory and chdir there.

    We rely on `make -n` so that no real commands are executed.
    This fixture consolidates setup for both basic Makefile tests and GitHub targets.
    """
    logger.debug("Setting up temporary Makefile test dir: %s", tmp_path)

    # Copy the main Makefile into the temporary working directory
    shutil.copy(root / "Makefile", tmp_path / "Makefile")

    # Copy core Rhiza Makefiles
    (tmp_path / ".rhiza").mkdir(exist_ok=True)
    shutil.copy(root / ".rhiza" / "rhiza.mk", tmp_path / ".rhiza" / "rhiza.mk")

    # Copy .python-version file for PYTHON_VERSION variable
    if (root / ".python-version").exists():
        shutil.copy(root / ".python-version", tmp_path / ".python-version")

    # Copy .rhiza/.env if it exists (needed for GitHub targets and other configuration)
    if (root / ".rhiza" / ".env").exists():
        shutil.copy(root / ".rhiza" / ".env", tmp_path / ".rhiza" / ".env")
    else:
        # Create a minimal, deterministic .rhiza/.env for tests so they don't
        # depend on the developer's local configuration which may vary.
        env_content = "CUSTOM_SCRIPTS_FOLDER=.rhiza/customisations/scripts\n"
        (tmp_path / ".rhiza" / ".env").write_text(env_content)

    logger.debug("Copied Makefile from %s to %s", root / "Makefile", tmp_path / "Makefile")

    # Copy split Makefiles if they exist (maintaining directory structure)
    for split_file in SPLIT_MAKEFILES:
        source_path = root / split_file
        if source_path.exists():
            dest_path = tmp_path / split_file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, dest_path)
            logger.debug("Copied %s to %s", source_path, dest_path)

    # Move into tmp directory for isolation
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    logger.debug("Changed working directory to %s", tmp_path)
    try:
        yield
    finally:
        os.chdir(old_cwd)
        logger.debug("Restored working directory to %s", old_cwd)
