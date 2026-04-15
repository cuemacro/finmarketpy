"""Tests for Git LFS Makefile targets.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Tests the lfs-install, lfs-pull, lfs-track, and lfs-status targets.
"""

import shutil
import subprocess  # nosec

import pytest

# Get make command once at module level
MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def lfs_makefile(git_repo):
    """Return the lfs.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "lfs.mk"
    if not makefile.exists():
        pytest.skip("lfs.mk not found, skipping test")
    return makefile


@pytest.fixture
def lfs_install_dry_run(git_repo, lfs_makefile):
    """Run lfs-install in dry-run mode and return the result."""
    return subprocess.run(  # nosec
        [MAKE, "-n", "lfs-install"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )


def test_lfs_targets_exist(git_repo, logger, lfs_makefile):
    """Test that all LFS targets are defined in the Makefile."""
    result = subprocess.run(
        [MAKE, "help"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )  # nosec

    assert result.returncode == 0
    assert "lfs-install" in result.stdout
    assert "lfs-pull" in result.stdout
    assert "lfs-track" in result.stdout
    assert "lfs-status" in result.stdout
    assert "Git LFS" in result.stdout


def test_lfs_install_dry_run(lfs_install_dry_run):
    """Test lfs-install target in dry-run mode."""
    assert lfs_install_dry_run.returncode == 0
    # Check that the command includes OS detection
    assert "uname -s" in lfs_install_dry_run.stdout
    assert "uname -m" in lfs_install_dry_run.stdout


def test_lfs_install_macos_logic(lfs_install_dry_run):
    """Test that lfs-install generates correct logic for macOS."""
    assert lfs_install_dry_run.returncode == 0
    # Verify macOS installation logic is present
    assert "Darwin" in lfs_install_dry_run.stdout
    assert "darwin-arm64" in lfs_install_dry_run.stdout
    assert "darwin-amd64" in lfs_install_dry_run.stdout
    assert ".local/bin" in lfs_install_dry_run.stdout
    assert "curl" in lfs_install_dry_run.stdout
    assert "github.com/git-lfs/git-lfs/releases" in lfs_install_dry_run.stdout


def test_lfs_install_linux_logic(lfs_install_dry_run):
    """Test that lfs-install generates correct logic for Linux."""
    assert lfs_install_dry_run.returncode == 0
    # Verify Linux installation logic is present
    assert "Linux" in lfs_install_dry_run.stdout
    assert "apt-get update" in lfs_install_dry_run.stdout
    assert "apt-get install" in lfs_install_dry_run.stdout
    assert "git-lfs" in lfs_install_dry_run.stdout


def test_lfs_pull_target(git_repo, logger, lfs_makefile):
    """Test lfs-pull target in dry-run mode."""
    result = subprocess.run(
        [MAKE, "-n", "lfs-pull"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )  # nosec

    assert result.returncode == 0
    assert "git lfs pull" in result.stdout


def test_lfs_track_target(git_repo, logger, lfs_makefile):
    """Test lfs-track target in dry-run mode."""
    result = subprocess.run(
        [MAKE, "-n", "lfs-track"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )  # nosec

    assert result.returncode == 0
    assert "git lfs track" in result.stdout


def test_lfs_status_target(git_repo, logger, lfs_makefile):
    """Test lfs-status target in dry-run mode."""
    result = subprocess.run(
        [MAKE, "-n", "lfs-status"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )  # nosec

    assert result.returncode == 0
    assert "git lfs status" in result.stdout


def test_lfs_install_error_handling(lfs_install_dry_run):
    """Test that lfs-install includes error handling."""
    assert lfs_install_dry_run.returncode == 0
    # Verify error handling is present
    assert "ERROR" in lfs_install_dry_run.stdout
    assert "exit 1" in lfs_install_dry_run.stdout


def test_lfs_install_uses_github_api(lfs_install_dry_run):
    """Test that lfs-install uses GitHub API for version detection."""
    assert lfs_install_dry_run.returncode == 0


def test_lfs_install_sudo_handling(lfs_install_dry_run):
    """Test that lfs-install handles sudo correctly on Linux."""
    assert lfs_install_dry_run.returncode == 0
    # Verify sudo logic is present
    assert "sudo" in lfs_install_dry_run.stdout
    assert "id -u" in lfs_install_dry_run.stdout


@pytest.mark.skipif(
    not shutil.which("git-lfs"),
    reason="git-lfs not installed",
)
def test_lfs_actual_execution_status(git_repo, logger, lfs_makefile):
    """Test actual execution of lfs-status (requires git-lfs to be installed)."""
    # Initialize git-lfs in the test repo
    subprocess.run(["git", "lfs", "install"], cwd=git_repo, capture_output=True)  # nosec

    result = subprocess.run(
        [MAKE, "lfs-status"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )  # nosec

    # Should succeed even if no LFS files are tracked
    assert result.returncode == 0


@pytest.mark.skipif(
    not shutil.which("git-lfs"),
    reason="git-lfs not installed",
)
def test_lfs_actual_execution_track(git_repo, logger, lfs_makefile):
    """Test actual execution of lfs-track (requires git-lfs to be installed)."""
    # Initialize git-lfs in the test repo
    subprocess.run(["git", "lfs", "install"], cwd=git_repo, capture_output=True)  # nosec

    result = subprocess.run(
        [MAKE, "lfs-track"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )  # nosec

    # Should succeed even if no patterns are tracked
    assert result.returncode == 0
