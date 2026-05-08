"""[US3] Config validation tests for the `second_relay` block."""

import json
import os
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import patch

import pytest
from jsonschema.exceptions import ValidationError

from dm_mac.models.machine import MachinesConfig
from dm_mac.models.machine import SecondRelayConfig

pbm: str = "dm_mac.models.machine"


def _load(tmp_path: Path, conf: Dict[str, Any]) -> MachinesConfig:
    cpath: str = str(os.path.join(tmp_path, "machines.json"))
    with open(cpath, "w") as fh:
        json.dump(conf, fh)
    with patch.dict(os.environ, {"MACHINES_CONFIG": cpath}):
        with patch(f"{pbm}.MachineState", autospec=True):
            return MachinesConfig()


class TestSecondRelayConfigPositive:
    """[US3 T033] Positive validation cases for second_relay block."""

    def test_minimal(self, tmp_path: Path) -> None:
        cls = _load(
            tmp_path,
            {
                "m1": {
                    "authorizations_or": ["primary"],
                    "second_relay": {"authorizations_or": ["secondary"]},
                }
            },
        )
        m = cls.machines_by_name["m1"]
        assert isinstance(m.second_relay, SecondRelayConfig)
        assert m.second_relay.authorizations_or == ["secondary"]
        assert m.second_relay.unauthorized_warn_only is False
        assert m.second_relay.always_enabled is False
        assert m.second_relay.alias is None

    def test_all_options(self, tmp_path: Path) -> None:
        cls = _load(
            tmp_path,
            {
                "m1": {
                    "authorizations_or": ["primary"],
                    "second_relay": {
                        "authorizations_or": ["secondary"],
                        "unauthorized_warn_only": True,
                        "always_enabled": True,
                        "alias": "Rotary",
                    },
                }
            },
        )
        m = cls.machines_by_name["m1"]
        assert m.second_relay.unauthorized_warn_only is True
        assert m.second_relay.always_enabled is True
        assert m.second_relay.alias == "Rotary"

    def test_alias_only(self, tmp_path: Path) -> None:
        cls = _load(
            tmp_path,
            {
                "m1": {
                    "authorizations_or": ["primary"],
                    "second_relay": {
                        "authorizations_or": ["secondary"],
                        "alias": "Rotary",
                    },
                }
            },
        )
        assert cls.machines_by_name["m1"].second_relay.alias == "Rotary"

    def test_as_dict_includes_second_relay(self, tmp_path: Path) -> None:
        cls = _load(
            tmp_path,
            {
                "m1": {
                    "authorizations_or": ["primary"],
                    "second_relay": {"authorizations_or": ["secondary"]},
                }
            },
        )
        d = cls.machines_by_name["m1"].as_dict
        assert "second_relay" in d
        assert d["second_relay"]["authorizations_or"] == ["secondary"]


class TestSecondRelayConfigNegative:
    """[US3 T034] Negative validation cases for second_relay block."""

    def test_missing_authorizations_or(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _load(
                tmp_path,
                {"m1": {"authorizations_or": ["p"], "second_relay": {}}},
            )
        msg = str(exc_info.value)
        assert "authorizations_or" in msg

    def test_empty_authorizations_or(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _load(
                tmp_path,
                {
                    "m1": {
                        "authorizations_or": ["p"],
                        "second_relay": {"authorizations_or": []},
                    }
                },
            )
        msg = str(exc_info.value)
        # The message should reflect minItems failure
        assert (
            "[]" in msg
            or "minItems" in msg
            or "non-empty" in msg.lower()
            or "shortest" in msg.lower()
        )

    def test_unknown_field(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _load(
                tmp_path,
                {
                    "m1": {
                        "authorizations_or": ["p"],
                        "second_relay": {
                            "authorizations_or": ["s"],
                            "bogus_key": True,
                        },
                    }
                },
            )
        msg = str(exc_info.value)
        assert "bogus_key" in msg or "Additional properties" in msg

    def test_nested_second_relay(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _load(
                tmp_path,
                {
                    "m1": {
                        "authorizations_or": ["p"],
                        "second_relay": {
                            "authorizations_or": ["s"],
                            "second_relay": {"authorizations_or": ["x"]},
                        },
                    }
                },
            )
        msg = str(exc_info.value)
        # Either nested second_relay rejected as additionalProperties violation
        assert "second_relay" in msg
