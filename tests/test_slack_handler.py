"""Tests for SlackHandler class."""

import os
from pathlib import Path
from time import time
from typing import Any
from typing import Dict
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

from freezegun import freeze_time
from quart import Quart
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay

from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig
from dm_mac.slack_handler import Message
from dm_mac.slack_handler import SlackHandler


pbm = "dm_mac.slack_handler"


class TestMessage:
    """Test the Message helper class."""

    def test_message(self) -> None:
        """Test it."""
        expected = Message(
            text="my text",
            user_id="U1111",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        assert expected.as_dict == {
            "raw_text": "my text",
            "command": ["text"],
            "user_id": "U1111",
            "user_name": "User Name",
            "user_handle": "displayName",
            "channel_id": "Cadmin",
            "channel_name": "AdminChannel",
        }
        assert expected == Message(
            text="my text",
            user_id="U1111",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        assert expected != Message(
            text="other text",
            user_id="U1111",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        assert expected != "another type"


class TestSlackHandler:
    """Test SlackHandler app mention."""

    @patch.dict(
        "os.environ",
        {
            "SLACK_CONTROL_CHANNEL_ID": "Cadmin",
            "SLACK_OOPS_CHANNEL_ID": "Coops",
            "SLACK_BOT_TOKEN": "btoken",
            "SLACK_SIGNING_SECRET": "secret",
        },
    )
    def setup_method(self, _) -> None:
        """Setup for each method in the class."""
        self.quart_app = Mock(spec_set=Quart)
        self.slack_app = AsyncMock(spec_set=AsyncApp)
        self.slack_client = AsyncMock()
        type(self.slack_app).client = self.slack_client

        async def users_info(user=None):
            res = MagicMock()
            if user == "U1111":
                res.data = {
                    "ok": True,
                    "user": {
                        "is_bot": False,
                        "is_app_user": False,
                        "profile": {
                            "real_name_normalized": "User Name",
                            "display_name_normalized": "displayName",
                        },
                    },
                }
            elif user == "U2222":
                res.data = {
                    "ok": True,
                    "user": {
                        "is_bot": True,
                        "is_app_user": False,
                        "profile": {
                            "real_name_normalized": "Bot Name",
                            "display_name_normalized": "botName",
                        },
                    },
                }
            else:
                res.data = {"ok": False}
            return res

        async def conversations_info(channel=None):
            res = MagicMock()
            res.data = {"ok": False}
            if channel == "Cadmin":
                res.data = {"ok": True, "channel": {"name": "AdminChannel"}}
            elif channel == "Coops":
                res.data = {"ok": True, "channel": {"name": "OopsChannel"}}
            return res

        self.slack_client.conversations_info.side_effect = conversations_info
        self.slack_client.users_info.side_effect = users_info
        with patch(f"{pbm}.AsyncApp") as self.m_async:
            self.m_async.return_value = self.slack_app
            self.cls = SlackHandler(self.quart_app)

    def test_init(self) -> None:
        """Test class __init__ method."""
        assert self.cls.control_channel_id == "Cadmin"
        assert self.cls.oops_channel_id == "Coops"
        assert self.cls.quart == self.quart_app
        assert self.m_async.mock_calls == [
            call(token="btoken", signing_secret="secret"),
            call().event("app_mention"),
            call().event("app_mention")(self.cls.app_mention),
        ]
        assert self.slack_app.mock_calls == [
            call.event("app_mention"),
            call.event("app_mention")(self.cls.app_mention),
        ]
        assert self.cls.app == self.slack_app

    async def test_app_mention_valid_command(self) -> None:
        """Test when the app receives a valid command."""
        msg = "<@U12345678> status"
        body: Dict[str, Any] = {
            "event": {
                "text": msg,
                "user": "U1111",
                "channel": "Cadmin",
            },
            "authorizations": [{"user_id": "U12345678"}],
        }
        say = AsyncMock(spec_set=AsyncSay)
        with patch(
            f"{pbm}.SlackHandler.handle_command", new_callable=AsyncMock
        ) as m_handle:
            await self.cls.app_mention(body, say)
        expected = Message(
            text=msg,
            user_id="U1111",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        assert m_handle.mock_calls == [call(expected, say)]
        assert self.slack_client.mock_calls == [
            call.users_info(user="U1111"),
            call.conversations_info(channel="Cadmin"),
        ]

    async def test_app_mention_invalid_message_start(self) -> None:
        """Test when the app receives a valid command."""
        msg = "notMyUserId status"
        body: Dict[str, Any] = {
            "event": {
                "text": msg,
                "user": "U1111",
                "channel": "Cadmin",
            },
            "authorizations": [{"user_id": "U12345678"}],
        }
        say = AsyncMock(spec_set=AsyncSay)
        with patch(
            f"{pbm}.SlackHandler.handle_command", new_callable=AsyncMock
        ) as m_handle:
            await self.cls.app_mention(body, say)
        assert m_handle.mock_calls == []
        assert self.slack_client.mock_calls == []

    async def test_app_mention_from_bot(self) -> None:
        """Test when the app receives a valid command."""
        msg = "<@U12345678> status"
        body: Dict[str, Any] = {
            "event": {
                "text": msg,
                "user": "U2222",
                "channel": "Cadmin",
            },
            "authorizations": [{"user_id": "U12345678"}],
        }
        say = AsyncMock(spec_set=AsyncSay)
        with patch(
            f"{pbm}.SlackHandler.handle_command", new_callable=AsyncMock
        ) as m_handle:
            await self.cls.app_mention(body, say)
        assert m_handle.mock_calls == []
        assert self.slack_client.mock_calls == [
            call.users_info(user="U2222"),
            call.conversations_info(channel="Cadmin"),
        ]

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_status_admin_channel(self, tmp_path) -> None:
        """Status request from someone in admin channel."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = True
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        mconf.machines_by_name["metal-mill"].state.relay_desired_state = False
        mconf.machines_by_name["metal-mill"].state.last_checkin = time() - 10
        mconf.machines_by_name["metal-mill"].state.last_update = time() - 90
        mconf.machines_by_name["metal-mill"].state.uptime = 86400
        mconf.machines_by_name["hammer"].state.is_oopsed = False
        mconf.machines_by_name["hammer"].state.is_locked_out = False
        mconf.machines_by_name["hammer"].state.relay_desired_state = False
        mconf.machines_by_name["hammer"].state.last_checkin = time() - 60
        mconf.machines_by_name["hammer"].state.last_update = time() - 60
        mconf.machines_by_name["hammer"].state.uptime = 120
        mconf.machines_by_name["permissive-lathe"].state.is_oopsed = False
        mconf.machines_by_name["permissive-lathe"].state.is_locked_out = True
        mconf.machines_by_name["permissive-lathe"].state.relay_desired_state = False
        mconf.machines_by_name["permissive-lathe"].state.last_checkin = (
            time() - (86400 * 7) + 240
        )
        mconf.machines_by_name["permissive-lathe"].state.last_update = time() - (
            86400 * 7
        )
        mconf.machines_by_name["permissive-lathe"].state.uptime = 360
        mconf.machines_by_name["restrictive-lathe"].state.is_oopsed = False
        mconf.machines_by_name["restrictive-lathe"].state.is_locked_out = False
        mconf.machines_by_name["restrictive-lathe"].state.relay_desired_state = True
        mconf.machines_by_name["restrictive-lathe"].state.last_checkin = time() - 10
        mconf.machines_by_name["restrictive-lathe"].state.last_update = time() - 600
        mconf.machines_by_name["restrictive-lathe"].state.uptime = 3603
        msg = Message(
            text="<@U12345678> status",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        expected = (
            "esp32test: Idle \n"
            "hammer: Idle (last contact a minute ago; last update a minute ago;"
            " uptime 2 minutes)\n"
            "metal-mill: Oopsed (last contact 10 seconds ago; last update a "
            "minute ago; uptime a day)\n"
            "permissive-lathe: Locked out (last contact 6 days ago; "
            "last update 7 days ago; uptime 6 minutes)\n"
            "restrictive-lathe: In use (last contact 10 seconds ago; "
            "last update 10 minutes ago; uptime an hour)\n"
        )
        assert say.mock_calls == [call(expected)]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_status_oops_channel(self, tmp_path) -> None:
        """Status request from someone in oops channel."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = True
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        mconf.machines_by_name["metal-mill"].state.relay_desired_state = False
        mconf.machines_by_name["metal-mill"].state.last_checkin = time() - 10
        mconf.machines_by_name["metal-mill"].state.last_update = time() - 90
        mconf.machines_by_name["metal-mill"].state.uptime = 86400
        mconf.machines_by_name["hammer"].state.is_oopsed = False
        mconf.machines_by_name["hammer"].state.is_locked_out = False
        mconf.machines_by_name["hammer"].state.relay_desired_state = False
        mconf.machines_by_name["hammer"].state.last_checkin = time() - 60
        mconf.machines_by_name["hammer"].state.last_update = time() - 60
        mconf.machines_by_name["hammer"].state.uptime = 120
        mconf.machines_by_name["permissive-lathe"].state.is_oopsed = False
        mconf.machines_by_name["permissive-lathe"].state.is_locked_out = True
        mconf.machines_by_name["permissive-lathe"].state.relay_desired_state = False
        mconf.machines_by_name["permissive-lathe"].state.last_checkin = (
            time() - (86400 * 7) + 240
        )
        mconf.machines_by_name["permissive-lathe"].state.last_update = time() - (
            86400 * 7
        )
        mconf.machines_by_name["permissive-lathe"].state.uptime = 360
        mconf.machines_by_name["restrictive-lathe"].state.is_oopsed = False
        mconf.machines_by_name["restrictive-lathe"].state.is_locked_out = False
        mconf.machines_by_name["restrictive-lathe"].state.relay_desired_state = True
        mconf.machines_by_name["restrictive-lathe"].state.last_checkin = time() - 10
        mconf.machines_by_name["restrictive-lathe"].state.last_update = time() - 600
        mconf.machines_by_name["restrictive-lathe"].state.uptime = 3603
        msg = Message(
            text="<@U12345678> status",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Coops",
            channel_name="OopsChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        expected = (
            "esp32test: Idle \n"
            "hammer: Idle (last contact a minute ago; "
            "last update a minute ago; uptime 2 minutes)\n"
            "metal-mill: Oopsed (last contact 10 seconds ago; "
            "last update a minute ago; uptime a day)\n"
            "permissive-lathe: Locked out (last contact 6 days ago; "
            "last update 7 days ago; uptime 6 minutes)\n"
            "restrictive-lathe: In use (last contact 10 seconds ago; "
            "last update 10 minutes ago; uptime an hour)\n"
        )
        assert say.mock_calls == [call(expected)]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_help(self, tmp_path) -> None:
        """Help or unknown command."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        msg = Message(
            text="<@U12345678> help",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [call(self.cls.HELP_RESPONSE)]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_oops(self, tmp_path) -> None:
        """Oops command."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> oops metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == []
        assert self.slack_client.mock_calls == [
            call.chat_postMessage(
                channel="Cadmin",
                text="Machine metal-mill oopsed via Slack by unknown user.",
            ),
            call.chat_postMessage(
                channel="Coops", text="Machine metal-mill has been Oops'ed!"
            ),
        ]
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_oopsed is True

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_oops_already_oopsed(self, tmp_path) -> None:
        """Oops command when already oopsed."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = True
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> oops metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [call("Machine metal-mill is already oopsed.")]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_oopsed is True

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_oops_invalid_machine(self, tmp_path) -> None:
        """Oops command with invalid machine name."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> oops invalid-name",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [
            call(
                "Invalid machine name 'invalid-name'. "
                "Use status command to list all machines."
            )
        ]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_lock(self, tmp_path) -> None:
        """Lock command."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> lock metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == []
        assert self.slack_client.mock_calls == [
            call.chat_postMessage(
                channel="Cadmin", text="Machine metal-mill locked-out via Slack."
            ),
            call.chat_postMessage(
                channel="Coops",
                text="Machine metal-mill is locked-out for maintenance.",
            ),
        ]
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_locked_out is True

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_lock_already_locked(self, tmp_path) -> None:
        """Lock command when already locked."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = True
        msg = Message(
            text="<@U12345678> lock metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [call("Machine metal-mill is already locked-out.")]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_locked_out is True

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_lock_invalid_machine(self, tmp_path) -> None:
        """Lock command with invalid machine name."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> lock invalid-name",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [
            call(
                "Invalid machine name 'invalid-name'. "
                "Use status command to list all machines."
            )
        ]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_clear_when_oops(self, tmp_path) -> None:
        """Clear command when oopsed."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = True
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> clear metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == []
        assert self.slack_client.mock_calls == [
            call.chat_postMessage(
                channel="Cadmin", text="Machine metal-mill un-oopsed via Slack."
            ),
            call.chat_postMessage(
                channel="Coops", text="Machine metal-mill oops has been cleared."
            ),
        ]
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_oopsed is False
        assert mconf.machines_by_name["metal-mill"].state.is_locked_out is False

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_clear_when_locked(self, tmp_path) -> None:
        """Clear command when locked."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = True
        msg = Message(
            text="<@U12345678> clear metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == []
        assert self.slack_client.mock_calls == [
            call.chat_postMessage(
                channel="Cadmin",
                text="Machine metal-mill locked-out cleared via Slack.",
            ),
            call.chat_postMessage(
                channel="Coops",
                text="Machine metal-mill is no longer locked-out for " "maintenance.",
            ),
        ]
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_oopsed is False
        assert mconf.machines_by_name["metal-mill"].state.is_locked_out is False

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_clear_when_clear(self, tmp_path) -> None:
        """Clear command when already clear."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> clear metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [
            call("Machine metal-mill is not oopsed or locked-out.")
        ]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []
        assert mconf.machines_by_name["metal-mill"].state.is_oopsed is False
        assert mconf.machines_by_name["metal-mill"].state.is_locked_out is False

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_clear_invalid_machine(self, tmp_path) -> None:
        """Clear command with invalid machine name."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        mconf: MachinesConfig = self.quart_app.config["MACHINES"]
        mconf.machines_by_name["metal-mill"].state.is_oopsed = False
        mconf.machines_by_name["metal-mill"].state.is_locked_out = False
        msg = Message(
            text="<@U12345678> clear invalid-name",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Cadmin",
            channel_name="AdminChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == [
            call(
                "Invalid machine name 'invalid-name'. "
                "Use status command to list all machines."
            )
        ]
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []

    @freeze_time("2023-07-16 03:14:08", tz_offset=0)
    async def test_handle_command_non_admin_channel(self, tmp_path) -> None:
        """Admin-only command from a non-admin channel."""
        self.slack_app.reset_mock()
        self.slack_client.reset_mock()
        setup_machines(tmp_path, self)
        msg = Message(
            text="<@U12345678> clear metal-mill",
            user_id="U5678",
            user_name="User Name",
            user_handle="displayName",
            channel_id="Coops",
            channel_name="OopsChannel",
        )
        say = AsyncMock()
        await self.cls.handle_command(msg, say)
        assert say.mock_calls == []
        assert self.slack_client.mock_calls == []
        assert self.slack_app.mock_calls == []


def setup_machines(fixture_dir: Path, test_class: TestSlackHandler) -> None:
    fpath: str = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
    )
    with patch.dict(
        "os.environ",
        {
            "USERS_CONFIG": os.path.join(fpath, "users.json"),
            "MACHINES_CONFIG": os.path.join(fpath, "machines.json"),
            "MACHINE_STATE_DIR": str(os.path.join(fixture_dir, "machine_state")),
        },
    ):
        type(test_class.quart_app).config = {
            "MACHINES": MachinesConfig(),
            "USERS": UsersConfig(),
            "SLACK_HANDLER": test_class.cls,
        }
