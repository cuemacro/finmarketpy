"""Tests for the GitHub Agentic Workflows (gh-aw) Makefile targets using safe dry-runs.

These tests validate that the gh-aw.mk targets are correctly exposed
and emit the expected commands without actually executing them.
"""

from __future__ import annotations

# Import run_make from local conftest (setup_tmp_makefile is autouse)
from api.conftest import run_make


def test_gh_aw_targets_exist(logger):
    """Verify that gh-aw targets are listed in help."""
    result = run_make(logger, ["help"], dry_run=False)
    output = result.stdout

    expected_targets = [
        "install-gh-aw",
        "gh-aw-compile",
        "gh-aw-compile-strict",
        "gh-aw-status",
        "gh-aw-run",
        "gh-aw-init",
        "gh-aw-secrets",
        "gh-aw-logs",
        "gh-aw-validate",
        "gh-aw-setup",
    ]

    for target in expected_targets:
        assert target in output, f"Target {target} not found in help output"


def test_install_gh_aw_dry_run(logger):
    """Verify install-gh-aw target dry-run."""
    result = run_make(logger, ["install-gh-aw"])
    assert result.returncode == 0


def test_gh_aw_compile_dry_run(logger):
    """Verify gh-aw-compile target dry-run."""
    result = run_make(logger, ["gh-aw-compile"])
    assert result.returncode == 0


def test_gh_aw_compile_strict_dry_run(logger):
    """Verify gh-aw-compile-strict target dry-run."""
    result = run_make(logger, ["gh-aw-compile-strict"])
    assert result.returncode == 0


def test_gh_aw_status_dry_run(logger):
    """Verify gh-aw-status target dry-run."""
    result = run_make(logger, ["gh-aw-status"])
    assert result.returncode == 0


def test_gh_aw_init_dry_run(logger):
    """Verify gh-aw-init target dry-run."""
    result = run_make(logger, ["gh-aw-init"])
    assert result.returncode == 0


def test_gh_aw_secrets_dry_run(logger):
    """Verify gh-aw-secrets target dry-run."""
    result = run_make(logger, ["gh-aw-secrets"])
    assert result.returncode == 0


def test_gh_aw_logs_dry_run(logger):
    """Verify gh-aw-logs target dry-run."""
    result = run_make(logger, ["gh-aw-logs"])
    assert result.returncode == 0


def test_gh_aw_validate_dry_run(logger):
    """Verify gh-aw-validate target dry-run."""
    result = run_make(logger, ["gh-aw-validate"])
    assert result.returncode == 0


def test_gh_aw_setup_dry_run(logger):
    """Verify gh-aw-setup target dry-run."""
    result = run_make(logger, ["gh-aw-setup"])
    # gh-aw-setup is interactive, so dry-run should succeed without interaction
    assert result.returncode == 0
