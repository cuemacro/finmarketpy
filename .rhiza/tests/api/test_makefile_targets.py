"""Tests for the Makefile targets and help output using safe dry-runs.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

These tests validate that the Makefile exposes expected targets and emits
the correct commands without actually executing them, by invoking `make -n`
(dry-run). We also pass `-s` to reduce noise in CI logs. This approach keeps
tests fast, portable, and free of side effects like network or environment
changes.
"""

from __future__ import annotations

import os

import pytest
from api.conftest import SPLIT_MAKEFILES, run_make, setup_rhiza_git_repo, strip_ansi


def assert_uvx_command_uses_version(output: str, tmp_path, command_fragment: str):
    """Assert uvx command uses .python-version when present, else fallback checks."""
    python_version_file = tmp_path / ".python-version"
    if python_version_file.exists():
        python_version = python_version_file.read_text().strip()
        assert f"uvx -p {python_version} {command_fragment}" in output
    else:
        assert "uvx -p" in output
        assert command_fragment in output


class TestMakefile:
    """Smoke tests for Makefile help and common targets using make -n."""

    def test_default_goal_is_help(self, logger):
        """Default goal should render the help index with known targets."""
        proc = run_make(logger)
        out = proc.stdout
        assert "Usage:" in out
        assert "Targets:" in out
        # ensure a few known targets appear in the help index
        for target in ["install", "fmt", "deptry", "test", "help"]:
            assert target in out

    def test_help_target(self, logger):
        """Explicit `make help` prints usage, targets, and section headers."""
        proc = run_make(logger, ["help"])
        out = proc.stdout
        assert "Usage:" in out
        assert "Targets:" in out
        assert "Bootstrap" in out or "Meta" in out  # section headers

    def test_fmt_target_dry_run(self, logger, tmp_path):
        """Fmt target should invoke pre-commit via uvx with Python version in dry-run output."""
        # Create clean environment without PYTHON_VERSION so Makefile reads from .python-version
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["fmt"], env=env)
        out = proc.stdout
        assert_uvx_command_uses_version(out, tmp_path, "pre-commit run --all-files")

    def test_deptry_target_dry_run(self, logger, tmp_path):
        """Deptry target should invoke deptry via uvx with Python version in dry-run output."""
        # Create a mock SOURCE_FOLDER directory so the deptry command runs
        source_folder = tmp_path / "src"
        source_folder.mkdir(exist_ok=True)

        # Update .env to set SOURCE_FOLDER
        env_file = tmp_path / ".rhiza" / ".env"
        env_content = env_file.read_text()
        env_content += "\nSOURCE_FOLDER=src\n"
        env_file.write_text(env_content)

        # Create clean environment without PYTHON_VERSION so Makefile reads from .python-version
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["deptry"], env=env)

        out = proc.stdout
        assert_uvx_command_uses_version(out, tmp_path, "deptry src")

    def test_typecheck_target_dry_run(self, logger, tmp_path):
        """Typecheck target should invoke ty via uv run in dry-run output."""
        # Create a mock SOURCE_FOLDER directory so the typecheck command runs
        source_folder = tmp_path / "src"
        source_folder.mkdir(exist_ok=True)

        # Update .env to set SOURCE_FOLDER
        env_file = tmp_path / ".rhiza" / ".env"
        env_content = env_file.read_text()
        env_content += "\nSOURCE_FOLDER=src\n"
        env_file.write_text(env_content)

        proc = run_make(logger, ["typecheck"])
        out = proc.stdout
        # Check for uv run command
        assert "uv run ty check src" in out

    def test_test_target_dry_run(self, logger):
        """Test target should invoke pytest via uv with coverage and HTML outputs in dry-run output."""
        proc = run_make(logger, ["test"])
        out = proc.stdout
        # Expect key steps
        assert "mkdir -p _tests/html-coverage _tests/html-report" in out
        # Check for uv command running pytest
        assert "uv run pytest" in out
        # Check for XML coverage report
        assert "--cov-report=xml:_tests/coverage.xml" in out

    def test_test_target_without_source_folder(self, logger, tmp_path):
        """Test target should run without coverage when SOURCE_FOLDER doesn't exist."""
        # Update .env to set SOURCE_FOLDER to a non-existent directory
        env_file = tmp_path / ".rhiza" / ".env"
        env_content = env_file.read_text()
        env_content += "\nSOURCE_FOLDER=nonexistent_src\n"
        env_file.write_text(env_content)

        # Create tests folder
        tests_folder = tmp_path / "tests"
        tests_folder.mkdir(exist_ok=True)

        proc = run_make(logger, ["test"])
        out = proc.stdout
        # Should see warning about missing source folder
        assert "if [ -d nonexistent_src ]" in out
        # Should still run pytest but without coverage flags
        assert "uv run pytest" in out
        assert "--html=_tests/html-report/report.html" in out

    def test_python_version_defaults_to_3_13_if_missing(self, logger, tmp_path):
        """`PYTHON_VERSION` should default to `3.13` if .python-version is missing."""
        # Ensure .python-version does not exist
        python_version_file = tmp_path / ".python-version"
        if python_version_file.exists():
            python_version_file.unlink()

        # Create clean environment without PYTHON_VERSION
        env = os.environ.copy()
        env.pop("PYTHON_VERSION", None)

        proc = run_make(logger, ["print-PYTHON_VERSION"], dry_run=False, env=env)
        out = strip_ansi(proc.stdout)
        assert "Value of PYTHON_VERSION:\n3.13" in out

    def test_uv_no_modify_path_is_exported(self, logger):
        """`UV_NO_MODIFY_PATH` should be set to `1` in the Makefile."""
        proc = run_make(logger, ["print-UV_NO_MODIFY_PATH"], dry_run=False)
        out = strip_ansi(proc.stdout)
        assert "Value of UV_NO_MODIFY_PATH:\n1" in out

    def test_that_target_coverage_is_configurable(self, logger):
        """Test target should respond to COVERAGE_FAIL_UNDER variable."""
        # Default case: ensure the flag is present
        proc = run_make(logger, ["test"])
        assert "--cov-fail-under=" in proc.stdout

        # Override case: ensure the flag takes the specific value
        proc_override = run_make(logger, ["test", "COVERAGE_FAIL_UNDER=42"])
        assert "--cov-fail-under=42" in proc_override.stdout

    def test_coverage_badge_target_dry_run(self, logger, tmp_path):
        """Coverage-badge target should invoke genbadge via uvx and push to gh-pages in dry-run output."""
        # Create a mock coverage JSON file so the target proceeds past the guard
        tests_dir = tmp_path / "_tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "coverage.json").write_text("{}")

        proc = run_make(logger, ["coverage-badge"])
        out = proc.stdout
        assert "genbadge coverage" in out
        assert "_tests/coverage.json" in out
        assert "coverage-badge.svg" in out
        assert "gh-pages" in out

    def test_coverage_badge_skips_without_source_folder(self, logger, tmp_path):
        """Coverage-badge target should include a guard check for SOURCE_FOLDER in dry-run output."""
        # Update .env to set SOURCE_FOLDER to a non-existent directory
        env_file = tmp_path / ".rhiza" / ".env"
        env_content = env_file.read_text()
        env_content += "\nSOURCE_FOLDER=nonexistent_src\n"
        env_file.write_text(env_content)

        proc = run_make(logger, ["coverage-badge"])
        out = proc.stdout
        # Should contain the guard check for missing source folder
        assert "if [ ! -d" in out
        assert "nonexistent_src" in out
        assert "skipping coverage-badge" in out

    def test_suppression_audit_target_dry_run(self, logger):
        """Suppression-audit target should invoke the Python audit script via uv run in dry-run output."""
        proc = run_make(logger, ["suppression-audit"])
        out = proc.stdout
        assert "uv run python" in out
        assert "suppression_audit.py" in out

    def test_license_target_dry_run(self, logger):
        """License target should invoke pip-licenses via uv run --with in dry-run output."""
        proc = run_make(logger, ["license"])
        out = proc.stdout
        assert "uv run --with pip-licenses pip-licenses" in out
        assert "--fail-on=" in out
        assert "GPL" in out

    def test_license_fail_on_is_configurable(self, logger):
        """License target should use the LICENSE_FAIL_ON variable for the fail-on list."""
        proc = run_make(logger, ["license", "LICENSE_FAIL_ON=MIT;Apache"])
        out = proc.stdout
        assert '--fail-on="MIT;Apache"' in out


