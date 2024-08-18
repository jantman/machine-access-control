"""Model representing a machine."""

import logging
import os
import pickle
from logging import Logger
from logging import getLogger
from time import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import cast

from filelock import FileLock
from jsonschema import validate

from dm_mac.models.users import UsersConfig
from dm_mac.utils import load_json_config


logger: Logger = getLogger(__name__)


CONFIG_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "patternProperties": {
        "^[a-z0-9_-]+$": {
            "type": "object",
            "required": ["authorizations_or"],
            "properties": {
                "authorizations_or": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of authorizations required to "
                    "operate machine, any one of which "
                    "is sufficient.",
                },
                "unauthorized_warn_only": {
                    "type": "boolean",
                    "description": "If set, allow anyone to operate machine "
                    "but log and display a warning if the "
                    "operator is not authorized.",
                },
            },
            "additionalProperties": False,
            "description": "Unique machine name, alphanumeric _ and - only.",
        }
    },
}


class Machine:
    """Object representing a machine and its state and configuration."""

    def __init__(
        self,
        name: str,
        authorizations_or: List[str],
        unauthorized_warn_only: bool = False,
    ):
        """Initialize a new MachineState instance."""
        #: The name of the machine
        self.name: str = name
        #: List of OR'ed authorizations, any of which is sufficient
        self.authorizations_or: List[str] = authorizations_or
        #: Whether to allow anyone to operate machine regardless of
        #: authorization, just logging/displaying a warning if unauthorized
        self.unauthorized_warn_only: bool = unauthorized_warn_only
        #: state of the machine
        self.state: "MachineState" = MachineState(self)

    def update(
        self, users: UsersConfig, **kwargs: Any
    ) -> Dict[str, str | bool | float | List[float]]:
        """Pass directly to self.state and return result."""
        return self.state.update(users, **kwargs)

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Return a dict representation of this machine."""
        return {
            "name": self.name,
            "authorizations_or": self.authorizations_or,
            "unauthorized_warn_only": self.unauthorized_warn_only,
        }


class MachinesConfig:
    """Class representing machines configuration file."""

    def __init__(self) -> None:
        """Initialize MachinesConfig."""
        logger.debug("Initializing MachinesConfig")
        self.machines_by_name: Dict[str, Machine] = {}
        self.machines: List[Machine] = []
        mdict: Dict[str, Any]
        mname: str
        for mname, mdict in self._load_and_validate_config().items():
            mach: Machine = Machine(name=mname, **mdict)
            self.machines.append(mach)
            self.machines_by_name[mach.name] = mach

    def _load_and_validate_config(self) -> Dict[str, Dict[str, Any]]:
        """Load and validate the config file."""
        config: Dict[str, Dict[str, Any]] = cast(
            Dict[str, Dict[str, Any]],
            load_json_config("MACHINES_CONFIG", "machines.json"),
        )
        MachinesConfig.validate_config(config)
        return config

    @staticmethod
    def validate_config(config: Dict[str, Dict[str, Any]]) -> None:
        """Validate configuration via jsonschema."""
        logger.debug("Validating Users config")
        validate(config, CONFIG_SCHEMA)
        logger.debug("Users is valid")


class MachineState:
    """Object representing frozen state in time of a machine."""

    DEFAULT_DISPLAY_TEXT: str = "Please Insert\nRFID Card"

    OOPS_DISPLAY_TEXT: str = "Oops!! Please\ncheck/post Slack"

    LOCKOUT_DISPLAY_TEXT: str = "Down for\nmaintenance"

    STATUS_LED_BRIGHTNESS: float = 0.5

    def __init__(self, machine: Machine, load_state: bool = True):
        """Initialize a new MachineState instance."""
        logger.debug("Instantiating new MachineState for %s", machine)
        #: The Machine that this state is for
        self.machine: Machine = machine
        #: Float timestamp of the machine's last checkin time
        self.last_checkin: float | None = None
        #: Float timestamp of the last time that machine state changed in a
        #: meaningful way, i.e. RFID value or Oops
        self.last_update: float | None = None
        #: Value of the RFID card/fob in use, or None if not present.
        self.rfid_value: str | None = None
        #: Float timestamp when `rfid_value` last changed to a non-None value.
        self.rfid_present_since: float | None = None
        #: Whether the output relay should be on or not.
        self.relay_desired_state: bool = False
        #: Whether the machine's Oops button has been pressed.
        self.is_oopsed: bool = False
        #: Whether the machine is locked out from use.
        self.is_locked_out: bool = False
        #: Last reported output ammeter reading (if equipped).
        self.current_amps: float = 0
        #: Text currently displayed on the machine LCD screen
        self.display_text: str = self.DEFAULT_DISPLAY_TEXT
        #: Uptime of the machine's ESP32 in seconds
        self.uptime: float = 0.0
        #: RGB values for status LED; floats 0 to 1
        self.status_led_rgb: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        #: status LED brightness value; float 0 to 1
        self.status_led_brightness: float = 0.0
        #: ESP32 WiFi signal strength in dB
        self.wifi_signal_db: Optional[float] = None
        #: ESP32 WiFi signal strength in percent
        self.wifi_signal_percent: Optional[float] = None
        #: ESP32 internal temperature in °C
        self.internal_temperature_c: Optional[float] = None
        #: Path to the directory to save machine state in
        self._state_dir: str = os.environ.get("MACHINE_STATE_DIR", "machine_state")
        os.makedirs(self._state_dir, exist_ok=True)
        #: Path to pickled state file
        self._state_path: str = os.path.join(
            self._state_dir, f"{self.machine.name}-state.pickle"
        )
        if load_state:
            self._load_from_cache()
        else:
            logger.warning("State loading disabled for machine %s", self.machine.name)

    def _save_cache(self) -> None:
        """Save machine state cache to disk."""
        logger.debug("Getting lock for state file: %s", self._state_path + ".lock")
        lock = FileLock(self._state_path + ".lock")
        with lock:
            data: Dict[str, Any] = {
                "machine_name": self.machine.name,
                "last_checkin": self.last_checkin,
                "last_update": self.last_update,
                "rfid_value": self.rfid_value,
                "rfid_present_since": self.rfid_present_since,
                "relay_desired_state": self.relay_desired_state,
                "is_oopsed": self.is_oopsed,
                "is_locked_out": self.is_locked_out,
                "current_amps": self.current_amps,
                "display_text": self.display_text,
                "uptime": self.uptime,
                "status_led_rgb": self.status_led_rgb,
                "status_led_brightness": self.status_led_brightness,
                "wifi_signal_db": self.wifi_signal_db,
                "wifi_signal_percent": self.wifi_signal_percent,
                "internal_temperature_c": self.internal_temperature_c,
            }
            logger.debug("Saving state to: %s", self._state_path)
            with open(self._state_path, "wb") as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        logger.debug("State saved.")

    def _load_from_cache(self) -> None:
        """Load machine state cache from disk."""
        if not os.path.exists(self._state_path):
            logger.info("State file does not yet exist: %s", self._state_path)
            return
        logger.debug("Getting lock for state file: %s", self._state_path + ".lock")
        lock = FileLock(self._state_path + ".lock")
        with lock:
            logger.debug("Loading state from: %s", self._state_path)
            with open(self._state_path, "rb") as f:
                data = pickle.load(f)
            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)
        logger.debug("State loaded.")

    def _handle_reboot(self) -> None:
        """Handle when the ESP32 (MCU) has rebooted since last checkin.

        This logs out the current user if logged in and turns off the relay if
        turned on.
        """
        logging.getLogger("AUTH").warning(
            "Machine %s rebooted; resetting relay and RFID state", self.machine.name
        )
        raise NotImplementedError()

    def update(
        self,
        users: UsersConfig,
        oops: bool = False,
        rfid_value: Optional[str] = None,
        uptime: Optional[float] = None,
        wifi_signal_db: Optional[float] = None,
        wifi_signal_percent: Optional[float] = None,
        internal_temperature_c: Optional[float] = None,
        amps: Optional[float] = None,
    ) -> Dict[str, str | bool | float | List[float]]:
        """Handle an update to the machine via API."""
        if amps is not None:
            self.current_amps = amps
        if uptime is not None:
            if uptime < self.uptime:
                logger.warning(
                    "Uptime of %s is less than last uptime of %s; machine "
                    "control unit has rebooted",
                    uptime,
                    self.uptime,
                )
                self._handle_reboot()
            self.uptime = uptime
        if wifi_signal_db is not None:
            self.wifi_signal_db = wifi_signal_db
        if wifi_signal_percent is not None:
            self.wifi_signal_percent = wifi_signal_percent
        if internal_temperature_c is not None:
            self.internal_temperature_c = internal_temperature_c
        self.last_checkin = time()
        if oops:
            self._handle_oops(users)
            self.last_update = time()
        if rfid_value != self.rfid_value:
            self._handle_rfid_change(users, rfid_value)
            self.last_update = time()
        self._save_cache()
        return self.machine_response

    def _handle_oops(self, users: UsersConfig) -> None:
        """Handle oops button press."""
        ustr: str = ""
        if self.rfid_value:
            ustr = " RFID card is present but unknown."
            if user := users.users_by_fob[self.rfid_value]:
                ustr = f" Current user is: {user.full_name}."
        logging.getLogger("AUTH").warning(
            "Machine %s was Oopsed.%s", self.machine.name, ustr
        )
        self.is_oopsed = True
        self.relay_desired_state = False
        self.display_text = self.OOPS_DISPLAY_TEXT
        self.status_led_rgb = (1.0, 0.0, 0.0)
        self.status_led_brightness = self.STATUS_LED_BRIGHTNESS

    def _handle_rfid_change(
        self, users: UsersConfig, rfid_value: Optional[str] = None
    ) -> None:
        """Handle change in the RFID value."""
        """
        logging.getLogger("AUTH").warning(
            "Machine %s rebooted; resetting relay and RFID state", self.machine.name
        )
        """
        pass

    @property
    def machine_response(self) -> Dict[str, str | bool | float | List[float]]:
        """Return the response dict to send to the machine."""
        return {
            "relay": self.relay_desired_state,
            "display": self.display_text,
            "oops_led": self.is_oopsed,
            "status_led_rgb": [x for x in self.status_led_rgb],
            "status_led_brightness": self.status_led_brightness,
        }
