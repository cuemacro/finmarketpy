from pathlib import Path  # noqa: D100

import pytest


@pytest.fixture(scope="session", name="resource_dir")
def resource_fixture() -> Path:
    """Resource fixture."""
    return Path(__file__).parent / "resources"
