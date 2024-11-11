"""Tests for models.users."""

import json
import os
import shutil
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from jsonschema.exceptions import ValidationError

from dm_mac.models.users import User
from dm_mac.models.users import UsersConfig


class TestUsersConfig:
    """Tests for models.users.UsersConfig."""

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_default_config(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf_path: str = os.path.join(
            fixtures_path, "test_neongetter", "users-happy.json"
        )
        shutil.copy(conf_path, os.path.join(tmp_path, "users.json"))
        os.chdir(tmp_path)
        cls: UsersConfig = UsersConfig()
        assert len(cls.users) == 594
        assert len(cls.users_by_fob) == 594
        assert cls.load_time == 1689477248.0

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_config_path(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf: List[Dict[str, Any]] = [
            {
                "account_id": "410",
                "authorizations": ["Dimensioning Tools", "Woodshop 101"],
                "email": "brian36@example.com",
                "expiration_ymd": "2024-08-27",
                "fob_codes": ["0725858614"],
                "full_name": "Andrew Schwartz",
                "first_name": "Andrew",
                "preferred_name": "PAndrew",
            },
            {
                "account_id": "411",
                "authorizations": [],
                "email": "zyoung@example.org",
                "expiration_ymd": "2024-08-10",
                "fob_codes": ["0913350505"],
                "full_name": "Tyler Young Jr.",
                "first_name": "Tyler",
                "preferred_name": "PTyler",
            },
            {
                "account_id": "412",
                "authorizations": ["Glowforge"],
                "email": "joshua99@example.net",
                "expiration_ymd": "2024-12-18",
                "fob_codes": ["5683773370"],
                "full_name": "Rachel Richmond",
                "first_name": "Rachel",
                "preferred_name": "PRachel",
            },
        ]
        cpath: str = str(os.path.join(tmp_path, "foobar.json"))
        with open(cpath, "w") as fh:
            json.dump(conf, fh, sort_keys=True, indent=4)
        with patch.dict(os.environ, {"USERS_CONFIG": cpath}):
            cls: UsersConfig = UsersConfig()
        assert len(cls.users) == 3
        assert len(cls.users_by_fob) == 3
        assert isinstance(cls.users_by_fob["5683773370"], User)
        assert cls.users_by_fob["5683773370"].as_dict == conf[2]
        for x in range(0, len(conf)):
            assert isinstance(cls.users[x], User)
            assert cls.users[x].as_dict == conf[x]
        assert cls.load_time == 1689477248.0

    def test_invalid_config(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf: List[Dict[str, Any]] = [
            {
                "account_id": "410",
                "authorizations": ["Dimensioning Tools", "Woodshop 101"],
                "email": "brian36@example.com",
                "expiration_ymd": "2024-08-27",
                "fob_codes": ["0725858614"],
                "full_name": "Andrew Schwartz",
                "first_name": "Andrew",
                "preferred_name": "PAndrew",
            },
            {
                "account_id": "411",
                "authorizations": [],
                "INVALID_KEY": "zyoung@example.org",
                "expiration_ymd": "2024-08-10",
                "fob_codes": ["0913350505"],
                "full_name": "Tyler Young Jr.",
                "first_name": "Tyler",
                "preferred_name": "PTyler",
            },
            {
                "account_id": "412",
                "authorizations": ["Glowforge"],
                "email": "joshua99@example.net",
                "expiration_ymd": "2024-12-18",
                "fob_codes": ["5683773370"],
                "full_name": "Rachel Richmond",
                "first_name": "Rachel",
                "preferred_name": "PRachel",
            },
        ]
        cpath: str = str(os.path.join(tmp_path, "users.json"))
        with open(cpath, "w") as fh:
            json.dump(conf, fh, sort_keys=True, indent=4)
        os.chdir(tmp_path)
        with pytest.raises(ValidationError):
            UsersConfig()


class TestUser:
    """Tests for User class."""

    def test_eq(self) -> None:
        """Test equality."""
        u1: User = User(
            fob_codes=["0123", "456"],
            account_id="100",
            full_name="John Doe",
            first_name="John",
            preferred_name="PJohn",
            email="john@example.com",
            expiration_ymd="2027-09-10",
            authorizations=[],
        )
        u2: User = User(
            fob_codes=["0123", "456"],
            account_id="333",
            full_name="John Doe",
            first_name="John",
            preferred_name="PJohn",
            email="john@example.com",
            expiration_ymd="2027-09-10",
            authorizations=[],
        )
        u3: User = User(
            fob_codes=["0123", "456"],
            account_id="100",
            full_name="John Doe",
            first_name="John",
            preferred_name="PJohn",
            email="john@example.com",
            expiration_ymd="2027-09-10",
            authorizations=[],
        )
        assert u1 != u2
        assert u1 == u3
        assert u1 != Mock()
