"""Integration test for .rhiza/make.d/test.mk to verify that it handles the case of missing test files correctly."""

from test_utils import run_make


def test_missing_tests_warning(git_repo, logger):
    """Test that missing tests trigger a warning but do not fail (exit 0)."""
    # 1. Setup a minimal Makefile in the test repo
    # We include .rhiza/make.d/test.mk but mock the 'install' dependency
    # and provide color variables used in the script.
    makefile_content = r"""
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Define folders expected by test.mk
TESTS_FOLDER := tests
SOURCE_FOLDER := src
VENV := .venv

# Mock install to avoid actual installation in test
install:
	@echo "Mock install"

# Include the target under test
include .rhiza/make.d/test.mk
"""
    (git_repo / "Makefile").write_text(makefile_content, encoding="utf-8")

    # 2. Ensure 'tests' folder exists but is empty/has no python test files
    tests_dir = git_repo / "tests"
    if tests_dir.exists():
        import shutil

        shutil.rmtree(tests_dir)
    tests_dir.mkdir()

    # 3. Run 'make test'
    # We use dry_run=False so the shell commands in the recipe actually execute.
    # The 'check=False' allows us to assert the return code ourselves,
    # though we expect 0 now.
    result = run_make(logger, ["test"], check=False, dry_run=False)

    # 4. output for debugging
    logger.info("make stdout: %s", result.stdout)
    logger.info("make stderr: %s", result.stderr)

    # 5. Verify results
    assert result.returncode == 0, "make test should exit with 0 when no tests found"

    # The warning message matches what we put in test.mk
    # "No test files found in {TESTS_FOLDER}, skipping tests"
    assert "No test files found in tests, skipping tests" in result.stdout
