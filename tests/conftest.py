"""Conftest for dm_mac - fixtures."""

import os

import pytest


@pytest.fixture()
def fixtures_path() -> str:
    """Return the absolute path to the fixtures directory."""
    testdir: str = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(testdir, "fixtures"))
