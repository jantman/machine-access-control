"""Views related to machine endpoints."""

from logging import Logger
from logging import getLogger
from typing import Dict
from typing import Optional

from flask import Response
from flask import current_app
from prometheus_client import Gauge
from prometheus_client import generate_latest
from prometheus_client.core import Metric
from prometheus_client.samples import Sample

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig


logger: Logger = getLogger(__name__)

CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


class LabeledGaugeMetricFamily(Metric):
    """Not sure why the upstream one doesn't allow labels..."""

    def __init__(
        self,
        name: str,
        documentation: str,
        value: Optional[float] = None,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
    ):
        """Initialize LabeledGaugeMetricFamily."""
        Metric.__init__(self, name, documentation, "gauge", unit)
        if labels is None:
            labels = {}
        self._labels = labels
        if value is not None:
            self.add_metric(labels, value)

    def add_metric(self, labels: Dict[str, str], value: float) -> None:
        """Add a metric to the metric family.

        Args:
          labels: A dictionary of labels
          value: A float
        """
        self.samples.append(Sample(self.name, dict(labels | self._labels), value, None))


def prometheus_route() -> Response:
    """API method to return Prometheus-compatible metrics."""
    mconf: MachinesConfig = current_app.config["MACHINES"]  # noqa
    uconf: UsersConfig = current_app.config["USERS"]  # noqa
    mconf_load: Gauge = Gauge(
        "machine_config_load_timestamp",
        "The timestamp when the machine config was loaded",
    )
    mconf_load.set(mconf.load_time)
    uconf_load: Gauge = Gauge(
        "user_config_load_timestamp", "The timestamp when the users config was loaded"
    )
    uconf_load.set(uconf.load_time)
    stime: Gauge = Gauge(
        "app_start_timestamp", "The timestamp when the server app started"
    )
    stime.set(current_app.config["START_TIME"])
    numu: Gauge = Gauge("user_count", "The number of users configured")
    numu.set(len(uconf.users))
    numf: Gauge = Gauge("fob_count", "The number of fobs configured")
    numf.set(len(uconf.users_by_fob))
    # Machine metrics
    relay_state: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_relay_state", "The state of the machine relay"
    )
    oops_state: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_oops_state", "The Oops state of the machine"
    )
    lockout_state: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_lockout_state", "The lockout state of the machine"
    )
    unauth_state: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_unauth_warn_only_state",
        "The unauthorized_warn_only state of the machine",
    )
    m_checkin: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_last_checkin_timestamp", "The last checkin timestamp for the machine"
    )
    m_update: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_last_update_timestamp", "The last update timestamp of the machine"
    )
    m_rfid_present: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_rfid_present", "Whether a RFID fob is present in the machine"
    )
    m_rfid_present_since: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_rfid_present_since_timestamp",
        "The timestamp since the RFID was inserter into the machine",
    )
    current_amps: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_current_amps", "The amperage being used by the machine if applicable"
    )
    m_user: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_known_user", "Whether a known user RFID is inserted into the machine"
    )
    uptime: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_uptime_seconds", "The machine uptime seconds"
    )
    wifi_db: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_wifi_signal_db", "The machine WiFi signal in dB"
    )
    wifi_percent: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_wifi_signal_percent", "The machine WiFi signal in percent"
    )
    temp_c: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_esp_temperature_c", "The machine ESP32 internal temperature in °C"
    )
    led: LabeledGaugeMetricFamily = LabeledGaugeMetricFamily(
        "machine_status_led", "The machine status LED state"
    )
    m: Machine
    for m in mconf.machines:
        relay_state.add_metric(
            {"machine_name": m.name}, 1 if m.state.relay_desired_state else 0
        )
        oops_state.add_metric({"machine_name": m.name}, 1 if m.state.is_oopsed else 0)
        lockout_state.add_metric(
            {"machine_name": m.name}, 1 if m.state.is_locked_out else 0
        )
        unauth_state.add_metric(
            {"machine_name": m.name}, 1 if m.unauthorized_warn_only else 0
        )
        m_checkin.add_metric({"machine_name": m.name}, m.state.last_checkin or 0)
        m_update.add_metric({"machine_name": m.name}, m.state.last_update or 0)
        m_rfid_present.add_metric(
            {"machine_name": m.name}, 1 if m.state.rfid_value else 0
        )
        m_rfid_present_since.add_metric(
            {"machine_name": m.name}, m.state.rfid_present_since or 0
        )
        current_amps.add_metric({"machine_name": m.name}, m.state.current_amps)
        m_user.add_metric({"machine_name": m.name}, 1 if m.state.current_user else 0)
        uptime.add_metric({"machine_name": m.name}, m.state.uptime)
        wifi_db.add_metric({"machine_name": m.name}, m.state.wifi_signal_db or 0)
        wifi_percent.add_metric(
            {"machine_name": m.name}, m.state.wifi_signal_percent or 0
        )
        temp_c.add_metric({"machine_name": m.name}, m.state.internal_temperature_c or 0)
        led.add_metric(
            {"machine_name": m.name, "led_attribute": "red"}, m.state.status_led_rgb[0]
        )
        led.add_metric(
            {"machine_name": m.name, "led_attribute": "green"},
            m.state.status_led_rgb[1],
        )
        led.add_metric(
            {"machine_name": m.name, "led_attribute": "blue"}, m.state.status_led_rgb[2]
        )
        led.add_metric(
            {"machine_name": m.name, "led_attribute": "brightness"},
            m.state.status_led_brightness,
        )
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)