"""Tests for API Views."""

from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from .flask_test_helpers import test_app


class TestIndex:
    """Tests for API Index view."""

    def test_index_response(self, tmp_path: Path) -> None:
        """Test for API index response."""
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        response: TestResponse = client.get("/api/")
        assert response.status_code == 200
        assert response.text == "Nothing to see here..."
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"
