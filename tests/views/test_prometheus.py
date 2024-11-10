"""Tests for API Views."""

from pathlib import Path
from textwrap import dedent

from flask import Flask
from flask.testing import FlaskClient
from freezegun import freeze_time
from werkzeug.test import TestResponse

from dm_mac.views.prometheus import CONTENT_TYPE_LATEST

from .flask_test_helpers import app_and_client


class TestPrometheus:
    """Tests for API Prometheus view."""

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    def test_metrics_response(self, tmp_path: Path) -> None:
        """Test for API petrics response."""
        app: Flask
        client: FlaskClient
        app, client = app_and_client(tmp_path)
        response: TestResponse = client.get("/metrics")
        assert response.status_code == 200
        custom_metrics = (
            "\n"
            + response.text[
                response.text.find("# HELP machine_config_load_timestamp") :
            ]
        )
        expected = dedent(
            """
        # HELP machine_config_load_timestamp The timestamp when the machine config was loaded
        # TYPE machine_config_load_timestamp gauge
        machine_config_load_timestamp 1.689477248e+09
        # HELP user_config_load_timestamp The timestamp when the users config was loaded
        # TYPE user_config_load_timestamp gauge
        user_config_load_timestamp 1.689477248e+09
        # HELP app_start_timestamp The timestamp when the server app started
        # TYPE app_start_timestamp gauge
        app_start_timestamp 1.689477248e+09
        # HELP user_count The number of users configured
        # TYPE user_count gauge
        user_count 4.0
        # HELP fob_count The number of fobs configured
        # TYPE fob_count gauge
        fob_count 4.0
        # HELP machine_relay_state The state of the machine relay
        # TYPE machine_relay_state gauge
        machine_relay_state{machine_name="metal-mill"} 0.0
        machine_relay_state{machine_name="hammer"} 0.0
        machine_relay_state{machine_name="permissive-lathe"} 0.0
        machine_relay_state{machine_name="restrictive-lathe"} 0.0
        machine_relay_state{machine_name="esp32test"} 0.0
        # HELP machine_oops_state The Oops state of the machine
        # TYPE machine_oops_state gauge
        machine_oops_state{machine_name="metal-mill"} 0.0
        machine_oops_state{machine_name="hammer"} 0.0
        machine_oops_state{machine_name="permissive-lathe"} 0.0
        machine_oops_state{machine_name="restrictive-lathe"} 0.0
        machine_oops_state{machine_name="esp32test"} 0.0
        # HELP machine_lockout_state The lockout state of the machine
        # TYPE machine_lockout_state gauge
        machine_lockout_state{machine_name="metal-mill"} 0.0
        machine_lockout_state{machine_name="hammer"} 0.0
        machine_lockout_state{machine_name="permissive-lathe"} 0.0
        machine_lockout_state{machine_name="restrictive-lathe"} 0.0
        machine_lockout_state{machine_name="esp32test"} 0.0
        # HELP machine_unauth_warn_only_state The unauthorized_warn_only state of the machine
        # TYPE machine_unauth_warn_only_state gauge
        machine_unauth_warn_only_state{machine_name="metal-mill"} 0.0
        machine_unauth_warn_only_state{machine_name="hammer"} 1.0
        machine_unauth_warn_only_state{machine_name="permissive-lathe"} 1.0
        machine_unauth_warn_only_state{machine_name="restrictive-lathe"} 0.0
        machine_unauth_warn_only_state{machine_name="esp32test"} 1.0
        # HELP machine_last_checkin_timestamp The last checkin timestamp for the machine
        # TYPE machine_last_checkin_timestamp gauge
        machine_last_checkin_timestamp{machine_name="metal-mill"} 0.0
        machine_last_checkin_timestamp{machine_name="hammer"} 0.0
        machine_last_checkin_timestamp{machine_name="permissive-lathe"} 0.0
        machine_last_checkin_timestamp{machine_name="restrictive-lathe"} 0.0
        machine_last_checkin_timestamp{machine_name="esp32test"} 0.0
        # HELP machine_last_update_timestamp The last update timestamp of the machine
        # TYPE machine_last_update_timestamp gauge
        machine_last_update_timestamp{machine_name="metal-mill"} 0.0
        machine_last_update_timestamp{machine_name="hammer"} 0.0
        machine_last_update_timestamp{machine_name="permissive-lathe"} 0.0
        machine_last_update_timestamp{machine_name="restrictive-lathe"} 0.0
        machine_last_update_timestamp{machine_name="esp32test"} 0.0
        # HELP machine_rfid_present Whether a RFID fob is present in the machine
        # TYPE machine_rfid_present gauge
        machine_rfid_present{machine_name="metal-mill"} 0.0
        machine_rfid_present{machine_name="hammer"} 0.0
        machine_rfid_present{machine_name="permissive-lathe"} 0.0
        machine_rfid_present{machine_name="restrictive-lathe"} 0.0
        machine_rfid_present{machine_name="esp32test"} 0.0
        # HELP machine_rfid_present_since_timestamp The timestamp since the RFID was inserter into the machine
        # TYPE machine_rfid_present_since_timestamp gauge
        machine_rfid_present_since_timestamp{machine_name="metal-mill"} 0.0
        machine_rfid_present_since_timestamp{machine_name="hammer"} 0.0
        machine_rfid_present_since_timestamp{machine_name="permissive-lathe"} 0.0
        machine_rfid_present_since_timestamp{machine_name="restrictive-lathe"} 0.0
        machine_rfid_present_since_timestamp{machine_name="esp32test"} 0.0
        # HELP machine_current_amps The amperage being used by the machine if applicable
        # TYPE machine_current_amps gauge
        machine_current_amps{machine_name="metal-mill"} 0.0
        machine_current_amps{machine_name="hammer"} 0.0
        machine_current_amps{machine_name="permissive-lathe"} 0.0
        machine_current_amps{machine_name="restrictive-lathe"} 0.0
        machine_current_amps{machine_name="esp32test"} 0.0
        # HELP machine_known_user Whether a known user RFID is inserted into the machine
        # TYPE machine_known_user gauge
        machine_known_user{machine_name="metal-mill"} 0.0
        machine_known_user{machine_name="hammer"} 0.0
        machine_known_user{machine_name="permissive-lathe"} 0.0
        machine_known_user{machine_name="restrictive-lathe"} 0.0
        machine_known_user{machine_name="esp32test"} 0.0
        # HELP machine_uptime_seconds The machine uptime seconds
        # TYPE machine_uptime_seconds gauge
        machine_uptime_seconds{machine_name="metal-mill"} 0.0
        machine_uptime_seconds{machine_name="hammer"} 0.0
        machine_uptime_seconds{machine_name="permissive-lathe"} 0.0
        machine_uptime_seconds{machine_name="restrictive-lathe"} 0.0
        machine_uptime_seconds{machine_name="esp32test"} 0.0
        # HELP machine_wifi_signal_db The machine WiFi signal in dB
        # TYPE machine_wifi_signal_db gauge
        machine_wifi_signal_db{machine_name="metal-mill"} 0.0
        machine_wifi_signal_db{machine_name="hammer"} 0.0
        machine_wifi_signal_db{machine_name="permissive-lathe"} 0.0
        machine_wifi_signal_db{machine_name="restrictive-lathe"} 0.0
        machine_wifi_signal_db{machine_name="esp32test"} 0.0
        # HELP machine_wifi_signal_percent The machine WiFi signal in percent
        # TYPE machine_wifi_signal_percent gauge
        machine_wifi_signal_percent{machine_name="metal-mill"} 0.0
        machine_wifi_signal_percent{machine_name="hammer"} 0.0
        machine_wifi_signal_percent{machine_name="permissive-lathe"} 0.0
        machine_wifi_signal_percent{machine_name="restrictive-lathe"} 0.0
        machine_wifi_signal_percent{machine_name="esp32test"} 0.0
        # HELP machine_esp_temperature_c The machine ESP32 internal temperature in °C
        # TYPE machine_esp_temperature_c gauge
        machine_esp_temperature_c{machine_name="metal-mill"} 0.0
        machine_esp_temperature_c{machine_name="hammer"} 0.0
        machine_esp_temperature_c{machine_name="permissive-lathe"} 0.0
        machine_esp_temperature_c{machine_name="restrictive-lathe"} 0.0
        machine_esp_temperature_c{machine_name="esp32test"} 0.0
        # HELP machine_status_led The machine status LED state
        # TYPE machine_status_led gauge
        machine_status_led{led_attribute="red",machine_name="metal-mill"} 0.0
        machine_status_led{led_attribute="green",machine_name="metal-mill"} 0.0
        machine_status_led{led_attribute="blue",machine_name="metal-mill"} 0.0
        machine_status_led{led_attribute="brightness",machine_name="metal-mill"} 0.0
        machine_status_led{led_attribute="red",machine_name="hammer"} 0.0
        machine_status_led{led_attribute="green",machine_name="hammer"} 0.0
        machine_status_led{led_attribute="blue",machine_name="hammer"} 0.0
        machine_status_led{led_attribute="brightness",machine_name="hammer"} 0.0
        machine_status_led{led_attribute="red",machine_name="permissive-lathe"} 0.0
        machine_status_led{led_attribute="green",machine_name="permissive-lathe"} 0.0
        machine_status_led{led_attribute="blue",machine_name="permissive-lathe"} 0.0
        machine_status_led{led_attribute="brightness",machine_name="permissive-lathe"} 0.0
        machine_status_led{led_attribute="red",machine_name="restrictive-lathe"} 0.0
        machine_status_led{led_attribute="green",machine_name="restrictive-lathe"} 0.0
        machine_status_led{led_attribute="blue",machine_name="restrictive-lathe"} 0.0
        machine_status_led{led_attribute="brightness",machine_name="restrictive-lathe"} 0.0
        machine_status_led{led_attribute="red",machine_name="esp32test"} 0.0
        machine_status_led{led_attribute="green",machine_name="esp32test"} 0.0
        machine_status_led{led_attribute="blue",machine_name="esp32test"} 0.0
        machine_status_led{led_attribute="brightness",machine_name="esp32test"} 0.0
        """  # noqa: E501
        )
        assert custom_metrics == expected
        assert (
            response.headers["Content-Type"] == CONTENT_TYPE_LATEST + "; charset=utf-8"
        )
