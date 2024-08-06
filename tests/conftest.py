"""Conftest for dm_mac - fixtures."""

from typing import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from dm_mac import create_app


@pytest.fixture()
def app() -> Generator[Flask, None, None]:
    """Test App fixture - app instance configured for testing."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Test Client for making requests to test app."""
    return app.test_client()
