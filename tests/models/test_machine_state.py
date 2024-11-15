"""Tests for models.machine."""

import os
import pickle
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState
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
            "current_amps": 12,
            "display_text": MachineState.DEFAULT_DISPLAY_TEXT,
            "uptime": 0,
            "status_led_rgb": (0.25, 0.3, 0.4),
            "status_led_brightness": 0.25,
            "wifi_signal_db": 0.25,
            "wifi_signal_percent": 0.9,
            "internal_temperature_c": 52.1,
            "current_user": user,
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
        }
