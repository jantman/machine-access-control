"""Tests for models.machine."""

from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState


pbm: str = "dm_mac.models.machine"
pb: str = f"{pbm}.MachineState"


class TestMachineStateInit:
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
