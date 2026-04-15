"""Tests for the new Makefile API structure (Wrapper + Makefile.rhiza)."""

import os
import shutil
import subprocess  # nosec
from pathlib import Path

import pytest

# Get absolute paths for executables to avoid S607 warnings from CodeFactor/Bandit
GIT = shutil.which("git") or "/usr/bin/git"

# Files required for the API test environment
REQUIRED_FILES = [
    "Makefile",
    "pyproject.toml",
    "README.md",  # is needed to do uv sync, etc.
]

# Folders to copy recursively
REQUIRED_FOLDERS = [
    ".rhiza",
]

OPTIONAL_FOLDERS = [
    "tests",  # for tests/tests.mk
    "docker",  # for docker/docker.mk, if referenced
    "book",
    "presentation",
]


@pytest.fixture
def setup_api_env(logger, root, tmp_path: Path):
    """Set up the Makefile API test environment in a temp folder."""
    logger.debug("Setting up Makefile API test env in: %s", tmp_path)

    # Copy files
    for filename in REQUIRED_FILES:
        src = root / filename
        if src.exists():
            shutil.copy(src, tmp_path / filename)
        else:
            pytest.fail(f"Required file {filename} not found in root")

    # Copy required directories
    for folder in REQUIRED_FOLDERS:
        src = root / folder
        if src.exists():
            dest = tmp_path / folder
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            pytest.fail(f"Required folder {folder} not found in root")

    # Copy optional directories
    for folder in OPTIONAL_FOLDERS:
        src = root / folder
        if src.exists():
            dest = tmp_path / folder
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)

    # Create .rhiza/make.d and ensure no local.mk exists initially
    (tmp_path / ".rhiza" / "make.d").mkdir(parents=True, exist_ok=True)
    if (tmp_path / "local.mk").exists():
        (tmp_path / "local.mk").unlink()

    # Initialize git repo for rhiza tools (required for sync/validate)
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)  # nosec
    # Configure git user for commits if needed (some rhiza checks might need commits)
    subprocess.run([GIT, "config", "user.email", "you@example.com"], cwd=tmp_path, check=True, capture_output=True)  # nosec
    subprocess.run([GIT, "config", "user.name", "Rhiza Test"], cwd=tmp_path, check=True, capture_output=True)  # nosec
    # Add origin remote to simulate being in the rhiza repo (triggers the skip logic in rhiza.mk)
    subprocess.run(
        [GIT, "remote", "add", "origin", "https://github.com/jebel-quant/rhiza.git"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )  # nosec

    # Move to tmp dir
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_cwd)


# Import run_make from local conftest
from api.conftest import run_make  # noqa: E402


def test_api_delegation(logger, setup_api_env):
    """Test that 'make help' works and delegates to .rhiza/rhiza.mk."""
    result = run_make(logger, ["help"], dry_run=False)
    assert result.returncode == 0
    # "Rhiza Workflows" is a section in .rhiza/rhiza.mk
    assert "Rhiza Workflows" in result.stdout

    # Core targets from .rhiza/make.d/ should be available
    assert "test" in result.stdout or "install" in result.stdout


def test_minimal_setup_works(logger, setup_api_env):
    """Test that make works even if optional folders (tests, docker, etc.) are missing."""
    # Remove optional folders
    for folder in OPTIONAL_FOLDERS:
        p = setup_api_env / folder
        if p.exists():
            shutil.rmtree(p)

    # Also remove files that might be copied if they were in the root?
    # Just mainly folders.

    # Run make help
    result = run_make(logger, ["help"], dry_run=False)
    assert result.returncode == 0

    # Check that core rhiza targets exist
    assert "Rhiza Workflows" in result.stdout
    assert "sync" in result.stdout

    # Note: docker-build and other targets from .rhiza/make.d/ are always present
    # but they gracefully skip if their respective folders/files don't exist.
    # This is by design - targets are always available but handle missing resources.


def test_extension_mechanism(logger, setup_api_env):
    """Test that custom targets can be added in the root Makefile."""
    # Add a custom target to the root Makefile (before include line)
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    # Insert custom target before the include line
    new_content = (
        """.PHONY: custom-target
custom-target:
	@echo "Running custom target"

"""
        + original
    )
    makefile.write_text(new_content)

    result = run_make(logger, ["custom-target"], dry_run=False)
    assert result.returncode == 0
    assert "Running custom target" in result.stdout


def test_local_override(logger, setup_api_env):
    """Test that local.mk is included and can match targets."""
    local_file = setup_api_env / "local.mk"
    local_file.write_text("""
.PHONY: local-target
local-target:
	@echo "Running local target"
""")

    result = run_make(logger, ["local-target"], dry_run=False)
    assert result.returncode == 0
    assert "Running local target" in result.stdout


