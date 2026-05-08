"""Tests for models.machine."""

import asyncio
import os
import pickle
import time
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState
from dm_mac.models.machine import StateSaveTimeoutError
from dm_mac.models.users import User
from dm_mac.models.users import UsersConfig


pbm: str = "dm_mac.models.machine"
pb: str = f"{pbm}.MachineState"


class MachineStateTester:
    """Base class for testing MachineState()."""

    def setup_method(self) -> None:
        """Setup mocks and a test class instance."""
        self.machine: Machine = Mock(spec_set=Machine)
        type(self.machine).name = "MachineName"
        type(self.machine).second_relay = None
        with patch(f"{pb}._load_from_cache") as self.m_load:
            with patch(f"{pb}._save_cache") as self.m_save:
                with patch(f"{pbm}.os.makedirs"):
                    self.cls: MachineState = MachineState(self.machine)


class TestInit:
    """Tests for MachineState init method."""

    def test_happy_path(self) -> None:
        """Test happy path of init method."""
        mach: Machine = Mock(spec_set=Machine)
        type(mach).name = "MachineName"
        with patch(f"{pb}._load_from_cache", autospec=True) as m_load:
            with patch.dict(os.environ, {}, clear=True):
                with patch(f"{pbm}.os.makedirs") as m_make:
                    cls: MachineState = MachineState(mach)
        assert m_make.mock_calls == [call("machine_state", exist_ok=True)]
        assert m_load.mock_calls == [call(cls)]
        assert cls.machine == mach
        assert cls.last_checkin is None
        assert cls.last_update is None
        assert cls.rfid_value is None
        assert cls.rfid_present_since is None
        assert cls.relay_desired_state is False
        assert cls.current_user is None
        assert cls.is_oopsed is False
        assert cls.is_locked_out is False
        assert cls.current_amps == 0
        assert cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert cls.uptime == 0
        assert cls.status_led_rgb == (0, 0, 0)
        assert cls.status_led_brightness == 0
        assert cls.wifi_signal_db is None
        assert cls.wifi_signal_percent is None
        assert cls.internal_temperature_c is None
        assert cls._state_dir == "machine_state"
        assert cls._state_path == "machine_state/MachineName-state.pickle"

    def test_no_load(self) -> None:
        """Test init method with state loading disabled."""
        mach: Machine = Mock(spec_set=Machine)
        type(mach).name = "MachineName"
        with patch(f"{pb}._load_from_cache", autospec=True) as m_load:
            with patch.dict(os.environ, {}, clear=True):
                with patch(f"{pbm}.os.makedirs") as m_make:
                    cls: MachineState = MachineState(mach, load_state=False)
        assert m_make.mock_calls == [call("machine_state", exist_ok=True)]
        assert m_load.mock_calls == []
        assert cls.machine == mach
        assert cls.last_checkin is None
        assert cls.last_update is None
        assert cls.rfid_value is None
        assert cls.rfid_present_since is None
        assert cls.relay_desired_state is False
        assert cls.current_user is None
        assert cls.is_oopsed is False
        assert cls.is_locked_out is False
        assert cls.current_amps == 0
        assert cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert cls.uptime == 0
        assert cls.status_led_rgb == (0, 0, 0)
        assert cls.status_led_brightness == 0
        assert cls.wifi_signal_db is None
        assert cls.wifi_signal_percent is None
        assert cls.internal_temperature_c is None
        assert cls._state_dir == "machine_state"
        assert cls._state_path == "machine_state/MachineName-state.pickle"

    def test_alternate_state_dir(self) -> None:
        """Test with alternate state dir specified."""
        mach: Machine = Mock(spec_set=Machine)
        type(mach).name = "MachineName"
        with patch(f"{pb}._load_from_cache", autospec=True) as m_load:
            with patch.dict(os.environ, {"MACHINE_STATE_DIR": "/foo/bar/baz"}):
                with patch(f"{pbm}.os.makedirs") as m_make:
                    cls: MachineState = MachineState(mach)
        assert m_make.mock_calls == [call("/foo/bar/baz", exist_ok=True)]
        assert m_load.mock_calls == [call(cls)]
        assert cls.machine == mach
        assert cls.last_checkin is None
        assert cls.last_update is None
        assert cls.rfid_value is None
        assert cls.rfid_present_since is None
        assert cls.relay_desired_state is False
        assert cls.current_user is None
        assert cls.is_oopsed is False
        assert cls.is_locked_out is False
        assert cls.current_amps == 0
        assert cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert cls.uptime == 0
        assert cls.status_led_rgb == (0, 0, 0)
        assert cls.status_led_brightness == 0
        assert cls.wifi_signal_db is None
        assert cls.wifi_signal_percent is None
        assert cls.internal_temperature_c is None
        assert cls._state_dir == "/foo/bar/baz"
        assert cls._state_path == "/foo/bar/baz/MachineName-state.pickle"


