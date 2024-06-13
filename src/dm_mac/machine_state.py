"""Classes and functions related to machine state."""
from typing import Optional
from logging import getLogger, Logger
from time import time


logger: Logger = getLogger(__name__)

DEFAULT_DISPLAY_TEXT: str = 'Please Insert\nRFID Card'


class MachineState:
    """Object representing frozen state in time of a machine."""

    def __init__(self, machine_name: str):
        """Initialize a new MachineState instance."""
        logger.debug('Instantiating new MachineState for %s', machine_name)
        #: The name of the machine
        self.name: str = machine_name
        #: Float timestamp of the machine's last checkin time
        self.last_checkin: Optional[float] = None
        #: Float timestamp of the last time that machine state changed,
        #: not counting `current_amps` or timestamps.
        self.last_update: Optional[float] = None
        #: Value of the RFID card/fob in use, or None if not present.
        self.rfid_value: Optional[str] = None
        #: Float timestamp when `rfid_value` last changed to a non-None value.
        self.rfid_present_since: Optional[float] = None
        #: Whether the output relay is on or not.
        self.relay_is_on: bool = False
        #: Whether the output relay should be on or not.
        self.relay_desired_state: bool = False
        #: Whether the machine's Oops button has been pressed.
        self.is_oopsed: bool = False
        #: Whether the machine is locked out from use.
        self.is_locked_out: bool = False
        #: Whether the machine is force-enabled without RFID present.
        self.is_force_enabled: bool = False
        #: Last reported output ammeter reading (if equipped).
        self.current_amps: float = 0
        #: Text currently displayed on the machine LCD screen
        self.display_text: str = DEFAULT_DISPLAY_TEXT
        self._load_from_cache()

    def _save_cache(self):
        """Save machine state cache to disk."""
        raise NotImplementedError()

    def update_has_changes(
        self, rfid_value: str, relay_state: bool, oops: bool, amps: float
    ) -> bool:
        """Return whether or not the update causes changes to significant state values."""
        if (
            rfid_value != self.rfid_value or
            relay_state != self.relay_is_on or
            oops != self.is_oopsed
        ):
            return True
        return False

    def noop_update(self, amps: float):
        """Just update amps and last_checkin and save cache."""
        self.current_amps = amps
        self.last_checkin = time()
        self._save_cache()

    @property
    def machine_response(self) -> dict:
        """Return the response dict to send to the machine."""
        return {
            'relay': self.relay_desired_state,
            'display': self.display_text
        }