def test_local_override_pre_hook(logger, setup_api_env):
    """Test using local.mk to override a pre-hook."""
    local_file = setup_api_env / "local.mk"
    # We override pre-sync to print a marker (using double-colon to match rhiza.mk)
    local_file.write_text("""
pre-sync::
	@echo "[[LOCAL_PRE_SYNC]]"
""")

    # Run sync in dry-run.
    # Note: Makefile.rhiza defines pre-sync as empty rule (or with @:).
    # Make warns if we redefine a target unless it's a double-colon rule or we are careful.
    # But usually the last one loaded wins or they merge if double-colon.
    # The current definition in Makefile.rhiza is `pre-sync: ; @echo ...` or similar.
    # Wait, I defined it as `pre-sync: ; @:` (single colon).
    # So redefining it in local.mk (which is included AFTER) might trigger a warning but should work.

    result = run_make(logger, ["sync"], dry_run=False)
    # We might expect a warning about overriding commands for target `pre-sync`
    # checking stdout/stderr for the marker

    assert "[[LOCAL_PRE_SYNC]]" in result.stdout


def test_hook_execution_order(logger, setup_api_env):
    """Define hooks in root Makefile and verify execution order."""
    # Add hooks to root Makefile (before include line)
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        """pre-sync::
	@echo "STARTING_SYNC"

post-sync::
	@echo "FINISHED_SYNC"

"""
        + original
    )
    makefile.write_text(new_content)

    result = run_make(logger, ["sync"], dry_run=False)
    assert result.returncode == 0
    output = result.stdout

    # Check that markers are present
    assert "STARTING_SYNC" in output
    assert "FINISHED_SYNC" in output

    # Check order: STARTING_SYNC comes before FINISHED_SYNC
    start_index = output.find("STARTING_SYNC")
    finish_index = output.find("FINISHED_SYNC")
    assert start_index < finish_index


def test_override_core_target(logger, setup_api_env):
    """Verify that the root Makefile can override a core target (with warning)."""
    # Override 'fmt' which is defined in quality.mk
    # Add override AFTER the include line so it takes precedence
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        original
        + """
fmt:
	@echo "CUSTOM_FMT"
"""
    )
    makefile.write_text(new_content)

    result = run_make(logger, ["fmt"], dry_run=False)
    assert result.returncode == 0
    # It should run the custom one because it's defined after the include
    assert "CUSTOM_FMT" in result.stdout

    # We expect a warning on stderr about overriding
    assert "warning: overriding" in result.stderr.lower()
    assert "fmt" in result.stderr.lower()


def test_global_variable_override(logger, setup_api_env):
    """Test that global variables can be overridden in the root Makefile.

    This tests the pattern documented in CUSTOMIZATION.md:
    Set variables before the include line to override defaults.
    """
    # Add variable override to root Makefile (before include line)
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        """# Override default coverage threshold (defaults to 90)
COVERAGE_FAIL_UNDER := 42
export COVERAGE_FAIL_UNDER

"""
        + original
    )
    makefile.write_text(new_content)

    result = run_make(logger, ["print-COVERAGE_FAIL_UNDER"], dry_run=False)
    assert result.returncode == 0
    assert "42" in result.stdout


def test_pre_install_hook(logger, setup_api_env):
    """Test that pre-install hooks are executed before install.

    This tests the hook pattern documented in CUSTOMIZATION.md.
    """
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        """pre-install::
	@echo "[[PRE_INSTALL_HOOK]]"

"""
        + original
    )
    makefile.write_text(new_content)

    # Run install in dry-run mode to avoid actual installation
    result = run_make(logger, ["install"], dry_run=True)
    assert result.returncode == 0
    # In dry-run mode, the echo command is printed (not executed)
    assert "PRE_INSTALL_HOOK" in result.stdout


def test_post_install_hook(logger, setup_api_env):
    """Test that post-install hooks are executed after install.

    This tests the hook pattern documented in CUSTOMIZATION.md.
    """
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        """post-install::
	@echo "[[POST_INSTALL_HOOK]]"

"""
        + original
    )
    makefile.write_text(new_content)

    # Run install in dry-run mode
    result = run_make(logger, ["install"], dry_run=True)
    assert result.returncode == 0
    assert "POST_INSTALL_HOOK" in result.stdout


def test_multiple_hooks_accumulate(logger, setup_api_env):
    """Test that multiple hook definitions accumulate rather than override.

    This is a key feature of double-colon rules: the root Makefile and
    local.mk can both add to the same hook without conflicts.
    """
    # Add hook in root Makefile
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        """pre-sync::
	@echo "[[HOOK_A]]"

"""
        + original
    )
    makefile.write_text(new_content)

    # Add another hook in local.mk
    (setup_api_env / "local.mk").write_text("""pre-sync::
	@echo "[[HOOK_B]]"
""")

    result = run_make(logger, ["sync"], dry_run=False)
    assert result.returncode == 0
    # Both hooks should be present
    assert "[[HOOK_A]]" in result.stdout
    assert "[[HOOK_B]]" in result.stdout


def test_variable_override_before_include(logger, setup_api_env):
    """Test that variables set before include take precedence.

    Variables defined in the root Makefile before the include line
    should be available throughout the build.
    """
    # Set a variable and use it in a target (before include)
    makefile = setup_api_env / "Makefile"
    original = makefile.read_text()
    new_content = (
        """MY_CUSTOM_VAR := hello

.PHONY: show-var
show-var:
	@echo "MY_VAR=$(MY_CUSTOM_VAR)"

"""
        + original
    )
    makefile.write_text(new_content)

    result = run_make(logger, ["show-var"], dry_run=False)
    assert result.returncode == 0
    assert "MY_VAR=hello" in result.stdout
