from pathlib import Path

import pytest


@pytest.fixture(scope="session", name="resource_dir")
def resource_fixture() -> Path:
    """resource fixture"""
    return Path(__file__).parent / "resources"
