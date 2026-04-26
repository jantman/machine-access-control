"""Integration tests for second_relay support via /machine/update."""

import json
import os
from pathlib import Path

from freezegun import freeze_time
from quart import Quart
from quart import Response
from quart.typing import TestClientProtocol

from dm_mac.models.machine import MachineState

from .quart_test_helpers import app_and_client


# Fobs from tests/fixtures/users-second-relay.json
FOB_PRIMARY_ONLY = "1000000001"
FOB_SECONDARY_ONLY = "1000000002"
FOB_BOTH_AUTHS = "1000000003"
FOB_SHARED_ONLY = "1000000004"

# Fobs from tests/fixtures/users.json (used by US4 LCD invariance tests)
FOB_ASHLEY = "8114346998"  # has Metal Lathe etc.


def _client(tmp_path: Path):
    """Build app/client wired to the second-relay fixtures."""
    return app_and_client(
        tmp_path,
        user_conf="users-second-relay.json",
        machine_conf="machines-second-relay.json",
    )


async def _post_update(client: TestClientProtocol, mname: str, **overrides) -> Response:
    body = {
        "machine_name": mname,
        "oops": False,
        "rfid_value": "",
        "uptime": 12.3,
        "wifi_signal_db": -54,
        "wifi_signal_percent": 92,
        "internal_temperature_c": 53.89,
    }
    body.update(overrides)
    return await client.post("/api/machine/update", json=body)


# ---------------------------------------------------------------------------
# US1: primary-only operator on a second-relay-equipped machine
# ---------------------------------------------------------------------------


