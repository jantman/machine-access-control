"""Model representing a machine."""

import logging
import os
import pickle
from contextlib import nullcontext
from logging import Logger
from logging import getLogger
from threading import Lock
from time import time
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import cast

from filelock import FileLock
from humanize import naturaldelta
from jsonschema import validate
from quart import current_app

from dm_mac.models.users import User
from dm_mac.models.users import UsersConfig
from dm_mac.utils import load_json_config


if TYPE_CHECKING:  # pragma: no cover
    from dm_mac.slack_handler import SlackHandler


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
                "always_enabled": {
                    "type": "boolean",
                    "description": "If set, machine is always enabled and "
                    "does not require RFID authentication. "
                    "Displays 'Always On' and relay is always "
                    "on unless Oopsed or Locked.",
                },
                "alias": {
                    "type": "string",
                    "description": "Optional human-friendly alias for the machine. "
                    "Used in Slack messages and logs instead of the machine name.",
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
        always_enabled: bool = False,
        alias: Optional[str] = None,
    ):
        """Initialize a new MachineState instance."""
        #: The name of the machine
        self.name: str = name
        #: List of OR'ed authorizations, any of which is sufficient
        self.authorizations_or: List[str] = authorizations_or
        #: Whether to allow anyone to operate machine regardless of
        #: authorization, just logging/displaying a warning if unauthorized
        self.unauthorized_warn_only: bool = unauthorized_warn_only
        #: Whether machine is always enabled without RFID authentication
        self.always_enabled: bool = always_enabled
        #: Optional human-friendly alias for the machine
        self.alias: Optional[str] = alias
        #: state of the machine
        self.state: "MachineState" = MachineState(self)

    async def update(
        self, users: UsersConfig, **kwargs: Any
    ) -> Dict[str, str | bool | float | List[float]]:
        """Pass directly to self.state and return result."""
        return await self.state.update(users, **kwargs)

    async def lockout(self, slack: Optional["SlackHandler"] = None) -> None:
        """Pass directly to self.state."""
        self.state.lockout()
        source = "Slack"
        if not slack:
            slack = current_app.config.get("SLACK_HANDLER")
            source = "API"
        if not slack:
            # Slack integration is not enabled
            return
        await slack.log_lock(self, source)

    async def unlock(self, slack: Optional["SlackHandler"] = None) -> None:
        """Pass directly to self.state."""
        self.state.unlock()
        source = "Slack"
        if not slack:
            slack = current_app.config.get("SLACK_HANDLER")
            source = "API"
        if not slack:
            # Slack integration is not enabled
            return
        await slack.log_unlock(self, source)

    async def oops(self, slack: Optional["SlackHandler"] = None) -> None:
        """Pass directly to self.state."""
        self.state.oops()
        source = "Slack"
        if not slack:
            slack = current_app.config.get("SLACK_HANDLER")
            source = "API"
        if not slack:
            # Slack integration is not enabled
            return
        await slack.log_oops(self, source)

    async def unoops(self, slack: Optional["SlackHandler"] = None) -> None:
        """Pass directly to self.state."""
        self.state.unoops()
        source = "Slack"
        if not slack:
            slack = current_app.config.get("SLACK_HANDLER")
            source = "API"
        if not slack:
            # Slack integration is not enabled
            return
        await slack.log_unoops(self, source)

    @property
    def display_name(self) -> str:
        """Return the display name for this machine (alias if present, else name)."""
        return self.alias if self.alias else self.name

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Return a dict representation of this machine."""
        return {
            "name": self.name,
            "authorizations_or": self.authorizations_or,
            "unauthorized_warn_only": self.unauthorized_warn_only,
            "always_enabled": self.always_enabled,
            "alias": self.alias,
        }


class MachinesConfig:
    """Class representing machines configuration file."""

    def __init__(self) -> None:
        """Initialize MachinesConfig."""
        logger.debug("Initializing MachinesConfig")
        self.machines_by_name: Dict[str, Machine] = {}
        self.machines_by_alias: Dict[str, Machine] = {}
        self.machines: List[Machine] = []
        mdict: Dict[str, Any]
        mname: str
        for mname, mdict in self._load_and_validate_config().items():
            mach: Machine = Machine(name=mname, **mdict)
            self.machines.append(mach)
            self.machines_by_name[mach.name] = mach
            if mach.alias:
                self.machines_by_alias[mach.alias] = mach
        self.load_time: float = time()

    def get_machine(self, name_or_alias: str) -> Optional[Machine]:
        """Get a machine by name or alias."""
        return self.machines_by_name.get(name_or_alias) or self.machines_by_alias.get(
            name_or_alias
        )

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

    ALWAYS_ON_DISPLAY_TEXT: str = "Always On"

    STATUS_LED_BRIGHTNESS: float = 0.5

    def __init__(self, machine: Machine, load_state: bool = True):
        """Initialize a new MachineState instance."""
        logger.debug("Instantiating new MachineState for %s", machine)
        self._lock: Lock = Lock()
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
        #: Current user logged in to the machine
        self.current_user: Optional[User] = None
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
        with self._lock:
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
                    "current_user": self.current_user,
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
        with self._lock:
            lock = FileLock(self._state_path + ".lock")
            with lock:
                logger.debug("Loading state from: %s", self._state_path)
                with open(self._state_path, "rb") as f:
                    data = pickle.load(f)
                for k, v in data.items():
                    if hasattr(self, k):
                        setattr(self, k, v)
        logger.debug("State loaded.")

    async def _handle_reboot(self) -> None:
        """Handle when the ESP32 (MCU) has rebooted since last checkin.

        This logs out the current user if logged in and resets the machine state.
        For always-enabled machines, restores the always-on state.
        """
        logging.getLogger("AUTH").warning(
            "Machine %s rebooted; resetting relay and RFID state",
            self.machine.display_name,
        )
        # locking handled in update()
        self.current_user = None
        # Restore always-enabled state if applicable
        if self.machine.always_enabled:
            self.relay_desired_state = True
            self.display_text = self.ALWAYS_ON_DISPLAY_TEXT
            self.status_led_rgb = (0.0, 1.0, 0.0)
            self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
        else:
            self.relay_desired_state = False
            self.display_text = self.DEFAULT_DISPLAY_TEXT
            self.status_led_rgb = (0.0, 0.0, 0.0)
            self.status_led_brightness = 0.0
        # log to Slack, if enabled
        slack: Optional["SlackHandler"] = current_app.config.get("SLACK_HANDLER")
        if not slack:
            # Slack integration is not enabled
            return
        await slack.admin_log(f"Machine {self.machine.display_name} has rebooted.")

    def lockout(self) -> None:
        """Lock-out the machine."""
        logging.getLogger("OOPS").warning(
            "Machine %s was locked out for maintenance.", self.machine.display_name
        )
        with self._lock:
            self.is_locked_out = True
            self.relay_desired_state = False
            self.current_user = None
            self.display_text = self.LOCKOUT_DISPLAY_TEXT
            self.status_led_rgb = (1.0, 0.5, 0.0)
            self.status_led_brightness = self.STATUS_LED_BRIGHTNESS

    def unlock(self) -> None:
        """Un-lock-out the machine."""
        logging.getLogger("OOPS").warning(
            "Machine %s was removed from maintenance lock-out.",
            self.machine.display_name,
        )
        with self._lock:
            self.is_locked_out = False
            self.current_user = None
            # Restore always-enabled state if applicable
            if self.machine.always_enabled:
                self.relay_desired_state = True
                self.display_text = self.ALWAYS_ON_DISPLAY_TEXT
                self.status_led_rgb = (0.0, 1.0, 0.0)
                self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
            else:
                self.relay_desired_state = False
                self.display_text = self.DEFAULT_DISPLAY_TEXT
                self.status_led_rgb = (0.0, 0.0, 0.0)
                self.status_led_brightness = 0.0

    def oops(self, do_locking: bool = True) -> None:
        """Oops the machine."""
        logging.getLogger("OOPS").warning(
            "Machine %s was Oopsed.", self.machine.display_name
        )
        locker = self._lock if do_locking else nullcontext()
        with locker:
            self.is_oopsed = True
            self.relay_desired_state = False
            self.current_user = None
            self.display_text = self.OOPS_DISPLAY_TEXT
            self.status_led_rgb = (1.0, 0.0, 0.0)
            self.status_led_brightness = self.STATUS_LED_BRIGHTNESS

    def unoops(self, do_locking: bool = True) -> None:
        """Un-oops the machine."""
        logging.getLogger("OOPS").warning(
            "Machine %s was un-Oopsed.", self.machine.display_name
        )
        locker = self._lock if do_locking else nullcontext()
        with locker:
            self.is_oopsed = False
            self.current_user = None
            # Restore always-enabled state if applicable
            if self.machine.always_enabled:
                self.relay_desired_state = True
                self.display_text = self.ALWAYS_ON_DISPLAY_TEXT
                self.status_led_rgb = (0.0, 1.0, 0.0)
                self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
            else:
                self.relay_desired_state = False
                self.display_text = self.DEFAULT_DISPLAY_TEXT
                self.status_led_rgb = (0.0, 0.0, 0.0)
                self.status_led_brightness = 0

    async def update(
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
        if rfid_value is not None:
            rfid_value = rfid_value.rjust(10, "0")
        with self._lock:
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
                    await self._handle_reboot()
                self.uptime = uptime
            if wifi_signal_db is not None:
                self.wifi_signal_db = wifi_signal_db
            if wifi_signal_percent is not None:
                self.wifi_signal_percent = wifi_signal_percent
            if internal_temperature_c is not None:
                self.internal_temperature_c = internal_temperature_c
            self.last_checkin = time()
            if oops:
                await self._handle_oops(users)
                self.last_update = time()
            # Handle always-enabled machines - track RFID but maintain always-on state
            if (
                self.machine.always_enabled
                and not self.is_oopsed
                and not self.is_locked_out
            ):
                self.relay_desired_state = True
                self.display_text = self.ALWAYS_ON_DISPLAY_TEXT
                self.status_led_rgb = (0.0, 1.0, 0.0)
                self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
                self.last_update = time()
                # Track RFID changes for logging/auditing purposes
                if rfid_value != self.rfid_value:
                    await self._handle_rfid_tracking_always_enabled(users, rfid_value)
            elif rfid_value != self.rfid_value:
                if rfid_value is None:
                    await self._handle_rfid_remove()
                else:
                    await self._handle_rfid_insert(users, rfid_value)
                self.last_update = time()
        self._save_cache()
        return self.machine_response

    async def _handle_oops(self, users: UsersConfig) -> None:
        """Handle oops button press."""
        ustr: str = ""
        uname: Optional[str] = None
        if self.rfid_value:
            ustr = " RFID card is present but unknown."
            if user := users.users_by_fob.get(self.rfid_value):
                ustr = f" Current user is: {user.full_name}."
                uname = user.full_name
        logging.getLogger("OOPS").warning(
            "Machine %s was Oopsed.%s", self.machine.display_name, ustr
        )
        # locking handled in update()
        self.oops(do_locking=False)
        # log to Slack, if enabled
        slack: Optional["SlackHandler"] = current_app.config.get("SLACK_HANDLER")
        if not slack:
            # Slack integration is not enabled
            return
        src = "Oops button"
        if self.rfid_value:
            src += " with RFID present"
        else:
            src += " without RFID present"
        await slack.log_oops(self.machine, src, user_name=uname)

    async def _handle_rfid_remove(self) -> None:
        """Handle RFID card removed."""
        logging.getLogger("AUTH").info(
            "RFID logout on %s by %s; session duration %d seconds",
            self.machine.display_name,
            self.current_user.full_name if self.current_user else self.rfid_value,
            time() - cast(float, self.rfid_present_since),
        )
        log_str: str = (
            f"RFID logout on {self.machine.display_name} by "
            + (self.current_user.full_name if self.current_user else "unknown")
            + "; session duration "
            + naturaldelta(time() - cast(float, self.rfid_present_since))
        )
        # locking handled in update()
        self.rfid_value = None
        self.rfid_present_since = None
        self.current_user = None
        self.relay_desired_state = False
        if not self.is_oopsed and not self.is_locked_out:
            self.display_text = self.DEFAULT_DISPLAY_TEXT
            self.status_led_rgb = (0.0, 0.0, 0.0)
            self.status_led_brightness = 0.0
        # log to Slack, if enabled
        slack: Optional["SlackHandler"] = current_app.config.get("SLACK_HANDLER")
        if not slack:
            # Slack integration is not enabled
            return
        await slack.admin_log(log_str)

    async def _handle_rfid_insert(self, users: UsersConfig, rfid_value: str) -> None:
        """Handle change in the RFID value."""
        # locking handled in update()
        self.rfid_present_since = time()
        self.rfid_value = rfid_value
        user: Optional[User] = users.users_by_fob.get(rfid_value)
        slack: Optional["SlackHandler"] = current_app.config.get("SLACK_HANDLER")
        if not user:
            logging.getLogger("AUTH").warning(
                "RFID login attempt on %s by unknown fob %s",
                self.machine.display_name,
                rfid_value,
            )
            if self.is_oopsed or self.is_locked_out:
                if slack:
                    await slack.admin_log(
                        f"RFID login attempt on {self.machine.display_name} "
                        "by unknown fob when oopsed or locked out."
                    )
                return
            self.display_text = "Unknown RFID"
            self.status_led_rgb = (1.0, 0.0, 0.0)
            self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
            if slack:
                await slack.admin_log(
                    f"RFID login attempt on {self.machine.display_name} by unknown fob"
                )
            return
        # ok, we have a known user
        logname = f"{user.full_name} ({rfid_value})"
        if self.is_oopsed:
            logging.getLogger("AUTH").warning(
                "RFID login attempt while oopsed on %s by %s",
                self.machine.display_name,
                logname,
            )
            # don't change anything
            if slack:
                await slack.admin_log(
                    f"RFID login attempt on {self.machine.display_name} by "
                    f"{user.full_name} when oopsed."
                )
            return
        if self.is_locked_out:
            logging.getLogger("AUTH").warning(
                "RFID login attempt while locked out on %s by %s",
                self.machine.display_name,
                logname,
            )
            # don't change anything
            if slack:
                await slack.admin_log(
                    f"RFID login attempt on {self.machine.display_name} by "
                    f"{user.full_name} when machine locked-out."
                )
            return
        if await self._user_is_authorized(user, slack=slack):
            logging.getLogger("AUTH").info(
                "User %s (%s) authorized for %s; session start",
                user.full_name,
                user.account_id,
                self.machine.display_name,
            )
            self.current_user = user
            self.relay_desired_state = True
            self.display_text = f"Welcome,\n{user.preferred_name}"
            self.status_led_rgb = (0.0, 1.0, 0.0)
            self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
            if slack:
                await slack.admin_log(
                    f"RFID login on {self.machine.display_name} by authorized user "
                    f"{user.full_name}"
                )
        else:
            logging.getLogger("AUTH").info(
                "User %s (%s) UNAUTHORIZED for %s",
                user.full_name,
                user.account_id,
                self.machine.display_name,
            )
            self.relay_desired_state = False
            self.display_text = "Unauthorized"
            self.status_led_rgb = (1.0, 0.5, 0.0)  # orange
            self.status_led_brightness = self.STATUS_LED_BRIGHTNESS
            if slack:
                await slack.admin_log(
                    f"rejected RFID login on {self.machine.display_name} by "
                    f"UNAUTHORIZED user {user.full_name}"
                )

    async def _handle_rfid_tracking_always_enabled(
        self, users: UsersConfig, rfid_value: Optional[str]
    ) -> None:
        """Track RFID changes for always-enabled machines without changing state.

        This method logs RFID insertions and removals for auditing purposes while
        maintaining the always-on state of the machine.
        """
        # locking handled in update()
        if rfid_value is None:
            # RFID removed
            logging.getLogger("AUTH").info(
                "RFID removed on always-enabled machine %s (was %s); session duration %d seconds",
                self.machine.display_name,
                self.current_user.full_name if self.current_user else self.rfid_value,
                (
                    time() - cast(float, self.rfid_present_since)
                    if self.rfid_present_since
                    else 0
                ),
            )
            self.rfid_value = None
            self.rfid_present_since = None
            self.current_user = None
            # State remains always-on (relay/display/LED not changed)
        else:
            # RFID inserted
            self.rfid_present_since = time()
            self.rfid_value = rfid_value
            user: Optional[User] = users.users_by_fob.get(rfid_value)
            if user:
                self.current_user = user
                logging.getLogger("AUTH").info(
                    "RFID inserted on always-enabled machine %s by %s (%s)",
                    self.machine.display_name,
                    user.full_name,
                    rfid_value,
                )
            else:
                logging.getLogger("AUTH").warning(
                    "RFID inserted on always-enabled machine %s by unknown fob %s",
                    self.machine.display_name,
                    rfid_value,
                )
            # State remains always-on (relay/display/LED not changed)

    async def _user_is_authorized(
        self, user: User, slack: Optional["SlackHandler"] = None
    ) -> bool:
        """Return whether user is authorized for this machine."""
        for auth in self.machine.authorizations_or:
            if auth in user.authorizations:
                logging.getLogger("AUTH").info(
                    "User %s (%s) authorized for %s based on %s",
                    user.full_name,
                    user.account_id,
                    self.machine.display_name,
                    auth,
                )
                return True
        if self.machine.unauthorized_warn_only:
            logging.getLogger("AUTH").warning(
                "User %s (%s) authorized for %s based on "
                "unauthorized_warn_only==True",
                user.full_name,
                user.account_id,
                self.machine.display_name,
            )
            if slack:
                await slack.admin_log(
                    f"WARNING - Authorizing user {user.full_name} for "
                    f"{self.machine.display_name} based on unauthorized_warn_only "
                    "setting for machine. User is NOT authorized for this "
                    "machine."
                )
            return True
        return False

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
