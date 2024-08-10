"""Tests for models.machine."""

from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

from freezegun import freeze_time

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState


pbm: str = "dm_mac.models.machine"
pb: str = f"{pbm}.MachineState"


class MachineStateTester:
    """Base class for testing MachineState()."""

    def setup_method(self) -> None:
        """Setup mocks and a test class instance."""
        self.machine: Machine = Mock(spec_set=Machine)
        with patch(f"{pb}._load_from_cache") as self.m_load:
            with patch(f"{pb}._save_cache") as self.m_save:
                self.cls: MachineState = MachineState(self.machine)


class TestInit:
    """Tests for MachineState init method."""

    def test_happy_path(self) -> None:
        """Test happy path of init method."""
        mach: Machine = Mock(spec_set=Machine)
        with patch(f"{pb}._load_from_cache", autospec=True) as m_load:
            cls: MachineState = MachineState(mach)
        assert m_load.mock_calls == [call(cls)]
        assert cls.machine == mach
        assert cls.last_checkin is None
        assert cls.last_update is None
        assert cls.rfid_value is None
        assert cls.rfid_present_since is None
        assert cls.relay_is_on is False
        assert cls.relay_desired_state is False
        assert cls.is_oopsed is False
        assert cls.is_locked_out is False
        assert cls.current_amps == 0
        assert cls.display_text == MachineState.DEFAULT_DISPLAY_TEXT


class TestNoopUpdate(MachineStateTester):
    """Tests for MachineState.noop_update()."""

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_happy_path(self) -> None:
        """Test happy path."""
        self.cls.current_amps = 23.4
        self.cls.last_checkin = 1723307862.0
        with patch(f"{pb}._save_cache") as m_save:
            self.cls.noop_update(0)
        assert self.cls.current_amps == 0
        assert self.cls.last_checkin == 1689477248.0
        assert m_save.mock_calls == [call()]


class TestMachineResponse(MachineStateTester):
    """Tests for MachineState.machine_response property."""

    def test_initial_state(self) -> None:
        """Test initial state for a new machine."""
        assert self.cls.machine_response == {
            "relay": False,
            "display": MachineState.DEFAULT_DISPLAY_TEXT,
        }

    def test_nondefault_state(self) -> None:
        """Test initial state for a new machine."""
        self.cls.relay_desired_state = True
        self.cls.display_text = "Some other\nText"
        assert self.cls.machine_response == {
            "relay": True,
            "display": "Some other\nText",
        }


class TestUpdateHasChanges(MachineStateTester):
    """Tests for MachineState.update_has_changes()."""

    def test_no_changes(self) -> None:
        """Test when update has no changes."""
        assert (
            self.cls.update_has_changes(
                rfid_value=None, relay_state=False, oops=False, amps=0
            )
            is False
        )

    def test_rfid_inserted(self) -> None:
        """Test when an RFID becomes present."""
        assert (
            self.cls.update_has_changes(
                rfid_value="12345", relay_state=False, oops=False, amps=0
            )
            is True
        )

    def test_rfid_removed(self) -> None:
        """Test when an RFID becomes absent."""
        self.cls.rfid_value = "12345"
        self.cls.relay_is_on = True
        assert (
            self.cls.update_has_changes(
                rfid_value=None, relay_state=True, oops=False, amps=0
            )
            is True
        )

    def test_relay_goes_on(self) -> None:
        """Test when the relay comes on."""
        assert (
            self.cls.update_has_changes(
                rfid_value=None, relay_state=True, oops=False, amps=0
            )
            is True
        )

    def test_relay_goes_off(self) -> None:
        """Test when the relay goes off."""
        self.cls.relay_is_on = True
        assert (
            self.cls.update_has_changes(
                rfid_value=None, relay_state=False, oops=False, amps=0
            )
            is True
        )

    def test_oops(self) -> None:
        """Test when oops is pressed."""
        assert (
            self.cls.update_has_changes(
                rfid_value=None, relay_state=False, oops=True, amps=0
            )
            is True
        )
