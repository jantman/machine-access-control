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
from slack_bolt.context.ack.async_ack import AsyncAck
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient
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

    #: Block Kit ``callback_id`` for the ``/oops-clear`` selection modal; used
    #: both when opening the modal and when routing its submission.
    MODAL_CALLBACK_ID: str = "oops_clear_modal"
    #: ``block_id`` of the machine-selection input block in the modal.
    MODAL_BLOCK_ID: str = "machine_block"
    #: ``action_id`` of the machine-selection ``static_select`` element.
    MODAL_ACTION_ID: str = "machine_select"

    HELP_RESPONSE: str = dedent("""
    Hi, I'm the Machine Access Control slack bot.
    Mention my username followed by one of these commands:
    "status" - list all machines and their status
    "oops <machine name>" - set Oops state on this machine immediately
    "lock <machine name>" - set maintenance lockout on this machine
    "clear <machine name>" - clear oops and/or maintenance lockout on this machine

    I am Free and Open Source software:
    https://github.com/jantman/machine-access-control
    """).strip()

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
        self.app.command("/oops-clear")(self.oops_clear_command)
        self.app.view(self.MODAL_CALLBACK_ID)(self.oops_clear_modal_submit)
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

    @staticmethod
    def _invalid_machine_msg(name_or_alias: str) -> str:
        """Return the standard 'invalid machine name or alias' message."""
        return (
            f"Invalid machine name or alias '{name_or_alias}'. Use status command "
            f"to list all machines."
        )

    async def _clear_machine(self, mach: Machine) -> Optional[str]:
        """Clear oops and/or maintenance lock-out status on a machine.

        Returns ``None`` if something was cleared (the resulting Slack channel
        posts from :py:meth:`Machine.unoops` / :py:meth:`Machine.unlock` cover
        the outcome), or a human-readable message string if the machine was
        already clear (so the caller can surface it to the requester).
        """
        acted = False
        if mach.state.is_oopsed:
            await mach.unoops(slack=self)
            acted = True
        if mach.state.is_locked_out:
            await mach.unlock(slack=self)
            acted = True
        if not acted:
            return f"Machine {mach.display_name} is not oopsed or locked-out."
        return None

    async def clear(self, msg: Message, say: AsyncSay) -> None:
        """Clear oops and lock status on a machine."""
        mname: str = " ".join(msg.command[1:])
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        mach: Optional[Machine] = mconf.get_machine(mname)
        if not mach:
            await say(self._invalid_machine_msg(mname))
            return
        result: Optional[str] = await self._clear_machine(mach)
        if result:
            await say(result)

    async def oops_clear_command(
        self, ack: AsyncAck, command: Dict[str, Any], client: AsyncWebClient
    ) -> None:
        """Handle the ``/oops-clear`` slash command.

        Usable only from the control channel. With an argument
        (``/oops-clear <machine name>``) it clears that machine directly.
        With no argument it opens a Block Kit modal to pick a machine to
        clear (see Milestone 3). ``ack`` is always called promptly so Slack
        does not report the command as failed; error/edge cases respond with
        an ephemeral message, while a successful clear acks silently (the
        resulting channel posts cover the outcome).
        """
        channel_id: str = command.get("channel_id", "")
        if channel_id != self.control_channel_id:
            logger.warning(
                "Ignoring /oops-clear from non-control channel %s", channel_id
            )
            await ack(
                "The `/oops-clear` command can only be used in the control channel."
            )
            return
        text: str = command.get("text", "").strip()
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        if text:
            mach: Optional[Machine] = mconf.get_machine(text)
            if not mach:
                await ack(self._invalid_machine_msg(text))
                return
            result: Optional[str] = await self._clear_machine(mach)
            if result:
                await ack(result)
            else:
                await ack()
            return
        # No machine specified: open a modal to pick from oopsed/locked machines.
        machines: List[Machine] = sorted(
            (m for m in mconf.machines if m.state.is_oopsed or m.state.is_locked_out),
            key=lambda m: m.display_name.lower(),
        )
        if not machines:
            await ack("No machines are currently oopsed or locked out.")
            return
        await ack()
        await client.views_open(
            trigger_id=command["trigger_id"],
            view=self._build_clear_modal(machines),
        )

    def _build_clear_modal(self, machines: List[Machine]) -> Dict[str, Any]:
        """Build the ``/oops-clear`` Block Kit selection modal.

        The modal has a single required input: a ``static_select`` dropdown of
        the given machines (option text = display name, value = machine name)
        with no default selection.
        """
        options: List[Dict[str, Any]] = [
            {
                "text": {"type": "plain_text", "text": mach.display_name},
                "value": mach.name,
            }
            for mach in machines
        ]
        return {
            "type": "modal",
            "callback_id": self.MODAL_CALLBACK_ID,
            "title": {"type": "plain_text", "text": "Clear Machine"},
            "submit": {"type": "plain_text", "text": "Clear"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": self.MODAL_BLOCK_ID,
                    "label": {"type": "plain_text", "text": "Machine to clear"},
                    "element": {
                        "type": "static_select",
                        "action_id": self.MODAL_ACTION_ID,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a machine",
                        },
                        "options": options,
                    },
                }
            ],
        }

    async def oops_clear_modal_submit(
        self, ack: AsyncAck, view: Dict[str, Any]
    ) -> None:
        """Handle submission of the ``/oops-clear`` selection modal.

        Acknowledges promptly to close the modal, then clears the selected
        machine. The machine may have been cleared between opening and
        submitting the modal; that and any unexpected missing selection are
        handled gracefully (no error raised).
        """
        await ack()
        try:
            selected: str = view["state"]["values"][self.MODAL_BLOCK_ID][
                self.MODAL_ACTION_ID
            ]["selected_option"]["value"]
        except (KeyError, TypeError):
            logger.warning("/oops-clear modal submitted with no machine selected")
            return
        mconf: MachinesConfig = self.quart.config["MACHINES"]
        mach: Optional[Machine] = mconf.get_machine(selected)
        if not mach:
            logger.warning("/oops-clear modal selected unknown machine '%s'", selected)
            return
        await self._clear_machine(mach)

    @staticmethod
    def _both_relays_suffix(machine: Machine) -> str:
        """Return ' (both relays)' if machine has second_relay, else empty."""
        return " (both relays)" if machine.second_relay is not None else ""

    async def log_unoops(self, machine: Machine, source: str) -> None:
        """
        Log when a machine is un-oopsed.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        Otherwise, updates to the relay/LCD/LED would be delayed by at least the
        timeout trying to post to Slack.
        """
        suffix = self._both_relays_suffix(machine)
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=f"Machine {machine.display_name} un-oopsed via {source}{suffix}.",
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
        suffix = self._both_relays_suffix(machine)
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=(
                    f"Machine {machine.display_name} oopsed via {source} by "
                    f"{user_name}{suffix}."
                ),
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
        suffix = self._both_relays_suffix(machine)
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=(
                    f"Machine {machine.display_name} locked-out cleared via "
                    f"{source}{suffix}."
                ),
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
        suffix = self._both_relays_suffix(machine)
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=(
                    f"Machine {machine.display_name} locked-out via "
                    f"{source}{suffix}."
                ),
            )
        )
        create_task(
            self.app.client.chat_postMessage(
                channel=self.oops_channel_id,
                text=f"Machine {machine.display_name} is locked-out for maintenance.",
            )
        )

    async def log_override_login(self, machine: "Machine", user_name: str) -> None:
        """
        Log an override login to the admin channel only.

        This uses :py:meth:`asyncio.create_task` to fire-and-forget the Slack
        postMessage call, so that we don't block on communication with Slack.
        """
        create_task(
            self.app.client.chat_postMessage(
                channel=self.control_channel_id,
                text=f"Override login on {machine.display_name} by {user_name}.",
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
