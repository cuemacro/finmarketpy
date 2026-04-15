"""Shared test utilities.

Helper functions used across the test suite. Extracted from conftest.py to avoid
relative imports and __init__.py requirements in test directories.

This file and its associated utilities flow down via a SYNC action from the
jebel-quant/rhiza repository (https://github.com/jebel-quant/rhiza).

Security Notes:
- S101 (assert usage): Asserts are used in test utilities to validate test setup conditions
- S603 (subprocess without shell=True): All subprocess calls use command lists with known
  executables (git, make), not user input, preventing shell injection
- S607 (subprocess with partial path): Git and make are resolved from PATH via shutil.which()
  with fallbacks, which is safe in controlled test environments
"""

import re
import shutil
import subprocess  # nosec B404 - subprocess module needed for git/make operations in test utilities

# Get absolute paths for executables to avoid S607 warnings
GIT = shutil.which("git") or "/usr/bin/git"
MAKE = shutil.which("make") or "/usr/bin/make"


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def run_make(
    logger, args: list[str] | None = None, check: bool = True, dry_run: bool = True, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Run `make` with optional arguments and return the completed process.

    Args:
        logger: Logger used to emit diagnostic messages during the run
        args: Additional arguments for make
        check: If True, raise on non-zero return code
        dry_run: If True, use -n to avoid executing commands
        env: Optional environment variables to pass to the subprocess
    """
    cmd = [MAKE]
    if args:
        cmd.extend(args)
    # Use -s to reduce noise, -n to avoid executing commands
    flags = "-sn" if dry_run else "-s"
    cmd.insert(1, flags)
    logger.info("Running command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)  # nosec B603
    logger.debug("make exited with code %d", result.returncode)
    if result.stdout:
        logger.debug("make stdout (truncated to 500 chars):\n%s", result.stdout[:500])
    if result.stderr:
        logger.debug("make stderr (truncated to 500 chars):\n%s", result.stderr[:500])
    if check and result.returncode != 0:
        msg = f"make failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        raise AssertionError(msg)
    return result


def setup_rhiza_git_repo():
    """Initialize a git repository and set remote to rhiza."""
    subprocess.run([GIT, "init"], check=True, capture_output=True)  # nosec B603
    subprocess.run(  # nosec B603
        [GIT, "remote", "add", "origin", "https://github.com/jebel-quant/rhiza"],
        check=True,
        capture_output=True,
    )
