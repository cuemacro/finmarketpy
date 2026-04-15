"""Integration test to verify VIRTUAL_ENV is unset for uv commands."""

import os

from test_utils import run_make


def test_virtual_env_not_exported(git_repo, logger):
    """Test that VIRTUAL_ENV is not exported to child processes when set in the environment."""
    # 1. Setup a minimal Makefile that includes rhiza.mk
    makefile_content = r"""
# Include rhiza.mk which has 'unexport VIRTUAL_ENV'
include .rhiza/rhiza.mk

# Create a test target that checks if VIRTUAL_ENV is exported
.PHONY: test-env
test-env:
	@echo "VIRTUAL_ENV in shell: '$$VIRTUAL_ENV'"
"""
    (git_repo / "Makefile").write_text(makefile_content, encoding="utf-8")

    # 2. Set VIRTUAL_ENV in the environment (simulating an activated venv)
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = "/some/absolute/path/.venv"

    # 3. Run 'make test-env' with VIRTUAL_ENV set
    result = run_make(logger, ["test-env"], check=True, dry_run=False, env=env)

    # 4. Output for debugging
    logger.info("make stdout: %s", result.stdout)
    logger.info("make stderr: %s", result.stderr)

    # 5. Verify that VIRTUAL_ENV is empty in the shell (not exported)
    # The output should contain "VIRTUAL_ENV in shell: ''"
    assert "VIRTUAL_ENV in shell: ''" in result.stdout, (
        f"VIRTUAL_ENV should be empty in shell commands, but got: {result.stdout}"
    )
