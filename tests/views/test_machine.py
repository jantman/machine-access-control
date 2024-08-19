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


class TestRouteSpecialCases:
    """Tests for /machine/update API endpoint special cases."""

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_unknown_machine(self, tmp_path: Path) -> None:
        """Test unknown machine."""
        # boilerplate for test
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        # send request
        mname: str = "unknown-machine-name"
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
        assert response.status_code == 404
        assert response.json == {
            "error": "No such machine: unknown-machine-name",
        }

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_execption(self, tmp_path: Path) -> None:
        """Test exception during machine update."""
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
                "foo": "bar",
            },
        )
        # check response
        assert response.status_code == 500
        assert response.json == {
            "error": "MachineState.update() got an unexpected keyword "
            "argument 'foo'",
        }


@freeze_time("2023-07-16 03:14:08", tz_offset=0)
class TestUpdateNewMachine:
    """Tests for /machine/update API endpoint for a brand new machine."""

    def test_initial_update(self, tmp_path: Path) -> None:
        """Test first update for a new machine."""
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
        assert ms.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert ms.current_amps == 0
        assert ms.uptime == 12.3
        assert ms.wifi_signal_db == -54
        assert ms.wifi_signal_percent == 92
        assert ms.internal_temperature_c == 53.89
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is False
        assert ms.is_locked_out is False
        assert ms.rfid_value is None
        assert ms.rfid_present_since is None
        assert ms.relay_desired_state is False
        assert ms.last_update is None
        assert ms.status_led_rgb == (0.0, 0.0, 0.0)
        assert ms.status_led_brightness == 0.0

    def test_initial_update_with_amps(self, tmp_path: Path) -> None:
        """Test first update for a new machine."""
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
                "amps": 0.0,
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
        assert ms.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert ms.current_amps == 0
        assert ms.uptime == 12.3
        assert ms.wifi_signal_db == -54
        assert ms.wifi_signal_percent == 92
        assert ms.internal_temperature_c == 53.89
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is False
        assert ms.is_locked_out is False
        assert ms.rfid_value is None
        assert ms.rfid_present_since is None
        assert ms.relay_desired_state is False
        assert ms.last_update is None
        assert ms.status_led_rgb == (0.0, 0.0, 0.0)
        assert ms.status_led_brightness == 0.0

    def test_empty_update(self, tmp_path: Path) -> None:
        """Test first incorrectly empty update for a new machine."""
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
        assert ms.display_text == MachineState.DEFAULT_DISPLAY_TEXT
        assert ms.current_amps == 0
        assert ms.uptime == 0.0
        assert ms.wifi_signal_db is None
        assert ms.wifi_signal_percent is None
        assert ms.internal_temperature_c is None
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is False
        assert ms.is_locked_out is False
        assert ms.rfid_value is None
        assert ms.rfid_present_since is None
        assert ms.relay_desired_state is False
        assert ms.last_update is None
        assert ms.status_led_rgb == (0.0, 0.0, 0.0)
        assert ms.status_led_brightness == 0.0


