"""[US3 T036] Prometheus tests for second-relay metrics."""

from pathlib import Path

from freezegun import freeze_time
from quart import Quart
from quart.typing import TestClientProtocol
from quart.wrappers import Response

from .quart_test_helpers import app_and_client


@freeze_time("2026-04-26 03:14:08", tz_offset=0)
class TestPrometheusSecondRelay:
    """Verify second-relay metrics emit only for second-relay machines."""

    async def test_second_relay_metrics_emitted(self, tmp_path: Path) -> None:
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(
            tmp_path,
            user_conf="users-second-relay.json",
            machine_conf="machines-second-relay.json",
        )
        response: Response = await client.get("/metrics")
        assert response.status_code == 200
        text = await response.get_data(True)
        # Four new metrics present
        assert "machine_second_relay_state" in text
        assert "machine_second_relay_configured" in text
        assert "machine_second_relay_unauth_warn_only" in text
        assert "machine_second_relay_always_enabled" in text
        # Exact label set for second-relay-strict (root alias "Second Relay Strict",
        # second_relay alias "Strict Accessory"):
        assert (
            'machine_second_relay_configured{display_name="Second Relay Strict",'
            'machine_name="second-relay-strict",'
            'second_relay_alias="Strict Accessory"} 1.0'
        ) in text
        # And for second-relay-warn (no root alias, no second_relay alias):
        assert (
            'machine_second_relay_configured{display_name="second-relay-warn",'
            'machine_name="second-relay-warn",second_relay_alias=""} 1.0'
        ) in text
        assert (
            'machine_second_relay_unauth_warn_only{display_name="second-relay-warn",'
            'machine_name="second-relay-warn",second_relay_alias=""} 1.0'
        ) in text
        # always_enabled flag set on second-relay-always:
        assert (
            'machine_second_relay_always_enabled{display_name="second-relay-always",'
            'machine_name="second-relay-always",second_relay_alias=""} 1.0'
        ) in text
        # No sample for the single-relay machine in this fixture
        for line in text.splitlines():
            if line.startswith("machine_second_relay_"):
                # Only entries for machines with a configured second_relay
                # — i.e., not single-relay-machine
                assert 'machine_name="single-relay-machine"' not in line

    async def test_second_relay_metrics_not_emitted_when_unconfigured(
        self, tmp_path: Path
    ) -> None:
        """No second-relay metrics whatsoever for fixture without any second_relay."""
        app: Quart
        client: TestClientProtocol
        app, client = app_and_client(tmp_path)
        response: Response = await client.get("/metrics")
        text = await response.get_data(True)
        assert "machine_second_relay_state" not in text
        assert "machine_second_relay_configured" not in text
        assert "machine_second_relay_unauth_warn_only" not in text
        assert "machine_second_relay_always_enabled" not in text
