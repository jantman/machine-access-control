"""Unit tests for SecondRelayConfig and second-relay decision logic."""

import os
import pickle
from pathlib import Path
from typing import Iterable
from typing import Optional
from unittest.mock import Mock
from unittest.mock import patch

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState
from dm_mac.models.machine import SecondRelayConfig
from dm_mac.models.users import User


pbm: str = "dm_mac.models.machine"
pb: str = f"{pbm}.MachineState"


def _make_user(name: str, auths: Iterable[str]) -> User:
    """Make a real User-like object for tests."""
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


def _make_machine_state(
    second_relay: Optional[SecondRelayConfig] = None,
    root_always_enabled: bool = False,
) -> MachineState:
    """Build a MachineState with a real Machine wrapping a SecondRelayConfig."""
    mach: Machine = Mock(spec_set=Machine)
    type(mach).name = "MachineName"
    type(mach).display_name = "Machine Display"
    type(mach).second_relay = second_relay
    type(mach).always_enabled = root_always_enabled
    with patch(f"{pb}._load_from_cache"):
        with patch(f"{pbm}.os.makedirs"):
            cls = MachineState(mach)
    return cls


class TestUserIsSecondAuthorized:
    """Unit tests for _user_is_second_authorized helper."""

    def test_no_second_relay(self) -> None:
        cls = _make_machine_state(second_relay=None)
        user = _make_user("u1", ["secondary_auth"])
        assert cls._user_is_second_authorized(user) is False

    def test_user_holds_required_auth(self) -> None:
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        user = _make_user("u1", ["primary_auth", "secondary_auth"])
        assert cls._user_is_second_authorized(user) is True

    def test_user_lacks_required_auth(self) -> None:
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        user = _make_user("u1", ["primary_auth"])
        assert cls._user_is_second_authorized(user) is False


class TestResolveSecondRelay:
    """Unit tests covering the _resolve_second_relay decision tree."""

    def test_no_second_relay_configured(self) -> None:
        """[US1/US4] No second_relay configured -> False/None."""
        cls = _make_machine_state(second_relay=None)
        cls.relay_desired_state = True
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization is None

    def test_primary_off_short_circuits(self) -> None:
        """[US1] Primary relay off -> second relay False/None regardless."""
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = False
        cls.current_user = _make_user("u1", ["primary_auth", "secondary_auth"])
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization is None

    def test_secondary_only_user_primary_off(self) -> None:
        """[US1] Secondary-only user has no primary -> primary off short-circuits."""
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = False
        cls.current_user = _make_user("u_sec", ["secondary_auth"])
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization is None

    def test_primary_only_denied(self) -> None:
        """[US1] Primary-authorized user lacking secondary -> denied."""
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = True
        cls.current_user = _make_user("u_prim", ["primary_auth"])
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization == "denied"

    def test_both_auths_granted(self) -> None:
        """[US2] Both auths -> True/granted."""
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = True
        cls.current_user = _make_user("u_both", ["primary_auth", "secondary_auth"])
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is True
        assert cls.second_relay_authorization == "granted"

    def test_warn_only_override(self) -> None:
        """[US2] unauthorized_warn_only set, primary-only user -> True/warn."""
        sr = SecondRelayConfig(
            authorizations_or=["secondary_auth"], unauthorized_warn_only=True
        )
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = True
        cls.current_user = _make_user("u_prim", ["primary_auth"])
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is True
        assert cls.second_relay_authorization == "warn"

    def test_always_enabled(self) -> None:
        """[US2] always_enabled second relay -> True/always_enabled."""
        sr = SecondRelayConfig(
            authorizations_or=["secondary_auth"], always_enabled=True
        )
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = True
        cls.current_user = _make_user("u_prim", ["primary_auth"])
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is True
        assert cls.second_relay_authorization == "always_enabled"

    def test_always_enabled_off_when_primary_off(self) -> None:
        """[US2] always_enabled=true does NOT energize when primary is off."""
        sr = SecondRelayConfig(
            authorizations_or=["secondary_auth"], always_enabled=True
        )
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = False
        cls.current_user = None
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization is None

    def test_warn_only_with_no_current_user_short_circuits(self) -> None:
        """warn-only must NOT energize the accessory when no user is present.

        Scenario: root machine is always_enabled (so primary relay is on
        even without RFID) and second_relay has unauthorized_warn_only=true
        but NOT always_enabled. There is no identified operator, so the
        warn-only override does not apply and the second relay stays off.
        """
        sr = SecondRelayConfig(
            authorizations_or=["secondary_auth"], unauthorized_warn_only=True
        )
        cls = _make_machine_state(second_relay=sr, root_always_enabled=True)
        cls.relay_desired_state = True  # always_enabled root
        cls.current_user = None
        cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization is None

    def test_fail_closed_on_exception(self) -> None:
        """Defensive: any exception during resolve fails closed."""
        sr = SecondRelayConfig(authorizations_or=["secondary_auth"])
        cls = _make_machine_state(second_relay=sr)
        cls.relay_desired_state = True
        # current_user is a value that raises when accessed
        with patch.object(
            type(cls),
            "_user_is_second_authorized",
            side_effect=RuntimeError("boom"),
        ):
            cls.current_user = _make_user("u", ["x"])
            cls._resolve_second_relay()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization == "denied"


