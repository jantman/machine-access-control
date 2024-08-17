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
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)  # noqa
    logger.warning("UPDATE request: %s", data)
    # machine_name: str = data.pop("name")
    # get the MachineState object for this machine, or else return an error
    #    that error should be formatted for display on the device (helper
    #    method for this)
    # check if this data would update the state; if not, just call
    #    noop_update() and return the same display value
    return jsonify({"error": "not implemented"}), 501
