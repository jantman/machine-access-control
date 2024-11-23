from dm_mac import main


class TestMain:

    def test_happy_path_no_slack(self):
        # patch sys.argv
        # patch set_log_debug and _info
        # patch asyncio.get_event_loop
        # patch create_app()
        # patch ... all the slack stuff
        pass