class TestSaveCache(MachineStateTester):
    """Test _save_cache() method."""

    def test_defaults(self, tmp_path: Path) -> None:
        """Test happy path."""
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        self.cls._save_cache()
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "rb") as f:
            state = pickle.load(f)
        assert state == {
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
            "second_relay_desired_state": False,
            "second_relay_authorization": None,
            "state_save_timeouts": 0,
        }

    def test_non_defaults(self, tmp_path: Path, fixtures_path: str) -> None:
        """Test happy path."""
        with patch.dict(
            "os.environ",
            {
                "USERS_CONFIG": os.path.join(fixtures_path, "users.json"),
                "MACHINES_CONFIG": os.path.join(fixtures_path, "machines.json"),
            },
        ):
            uconf: UsersConfig = UsersConfig()
        user: User = uconf.users_by_fob["8682768676"]
        self.cls.last_checkin = 1234
        self.cls.last_update = 5678
        self.cls.rfid_value = "8682768676"
        self.cls.current_user = user
        self.cls.rfid_present_since = 34567
        self.cls.relay_desired_state = True
        self.cls.is_oopsed = True
        self.cls.is_locked_out = True
        self.cls.current_amps = 12
        self.cls.status_led_rgb = (0.25, 0.3, 0.4)
        self.cls.status_led_brightness = 0.25
        self.cls.wifi_signal_db = 0.25
        self.cls.wifi_signal_percent = 0.9
        self.cls.internal_temperature_c = 52.1
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        self.cls._save_cache()
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "rb") as f:
            state = pickle.load(f)
        assert state == {
            "machine_name": "MachineName",
            "last_checkin": 1234,
            "last_update": 5678,
            "rfid_value": "8682768676",
            "rfid_present_since": 34567,
            "relay_desired_state": True,
            "is_oopsed": True,
            "is_locked_out": True,
            "is_override_login": False,
            "current_amps": 12,
            "display_text": MachineState.DEFAULT_DISPLAY_TEXT,
            "uptime": 0,
            "status_led_rgb": (0.25, 0.3, 0.4),
            "status_led_brightness": 0.25,
            "wifi_signal_db": 0.25,
            "wifi_signal_percent": 0.9,
            "internal_temperature_c": 52.1,
            "current_user": user,
            "second_relay_desired_state": False,
            "second_relay_authorization": None,
            "state_save_timeouts": 0,
        }