@freeze_time("2023-07-16 03:14:08", tz_offset=0)
class TestOops:
    """Tests for oops button being pressed."""

    def test_oops_without_user(self, tmp_path: Path) -> None:
        """Test oops button pressed with no user logged in."""
        # boilerplate for test
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        # set up state
        mname: str = "metal-mill"
        m: Machine = app.config["MACHINES"].machines_by_name[mname]
        # send request
        response: TestResponse = client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": True,
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
            "display": MachineState.OOPS_DISPLAY_TEXT,
            "oops_led": True,
            "status_led_rgb": [1.0, 0, 0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }
        # boilerplate to read state from disk
        with patch.dict("os.environ", {"MACHINE_STATE_DIR": m.state._state_dir}):
            ms: MachineState = MachineState(m)
        # verify state
        assert ms.display_text == MachineState.OOPS_DISPLAY_TEXT
        assert ms.current_amps == 0
        assert ms.uptime == 12.3
        assert ms.wifi_signal_db == -54
        assert ms.wifi_signal_percent == 92
        assert ms.internal_temperature_c == 53.89
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is True
        assert ms.is_locked_out is False
        assert ms.rfid_value is None
        assert ms.rfid_present_since is None
        assert ms.relay_desired_state is False
        assert ms.last_update == 1689477248.0
        assert ms.status_led_rgb == (1.0, 0.0, 0.0)
        assert ms.status_led_brightness == MachineState.STATUS_LED_BRIGHTNESS

    def test_oops_released_without_user(self, tmp_path: Path) -> None:
        """Test nothing different happens when oops button is released."""
        # boilerplate for test
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        # set up state
        mname: str = "metal-mill"
        m: Machine = app.config["MACHINES"].machines_by_name[mname]
        m.state.is_oopsed = True
        m.state.relay_desired_state = False
        m.state.display_text = MachineState.OOPS_DISPLAY_TEXT
        m.state.status_led_rgb = (1.0, 0.0, 0.0)
        m.state.status_led_brightness = MachineState.STATUS_LED_BRIGHTNESS
        m.state.last_checkin = 1689477200.0
        m.state.last_update = 1689477200.0
        m.state.uptime = 12.3
        # send request
        response: TestResponse = client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "",
                "uptime": 13.6,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        # check response
        assert response.status_code == 200
        assert response.json == {
            "relay": False,
            "display": MachineState.OOPS_DISPLAY_TEXT,
            "oops_led": True,
            "status_led_rgb": [1.0, 0, 0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }
        # boilerplate to read state from disk
        with patch.dict("os.environ", {"MACHINE_STATE_DIR": m.state._state_dir}):
            ms: MachineState = MachineState(m)
        # verify state
        assert ms.display_text == MachineState.OOPS_DISPLAY_TEXT
        assert ms.current_amps == 0
        assert ms.uptime == 13.6
        assert ms.wifi_signal_db == -54
        assert ms.wifi_signal_percent == 92
        assert ms.internal_temperature_c == 53.89
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is True
        assert ms.is_locked_out is False
        assert ms.rfid_value is None
        assert ms.rfid_present_since is None
        assert ms.relay_desired_state is False
        assert ms.last_update == 1689477200.0
        assert ms.status_led_rgb == (1.0, 0.0, 0.0)
        assert ms.status_led_brightness == MachineState.STATUS_LED_BRIGHTNESS

    def test_oops_with_user(self, tmp_path: Path) -> None:
        """Test oops button pressed with a user logged in (and relay on)."""
        pass

    def test_oops_released_with_user(self, tmp_path: Path) -> None:
        """Test nothing different happens when oops button is released."""
        pass

    def test_oops_with_user_and_locked_out(self, tmp_path: Path) -> None:
        """Test oops button pressed with a user logged in and machine locked out."""
        pass

    def test_oops_without_user_and_locked_out(self, tmp_path: Path) -> None:
        """Test oops button pressed w/0 user and with machine locked out."""
        pass


@freeze_time("2023-07-16 03:14:08", tz_offset=0)
class TestRfidNormalState:
    """Tests for RFID value changed in a normal state.

    i.e. not oopsed, locked out, or set to unauthorized_warn_only.
    """

    def test_rfid_authorized_inserted(self, tmp_path: Path) -> None:
        """Test when an authorized RFID card is inserted."""
        # boilerplate for test
        app: Flask
        client: FlaskClient
        app, client = test_app(tmp_path)
        # set up state
        mname: str = "metal-mill"
        m: Machine = app.config["MACHINES"].machines_by_name[mname]
        # send request
        response: TestResponse = client.post(
            "/api/machine/update",
            json={
                "machine_name": mname,
                "oops": False,
                "rfid_value": "8114346998",
                "uptime": 13.6,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        # check response
        assert response.status_code == 200
        assert response.json == {
            "relay": True,
            "display": "Welcome,\nPAshley",
            "oops_led": False,
            "status_led_rgb": [0.0, 1.0, 0.0],
            "status_led_brightness": MachineState.STATUS_LED_BRIGHTNESS,
        }
        # boilerplate to read state from disk
        with patch.dict("os.environ", {"MACHINE_STATE_DIR": m.state._state_dir}):
            ms: MachineState = MachineState(m)
        # verify state
        assert ms.display_text == "Welcome,\nPAshley"
        assert ms.current_amps == 0
        assert ms.uptime == 13.6
        assert ms.wifi_signal_db == -54
        assert ms.wifi_signal_percent == 92
        assert ms.internal_temperature_c == 53.89
        assert ms.last_checkin == 1689477248.0
        assert ms.is_oopsed is False
        assert ms.is_locked_out is False
        assert ms.rfid_value == "8114346998"
        assert ms.rfid_present_since == 1689477248.0
        assert ms.current_user == app.config["USERS"].users_by_fob["8114346998"]
        assert ms.relay_desired_state is True
        assert ms.last_update == 1689477248.0
        assert ms.status_led_rgb == (1.0, 0.0, 0.0)
        assert ms.status_led_brightness == MachineState.STATUS_LED_BRIGHTNESS

    def test_rfid_authorized_inserted_zeropad(self, tmp_path: Path) -> None:
        """Test when an auth RFID card is inserted but < 10 characters."""
        pass

    def test_rfid_authorized_removed(self, tmp_path: Path) -> None:
        """Test when an authorized RFID card is removed."""
        pass

    def test_rfid_unauthorized_inserted_zeropad(self, tmp_path: Path) -> None:
        """Test when an unauth RFID card is inserted but < 10 characters."""
        pass

    def test_rfid_unauthorized_removed(self, tmp_path: Path) -> None:
        """Test when an unauthorized RFID card is removed."""
        pass

    def test_rfid_unknown_inserted(self, tmp_path: Path) -> None:
        """Test when an unknown RFID card is inserted."""
        pass

    def test_rfid_unknown_removed(self, tmp_path: Path) -> None:
        """Test when an unknown RFID card is removed."""
        pass


# repeat that above class for unauthorized_warn_only, oopsed, and locked out
