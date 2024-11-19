"""Slack app."""

import os
from slack_bolt import App
from slack_bolt.adapter.quart import AsyncQuartReceiver
from quart import Quart
import logging

logger: logging.Logger = logging.getLogger(__name__)


class SlackApp:
    """MAC Slack App."""

    def __init__(self, app: Quart) -> None:
        receiver: AsyncQuartReceiver = AsyncQuartReceiver(app)
        self.app: App = App(
            token=os.environ("SLACK_APP_TOKEN"),
            signing_secret=os.environ("SLACK_SIGNING_SECRET"),
            receiver=receiver
        )

    @self.app.event("app_mention")
    async def handle_app_mention(self, event, say):
        logging.info("app mention event=%s say=%s", event, say)
