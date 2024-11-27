from typing import List
from unittest.mock import DEFAULT
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

from dm_mac import main


class TestMain:

    @patch("sys.argv", ["mac-server"])
    @patch.dict("os.environ", {"SLACK_APP_TOKEN": "app-token"})
    def test_with_slack(self):
        mocks: List[MagicMock]
        with patch.multiple(
            "dm_mac",
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            get_event_loop=DEFAULT,
            SlackHandler=DEFAULT,
            AsyncSocketModeHandler=DEFAULT,
            logger=DEFAULT,
            create_app=DEFAULT,
            new_callable=MagicMock,
        ) as mocks:
            slack_app = MagicMock()
            type(mocks["SlackHandler"].return_value).app = slack_app
            loop = MagicMock()
            app = MagicMock()
            handler = MagicMock()
            mocks["get_event_loop"].return_value = loop
            mocks["create_app"].return_value = app
            mocks["AsyncSocketModeHandler"].return_value = handler
            main()
        assert mocks["set_log_debug"].mock_calls == []
        assert mocks["set_log_info"].mock_calls == [call(mocks["logger"])]
        assert mocks["create_app"].mock_calls == [
            call(),
            call().config.update({"SLACK_HANDLER": mocks["SlackHandler"].return_value}),
            call().run(loop=loop, debug=False, host="0.0.0.0"),
        ]
        assert app.mock_calls == [
            call.config.update({"SLACK_HANDLER": mocks["SlackHandler"].return_value}),
            call.run(loop=loop, debug=False, host="0.0.0.0"),
        ]
        assert mocks["SlackHandler"].mock_calls == [call(app)]
        assert mocks["AsyncSocketModeHandler"].mock_calls == [
            call(slack_app, "app-token", loop=loop),
            call().start_async(),
        ]
        assert loop.mock_calls == [call.create_task(handler.start_async())]
        assert app.mock_calls == [
            call.config.update({"SLACK_HANDLER": mocks["SlackHandler"].return_value}),
            call.run(loop=loop, debug=False, host="0.0.0.0"),
        ]

    @patch("sys.argv", ["mac-server", "-v"])
    @patch.dict("os.environ", {"SLACK_APP_TOKEN": ""})
    def test_without_slack(self):
        mocks: List[MagicMock]
        with patch.multiple(
            "dm_mac",
            set_log_debug=DEFAULT,
            set_log_info=DEFAULT,
            get_event_loop=DEFAULT,
            SlackHandler=DEFAULT,
            AsyncSocketModeHandler=DEFAULT,
            logger=DEFAULT,
            create_app=DEFAULT,
            new_callable=MagicMock,
        ) as mocks:
            slack_app = MagicMock()
            type(mocks["SlackHandler"].return_value).app = slack_app
            loop = MagicMock()
            app = MagicMock()
            handler = MagicMock()
            mocks["get_event_loop"].return_value = loop
            mocks["create_app"].return_value = app
            mocks["AsyncSocketModeHandler"].return_value = handler
            main()
        assert mocks["set_log_debug"].mock_calls == [call(mocks["logger"])]
        assert mocks["set_log_info"].mock_calls == []
        assert mocks["create_app"].mock_calls == [
            call(),
            call().run(loop=loop, debug=False, host="0.0.0.0"),
        ]
        assert app.mock_calls == [call.run(loop=loop, debug=False, host="0.0.0.0")]
        assert mocks["SlackHandler"].mock_calls == []
        assert mocks["AsyncSocketModeHandler"].mock_calls == []
        assert loop.mock_calls == []
        assert app.mock_calls == [call.run(loop=loop, debug=False, host="0.0.0.0")]
