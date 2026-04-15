"""Tests for book-related Makefile targets and their resilience."""

import shutil
import subprocess  # nosec

import pytest

MAKE = shutil.which("make") or "/usr/bin/make"


@pytest.fixture
def book_makefile(git_repo):
    """Return the book.mk path or skip tests if missing."""
    makefile = git_repo / ".rhiza" / "make.d" / "book.mk"
    if not makefile.exists():
        pytest.skip("book.mk not found, skipping test")
    return makefile


def test_no_book_folder(git_repo, book_makefile):
    """Test that make targets work gracefully when book folder is missing.

    Now that book-related targets are defined in .rhiza/make.d/, they are always
    available but check internally for the existence of the book folder.
    Using dry-run (-n) to test the target logic without actually executing.
    """
    if (git_repo / "book").exists():
        shutil.rmtree(git_repo / "book")
    assert not (git_repo / "book").exists()

    # Targets are now always defined via .rhiza/make.d/
    # Use dry-run to verify they exist and can be parsed
    for target in ["book"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)  # nosec
        # Target should exist (not "no rule to make target")
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/"
        )


def test_book_folder_but_no_mk(git_repo, book_makefile):
    """Test behavior when book folder exists but is empty.

    With the new architecture, targets are always defined in .rhiza/make.d/book.mk,
    so they should exist regardless of the book folder contents.
    """
    # ensure book folder exists but is empty
    if (git_repo / "book").exists():
        shutil.rmtree(git_repo / "book")
    # create an empty book folder
    (git_repo / "book").mkdir()

    # assert the book folder exists
    assert (git_repo / "book").exists()
    # assert the git_repo / "book" folder is empty
    assert not list((git_repo / "book").iterdir())

    # Targets are now always defined via .rhiza/make.d/
    # Use dry-run to verify they exist and can be parsed
    for target in ["book"]:
        result = subprocess.run([MAKE, "-n", target], cwd=git_repo, capture_output=True, text=True)  # nosec
        # Target should exist (not "no rule to make target")
        assert "no rule to make target" not in result.stderr.lower(), (
            f"Target {target} should be defined in .rhiza/make.d/"
        )


def test_book_folder(git_repo, book_makefile):
    """Test that .rhiza/make.d/book.mk defines the expected phony targets."""
    content = book_makefile.read_text()

    # get the list of phony targets from the Makefile
    phony_targets = [line.strip() for line in content.splitlines() if line.startswith(".PHONY:")]
    if not phony_targets:
        pytest.skip("No .PHONY targets found in book.mk")

    # Collect all targets from all .PHONY lines
    all_targets = set()
    for phony_line in phony_targets:
        targets = phony_line.split(":")[1].strip().split()
        all_targets.update(targets)

    expected_targets = {"book", "mkdocs-build", "test", "benchmark", "stress", "hypothesis-test"}
    assert expected_targets.issubset(all_targets), (
        f"Expected phony targets to include {expected_targets}, got {all_targets}"
    )


def test_book_noop_targets_defined(book_makefile):
    """Test that book.mk defines no-op fallback targets for build resilience.

    These no-op double-colon rules ensure 'make book' succeeds even when
    test.mk is not available or tests are not installed.
    """
    content = book_makefile.read_text()
    for target in ["test", "benchmark", "stress", "hypothesis-test"]:
        assert f"{target}::" in content, (
            f"book.mk should define a no-op '::' fallback for '{target}' to ensure build resilience"
        )


def test_book_without_logo_file(git_repo, book_makefile):
    """Test that book target works when LOGO_FILE is not set or empty.

    The build should succeed gracefully without a logo, and the generated
    HTML template should hide the logo element via onerror handler.
    """
    makefile = git_repo / "Makefile"
    if not makefile.exists():
        pytest.skip("Makefile not found")

    # Read current Makefile content
    content = makefile.read_text()

    # Remove or comment out LOGO_FILE if present
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if line.strip().startswith("LOGO_FILE"):
            # Comment out the line
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    makefile.write_text("\n".join(new_lines))

    # Dry-run the book target - it should still be valid
    result = subprocess.run([MAKE, "-n", "book"], cwd=git_repo, capture_output=True, text=True)  # nosec
    assert "no rule to make target" not in result.stderr.lower(), "book target should work without LOGO_FILE"
    # Should not have errors about missing logo variable
    assert result.returncode == 0, f"Dry-run failed: {result.stderr}"


def test_book_with_missing_logo_file(git_repo, book_makefile):
    """Test that book target warns when LOGO_FILE points to non-existent file.

    The build should succeed but emit a warning about the missing logo.
    """
    makefile = git_repo / "Makefile"
    if not makefile.exists():
        pytest.skip("Makefile not found")

    # Read current Makefile content and set LOGO_FILE to non-existent path
    content = makefile.read_text()
    lines = content.splitlines()
    new_lines = []
    logo_set = False
    for line in lines:
        if line.strip().startswith("LOGO_FILE"):
            new_lines.append("LOGO_FILE=nonexistent/path/logo.svg")
            logo_set = True
        else:
            new_lines.append(line)
    if not logo_set:
        # Insert LOGO_FILE before the include line
        for i, line in enumerate(new_lines):
            if line.strip().startswith("include"):
                new_lines.insert(i, "LOGO_FILE=nonexistent/path/logo.svg")
                break
    makefile.write_text("\n".join(new_lines))

    # Dry-run should still succeed
    result = subprocess.run([MAKE, "-n", "book"], cwd=git_repo, capture_output=True, text=True)  # nosec
    assert result.returncode == 0, f"Dry-run failed with missing logo: {result.stderr}"
