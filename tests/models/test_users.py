"""Tests for models.users."""

import json
import os
import shutil
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from unittest.mock import patch

import pytest
from jsonschema.exceptions import ValidationError

from dm_mac.models.users import User
from dm_mac.models.users import UsersConfig


class TestUsersConfig:
    """Tests for models.users.UsersConfig."""

    def test_default_config(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf_path: str = os.path.join(
            fixtures_path, "test_neongetter", "users-happy.json"
        )
        shutil.copy(conf_path, os.path.join(tmp_path, "users.json"))
        os.chdir(tmp_path)
        cls: UsersConfig = UsersConfig()
        assert len(cls.users) == 588
        assert len(cls.users_by_fob) == 586

    def test_config_path(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf: List[Dict[str, Any]] = [
            {
                "account_id": "410",
                "authorizations": ["Dimensioning Tools", "Woodshop 101"],
                "email": "brian36@example.com",
                "expiration_ymd": "2024-08-27",
                "fob_codes": ["0725858614"],
                "name": "Andrew Schwartz",
            },
            {
                "account_id": "411",
                "authorizations": [],
                "email": "zyoung@example.org",
                "expiration_ymd": "2024-08-10",
                "fob_codes": ["0913350505"],
                "name": "Tyler Young Jr.",
            },
            {
                "account_id": "412",
                "authorizations": ["Glowforge"],
                "email": "joshua99@example.net",
                "expiration_ymd": "2024-12-18",
                "fob_codes": ["5683773370"],
                "name": "Rachel Richmond",
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

    def test_invalid_config(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf: List[Dict[str, Any]] = [
            {
                "account_id": "410",
                "authorizations": ["Dimensioning Tools", "Woodshop 101"],
                "email": "brian36@example.com",
                "expiration_ymd": "2024-08-27",
                "fob_codes": ["0725858614"],
                "name": "Andrew Schwartz",
            },
            {
                "account_id": "411",
                "authorizations": [],
                "INVALID_KEY": "zyoung@example.org",
                "expiration_ymd": "2024-08-10",
                "fob_codes": ["0913350505"],
                "name": "Tyler Young Jr.",
            },
            {
                "account_id": "412",
                "authorizations": ["Glowforge"],
                "email": "joshua99@example.net",
                "expiration_ymd": "2024-12-18",
                "fob_codes": ["5683773370"],
                "name": "Rachel Richmond",
            },
        ]
        cpath: str = str(os.path.join(tmp_path, "users.json"))
        with open(cpath, "w") as fh:
            json.dump(conf, fh, sort_keys=True, indent=4)
        os.chdir(tmp_path)
        with pytest.raises(ValidationError):
            UsersConfig()
