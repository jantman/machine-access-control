"""Conftest for dm_mac - fixtures."""

import os
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def preserve_cwd() -> Generator[None, None, None]:
    """Preserve and restore the current working directory for each test.

    This ensures test isolation when tests use os.chdir().
    """
    original_cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(original_cwd)


@pytest.fixture()
def fixtures_path() -> str:
    """Return the absolute path to the fixtures directory."""
    testdir: str = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(testdir, "fixtures"))
