"""Tests for the .rhiza/requirements folder structure.

This test ensures that the requirements folder exists and contains the expected
requirement files for development dependencies.
"""

from typing import ClassVar


class TestRequirementsFolder:
    """Tests for the .rhiza/requirements folder structure."""

    # Expected requirements files
    EXPECTED_REQUIREMENTS_FILES: ClassVar[list[str]] = [
        # "tests.txt",   # may not be present in all repositories
        # "marimo.txt",  # may not be present in all repositories
        "docs.txt",
        "tools.txt",
    ]

    def test_requirements_folder_exists(self, root):
        """Requirements folder should exist in .rhiza directory."""
        requirements_dir = root / ".rhiza" / "requirements"
        assert requirements_dir.exists(), ".rhiza/requirements directory should exist"
        assert requirements_dir.is_dir(), ".rhiza/requirements should be a directory"

    def test_requirements_files_exist(self, root):
        """All expected requirements files should exist."""
        requirements_dir = root / ".rhiza" / "requirements"
        for filename in self.EXPECTED_REQUIREMENTS_FILES:
            filepath = requirements_dir / filename
            assert filepath.exists(), f"{filename} should exist in requirements folder"
            assert filepath.is_file(), f"{filename} should be a file"

    def test_requirements_files_not_empty(self, root):
        """Requirements files should not be empty."""
        requirements_dir = root / ".rhiza" / "requirements"
        for filename in self.EXPECTED_REQUIREMENTS_FILES:
            filepath = requirements_dir / filename
            content = filepath.read_text()
            # Filter out comments and empty lines
            lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
            assert len(lines) > 0, f"{filename} should contain at least one dependency"

    def test_readme_exists_in_requirements_folder(self, root):
        """README.md should exist in requirements folder."""
        readme_path = root / ".rhiza" / "requirements" / "README.md"
        assert readme_path.exists(), "README.md should exist in requirements folder"
        assert readme_path.is_file(), "README.md should be a file"
        content = readme_path.read_text()
        assert len(content) > 0, "README.md should not be empty"