class TestMakefileRootFixture:
    """Tests for root fixture usage in Makefile tests."""

    def test_makefile_exists_at_root(self, root):
        """Makefile should exist at repository root."""
        makefile = root / "Makefile"
        assert makefile.exists()
        assert makefile.is_file()

    def test_makefile_contains_targets(self, root):
        """Makefile should contain expected targets (including split files)."""
        makefile = root / "Makefile"
        content = makefile.read_text()

        # Read split Makefiles as well
        for split_file in SPLIT_MAKEFILES:
            split_path = root / split_file
            if split_path.exists():
                content += "\n" + split_path.read_text()

        expected_targets = ["install", "fmt", "test", "deptry", "help"]
        for target in expected_targets:
            assert f"{target}:" in content or f".PHONY: {target}" in content

    def test_validate_target_skips_in_rhiza_repo(self, logger):
        """Validate target should skip execution in rhiza repository."""
        setup_rhiza_git_repo()

        proc = run_make(logger, ["validate"], dry_run=False)
        # out = strip_ansi(proc.stdout)
        # assert "[INFO] Skipping validate in rhiza repository" in out
        assert proc.returncode == 0

    def test_sync_target_skips_in_rhiza_repo(self, logger):
        """Sync target should skip execution in rhiza repository."""
        setup_rhiza_git_repo()

        proc = run_make(logger, ["sync"], dry_run=False)
        # out = strip_ansi(proc.stdout)
        # assert "[INFO] Skipping sync in rhiza repository" in out
        assert proc.returncode == 0

    def test_sync_experimental_target_skips_in_rhiza_repo(self, logger):
        """Sync-experimental target should skip execution in rhiza repository."""
        setup_rhiza_git_repo()

        proc = run_make(logger, ["sync-experimental"], dry_run=False)
        assert proc.returncode == 0

    def test_materialize_target_is_deprecated(self, logger):
        """Materialize target should print a deprecation warning and delegate to sync."""
        setup_rhiza_git_repo()

        proc = run_make(logger, ["materialize"], dry_run=False)
        out = strip_ansi(proc.stdout)
        assert proc.returncode == 0
        assert "deprecated" in out.lower()
        assert "sync" in out


