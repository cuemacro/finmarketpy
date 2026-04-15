"""Tests for book.mk Makefile targets and the MKDOCS_EXTRA_PACKAGES variable."""

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


def test_mkdocs_extra_packages_variable_defined(book_makefile):
    """Test that MKDOCS_EXTRA_PACKAGES is declared with a default-empty value."""
    content = book_makefile.read_text()
    assert "MKDOCS_EXTRA_PACKAGES ?=" in content, "book.mk should declare MKDOCS_EXTRA_PACKAGES with a ?= default"


def test_mkdocs_extra_packages_used_in_build(book_makefile):
    """Test that MKDOCS_EXTRA_PACKAGES is spliced into the mkdocs build uvx command."""
    content = book_makefile.read_text()
    # The variable must appear on the same line as 'mkdocs build'
    build_lines = [line for line in content.splitlines() if "mkdocs build" in line]
    assert build_lines, "book.mk should contain a 'mkdocs build' invocation"
    assert any("$(MKDOCS_EXTRA_PACKAGES)" in line for line in build_lines), (
        "mkdocs build line should include $(MKDOCS_EXTRA_PACKAGES)"
    )


def test_mkdocs_extra_packages_used_in_serve(book_makefile):
    """Test that MKDOCS_EXTRA_PACKAGES is spliced into the mkdocs-serve uvx command."""
    content = book_makefile.read_text()
    serve_lines = [line for line in content.splitlines() if "mkdocs serve" in line]
    assert serve_lines, "book.mk should contain a 'mkdocs serve' invocation"
    assert any("$(MKDOCS_EXTRA_PACKAGES)" in line for line in serve_lines), (
        "mkdocs serve line should include $(MKDOCS_EXTRA_PACKAGES)"
    )


def test_mkdocs_build_dry_run_with_extra_packages(git_repo, book_makefile):
    """Test that passing MKDOCS_EXTRA_PACKAGES on the command line is accepted by make.

    Validates both a single package and multiple packages to confirm the variable
    correctly extends the uvx invocation in all cases.
    """
    for extra in [
        "--with mkdocs-graphviz",
        "--with mkdocs-graphviz --with mkdocs-mermaid2",
    ]:
        result = subprocess.run(  # nosec
            [MAKE, "-n", "book", f"MKDOCS_EXTRA_PACKAGES={extra}"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "no rule to make target" not in result.stderr.lower(), "book should be a defined target"
        assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
        # Each extra package flag should appear in the dry-run output
        for pkg in ["mkdocs-graphviz", "mkdocs-mermaid2"][: len(extra.split("--with")) - 1]:
            assert pkg in result.stdout, (
                f"MKDOCS_EXTRA_PACKAGES package '{pkg}' should be visible in the dry-run command"
            )
