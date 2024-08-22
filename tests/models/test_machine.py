"""Tests for models.machine."""

import json
import os
import shutil
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import call
from unittest.mock import patch

import pytest
from jsonschema.exceptions import ValidationError

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachinesConfig


pbm: str = "dm_mac.models.machine"


class TestMachinesConfig:
    """Tests for models.machine.MachinesConfig."""

    def test_default_config(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf_path: str = os.path.join(fixtures_path, "machines.json")
        shutil.copy(conf_path, os.path.join(tmp_path, "machines.json"))
        os.chdir(tmp_path)
        with patch(f"{pbm}.MachineState", autospec=True):
            cls: MachinesConfig = MachinesConfig()
        assert len(cls.machines) == 5
        assert len(cls.machines_by_name) == 5

    def test_config_path(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf: Dict[str, Dict[str, Any]] = {
            "metal-mill": {"authorizations_or": ["Metal Mill"]},
            "hammer": {
                "authorizations_or": [
                    "Woodshop Orientation",
                    "Woodshop 201",
                    "Woodshop 101",
                ],
                "unauthorized_warn_only": True,
            },
        }
        cpath: str = str(os.path.join(tmp_path, "foobar.json"))
        with open(cpath, "w") as fh:
            json.dump(conf, fh, sort_keys=True, indent=4)
        with patch.dict(os.environ, {"MACHINES_CONFIG": cpath}):
            with patch(f"{pbm}.MachineState", autospec=True):
                cls: MachinesConfig = MachinesConfig()
        assert len(cls.machines) == 2
        assert len(cls.machines_by_name) == 2
        assert isinstance(cls.machines_by_name["hammer"], Machine)
        assert cls.machines_by_name["hammer"].name == "hammer"
        assert (
            cls.machines_by_name["hammer"].authorizations_or
            == conf["hammer"]["authorizations_or"]
        )
        assert cls.machines_by_name["hammer"].unauthorized_warn_only is True
        for x in range(0, len(conf)):
            assert isinstance(cls.machines[x], Machine)
        assert cls.machines_by_name["metal-mill"].as_dict == {
            "name": "metal-mill",
            "authorizations_or": ["Metal Mill"],
            "unauthorized_warn_only": False,
        }

    def test_invalid_config(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test using default config file path."""
        conf: Dict[str, Dict[str, Any]] = {
            "metal-mill": {"authorizations_or": ["Metal Mill"]},
            "hammer": {
                "authorizations_or": [
                    "Woodshop Orientation",
                    "Woodshop 201",
                    "Woodshop 101",
                ],
                "unauthorized_warn_only": True,
            },
            "invalid": {
                "bad_key": 4,
            },
        }
        cpath: str = str(os.path.join(tmp_path, "machines.json"))
        with open(cpath, "w") as fh:
            json.dump(conf, fh, sort_keys=True, indent=4)
        os.chdir(tmp_path)
        with pytest.raises(ValidationError):
            with patch(f"{pbm}.MachineState", autospec=True):
                MachinesConfig()


class TestMachine:
    """Tests for models.machine.Machine."""

    def test_happy_path(self) -> None:
        """Test for happy path."""
        with patch(f"{pbm}.MachineState", autospec=True) as m_state:
            cls: Machine = Machine(
                name="mName",
                authorizations_or=["Foo", "Bar"],
            )
        assert cls.name == "mName"
        assert cls.authorizations_or == ["Foo", "Bar"]
        assert cls.unauthorized_warn_only is False
        assert m_state.mock_calls == [call(cls)]
        assert cls.state == m_state.return_value
        assert cls.as_dict == {
            "name": "mName",
            "authorizations_or": ["Foo", "Bar"],
            "unauthorized_warn_only": False,
        }

    def test_unauth_warn(self) -> None:
        """Test for happy path."""
        with patch(f"{pbm}.MachineState", autospec=True) as m_state:
            cls: Machine = Machine(
                name="mName",
                authorizations_or=["Foo", "Bar"],
                unauthorized_warn_only=True,
            )
        assert cls.name == "mName"
        assert cls.authorizations_or == ["Foo", "Bar"]
        assert cls.unauthorized_warn_only is True
        assert m_state.mock_calls == [call(cls)]
        assert cls.state == m_state.return_value
        assert cls.as_dict == {
            "name": "mName",
            "authorizations_or": ["Foo", "Bar"],
            "unauthorized_warn_only": True,
        }
