"""Dependency health tests — validate requirements files and pyproject.toml content."""

import re
import tomllib


def test_pyproject_has_requires_python(root):
    """Verify that pyproject.toml declares requires-python in [project]."""
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)

    assert "project" in pyproject, "[project] section missing from pyproject.toml"
    assert "requires-python" in pyproject["project"], "requires-python missing from [project] section"

    requires_python = pyproject["project"]["requires-python"]
    assert isinstance(requires_python, str), "requires-python must be a string"
    assert requires_python.strip(), "requires-python cannot be empty"


def test_requirements_files_are_valid_pip_specifiers(root):
    """Verify that all lines in requirements files are valid pip requirement specifiers."""
    requirements_dir = root / ".rhiza" / "requirements"
    assert requirements_dir.exists(), ".rhiza/requirements directory not found"

    # Pattern for valid requirement specifier (simplified check)
    # Matches: package, package>=1.0, package[extra], git+https://...
    valid_specifier_pattern = re.compile(
        r"^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?|git\+https?://)",
        re.IGNORECASE,
    )

    for req_file in requirements_dir.glob("*.txt"):
        if req_file.name == "README.md":
            continue

        with req_file.open() as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Basic validation: line should start with a valid package name or git URL
                assert valid_specifier_pattern.match(line), (
                    f"{req_file.name}:{line_num} - Invalid requirement specifier: {line}"
                )


def test_no_duplicate_packages_across_requirements(root):
    """Verify that no package appears in multiple requirements files."""
    requirements_dir = root / ".rhiza" / "requirements"
    assert requirements_dir.exists(), ".rhiza/requirements directory not found"

    # Known packages that intentionally appear in multiple files
    # python-dotenv is used by both test infrastructure and development tools
    allowed_duplicates = {"python-dotenv"}

    # Map of package name (lowercase) to list of files it appears in
    package_locations = {}

    # Pattern to extract package name from requirement line
    # Matches the package name before any version specifier, extra, or URL fragment
    package_name_pattern = re.compile(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)", re.IGNORECASE)

    for req_file in requirements_dir.glob("*.txt"):
        if req_file.name == "README.md":
            continue

        with req_file.open() as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Extract package name
                match = package_name_pattern.match(line)
                if match:
                    package_name = match.group(1).lower()

                    if package_name not in package_locations:
                        package_locations[package_name] = []

                    package_locations[package_name].append(req_file.name)

    # Find duplicates (excluding allowed ones)
    duplicates = {
        pkg: files for pkg, files in package_locations.items() if len(files) > 1 and pkg not in allowed_duplicates
    }

    if duplicates:
        duplicate_list = [f"{pkg} ({', '.join(files)})" for pkg, files in duplicates.items()]
        msg = f"Packages found in multiple requirements files: {', '.join(duplicate_list)}"
        raise AssertionError(msg)


def test_dotenv_in_test_requirements(root):
    """Verify that python-dotenv is listed in tests.txt (test suite depends on it)."""
    tests_req_path = root / ".rhiza" / "requirements" / "tests.txt"
    assert tests_req_path.exists(), "tests.txt not found"

    with tests_req_path.open() as f:
        content = f.read().lower()

    # Check for python-dotenv (case-insensitive)
    assert "python-dotenv" in content, "python-dotenv not found in tests.txt (required by test suite)"
