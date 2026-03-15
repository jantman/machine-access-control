"""Views related to machine endpoints."""

from logging import Logger
from logging import getLogger
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from quart import Blueprint
from quart import Response
from quart import current_app
from quart import jsonify
from quart import request
from quart_schema import document_response
from quart_schema import tag
from quart_schema import validate_request

from dm_mac.models.api_schemas import ErrorResponse
from dm_mac.models.api_schemas import MachineUpdateRequest
from dm_mac.models.api_schemas import MachineUpdateResponse
from dm_mac.models.api_schemas import SuccessResponse
from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig


logger: Logger = getLogger(__name__)

machineapi: Blueprint = Blueprint("machine", __name__, url_prefix="/machine")


@machineapi.route("/update", methods=["POST"])
@tag(["Machine"])
@validate_request(MachineUpdateRequest)
@document_response(MachineUpdateResponse, 200)
@document_response(ErrorResponse, 404)
@document_response(ErrorResponse, 500)
async def update(data: MachineUpdateRequest) -> Tuple[Response, int]:
    """Update machine state from MCU.

    Called by ESP32-based Machine Control Units to report current state
    (RFID value, oops button, uptime, WiFi signal, temperature, optional
    amperage) and receive desired outputs (relay state, LCD text, LED colors).
    """
    update_kwargs: Dict[str, Any] = {
        "oops": data.oops,
        "rfid_value": data.rfid_value if data.rfid_value != "" else None,
        "uptime": data.uptime,
        "wifi_signal_db": data.wifi_signal_db,
        "wifi_signal_percent": data.wifi_signal_percent,
        "internal_temperature_c": data.internal_temperature_c,
        "amps": data.amps,
    }
    logger.info("UPDATE request: machine_name=%s %s", data.machine_name, update_kwargs)
    mconf: MachinesConfig = current_app.config["MACHINES"]  # noqa
    machine: Optional[Machine] = mconf.machines_by_name.get(data.machine_name)
    if not machine:
        return jsonify({"error": f"No such machine: {data.machine_name}"}), 404
    users: UsersConfig = current_app.config["USERS"]  # noqa
    try:
        resp = await machine.update(users, **update_kwargs)
        return jsonify(resp), 200
    except Exception as ex:
        logger.error("Error in machine update %s: %s", update_kwargs, ex, exc_info=True)
        return jsonify({"error": str(ex)}), 500


@machineapi.route("/oops/<machine_name>", methods=["POST", "DELETE"])
@tag(["Machine"])
@document_response(SuccessResponse, 200)
@document_response(ErrorResponse, 404)
@document_response(ErrorResponse, 500)
async def oops(machine_name: str) -> Tuple[Response, int]:
    """Set or clear machine Oops state.

    POST to set the machine into Oops (maintenance needed) state.
    DELETE to clear the Oops state.
    """
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
@tag(["Machine"])
@document_response(SuccessResponse, 200)
@document_response(ErrorResponse, 404)
@document_response(ErrorResponse, 500)
async def locked_out(machine_name: str) -> Tuple[Response, int]:
    """Set or clear machine lockout state.

    POST to lock out a machine (prevent all use).
    DELETE to unlock the machine.
    """
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
