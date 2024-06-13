"""Tests for API Views."""

from flask.testing import FlaskClient
from werkzeug.test import TestResponse


class TestIndex:
    """Tests for API Index view."""

    def test_index_response(self, client: FlaskClient):
        """Test for API index response."""
        response: TestResponse = client.get("/api/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"
