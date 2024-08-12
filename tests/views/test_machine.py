"""Tests for /machine API endpoints."""

from flask.testing import FlaskClient
from werkzeug.test import TestResponse


class TestUpdate:
    """Tests for /machine/update API endpoint."""

    def test_noop_update_idle_machine(self, client: FlaskClient) -> None:
        """Test for API index response."""
        response: TestResponse = client.post("/api/machine/update", json={"foo": "bar"})
        assert response.status_code == 501
        assert response.json == {"error": "not implemented"}


"""
Questions:

1. Where do I load the machine/user configs? In create_app()?
2. Do I _need_ to use `app.test_client()` via the pytest fixture, or can I just
import create_app() here and call its .test_client() within my test methods?
3. If not, how do I handle setup of the configs unique for each
"""
