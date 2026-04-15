"""Tests for the root pytest fixture that yields the repository root Path.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

This module ensures the fixture resolves to the true project root and that
expected files/directories exist, enabling other tests to locate resources
reliably.
"""

import pytest


class TestRootFixture:
    """Tests for the root fixture that provides repository root path."""

    def test_root_resolves_correctly_from_nested_location(self, root):
        """Root should correctly resolve to repository root from .rhiza/tests/."""
        conftest_path = root / ".rhiza" / "tests" / "conftest.py"
        assert conftest_path.exists()

    def test_root_contains_expected_directories(self, root):
        """Root should contain all expected project directories."""
        required_dirs = [".rhiza"]
        optional_dirs = ["src", "tests", "book"]  # src/ is optional (rhiza itself doesn't have one)

        for dirname in required_dirs:
            assert (root / dirname).exists(), f"Required directory {dirname} not found"

        # Check that at least one CI directory exists (.github or .gitlab)
        ci_dirs = [".github", ".gitlab"]
        if not any((root / ci_dir).exists() for ci_dir in ci_dirs):
            pytest.fail(f"At least one CI directory from {ci_dirs} must exist")

        for dirname in optional_dirs:
            if not (root / dirname).exists():
                pytest.skip(f"Optional directory {dirname} not present in this project")

    def test_root_contains_expected_files(self, root):
        """Root should contain all expected configuration files."""
        required_files = [
            "pyproject.toml",
            "README.md",
            "Makefile",
        ]
        optional_files = [
            "ruff.toml",
            ".gitignore",
            ".editorconfig",
        ]

        for filename in required_files:
            assert (root / filename).exists(), f"Required file {filename} not found"

        for filename in optional_files:
            if not (root / filename).exists():
                pytest.skip(f"Optional file {filename} not present in this project")
