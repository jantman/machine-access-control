"""Views related to machine endpoints."""

from logging import Logger
from logging import getLogger
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import cast

from quart import Blueprint
from quart import Response
from quart import current_app
from quart import jsonify
from quart import request

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig


logger: Logger = getLogger(__name__)

machineapi: Blueprint = Blueprint("machine", __name__, url_prefix="/machine")


@machineapi.route("/update", methods=["POST"])
async def update() -> Tuple[Response, int]:
    """API method to update machine state.

    Accepts POSTed JSON containing the following key/value pairs:

    - ``machine_name`` (string) - name of the machine sending the update
    - ``oops`` (boolean) - whether the oops button is pressed
    - ``rfid_value`` (string) - value of the RFID fob/card that is currently
        present in the machine, or empty string if none present. Note that
        ESPHome strips leading zeroes from this, so inside this method it is
        left-padded with zeroes to a length of 10 characters.
    - ``uptime`` (float) - uptime of the ESP32 (MCU).
    - ``wifi_signal_db`` (float) - WiFi signal strength in dB
    - ``wifi_signal_percent`` (float) - WiFi signal strength in percent
    - ``internal_temperature_c`` (float) - internal temperature of the ESP32 in
        °C.
    - ``amps`` (float; optional) - amperage value from the current clamp
        ammeter, if present, or 0.0 otherwise.

    EXAMPLE Payloads for ESP without amperage sensor
    ------------------------------------------------

    Oops button pressed when no RFID present
    ++++++++++++++++++++++++++++++++++++++++

    .. code-block:: python

       {
           'machine_name': 'esp32test',
           'oops': True,
           'rfid_value': '',
           'uptime': 59.29299927,
           'wifi_signal_db': -58,
           'wifi_signal_percent': 84,
           'internal_temperature_c': 53.88888931
       }

    RFID inserted (tag 0014916441)
    ++++++++++++++++++++++++++++++

    .. code-block:: python

       {
           'machine_name': 'esp32test',
           'oops': False,
           'rfid_value': '14916441',
           'uptime': 59.29299927,
           'wifi_signal_db': -58,
           'wifi_signal_percent': 84,
           'internal_temperature_c': 53.88888931
       }

    Oops button pressed when RFID present
    +++++++++++++++++++++++++++++++++++++

    .. code-block:: python

       {
           'machine_name': 'esp32test',
           'oops': True,
           'rfid_value': '14916441',
           'uptime': 59.29299927,
           'wifi_signal_db': -58,
           'wifi_signal_percent': 84,
           'internal_temperature_c': 53.88888931
       }

    RFID removed
    ++++++++++++

    .. code-block:: python

       {
           'machine_name': 'esp32test',
           'oops': False,
           'rfid_value': '',
           'uptime': 119.2929993,
           'wifi_signal_db': -54,
           'wifi_signal_percent': 92,
           'internal_temperature_c': 53.88888931
       }
    """
    data: Dict[str, Any] = cast(Dict[str, Any], await request.json)  # noqa
    logger.info("UPDATE request: %s", data)
    machine_name: str = data.pop("machine_name")
    mconf: MachinesConfig = current_app.config["MACHINES"]  # noqa
    machine: Optional[Machine] = mconf.machines_by_name.get(machine_name)
    if not machine:
        return jsonify({"error": f"No such machine: {machine_name}"}), 404
    users: UsersConfig = current_app.config["USERS"]  # noqa
    if data.get("rfid_value") == "":
        data["rfid_value"] = None
    try:
        resp = await machine.update(users, **data)
        return jsonify(resp), 200
    except Exception as ex:
        logger.error("Error in machine update %s: %s", data, ex, exc_info=True)
        return jsonify({"error": str(ex)}), 500


@machineapi.route("/oops/<machine_name>", methods=["POST", "DELETE"])
async def oops(machine_name: str) -> Tuple[Response, int]:
    """API method to set or un-set machine Oops state."""
    method: str = request.method
    logger.warning("%s oops on machine %s", method, machine_name)
    mconf: MachinesConfig = current_app.config["MACHINES"]  # noqa
    machine: Optional[Machine] = mconf.machines_by_name.get(machine_name)
    if not machine:
        return jsonify({"error": f"No such machine: {machine_name}"}), 404
    try:
        if method == "DELETE":
            await machine.unoops()
        else:
            await machine.oops()
        machine.state._save_cache()
        return jsonify({"success": True}), 200
    except Exception as ex:
        logger.error(
            "Error in %s oops for machine %s: %s",
            method,
            machine_name,
            ex,
            exc_info=True,
        )
        return jsonify({"error": str(ex)}), 500


@machineapi.route("/locked_out/<machine_name>", methods=["POST", "DELETE"])
async def locked_out(machine_name: str) -> Tuple[Response, int]:
    """API method to set or un-set machine locked out state."""
    method: str = request.method
    logger.warning("%s lock-out on machine %s", method, machine_name)
    mconf: MachinesConfig = current_app.config["MACHINES"]  # noqa
    machine: Optional[Machine] = mconf.machines_by_name.get(machine_name)
    if not machine:
        return jsonify({"error": f"No such machine: {machine_name}"}), 404
    try:
        if method == "DELETE":
            await machine.unlock()
        else:
            await machine.lockout()
        machine.state._save_cache()
        return jsonify({"success": True}), 200
    except Exception as ex:
        logger.error(
            "Error in %s locked_out for machine %s: %s",
            method,
            machine_name,
            ex,
            exc_info=True,
        )
        return jsonify({"error": str(ex)}), 500
