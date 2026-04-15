"""Stress tests for Git operations.

Tests Git operations under concurrent load to verify stability and
proper handling of concurrent Git commands.
"""

from __future__ import annotations

import concurrent.futures
import shutil
import subprocess
from pathlib import Path

import pytest

# Get absolute paths for executables
GIT = shutil.which("git") or "/usr/bin/git"


@pytest.mark.stress
def test_concurrent_git_status(root: Path, concurrent_workers: int):
    """Test concurrent git status operations.

    Verifies that multiple git status commands can run concurrently
    without conflicts.
    """

    def run_git_status():
        """Run git status and return success status."""
        result = subprocess.run(  # nosec
            [GIT, "--no-pager", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_git_status) for _ in range(concurrent_workers * 2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_git_log(root: Path, concurrent_workers: int):
    """Test concurrent git log operations.

    Verifies that multiple git log commands can run concurrently.
    """

    def run_git_log():
        """Run git log and return success status."""
        result = subprocess.run(  # nosec
            [GIT, "--no-pager", "log", "-1", "--oneline"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_git_log) for _ in range(concurrent_workers * 2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_repeated_git_operations(root: Path, stress_iterations: int):
    """Test repeated Git read operations.

    Verifies that repeated git operations don't degrade or leak resources.
    """
    results = []

    commands = [
        [GIT, "--no-pager", "status", "--short"],
        [GIT, "--no-pager", "log", "-1", "--oneline"],
        [GIT, "--no-pager", "branch", "--list"],
        [GIT, "rev-parse", "HEAD"],
    ]

    for i in range(stress_iterations):
        cmd = commands[i % len(commands)]
        result = subprocess.run(  # nosec
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
        )
        results.append(result.returncode == 0)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_git_diff(root: Path, concurrent_workers: int):
    """Test concurrent git diff operations.

    Verifies that multiple git diff commands can run concurrently.
    """

    def run_git_diff():
        """Run git diff and return success status."""
        result = subprocess.run(  # nosec
            [GIT, "--no-pager", "diff", "--name-only"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_git_diff) for _ in range(concurrent_workers * 2)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_rapid_git_rev_parse(root: Path, stress_iterations: int):
    """Test rapid git rev-parse operations.

    Verifies that rapid git rev-parse calls (used in release script)
    work correctly without degradation.
    """
    results = []

    for _ in range(stress_iterations):
        result = subprocess.run(  # nosec
            [GIT, "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        results.append(result.returncode == 0 and len(result.stdout.strip()) == 40)

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"


@pytest.mark.stress
def test_concurrent_git_show(root: Path, concurrent_workers: int):
    """Test concurrent git show operations.

    Verifies that multiple git show commands can run concurrently.
    """

    def run_git_show():
        """Run git show and return success status."""
        result = subprocess.run(  # nosec
            [GIT, "--no-pager", "show", "HEAD", "--stat"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(run_git_show) for _ in range(concurrent_workers)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"
