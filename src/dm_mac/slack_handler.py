import logging
import os
import time
from asyncio import create_task
from textwrap import dedent
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from humanize import naturaldelta
from quart import Quart
from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_slack_response import AsyncSlackResponse

from dm_mac.models.machine import Machine
from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig


logger: logging.Logger = logging.getLogger(__name__)


class Message:
    """Represent an incoming message."""

    def __init__(
        self,
        text: str,
        user_id: str,
        user_name: str,
        user_handle: str,
        channel_id: str,
        channel_name: str,
    ):
        self._raw_text: str = text
        self.command: List[str] = text.split(" ")[1:]
        self.user_id: str = user_id
        self.user_name: str = user_name
        self.user_handle: str = user_handle
        self.channel_id: str = channel_id
        self.channel_name: str = channel_name

    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self._raw_text,
            "command": self.command,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_handle": self.user_handle,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
        }

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.as_dict == other.as_dict


class SlackHandler:
    """Handle Slack integration."""

    HELP_RESPONSE: str = dedent(
        """
    Hi, I'm the Machine Access Control slack bot.
    Mention my username followed by one of these commands:
    "status" - list all machines and their status
    "oops <machine name>" - set Oops state on this machine immediately
    "lock <machine name>" - set maintenance lockout on this machine
    "clear <machine name>" - clear oops and/or maintenance lockout on this machine

    I am Free and Open Source software:
    https://github.com/jantman/machine-access-control
    """
    ).strip()

    def __init__(self, quart_app: Quart):
        logger.info("Initializing SlackHandler.")
        self.control_channel_id = os.environ["SLACK_CONTROL_CHANNEL_ID"]
        self.oops_channel_id = os.environ["SLACK_OOPS_CHANNEL_ID"]
        self.quart: Quart = quart_app
        self.app: AsyncApp = AsyncApp(
            token=os.environ["SLACK_BOT_TOKEN"],
            signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        )
        self.app.event("app_mention")(self.app_mention)
        logger.debug("SlackHandler initialized.")

    async def app_mention(self, body: Dict[str, Any], say: AsyncSay) -> None:
        """
        Handle an at-mention of our app in Slack.

        Body is a dict with string keys, which is documented at
        <https://api.slack.com/events/app_mention>. The important bits are
        in the ``event`` nested dict.

        The parts of the ``event`` dict within ``body`` that are of interest to
        us are:

        * ``user`` - the user ID (string beginning with "U") of the person who
          mentioned us.
        * ``text`` - the string text of the message that mentioned us.
        * ``channel`` - the channel ID (string beginning with "C") of the
          channel that the message was in.
        """
        message_text: str = body["event"]["text"].strip()
        my_id: str = body["authorizations"][0]["user_id"]
        if not message_text.startswith(f"<@{my_id}> "):
            logger.warning(
                "Ignoring Slack mention with improper format: %s", message_text
            )
            return None
        user: AsyncSlackResponse = await self.app.client.users_info(
            user=body["event"]["user"]
        )
        assert user.data["ok"] is True
        user_name: str = user.data["user"]["profile"]["real_name_normalized"]
        user_handle: str = user.data["user"]["profile"]["display_name_normalized"]
        user_is_bot: bool = (
            user.data["user"]["is_bot"] or user.data["user"]["is_app_user"]
        )
        channel: AsyncSlackResponse = await self.app.client.conversations_info(
            channel=body["event"]["channel"]
        )
        assert channel.data["ok"] is True
        channel_name: str = channel.data["channel"]["name"]
        logger.info(
            "Slack mention in #%s (%s) by %s (@%s; %s): %s",
            channel_name,
            body["event"]["channel"],
            user_name,
            user_handle,
            body["event"]["user"],
            message_text,
        )
        if user_is_bot:
            logger.warning("Ignoring mention by bot/app user %s", user_name)
            return None
        msg: Message = Message(
            text=message_text,
            user_id=body["event"]["user"],
            user_name=user_name,
            user_handle=user_handle,
            channel_id=body["event"]["channel"],
            channel_name=channel_name,
        )
        await self.handle_command(msg, say)

    async def handle_command(self, msg: Message, say: AsyncSay) -> None:
        """Handle a command sent to the bot."""
        if msg.command[0] in ["list", "status"]:
            await self.machine_status(say)
            return None
        if msg.channel_id != self.control_channel_id:
            logger.warning(
                "Ignoring non-status mention in #%s (%s) - not control channel",
                msg.channel_name,
                msg.channel_id,
            )
            return None
        if msg.command[0] == "oops" and len(msg.command) >= 2:
            return await self.oops(msg, say)
        elif msg.command[0] == "lock" and len(msg.command) >= 2:
            return await self.lock(msg, say)
        elif msg.command[0] == "clear" and len(msg.command) >= 2:
            return await self.clear(msg, say)
        await say(self.HELP_RESPONSE)

    async def machine_status(self, say: AsyncSay) -> None:
        """Respond with machine status."""
        server_uptime: str = naturaldelta(time.time() - self.quart.config["START_TIME"])
        uconf: UsersConfig = self.quart.config["USERS"]
        users_config_age: str = naturaldelta(time.time() - uconf.file_mtime)
        num_users: int = len(uconf.users)
        num_fobs: int = len(uconf.users_by_fob)
        resp: str = (
            f"Server uptime: {server_uptime}\n"
            f"Users config: {users_config_age} old, {num_users} users, {num_fobs} fobs\n\n"
        )
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        mname: str
        mach: Machine
        for mname, mach in sorted(mconf.machines_by_name.items()):
            resp += mach.display_name + ": "
            if mach.state.is_oopsed or mach.state.is_locked_out:
                if mach.state.is_oopsed:
                    resp += "Oopsed "
                if mach.state.is_locked_out:
                    resp += "Locked out "
            elif mach.state.relay_desired_state:
                resp += "In use "
            else:
                resp += "Idle "
            try:
                ci: str = naturaldelta(time.time() - mach.state.last_checkin)
                ud: str = naturaldelta(time.time() - mach.state.last_update)
                ut: str = naturaldelta(mach.state.uptime)
                resp += (
                    f"(last contact {ci} ago; last update {ud} ago; " f"uptime {ut})\n"
                )
            except TypeError:
                # machine has not checked in ever
                resp += "\n"
        await say(resp)

    async def oops(self, msg: Message, say: AsyncSay) -> None:
        """Set oops status on a machine."""
        mname: str = " ".join(msg.command[1:])
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        mach: Optional[Machine] = mconf.get_machine(mname)
        if not mach:
            await say(
                f"Invalid machine name or alias '{mname}'. Use status command to "
                f"list all machines."
            )
            return
        if mach.state.is_oopsed:
            await say(f"Machine {mach.display_name} is already oopsed.")
            return
        await mach.oops(slack=self)

    async def lock(self, msg: Message, say: AsyncSay) -> None:
        """Set lock status on a machine."""
        mname: str = " ".join(msg.command[1:])
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        mach: Optional[Machine] = mconf.get_machine(mname)
        if not mach:
            await say(
                f"Invalid machine name or alias '{mname}'. Use status command to "
                f"list all machines."
            )
            return
        if mach.state.is_locked_out:
            await say(f"Machine {mach.display_name} is already locked-out.")
            return
        await mach.lockout(slack=self)

    async def clear(self, msg: Message, say: AsyncSay) -> None:
        """Clear oops and lock status on a machine."""
        mname: str = " ".join(msg.command[1:])
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        mach: Optional[Machine] = mconf.get_machine(mname)
        if not mach:
            await say(
                f"Invalid machine name or alias '{mname}'. Use status command to "
                f"list all machines."
            )
            return
        acted = False
        if mach.state.is_oopsed:
            await mach.unoops(slack=self)
            acted = True
        if mach.state.is_locked_out:
            await mach.unlock(slack=self)
            acted = True
        if not acted:
            await say(f"Machine {mach.display_name} is not oopsed or locked-out.")

    async def log_unoops(self, machine: Machine, source: str) -> None:
        """
        Log when a machine is un-oopsed.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        Otherwise, updates to the relay/LCD/LED would be delayed by at least the
        timeout trying to post to Slack.
        """
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=f"Machine {machine.display_name} un-oopsed via {source}.",
            )
        )
        create_task(
            self.app.client.chat_postMessage(
                channel=self.oops_channel_id,
                text=f"Machine {machine.display_name} oops has been cleared.",
            )
        )

    async def log_oops(
        self, machine: Machine, source: str, user_name: Optional[str] = "unknown user"
    ) -> None:
        """
        Log when a machine is oopsed.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        Otherwise, updates to the relay/LCD/LED would be delayed by at least the
        timeout trying to post to Slack.
        """
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=f"Machine {machine.display_name} oopsed via {source} by {user_name}.",
            )
        )
        create_task(
            self.app.client.chat_postMessage(
                channel=self.oops_channel_id,
                text=f"Machine {machine.display_name} has been Oops'ed!",
            )
        )

    async def log_unlock(self, machine: Machine, source: str) -> None:
        """
        Log when a machine is un-locked.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        Otherwise, updates to the relay/LCD/LED would be delayed by at least the
        timeout trying to post to Slack.
        """
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=f"Machine {machine.display_name} locked-out cleared via {source}.",
            )
        )
        create_task(
            self.app.client.chat_postMessage(
                channel=self.oops_channel_id,
                text=f"Machine {machine.display_name} is no longer locked-out for "
                f"maintenance.",
            )
        )

    async def log_lock(self, machine: Machine, source: str) -> None:
        """
        Log when a machine is locked.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        Otherwise, updates to the relay/LCD/LED would be delayed by at least the
        timeout trying to post to Slack.
        """
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=f"Machine {machine.display_name} locked-out via {source}.",
            )
        )
        create_task(
            self.app.client.chat_postMessage(
                channel=self.oops_channel_id,
                text=f"Machine {machine.display_name} is locked-out for maintenance.",
            )
        )

    async def admin_log(self, message: str) -> None:
        """
        Log a string to the admin channel only.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        Otherwise, updates to the relay/LCD/LED would be delayed by at least the
        timeout trying to post to Slack.
        """
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id, text=message
            )
        )