class TestLoadFromCache(MachineStateTester):
    """Test loading cache."""

    def test_defaults(self, tmp_path: Path, fixtures_path: str) -> None:
        """Test loading config with defaults."""
        # confirm initial values
        assert self.cls.last_checkin is None
        assert self.cls.last_update is None
        assert self.cls.rfid_value is None
        assert self.cls.rfid_present_since is None
        assert self.cls.current_user is None
        assert self.cls.relay_desired_state is False
        assert self.cls.is_oopsed is False
        assert self.cls.is_locked_out is False
        assert self.cls.current_amps == 0
        assert self.cls.status_led_rgb == (0, 0, 0)
        assert self.cls.status_led_brightness == 0
        assert self.cls.wifi_signal_db is None
        assert self.cls.wifi_signal_percent is None
        assert self.cls.internal_temperature_c is None
        assert self.cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert self.cls.uptime == 0
        # state data
        state = {
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
        # write save file
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "wb") as f:
            pickle.dump(state, f, pickle.HIGHEST_PROTOCOL)
        self.cls._load_from_cache()
        assert self.cls.last_checkin is None
        assert self.cls.last_update is None
        assert self.cls.rfid_value is None
        assert self.cls.rfid_present_since is None
        assert self.cls.relay_desired_state is False
        assert self.cls.is_oopsed is False
        assert self.cls.is_locked_out is False
        assert self.cls.current_amps == 0
        assert self.cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert self.cls.uptime == 0
        assert self.cls.status_led_rgb == (0, 0, 0)
        assert self.cls.status_led_brightness == 0
        assert self.cls.wifi_signal_db is None
        assert self.cls.wifi_signal_percent is None
        assert self.cls.internal_temperature_c is None
        assert self.cls.current_user is None

    def test_not_defaults(self, tmp_path: Path, fixtures_path: str) -> None:
        """Test loading config with non-defaults."""
        with patch.dict(
            "os.environ",
            {
                "USERS_CONFIG": os.path.join(fixtures_path, "users.json"),
                "MACHINES_CONFIG": os.path.join(fixtures_path, "machines.json"),
            },
        ):
            uconf: UsersConfig = UsersConfig()
        user: User = uconf.users_by_fob["8682768676"]
        # state data
        state = {
            "machine_name": "MachineName",
            "last_checkin": 123,
            "last_update": 456,
            "rfid_value": "8682768676",
            "rfid_present_since": 789,
            "relay_desired_state": True,
            "is_oopsed": True,
            "is_locked_out": True,
            "is_override_login": False,
            "current_amps": 12,
            "display_text": "Some text",
            "uptime": 1234,
            "status_led_rgb": (0.25, 0.3, 0.4),
            "status_led_brightness": 0.25,
            "wifi_signal_db": 0.25,
            "wifi_signal_percent": 0.9,
            "internal_temperature_c": 52.1,
            "current_user": user,
        }
        # write save file
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "wb") as f:
            pickle.dump(state, f, pickle.HIGHEST_PROTOCOL)
        self.cls._load_from_cache()
        assert self.cls.last_checkin == 123
        assert self.cls.last_update == 456
        assert self.cls.rfid_value == "8682768676"
        assert self.cls.rfid_present_since == 789
        assert self.cls.relay_desired_state is True
        assert self.cls.is_oopsed is True
        assert self.cls.is_locked_out is True
        assert self.cls.current_amps == 12
        assert self.cls.display_text == "Some text"
        assert self.cls.uptime == 1234
        assert self.cls.status_led_rgb == (0.25, 0.3, 0.4)
        assert self.cls.status_led_brightness == 0.25
        assert self.cls.wifi_signal_db == 0.25
        assert self.cls.wifi_signal_percent == 0.9
        assert self.cls.internal_temperature_c == 52.1
        assert self.cls.current_user == user

    def test_does_not_exist(self, tmp_path: Path) -> None:
        """Test when state file does not exist."""
        # confirm initial values
        assert self.cls.last_checkin is None
        assert self.cls.last_update is None
        assert self.cls.rfid_value is None
        assert self.cls.rfid_present_since is None
        assert self.cls.relay_desired_state is False
        assert self.cls.is_oopsed is False
        assert self.cls.is_locked_out is False
        assert self.cls.current_amps == 0
        assert self.cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert self.cls.uptime == 0
        assert self.cls.wifi_signal_db is None
        assert self.cls.wifi_signal_percent is None
        assert self.cls.internal_temperature_c is None
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        self.cls._load_from_cache()
        # should not have any changes
        assert self.cls.last_checkin is None
        assert self.cls.last_update is None
        assert self.cls.rfid_value is None
        assert self.cls.rfid_present_since is None
        assert self.cls.relay_desired_state is False
        assert self.cls.is_oopsed is False
        assert self.cls.is_locked_out is False
        assert self.cls.current_amps == 0
        assert self.cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert self.cls.uptime == 0
        assert self.cls.status_led_rgb == (0, 0, 0)
        assert self.cls.status_led_brightness == 0
        assert self.cls.wifi_signal_db is None
        assert self.cls.wifi_signal_percent is None
        assert self.cls.internal_temperature_c is None


class TestMachineResponse(MachineStateTester):
    """Tests for MachineState.machine_response property."""

    def test_initial_state(self) -> None:
        """Test initial state for a new machine."""
        assert self.cls.machine_response == {
            "relay": False,
            "display": MachineState.DEFAULT_DISPLAY_TEXT,
            "oops_led": False,
            "status_led_rgb": [0.0, 0.0, 0.0],
            "status_led_brightness": 0.0,
            "second_relay": False,
        }

    def test_nondefault_state(self) -> None:
        """Test initial state for a new machine."""
        self.cls.relay_desired_state = True
        self.cls.display_text = "Some other\nText"
        self.cls.is_oopsed = True
        self.cls.status_led_rgb = (0.25, 0.3, 0.4)
        self.cls.status_led_brightness = 0.25
        assert self.cls.machine_response == {
            "relay": True,
            "display": "Some other\nText",
            "oops_led": True,
            "status_led_rgb": [0.25, 0.3, 0.4],
            "status_led_brightness": 0.25,
            "second_relay": False,
        }


