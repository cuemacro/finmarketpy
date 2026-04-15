"""Test configuration and shared fixtures.

Security note: test code uses assert statements (S101), which are safe and
intentional in the pytest context. subprocess calls (S603/S607) in tests run
only known, fixed commands and are reviewed to prevent injection.
"""

from pathlib import Path

import pytest


@pytest.fixture(scope="session", name="resource_dir")
def resource_fixture() -> Path:
    """Resource fixture."""
    return Path(__file__).parent / "resources"
