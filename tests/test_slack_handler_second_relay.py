"""[US3 T035] Slack handler tests for second-relay messaging."""

import os
from typing import Generator
from typing import Optional
from typing import Tuple
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from quart import Quart
from slack_bolt.async_app import AsyncApp

from dm_mac.models.machine import Machine
from dm_mac.models.machine import SecondRelayConfig
from dm_mac.slack_handler import SlackHandler


HandlerFixture = Tuple[SlackHandler, AsyncMock]


@pytest.fixture
def handler() -> Generator[HandlerFixture, None, None]:
    """Build a SlackHandler with mocked Slack app/client."""
    with patch.dict(
        os.environ,
        {
            "SLACK_CONTROL_CHANNEL_ID": "Cadmin",
            "SLACK_OOPS_CHANNEL_ID": "Coops",
            "SLACK_BOT_TOKEN": "btoken",
            "SLACK_SIGNING_SECRET": "secret",
        },
    ):
        with patch("dm_mac.slack_handler.AsyncApp", spec=AsyncApp):
            quart_app = Mock(spec_set=Quart)
            h = SlackHandler(quart_app)
            mock_client = AsyncMock()
            type(h.app).client = mock_client
            yield h, mock_client


def _make_machine(
    name: str = "m1", second_relay: Optional[SecondRelayConfig] = None
) -> Machine:
    mach = Mock(spec_set=Machine)
    type(mach).name = name
    type(mach).display_name = name
    type(mach).second_relay = second_relay
    return mach


class TestSlackBothRelaysSuffix:
    async def test_log_lock_with_second_relay(self, handler: HandlerFixture) -> None:
        h, client = handler
        sr = SecondRelayConfig(authorizations_or=["s"])
        mach = _make_machine(second_relay=sr)
        await h.log_lock(mach, "Slack")
        # find the control_channel_id call
        admin_calls = [
            c
            for c in client.chat_postMessage.call_args_list
            if c.kwargs.get("channel") == "Cadmin"
        ]
        assert len(admin_calls) >= 1
        text = admin_calls[0].kwargs.get("text")
        assert "(both relays)" in text

    async def test_log_lock_without_second_relay(self, handler: HandlerFixture) -> None:
        h, client = handler
        mach = _make_machine(second_relay=None)
        await h.log_lock(mach, "Slack")
        admin_calls = [
            c
            for c in client.chat_postMessage.call_args_list
            if c.kwargs.get("channel") == "Cadmin"
        ]
        assert len(admin_calls) >= 1
        text = admin_calls[0].kwargs.get("text")
        assert "both relays" not in text

    async def test_log_oops_with_second_relay(self, handler: HandlerFixture) -> None:
        h, client = handler
        sr = SecondRelayConfig(authorizations_or=["s"])
        mach = _make_machine(second_relay=sr)
        await h.log_oops(mach, "Slack", user_name="Alice")
        admin_calls = [
            c
            for c in client.chat_postMessage.call_args_list
            if c.kwargs.get("channel") == "Cadmin"
        ]
        text = admin_calls[0].kwargs.get("text")
        assert "(both relays)" in text

    async def test_log_unlock_with_second_relay(self, handler: HandlerFixture) -> None:
        h, client = handler
        sr = SecondRelayConfig(authorizations_or=["s"])
        mach = _make_machine(second_relay=sr)
        await h.log_unlock(mach, "Slack")
        admin_calls = [
            c
            for c in client.chat_postMessage.call_args_list
            if c.kwargs.get("channel") == "Cadmin"
        ]
        text = admin_calls[0].kwargs.get("text")
        assert "(both relays)" in text

    async def test_log_unoops_with_second_relay(self, handler: HandlerFixture) -> None:
        h, client = handler
        sr = SecondRelayConfig(authorizations_or=["s"])
        mach = _make_machine(second_relay=sr)
        await h.log_unoops(mach, "Slack")
        admin_calls = [
            c
            for c in client.chat_postMessage.call_args_list
            if c.kwargs.get("channel") == "Cadmin"
        ]
        text = admin_calls[0].kwargs.get("text")
        assert "(both relays)" in text
