"""Views related to machine endpoints."""
from typing import Any, Dict
from flask import Blueprint, request, app


machine: Blueprint = Blueprint("machine", __name__, url_prefix="/machine")


@machine.route("/update", methods=['POST'])
def update():
    """
    API method to update machine state.

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
    """
    data: Dict[str, Any] = request.json
    machine_name: str = data.pop('name')
    # get the MachineState object for this machine, or else return an error
    #    that error should be formatted for display on the device (helper method for this)
    # check if this data would update the state; if not, just call noop_update() and return the same display value
