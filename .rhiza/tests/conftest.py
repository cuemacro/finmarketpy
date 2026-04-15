"""Pytest configuration and fixtures for setting up a mock git repository with versioning.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Provides test fixtures for testing git-based workflows and version management.

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
- S603 (subprocess without shell=True): All subprocess calls use lists of known commands (git),
  not user input, making them safe from shell injection
- S607 (subprocess with partial path): Using 'git' from PATH is acceptable in test fixtures
  as the test environment is controlled and git is a required development dependency
"""

import logging
import os
import pathlib
import shutil
import subprocess  # nosec B404 - subprocess module needed for git operations in test fixtures
import sys

import pytest

tests_root = pathlib.Path(__file__).resolve().parent
if str(tests_root) not in sys.path:
    sys.path.insert(0, str(tests_root))

from test_utils import GIT  # noqa: E402

MOCK_MAKE_SCRIPT = """#!/usr/bin/env python3
import sys

if len(sys.argv) > 1 and sys.argv[1] == "help":
    print("Mock Makefile Help")
    print("target: ## Description")
"""

MOCK_UV_SCRIPT = """#!/usr/bin/env python3
import sys
import re

try:
    from packaging.version import parse, InvalidVersion
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

def get_version():
    with open("pyproject.toml", "r") as f:
        content = f.read()
    match = re.search(r'version = "(.*?)"', content)
    return match.group(1) if match else "0.0.0"

def set_version(new_version):
    with open("pyproject.toml", "r") as f:
        content = f.read()
    new_content = re.sub(r'version = ".*?"', f'version = "{new_version}"', content)
    with open("pyproject.toml", "w") as f:
        f.write(new_content)

def bump_version(current, bump_type):
    major, minor, patch = map(int, current.split('.'))
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return current

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(1)

    if args[0] != "version":
        # It might be a uvx call if we use the same script, but let's keep them separate or handle it here.
        # For now, let's assume this is only for uv version commands as per original design.
        sys.exit(1)

    # uv version --short
    if "--short" in args and "--bump" not in args:
        print(get_version())
        return

    # uv version --bump <type> --dry-run --short
    if "--bump" in args and "--dry-run" in args and "--short" in args:
        bump_idx = args.index("--bump") + 1
        bump_type = args[bump_idx]
        current = get_version()
        print(bump_version(current, bump_type))
        return

    # uv version --bump <type> (actual update)
    if "--bump" in args and "--dry-run" not in args:
        bump_idx = args.index("--bump") + 1
        bump_type = args[bump_idx]
        current = get_version()
        new_ver = bump_version(current, bump_type)
        set_version(new_ver)
        return

    # uv version <version> --dry-run
    if len(args) >= 2 and not args[1].startswith("-") and "--dry-run" in args:
        version = args[1]
        if HAS_PACKAGING:
            try:
                parse(version)
            except InvalidVersion:
                sys.exit(1)
        else:
            # Simple validation: must start with a digit
            if not re.match(r"^\\d", version):
                sys.exit(1)
        # Just exit 0 if valid
        return

    # uv version <version> (actual update)
    if len(args) == 2 and not args[1].startswith("-"):
        set_version(args[1])
        return

if __name__ == "__main__":
    main()
"""


@pytest.fixture(scope="session")
def root():
    """Return the repository root directory as a pathlib.Path.

    Used by tests to locate files and scripts relative to the project root.
    """
    return pathlib.Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def logger():
    """Provide a session-scoped logger for tests.

    Returns:
        logging.Logger: Logger configured for the test session.
    """
    return logging.getLogger(__name__)


@pytest.fixture
def git_repo(root, tmp_path, monkeypatch):
    """Sets up a remote bare repo and a local clone with necessary files."""
    remote_dir = tmp_path / "remote.git"
    local_dir = tmp_path / "local"

    # 1. Create bare remote
    remote_dir.mkdir()
    subprocess.run([GIT, "init", "--bare", str(remote_dir)], check=True)  # nosec B603
    # Ensure the remote's default HEAD points to master for predictable behavior
    subprocess.run([GIT, "symbolic-ref", "HEAD", "refs/heads/master"], cwd=remote_dir, check=True)  # nosec B603

    # 2. Clone to local
    subprocess.run([GIT, "clone", str(remote_dir), str(local_dir)], check=True)  # nosec B603

    # Use monkeypatch to safely change cwd for the duration of the test
    monkeypatch.chdir(local_dir)

    # Ensure local default branch is 'master' to match test expectations
    subprocess.run([GIT, "checkout", "-b", "master"], check=True)  # nosec B603

    # Create pyproject.toml
    with open("pyproject.toml", "w") as f:
        f.write('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    # Create dummy uv.lock
    with open("uv.lock", "w") as f:
        f.write("")

    # Create bin/uv mock
    bin_dir = local_dir / "bin"
    bin_dir.mkdir()

    uv_path = bin_dir / "uv"
    with open(uv_path, "w") as f:
        f.write(MOCK_UV_SCRIPT)
    uv_path.chmod(0o755)

    make_path = bin_dir / "make"
    with open(make_path, "w") as f:
        f.write(MOCK_MAKE_SCRIPT)
    make_path.chmod(0o755)

    # Ensure our bin comes first on PATH so 'uv' resolves to mock
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")

    # Copy core Rhiza Makefiles
    (local_dir / ".rhiza").mkdir(parents=True, exist_ok=True)
    shutil.copy(root / ".rhiza" / "rhiza.mk", local_dir / ".rhiza" / "rhiza.mk")
    shutil.copy(root / "Makefile", local_dir / "Makefile")

    # Copy .rhiza/make.d/ directory (contains split makefiles)
    make_d_src = root / ".rhiza" / "make.d"
    if make_d_src.is_dir():
        make_d_dst = local_dir / ".rhiza" / "make.d"
        shutil.copytree(make_d_src, make_d_dst, dirs_exist_ok=True)

    book_src = root / "book"
    book_dst = local_dir / "book"
    if book_src.is_dir():
        shutil.copytree(book_src, book_dst, dirs_exist_ok=True)

    # Commit and push initial state
    subprocess.run([GIT, "config", "user.email", "test@example.com"], check=True)  # nosec B603
    subprocess.run([GIT, "config", "user.name", "Test User"], check=True)  # nosec B603
    subprocess.run([GIT, "add", "."], check=True)  # nosec B603
    subprocess.run([GIT, "commit", "-m", "Initial commit"], check=True)  # nosec B603
    subprocess.run([GIT, "push", "origin", "master"], check=True)  # nosec B603

    return local_dir
