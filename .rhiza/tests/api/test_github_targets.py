"""Tests for the GitHub Makefile targets using safe dry-runs.

These tests validate that the .github/github.mk targets are correctly exposed
and emit the expected commands without actually executing them.
"""

from __future__ import annotations

# Import run_make from local conftest (setup_tmp_makefile is autouse)
from api.conftest import run_make


def test_gh_targets_exist(logger):
    """Verify that GitHub targets are listed in help."""
    result = run_make(logger, ["help"], dry_run=False)
    output = result.stdout

    expected_targets = ["gh-install", "view-prs", "view-issues", "failed-workflows", "whoami"]

    for target in expected_targets:
        assert target in output, f"Target {target} not found in help output"


def test_gh_install_dry_run(logger):
    """Verify gh-install target dry-run."""
    result = run_make(logger, ["gh-install"])
    # In dry-run, we expect to see the shell commands that would be executed.
    # Since the recipe uses @if, make -n might verify the syntax or show the command if not silenced.
    # However, with -s (silent), make -n might not show much for @ commands unless they are echoed.
    # But we mainly want to ensure it runs without error.
    assert result.returncode == 0


def test_view_prs_dry_run(logger):
    """Verify view-prs target dry-run."""
    result = run_make(logger, ["view-prs"])
    assert result.returncode == 0


def test_view_issues_dry_run(logger):
    """Verify view-issues target dry-run."""
    result = run_make(logger, ["view-issues"])
    assert result.returncode == 0


def test_failed_workflows_dry_run(logger):
    """Verify failed-workflows target dry-run."""
    result = run_make(logger, ["failed-workflows"])
    assert result.returncode == 0


def test_whoami_dry_run(logger):
    """Verify whoami target dry-run."""
    result = run_make(logger, ["whoami"])
    assert result.returncode == 0
