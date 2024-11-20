import logging
import os

from quart import Quart
from slack_bolt.async_app import AsyncApp


logger: logging.Logger = logging.getLogger(__name__)


class SlackHandler:
    """Handle Slack integration."""

    def __init__(self, quart_app: Quart):
        logger.info("Initializing SlackHandler.")
        self.quart: Quart = quart_app
        self.app: AsyncApp = AsyncApp(
            token=os.environ["SLACK_BOT_TOKEN"],
            signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        )
        self.app.event("app_mention")(self.event_test)
        self.app.command("/hello-bolt-python")(self.command)
        logger.debug("SlackHandler initialized.")

    async def UNUSEDcheck_auth(self):
        authtest = await self.app.client.auth_test()
        logger.info(
            "Created Slack AsyncApp; name=%s; authtest=%s", self.app.name, authtest
        )

    async def event_test(self, body, say):
        logger.info(body)
        await say("What's up?")

    # or app.command(re.compile(r"/hello-.+"))(test_command)
    async def command(self, ack, body):
        user_id = body["user_id"]
        await ack(f"Hi <@{user_id}>!")
