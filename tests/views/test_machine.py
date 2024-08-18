"""Tests for /machine API endpoints."""

from pathlib import Path
from unittest.mock import patch

from flask import Flask
from flask.testing import FlaskClient
from freezegun import freeze_time
from werkzeug.test import TestResponse

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachineState

from .flask_test_helpers import test_app


class TestUpdateNewMachine:
    """Tests for /machine/update API endpoint for a brand new machine."""

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_initial_update(self, tmp_path: Path) -> None:
        """Test for API index response."""
        # boilerplate for test
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        # send request
        mname: str = "metal-mill"
        response: TestResponse = client.post(
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
        assert response.json == {
            "relay": False,
            "display": MachineState.DEFAULT_DISPLAY_TEXT,
            "oops_led": False,
            "status_led_rgb": [0, 0, 0],
            "status_led_brightness": 0,
        }
        # boilerplate to read state from disk
        m: Machine = app.config["MACHINES"].machines_by_name[mname]
        with patch.dict("os.environ", {"MACHINE_STATE_DIR": m.state._state_dir}):
            ms: MachineState = MachineState(m)
        # verify state
        assert ms.current_amps == 0
        assert ms.uptime == 12.3
        assert ms.wifi_signal_db == -54
        assert ms.wifi_signal_percent == 92
        assert ms.internal_temperature_c == 53.89
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is False
        assert ms.rfid_value is None
        assert ms.rfid_present_since is None
        assert ms.relay_desired_state is False
        assert ms.last_update is None