class TestOverrideLogin(MachineStateTester):
    """Tests for the oops/lockout override login feature."""

    def test_init_default(self) -> None:
        """Test that is_override_login defaults to False on init."""
        assert self.cls.is_override_login is False

    def test_save_cache_includes_override_login(self, tmp_path: Path) -> None:
        """Test that _save_cache persists is_override_login."""
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        self.cls.is_override_login = True
        self.cls._save_cache()
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "rb") as f:
            state = pickle.load(f)
        assert state["is_override_login"] is True

    def test_save_cache_override_login_false(self, tmp_path: Path) -> None:
        """Test that _save_cache persists is_override_login=False."""
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        self.cls._save_cache()
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "rb") as f:
            state = pickle.load(f)
        assert state["is_override_login"] is False

    def test_load_from_cache_with_override_login(self, tmp_path: Path) -> None:
        """Test that _load_from_cache loads is_override_login when present."""
        state = {
            "machine_name": "MachineName",
            "last_checkin": None,
            "last_update": None,
            "rfid_value": None,
            "rfid_present_since": None,
            "relay_desired_state": False,
            "is_oopsed": False,
            "is_locked_out": False,
            "is_override_login": True,
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
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "wb") as f:
            pickle.dump(state, f, pickle.HIGHEST_PROTOCOL)
        self.cls._load_from_cache()
        assert self.cls.is_override_login is True

    def test_load_from_cache_backward_compat(self, tmp_path: Path) -> None:
        """Test backward compat: old pickle without is_override_login defaults to False."""
        state = {
            "machine_name": "MachineName",
            "last_checkin": None,
            "last_update": None,
            "rfid_value": None,
            "rfid_present_since": None,
            "relay_desired_state": False,
            "is_oopsed": False,
            "is_locked_out": False,
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
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "wb") as f:
            pickle.dump(state, f, pickle.HIGHEST_PROTOCOL)
        self.cls._load_from_cache()
        # is_override_login not in pickle, so it stays at init default
        assert self.cls.is_override_login is False

    def test_oops_with_override_login_set(self) -> None:
        """Test that oops() still works when is_override_login is True."""
        self.cls.is_override_login = True
        self.cls.relay_desired_state = True
        self.cls.oops()
        assert self.cls.is_oopsed is True
        assert self.cls.relay_desired_state is False
        assert self.cls.current_user is None
        assert self.cls.display_text == MachineState.OOPS_DISPLAY_TEXT
        assert self.cls.status_led_rgb == (1.0, 0.0, 0.0)
        assert self.cls.status_led_brightness == MachineState.STATUS_LED_BRIGHTNESS
        # Note: oops() does not clear is_override_login itself
        # That is handled by the rfid remove / reboot paths

    def test_lockout_with_override_login_set(self) -> None:
        """Test that lockout() still works when is_override_login is True."""
        self.cls.is_override_login = True
        self.cls.relay_desired_state = True
        self.cls.lockout()
        assert self.cls.is_locked_out is True
        assert self.cls.relay_desired_state is False
        assert self.cls.current_user is None
        assert self.cls.display_text == MachineState.LOCKOUT_DISPLAY_TEXT
        assert self.cls.status_led_rgb == (1.0, 0.5, 0.0)
        assert self.cls.status_led_brightness == MachineState.STATUS_LED_BRIGHTNESS

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        """Test that is_override_login survives a save/load roundtrip."""
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        self.cls.is_override_login = True
        self.cls.is_oopsed = True
        self.cls.relay_desired_state = True
        self.cls._save_cache()
        # Reset state to defaults
        self.cls.is_override_login = False
        self.cls.is_oopsed = False
        self.cls.relay_desired_state = False
        # Load from cache should restore
        self.cls._load_from_cache()
        assert self.cls.is_override_login is True
        assert self.cls.is_oopsed is True
        assert self.cls.relay_desired_state is True


class TestAsyncSaveCache(MachineStateTester):
    """Tests for the timeout-bounded async ``save_cache`` wrapper."""

    @pytest.mark.asyncio
    async def test_happy_path_writes_pickle(self, tmp_path: Path) -> None:
        """Async wrapper completes well under the budget on a normal disk."""
        self.cls._state_path = str(tmp_path) + "/MachineName-state.pickle"
        await self.cls.save_cache()
        assert self.cls.state_save_timeouts == 0
        with open(os.path.join(tmp_path, "MachineName-state.pickle"), "rb") as f:
            state = pickle.load(f)
        assert state["machine_name"] == "MachineName"
        assert state["state_save_timeouts"] == 0

    @pytest.mark.asyncio
    async def test_timeout_raises_and_increments_counter(self) -> None:
        """A slow underlying save raises StateSaveTimeoutError and counts."""

        # Sleep just long enough to outlast the patched 0.1s budget; using
        # the unpatched STATE_SAVE_TIMEOUT_SEC (2.0s) here would make the
        # test sleep for 2.5s for no reason.
        def slow_save() -> None:
            time.sleep(0.3)

        with patch.object(self.cls, "_save_cache", side_effect=slow_save):
            with patch(f"{pbm}.STATE_SAVE_TIMEOUT_SEC", 0.1):
                with pytest.raises(StateSaveTimeoutError):
                    await self.cls.save_cache()
        assert self.cls.state_save_timeouts == 1

    @pytest.mark.asyncio
    async def test_first_timeout_does_not_notify_slack(self) -> None:
        """A single transient timeout must not page Slack."""

        def slow_save() -> None:
            time.sleep(0.5)

        slack = MagicMock()
        slack.app.client.chat_postMessage = AsyncMock()
        slack.control_channel_id = "C123"
        m_app = MagicMock()
        m_app.config = {"SLACK_HANDLER": slack}
        with patch(f"{pbm}.current_app", new=m_app):
            with patch.object(self.cls, "_save_cache", side_effect=slow_save):
                with patch(f"{pbm}.STATE_SAVE_TIMEOUT_SEC", 0.05):
                    with pytest.raises(StateSaveTimeoutError):
                        await self.cls.save_cache()
        assert self.cls.state_save_timeouts == 1
        slack.app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_second_timeout_notifies_slack(self) -> None:
        """The second-or-later timeout must fire a Slack notification."""

        def slow_save() -> None:
            time.sleep(0.5)

        slack = MagicMock()
        slack.app.client.chat_postMessage = AsyncMock()
        slack.control_channel_id = "C123"
        type(self.machine).display_name = "MachineDisplayName"
        # Pre-seed one prior timeout
        self.cls.state_save_timeouts = 1
        m_app = MagicMock()
        m_app.config = {"SLACK_HANDLER": slack}
        with patch(f"{pbm}.current_app", new=m_app):
            with patch.object(self.cls, "_save_cache", side_effect=slow_save):
                with patch(f"{pbm}.STATE_SAVE_TIMEOUT_SEC", 0.05):
                    with pytest.raises(StateSaveTimeoutError):
                        await self.cls.save_cache()
                    # Allow the create_task() to be scheduled before assertion
                    await asyncio.sleep(0)
        assert self.cls.state_save_timeouts == 2
        slack.app.client.chat_postMessage.assert_called_once()
        kwargs = slack.app.client.chat_postMessage.call_args.kwargs
        assert kwargs["channel"] == "C123"
        assert "MachineDisplayName" in kwargs["text"]
        assert "2" in kwargs["text"]

    @pytest.mark.asyncio
    async def test_single_flight_fails_fast_when_save_in_progress(self) -> None:
        """A second call while the first is still running fails immediately
        instead of spawning another thread (preventing pool exhaustion)."""

        # Use a real Event so the underlying thread blocks deterministically
        # and we can assert that no second thread was spawned.
        import threading

        block_thread = threading.Event()
        spawned: list[int] = []

        def slow_save() -> None:
            spawned.append(1)
            block_thread.wait(timeout=5.0)

        m_app = MagicMock()
        m_app.config = {}
        with patch(f"{pbm}.current_app", new=m_app):
            with patch.object(self.cls, "_save_cache", side_effect=slow_save):
                with patch(f"{pbm}.STATE_SAVE_TIMEOUT_SEC", 0.05):
                    # First call hits the budget timeout while the thread blocks
                    with pytest.raises(StateSaveTimeoutError) as exc1:
                        await self.cls.save_cache()
                    # Second call sees the still-running task and fails-fast
                    with pytest.raises(StateSaveTimeoutError) as exc2:
                        await self.cls.save_cache()

        # Release the blocked thread so the test exits cleanly
        block_thread.set()
        assert len(spawned) == 1, "second call must not have spawned a thread"
        assert "exceeded" in str(exc1.value)
        assert "already in flight" in str(exc2.value)
        assert self.cls.state_save_timeouts == 2

    @pytest.mark.asyncio
    async def test_no_slack_handler_does_not_error(self) -> None:
        """When SLACK_HANDLER is absent the notify path is silently skipped."""

        def slow_save() -> None:
            time.sleep(0.5)

        self.cls.state_save_timeouts = 5
        m_app = MagicMock()
        m_app.config = {}
        with patch(f"{pbm}.current_app", new=m_app):
            with patch.object(self.cls, "_save_cache", side_effect=slow_save):
                with patch(f"{pbm}.STATE_SAVE_TIMEOUT_SEC", 0.05):
                    with pytest.raises(StateSaveTimeoutError):
                        await self.cls.save_cache()
        assert self.cls.state_save_timeouts == 6