class TestMakeBump:
    """Tests for the 'make bump' target."""

    @pytest.fixture
    def mock_bin(self, tmp_path):
        """Create mock uv and uvx scripts in ./bin."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)

        uv = bin_dir / "uv"
        uv.write_text('#!/bin/sh\necho "[MOCK] uv $@"\n')
        uv.chmod(0o755)

        # Mock uvx to simulate version bump if arguments match
        uvx = bin_dir / "uvx"
        uvx_script = """#!/usr/bin/env python3
import sys
import re
from pathlib import Path

args = sys.argv[1:]
print(f"[MOCK] uvx {' '.join(args)}")

# Check if this is the bump command: "rhiza-tools>=0.3.3" bump
if "bump" in args:
    # Simulate bumping version in pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text()
        # Simple regex replacement for version
        # Assuming version = "0.1.0" -> "0.1.1"
        new_content = re.sub(r'version = "([0-9.]+)"', lambda m: f'version = "{m.group(1)[:-1]}{int(m.group(1)[-1]) + 1}"', content)
        pyproject.write_text(new_content)
        print(f"[MOCK] Bumped version in {pyproject}")
"""  # noqa: E501
        uvx.write_text(uvx_script)
        uvx.chmod(0o755)

        return bin_dir

    def test_bump_execution(self, logger, mock_bin, tmp_path):
        """Test 'make bump' execution with mocked tools and verify version change."""
        # Create dummy pyproject.toml with initial version
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('version = "0.1.0"\n[project]\nname = "test"\n')

        uv_bin = mock_bin / "uv"
        uvx_bin = mock_bin / "uvx"

        # Run make bump with dry_run=False to actually execute the shell commands
        result = run_make(logger, ["bump", f"UV_BIN={uv_bin}", f"UVX_BIN={uvx_bin}"], dry_run=False)

        # Verify that the mock tools were called
        assert "[MOCK] uvx rhiza-tools>=0.3.3 bump" in result.stdout
        assert "[MOCK] uv lock" in result.stdout

        # Verify that 'make install' was called (which calls uv sync)
        assert "[MOCK] uv sync" in result.stdout

        # Verify that the version was actually bumped by our mock
        new_content = pyproject.read_text()
        assert 'version = "0.1.1"' in new_content

    def test_bump_no_pyproject(self, logger, mock_bin, tmp_path):
        """Test 'make bump' execution without pyproject.toml."""
        # Ensure pyproject.toml does not exist
        pyproject = tmp_path / "pyproject.toml"
        if pyproject.exists():
            pyproject.unlink()

        uv_bin = mock_bin / "uv"
        uvx_bin = mock_bin / "uvx"

        result = run_make(logger, ["bump", f"UV_BIN={uv_bin}", f"UVX_BIN={uvx_bin}"], dry_run=False)

        # Check for warning message
        assert "No pyproject.toml found, skipping bump" in result.stdout

        # Ensure bump commands are NOT executed
        assert "[MOCK] uvx" not in result.stdout
        assert "[MOCK] uv lock" not in result.stdout
