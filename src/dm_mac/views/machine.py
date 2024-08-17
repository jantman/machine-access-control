"""Views related to machine endpoints."""

from logging import Logger
from logging import getLogger
from typing import Any
from typing import Dict
from typing import Tuple
from typing import cast

from flask import Blueprint
from flask import Response
from flask import jsonify
from flask import request


logger: Logger = getLogger(__name__)

machineapi: Blueprint = Blueprint("machine", __name__, url_prefix="/machine")


@machineapi.route("/update", methods=["POST"])
def update() -> Tuple[Response, int]:
    """API method to update machine state.

    Accepts POSTed JSON containing the following key/value pairs:

    - "name" (string) - name of the machine sending the update
    - "rfid_value" (string) - value of the RFID fob/card that is currently
        present in the machine, or empty string if none present
    - "relay_state" (boolean) - the current on/off (true/false) state of the
        relay
    - "oops" (boolean) - whether the oops button is pressed, or has been pressed
        since the last check-in
    - "amps" (float) - amperage value from the current clamp ammeter, if present,
        or 0.0 otherwise.
    - "uptime" (float) - uptime of the ESP32 managing the machine.

    EXAMPLE Payloads:

    - Oops button pressed when no RFID present:
       ``{'oops': True, 'rfid_value': '', 'uptime': 538.0189819}``
    - RFID inserted (tag 0014916441)
       ``{'oops': False, 'rfid_value': '14916441', 'uptime': 0.753000021}``
    - Oops button pressed when RFID present:
       ``{'oops': True, 'rfid_value': '14916441', 'uptime': 59.80699921}``
    - RFID removed:
       ``{'oops': False, 'rfid_value': '', 'uptime': 59.80699921}``
    """
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)  # noqa
    logger.warning("UPDATE request: %s", data)
    # machine_name: str = data.pop("name")
    # get the MachineState object for this machine, or else return an error
    #    that error should be formatted for display on the device (helper
    #    method for this)
    # check if this data would update the state; if not, just call
    #    noop_update() and return the same display value
    return jsonify({"error": "not implemented"}), 501