@freeze_time("2026-04-26 03:14:08", tz_offset=0)
class TestUS1PrimaryOnly:
    """[US1] Primary-only operator -> base relay on, second relay off."""

    async def test_primary_only_user_taps_in(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        response = await _post_update(
            client, "second-relay-strict", rfid_value=FOB_PRIMARY_ONLY
        )
        assert response.status_code == 200
        body = await response.json
        assert body["relay"] is True
        assert body["second_relay"] is False
        # LCD invariant: existing "Welcome,\n<preferred_name>" string
        assert body["display"] == "Welcome,\nPrimaryOnly"

    async def test_primary_only_user_taps_out(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        await _post_update(client, "second-relay-strict", rfid_value=FOB_PRIMARY_ONLY)
        response = await _post_update(
            client, "second-relay-strict", rfid_value="", uptime=20.0
        )
        body = await response.json
        assert body["relay"] is False
        assert body["second_relay"] is False

    async def test_secondary_only_user_unauthorized(self, tmp_path: Path) -> None:
        """Secondary-only user has no primary, so primary relay stays off."""
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        response = await _post_update(
            client, "second-relay-strict", rfid_value=FOB_SECONDARY_ONLY
        )
        body = await response.json
        assert body["relay"] is False
        assert body["second_relay"] is False


# ---------------------------------------------------------------------------
# US2: operator with both auths
# ---------------------------------------------------------------------------


@freeze_time("2026-04-26 03:14:08", tz_offset=0)
class TestUS2BothAuths:
    """[US2] Operator with both auths gets both relays."""

    async def test_both_auths_taps_in(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        response = await _post_update(
            client, "second-relay-strict", rfid_value=FOB_BOTH_AUTHS
        )
        body = await response.json
        assert body["relay"] is True
        assert body["second_relay"] is True

    async def test_both_auths_then_oops(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        await _post_update(client, "second-relay-strict", rfid_value=FOB_BOTH_AUTHS)
        response = await _post_update(
            client,
            "second-relay-strict",
            rfid_value=FOB_BOTH_AUTHS,
            oops=True,
            uptime=20.0,
        )
        body = await response.json
        assert body["relay"] is False
        assert body["second_relay"] is False
        assert body["display"] == MachineState.OOPS_DISPLAY_TEXT

    async def test_both_auths_then_lockout(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        await _post_update(client, "second-relay-strict", rfid_value=FOB_BOTH_AUTHS)
        # Lock the machine via API
        resp = await client.post("/api/machine/locked_out/second-relay-strict")
        assert resp.status_code == 200
        # Next update should report both relays off and lockout display
        response = await _post_update(
            client,
            "second-relay-strict",
            rfid_value=FOB_BOTH_AUTHS,
            uptime=20.0,
        )
        body = await response.json
        assert body["relay"] is False
        assert body["second_relay"] is False
        assert body["display"] == MachineState.LOCKOUT_DISPLAY_TEXT

    async def test_both_auths_tap_out(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        await _post_update(client, "second-relay-strict", rfid_value=FOB_BOTH_AUTHS)
        response = await _post_update(
            client, "second-relay-strict", rfid_value="", uptime=20.0
        )
        body = await response.json
        assert body["relay"] is False
        assert body["second_relay"] is False

    async def test_warn_only_primary_only_user(self, tmp_path: Path) -> None:
        """Warn-only second relay grants the relay to a primary-only user."""
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        response = await _post_update(
            client, "second-relay-warn", rfid_value=FOB_PRIMARY_ONLY
        )
        body = await response.json
        assert body["relay"] is True
        assert body["second_relay"] is True

    async def test_always_enabled_primary_only_user(self, tmp_path: Path) -> None:
        """always_enabled second relay tracks primary regardless of secondary."""
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        response = await _post_update(
            client, "second-relay-always", rfid_value=FOB_PRIMARY_ONLY
        )
        body = await response.json
        assert body["relay"] is True
        assert body["second_relay"] is True
        # Tap out -> both off
        response2 = await _post_update(
            client, "second-relay-always", rfid_value="", uptime=20.0
        )
        body2 = await response2.json
        assert body2["relay"] is False
        assert body2["second_relay"] is False

    async def test_shared_auth_grants_both(self, tmp_path: Path) -> None:
        """Same auth in both lists -> user with that auth gets both relays."""
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        response = await _post_update(
            client, "second-relay-shared", rfid_value=FOB_SHARED_ONLY
        )
        body = await response.json
        assert body["relay"] is True
        assert body["second_relay"] is True

    async def test_user_swap_clears_secondary(self, tmp_path: Path) -> None:
        """User swap (both -> primary-only) drops second_relay."""
        app: Quart
        client: TestClientProtocol
        app, client = _client(tmp_path)
        # Both-auth user taps in
        r1 = await _post_update(
            client, "second-relay-strict", rfid_value=FOB_BOTH_AUTHS
        )
        b1 = await r1.json
        assert b1["relay"] is True
        assert b1["second_relay"] is True
        # Tap out
        r2 = await _post_update(
            client, "second-relay-strict", rfid_value="", uptime=20.0
        )
        b2 = await r2.json
        assert b2["second_relay"] is False
        # Primary-only user taps in
        r3 = await _post_update(
            client, "second-relay-strict", rfid_value=FOB_PRIMARY_ONLY, uptime=21.0
        )
        b3 = await r3.json
        assert b3["relay"] is True
        assert b3["second_relay"] is False


# ---------------------------------------------------------------------------
# US4: backwards compatibility for single-relay machines
# ---------------------------------------------------------------------------


@freeze_time("2023-07-16 03:14:08", tz_offset=0)
class TestUS4SingleRelayCompat:
    """[US4] Single-relay machines unaffected (modulo always-emitted field)."""

    @staticmethod
    def _golden(name: str) -> dict:
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "fixtures",
            "golden-single-relay-response.json",
        )
        with open(path) as f:
            return json.load(f)[name]

    async def test_idle_no_fob_matches_golden(self, tmp_path: Path) -> None:
        """metal-mill single-relay machine, idle, response matches golden."""
        app: Quart
        client: TestClientProtocol
        # use the existing single-relay fixture
        app, client = app_and_client(tmp_path)
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": "metal-mill",
                "oops": False,
                "rfid_value": "",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        body = await response.json
        expected = dict(self._golden("idle_no_fob"))
        expected["second_relay"] = False
        assert body == expected

    async def test_authorized_login_lcd_unchanged(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": "metal-mill",
                "oops": False,
                "rfid_value": "8114346998",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        body = await response.json
        expected = dict(self._golden("authorized_user_logged_in"))
        expected["second_relay"] = False
        assert body == expected

    async def test_request_without_second_relay_state_accepted(
        self, tmp_path: Path
    ) -> None:
        """[US4 T030] MCU forward-compat: no second_relay_state in body."""
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": "metal-mill",
                "oops": False,
                "rfid_value": "",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
            },
        )
        assert response.status_code == 200
        body = await response.json
        assert body["second_relay"] is False

    async def test_request_with_second_relay_state_against_unconfigured(
        self, tmp_path: Path
    ) -> None:
        """[US4 T032a] MCU sends second_relay_state for a machine without one."""
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        response = await client.post(
            "/api/machine/update",
            json={
                "machine_name": "metal-mill",
                "oops": False,
                "rfid_value": "",
                "uptime": 12.3,
                "wifi_signal_db": -54,
                "wifi_signal_percent": 92,
                "internal_temperature_c": 53.89,
                "second_relay_state": True,
            },
        )
        assert response.status_code == 200
        body = await response.json
        assert body["second_relay"] is False

    async def test_no_second_relay_log_text_for_single_relay(
        self, tmp_path: Path, caplog
    ) -> None:
        """[US4 T032] No log mentions 'second relay', 'accessory', etc."""
        import logging

        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        with caplog.at_level(logging.DEBUG):
            await client.post(
                "/api/machine/update",
                json={
                    "machine_name": "metal-mill",
                    "oops": False,
                    "rfid_value": "8114346998",
                    "uptime": 12.3,
                    "wifi_signal_db": -54,
                    "wifi_signal_percent": 92,
                    "internal_temperature_c": 53.89,
                },
            )
            await client.post(
                "/api/machine/update",
                json={
                    "machine_name": "metal-mill",
                    "oops": False,
                    "rfid_value": "",
                    "uptime": 13.0,
                    "wifi_signal_db": -54,
                    "wifi_signal_percent": 92,
                    "internal_temperature_c": 53.89,
                },
            )
        text = " ".join(rec.getMessage() for rec in caplog.records).lower()
        assert "second relay" not in text
        assert "accessory" not in text
