"""Tests for API Views."""

from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from .flask_test_helpers import app_and_client


class TestProm:
    """Tests for API Prometheus view."""

    def test_metrics_response(self, tmp_path: Path) -> None:
        """Test for API petrics response."""
        app: Flask
        client: FlaskClient
        app, client = app_and_client(tmp_path)
        response: TestResponse = client.get("/metrics")
        assert response.status_code == 200
        assert response.text == "foo"
        assert response.headers["Content-Type"] == "text/plain; charset=utf-8"
