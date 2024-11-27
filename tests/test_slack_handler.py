"""Tests for SlackHandler class."""

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

from dm_mac.slack_handler import SlackHandler


pbm = "dm_mac.slack_handler"


class TestInit:
    """Test SlackHandler.__init__()."""

    @patch.dict(
        "os.environ",
        {
            "SLACK_BOT_TOKEN": "btkn",
            "SLACK_SIGNING_SECRET": "secret",
        },
    )
    def test_init(self) -> None:
        quart_app: MagicMock = MagicMock(name="quart_app")
        with patch(f"{pbm}.AsyncApp", new_callable=MagicMock) as aapp:
            cls = SlackHandler(quart_app)
        assert quart_app.mock_calls == []
        assert aapp.mock_calls == [
            call(token="btkn", signing_secret="secret"),
            call().event("app_mention"),
            call().event("app_mention")(cls.app_mention),
        ]
        assert cls.quart == quart_app
        assert cls.app == aapp.return_value
