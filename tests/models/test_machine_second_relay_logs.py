"""[US3 T037] Tests for structured AUTH logs from second-relay decisions."""

import logging
from typing import Iterable
from typing import Optional
from unittest.mock import Mock
from unittest.mock import patch

from _pytest.logging import LogCaptureFixture

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState
from dm_mac.models.machine import SecondRelayConfig
from dm_mac.models.users import User

pbm: str = "dm_mac.models.machine"
pb: str = f"{pbm}.MachineState"


def _make_user(name: str, auths: Iterable[str]) -> User:
    return User(
        fob_codes=["0000000000"],
        account_id="acct-" + name,
        full_name=name,
        first_name=name,
        last_name=name,
        preferred_name=name,
        email=f"{name}@example.net",
        expiration_ymd="2099-01-01",
        authorizations=list(auths),
    )


def _make_state(
    second_relay: Optional[SecondRelayConfig] = None,
    alias: Optional[str] = None,
) -> MachineState:
    mach: Machine = Mock(spec_set=Machine)
    type(mach).name = "m1"
    type(mach).display_name = alias if alias else "m1"
    type(mach).second_relay = second_relay
    type(mach).always_enabled = False
    with patch(f"{pb}._load_from_cache"):
        with patch(f"{pbm}.os.makedirs"):
            return MachineState(mach)


class TestStructuredAuthLogs:
    """AUTH logger emits one record per second-relay decision."""

    def test_granted_log(self, caplog: LogCaptureFixture) -> None:
        sr = SecondRelayConfig(authorizations_or=["secondary"], alias="Rotary")
        cls = _make_state(second_relay=sr, alias="Laser Cutter")
        cls.relay_desired_state = True
        cls.current_user = _make_user("Alice", ["primary", "secondary"])
        with caplog.at_level(logging.INFO, logger="AUTH"):
            cls._resolve_second_relay()
        assert any(
            "authorized for accessory Rotary on machine Laser Cutter" in r.getMessage()
            and "Alice" in r.getMessage()
            and "UNAUTHORIZED" not in r.getMessage()
            for r in caplog.records
        )

    def test_denied_log(self, caplog: LogCaptureFixture) -> None:
        sr = SecondRelayConfig(authorizations_or=["secondary"], alias="Rotary")
        cls = _make_state(second_relay=sr, alias="Laser Cutter")
        cls.relay_desired_state = True
        cls.current_user = _make_user("Bob", ["primary"])
        with caplog.at_level(logging.INFO, logger="AUTH"):
            cls._resolve_second_relay()
        assert any(
            "UNAUTHORIZED for accessory Rotary on machine Laser Cutter"
            in r.getMessage()
            and "Bob" in r.getMessage()
            for r in caplog.records
        )

    def test_warn_log(self, caplog: LogCaptureFixture) -> None:
        sr = SecondRelayConfig(
            authorizations_or=["secondary"],
            unauthorized_warn_only=True,
        )
        cls = _make_state(second_relay=sr)
        cls.relay_desired_state = True
        cls.current_user = _make_user("Carol", ["primary"])
        with caplog.at_level(logging.WARNING, logger="AUTH"):
            cls._resolve_second_relay()
        assert any(
            "warn-only override" in r.getMessage().lower()
            and "Carol" in r.getMessage()
            and r.levelname == "WARNING"
            for r in caplog.records
        )

    def test_always_enabled_log(self, caplog: LogCaptureFixture) -> None:
        sr = SecondRelayConfig(authorizations_or=["x"], always_enabled=True)
        cls = _make_state(second_relay=sr, alias="Mill")
        cls.relay_desired_state = True
        with caplog.at_level(logging.INFO, logger="AUTH"):
            cls._resolve_second_relay()
        assert any(
            "always-enabled" in r.getMessage().lower() and "Mill" in r.getMessage()
            for r in caplog.records
        )

    def test_uses_default_accessory_name_when_no_alias(
        self, caplog: LogCaptureFixture
    ) -> None:
        sr = SecondRelayConfig(authorizations_or=["secondary"])
        cls = _make_state(second_relay=sr, alias="Mill")
        cls.relay_desired_state = True
        cls.current_user = _make_user("Dan", ["primary", "secondary"])
        with caplog.at_level(logging.INFO, logger="AUTH"):
            cls._resolve_second_relay()
        assert any(
            "second relay" in r.getMessage() and "authorized" in r.getMessage().lower()
            for r in caplog.records
        )

    def test_no_log_when_not_configured(self, caplog: LogCaptureFixture) -> None:
        cls = _make_state(second_relay=None)
        cls.relay_desired_state = True
        with caplog.at_level(logging.DEBUG, logger="AUTH"):
            cls._resolve_second_relay()
        # No AUTH-logger record about accessory or second relay
        for r in caplog.records:
            if r.name == "AUTH":
                msg = r.getMessage().lower()
                assert "accessory" not in msg
                assert "second relay" not in msg
