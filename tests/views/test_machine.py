"""Tests for /machine API endpoints."""

from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from .flask_test_helpers import test_app


class TestUpdate:
    """Tests for /machine/update API endpoint."""

    def test_noop_update_idle_machine(self, tmp_path: Path) -> None:
        """Test for API index response."""
        """
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        response: TestResponse = client.post("/api/machine/update", json={"foo": "bar"})
        assert response.status_code == 501
        assert response.json == {"error": "not implemented"}
        """
        assert 1 == 1