class TestPickleBackwardsCompat:
    """[US4] T029 Pickle backwards-compat — old pickle missing new keys."""

    def test_old_pickle_loads_with_safe_defaults(self, tmp_path: Path) -> None:
        cls = _make_machine_state(second_relay=None)
        # Build pre-feature dict shape (no second_relay_* keys)
        old_state = {
            "machine_name": "MachineName",
            "last_checkin": None,
            "last_update": None,
            "rfid_value": None,
            "rfid_present_since": None,
            "relay_desired_state": False,
            "is_oopsed": False,
            "is_locked_out": False,
            "is_override_login": False,
            "current_amps": 0,
            "display_text": MachineState.DEFAULT_DISPLAY_TEXT,
            "uptime": 0,
            "status_led_rgb": (0, 0, 0),
            "status_led_brightness": 0,
            "wifi_signal_db": None,
            "wifi_signal_percent": None,
            "internal_temperature_c": None,
            "current_user": None,
        }
        cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "wb") as f:
            pickle.dump(old_state, f, pickle.HIGHEST_PROTOCOL)
        cls._load_from_cache()
        assert cls.second_relay_desired_state is False
        assert cls.second_relay_authorization is None

    def test_save_load_roundtrip_with_second_relay(self, tmp_path: Path) -> None:
        cls = _make_machine_state(second_relay=None)
        cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        cls.second_relay_desired_state = True
        cls.second_relay_authorization = "granted"
        cls._save_cache()
        cls.second_relay_desired_state = False
        cls.second_relay_authorization = None
        cls._load_from_cache()
        assert cls.second_relay_desired_state is True
        assert cls.second_relay_authorization == "granted"


class TestSecondRelayConfigClass:
    """Tests for SecondRelayConfig dataclass-like behavior."""

    def test_defaults(self) -> None:
        sr = SecondRelayConfig(authorizations_or=["x"])
        assert sr.authorizations_or == ["x"]
        assert sr.unauthorized_warn_only is False
        assert sr.always_enabled is False
        assert sr.alias is None
        assert sr.as_dict == {
            "authorizations_or": ["x"],
            "unauthorized_warn_only": False,
            "always_enabled": False,
            "alias": None,
        }

    def test_all_options(self) -> None:
        sr = SecondRelayConfig(
            authorizations_or=["a", "b"],
            unauthorized_warn_only=True,
            always_enabled=True,
            alias="Rotary",
        )
        assert sr.as_dict == {
            "authorizations_or": ["a", "b"],
            "unauthorized_warn_only": True,
            "always_enabled": True,
            "alias": "Rotary",
        }
