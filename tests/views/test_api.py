"""Tests for API Views."""

import os
from pathlib import Path
from shutil import copy
from unittest.mock import patch

from flask import Flask
from flask.testing import FlaskClient
from freezegun import freeze_time
from werkzeug.test import TestResponse

from dm_mac.models.users import UsersConfig

from .flask_test_helpers import app_and_client


class TestIndex:
    """Tests for API Index view."""

    def test_index_response(self, tmp_path: Path) -> None:
        """Test for API index response."""
        app: Flask
        client: FlaskClient
        app, client = app_and_client(tmp_path)
        response: TestResponse = client.get("/api/")
        assert response.status_code == 200
        assert response.text == "Nothing to see here..."
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"


@freeze_time("2023-07-16 03:14:08", tz_offset=0)
class TestReloadUsers:
    """Tests for reloading users."""

    def test_no_change(self, tmp_path: Path, fixtures_path: str) -> None:
        """Test /reload-users with no change."""
        # set things up
        uconf: str = str(os.path.join(tmp_path, "users.json"))
        copy(os.path.join(fixtures_path, "users.json"), uconf)
        with patch.dict("os.environ", {"USERS_CONFIG": uconf}):
            app: Flask
            client: FlaskClient
            app, client = app_and_client(tmp_path)
            users: UsersConfig = app.config["USERS"]
            users.load_time = 123456.0
            before = [x.as_dict for x in users.users]
            response: TestResponse = client.post("/api/reload-users")
        assert response.status_code == 200
        assert response.json == {
            "updated": 0,
            "removed": 0,
            "added": 0,
        }
        users = app.config["USERS"]
        assert users.load_time == 1689477248.0
        after = [x.as_dict for x in users.users]
        assert before == after
        assert len(users.users_by_fob) == 4
        assert users.users_by_fob["8114346998"].account_id == "1"
        assert users.users_by_fob["8682768676"].account_id == "2"
        assert users.users_by_fob["0091703745"].account_id == "3"
        assert users.users_by_fob["0014916441"].account_id == "4"

    def test_exception(self, tmp_path: Path, fixtures_path: str) -> None:
        """Test /reload-users when an exception is raised."""
        # set things up
        uconf: str = str(os.path.join(tmp_path, "users.json"))
        copy(os.path.join(fixtures_path, "users.json"), uconf)
        with patch.dict("os.environ", {"USERS_CONFIG": uconf}):
            app: Flask
            client: FlaskClient
            app, client = app_and_client(tmp_path)
            users: UsersConfig = app.config["USERS"]
            users.load_time = 123456.0
            before = [x.as_dict for x in users.users]
            with open(uconf, "w") as fh:
                fh.write("\n")
            response: TestResponse = client.post("/api/reload-users")
        assert response.status_code == 500
        assert response.json == {"error": "Expecting value: line 2 column 1 (char 1)"}
        users = app.config["USERS"]
        assert users.load_time == 123456.0
        after = [x.as_dict for x in users.users]
        assert before == after

    def test_changed(self, tmp_path: Path, fixtures_path: str) -> None:
        """Test /reload-users with changes."""
        # set things up
        uconf: str = str(os.path.join(tmp_path, "users.json"))
        copy(os.path.join(fixtures_path, "users.json"), uconf)
        with patch.dict("os.environ", {"USERS_CONFIG": uconf}):
            app: Flask
            client: FlaskClient
            app, client = app_and_client(tmp_path)
            app.config["USERS"].load_time = 123456.0
            copy(os.path.join(fixtures_path, "users-changed.json"), uconf)
            response: TestResponse = client.post("/api/reload-users")
        assert response.status_code == 200
        assert response.json == {
            "updated": 2,
            "removed": 1,
            "added": 1,
        }
        users: UsersConfig = app.config["USERS"]
        assert users.load_time == 1689477248.0
        after = [x.as_dict for x in users.users]
        assert after == [
            {
                "account_id": "1",
                "authorizations": [
                    "Woodshop Orientation",
                    "Woodshop 201",
                    "Woodshop 101",
                    "Metal Mill",
                    "Metal Lathe",
                    "Foobar",
                ],
                "email": "munoz@example.net",
                "expiration_ymd": "2024-08-18",
                "first_name": "Ashley",
                "fob_codes": ["8114346998", "0012348901"],
                "full_name": "Ashley Williams",
                "preferred_name": "PAshley",
            },
            {
                "account_id": "3",
                "authorizations": ["Woodshop 201", "Woodshop 101"],
                "email": "rossdaniel@example.net",
                "expiration_ymd": "2024-08-19",
                "first_name": "Kenneth",
                "fob_codes": ["0091703745"],
                "full_name": "Kenneth Hunter",
                "preferred_name": "PKenneth",
            },
            {
                "account_id": "4",
                "authorizations": [
                    "Woodshop Orientation",
                    "Woodshop 201",
                    "Woodshop 101",
                    "Metal Mill",
                    "Metal Lathe",
                ],
                "email": "jason@jasonantman.com",
                "expiration_ymd": "2099-01-01",
                "first_name": "Jason",
                "fob_codes": ["0014916441"],
                "full_name": "Jason Antman",
                "preferred_name": "jantman",
            },
            {
                "account_id": "19",
                "authorizations": ["Woodshop Orientation", "Metal Mill"],
                "email": "tony37@example.net",
                "expiration_ymd": "2024-08-18",
                "first_name": "James",
                "fob_codes": ["8682768000"],
                "full_name": "James Smith",
                "preferred_name": "PJames",
            },
        ]
        assert len(users.users_by_fob) == 5
        assert users.users_by_fob["8114346998"].account_id == "1"
        assert users.users_by_fob["0012348901"].account_id == "1"
        assert "8682768676" not in users.users_by_fob
        assert users.users_by_fob["0091703745"].account_id == "3"
        assert users.users_by_fob["0014916441"].account_id == "4"
        assert users.users_by_fob["8682768000"].account_id == "19"
