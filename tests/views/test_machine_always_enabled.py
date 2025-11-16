"""Tests for always-enabled machines."""

from pathlib import Path
from unittest.mock import patch

from freezegun import freeze_time
from quart import Quart
from quart import Response
from quart.typing import TestClientProtocol

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState

from .quart_test_helpers import app_and_client


class TestAlwaysEnabledMachine:
    """Tests for always-enabled machine functionality."""

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_always_enabled_basic(self, tmp_path: Path) -> None:
        """Test always-enabled machine shows 'Always On' with relay on."""
        # boilerplate for test
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        # send request
        mname: str = "always-on-machine"
        response: Response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        # check response
        assert response.status_code == 200
        assert await response.json == {
            "relay": True,
            "display": MachineState.ALWAYS_ON_DISPLAY_TEXT,
            "oops_led": False,
            "status_led_rgb": [0.0, 1.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }
        # boilerplate to read state from disk
        m: Machine = app.config["MACHINES"].machines_by_name[mname]
        with patch.dict("os.environ", {"MACHINE_STATE_DIR": m.state._state_dir}):
            ms: MachineState = MachineState(m)
        # verify state
        assert ms.display_text == MachineState.ALWAYS_ON_DISPLAY_TEXT
        assert ms.relay_desired_state is True
        assert ms.status_led_rgb == (0.0, 1.0, 0.0)
        assert ms.status_led_brightness == MachineState.STATUS_LED_BRIGHTNESS

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_always_enabled_oopsed(self, tmp_path: Path) -> None:
        """Test always-enabled machine exhibits correct Oops behavior."""
        # boilerplate for test
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        mname: str = "always-on-machine"

        # First, machine should be in always-on state
        response: Response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        assert response.status_code == 200
        json_response = await response.json
        assert json_response["relay"] is True
        assert json_response["display"] == MachineState.ALWAYS_ON_DISPLAY_TEXT

        # Oops the machine
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": True,
                "rfid_value": "",
                "uptime": 13.5,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        assert response.status_code == 200
        json_response = await response.json
        assert json_response == {
            "relay": False,
            "display": MachineState.OOPS_DISPLAY_TEXT,
            "oops_led": True,
            "status_led_rgb": [1.0, 0.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }

        # Release oops button (oops=false) - machine stays oopsed
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",
                "uptime": 14.7,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        assert response.status_code == 200
        json_response = await response.json
        # Machine stays oopsed when button is released
        assert json_response == {
            "relay": False,
            "display": MachineState.OOPS_DISPLAY_TEXT,
            "oops_led": True,
            "status_led_rgb": [1.0, 0.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }

        # Un-oops via API endpoint
        response = await client.delete(f"/api/machine/oops/{mname}")
        assert response.status_code == 200

        # Now machine should return to always-on state
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",
                "uptime": 15.9,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        assert response.status_code == 200
        json_response = await response.json
        # After un-oops, always-enabled machine returns to always-on state
        assert json_response == {
            "relay": True,
            "display": MachineState.ALWAYS_ON_DISPLAY_TEXT,
            "oops_led": False,
            "status_led_rgb": [0.0, 1.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_always_enabled_ignores_rfid_insert(self, tmp_path: Path) -> None:
        """Test always-enabled machine ignores RFID card insertion."""
        # boilerplate for test
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        mname: str = "always-on-machine"

        # Insert an RFID card (authorized user)
        response: Response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "1234567890",  # This is user 1 from users.json
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        # Machine should still show "Always On", not a welcome message
        assert response.status_code == 200
        json_response = await response.json
        assert json_response == {
            "relay": True,
            "display": MachineState.ALWAYS_ON_DISPLAY_TEXT,  # NOT "Welcome, <name>"
            "oops_led": False,
            "status_led_rgb": [0.0, 1.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_always_enabled_ignores_rfid_remove(self, tmp_path: Path) -> None:
        """Test always-enabled machine ignores RFID card removal."""
        # boilerplate for test
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        mname: str = "always-on-machine"

        # Insert an RFID card first
        response: Response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "1234567890",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        assert response.status_code == 200
        json_response = await response.json
        assert json_response["relay"] is True

        # Remove the RFID card
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",  # Empty = card removed
                "uptime": 13.5,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        # Machine should still be on with "Always On" display
        assert response.status_code == 200
        json_response = await response.json
        assert json_response == {
            "relay": True,  # Still on!
            "display": MachineState.ALWAYS_ON_DISPLAY_TEXT,  # Still "Always On"
            "oops_led": False,
            "status_led_rgb": [0.0, 1.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_always_enabled_first_contact(self, tmp_path: Path) -> None:
        """Test always-enabled machine is immediately enabled on first contact."""
        # boilerplate for test
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        mname: str = "always-on-machine"

        # First contact - no RFID, no oops, brand new machine
        response: Response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",
                "uptime": 1.0,  # Just started
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        # Machine should be immediately enabled
        assert response.status_code == 200
        json_response = await response.json
        assert json_response == {
            "relay": True,  # On immediately!
            "display": MachineState.ALWAYS_ON_DISPLAY_TEXT,
            "oops_led": False,
            "status_led_rgb": [0.0, 1.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }
