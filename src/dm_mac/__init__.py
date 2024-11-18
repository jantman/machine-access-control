"""Decatur Makers Machine Access Control."""

import argparse
import asyncio
import logging
import sys
from time import time

from quart import Quart
from quart import has_request_context
from quart import request
from quart.logging import default_handler

from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig
from dm_mac.views.api import api
from dm_mac.views.machine import machineapi
from dm_mac.views.prometheus import prometheus_route


logger: logging.Logger = logging.getLogger(__name__)

# BEGIN adding request information to logs


class RequestFormatter(logging.Formatter):
    """Custom log formatter to add request information."""

    def format(self, record: logging.LogRecord) -> str:
        """Custom log formatter to add request information."""
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


formatter = RequestFormatter(
    "%(asctime)s %(levelname)s:[%(remote_addr)s]:%(name)s:%(message)s"
)
default_handler.setFormatter(formatter)

# END adding request information to logs

# enable logging from libraries (i.e. everything but the views)
logging.getLogger().addHandler(default_handler)

logging.getLogger("AUTH").setLevel(logging.INFO)
logging.getLogger().setLevel(logging.INFO)

# see: https://github.com/pallets/flask/issues/4786#issuecomment-1416354177
api.register_blueprint(machineapi)


def create_app() -> Quart:
    """Factory to create the app."""
    app: Quart = Quart("dm_mac")
    app.config.update({"MACHINES": MachinesConfig()})
    app.config.update({"USERS": UsersConfig()})
    app.config.update({"START_TIME": time()})
    app.register_blueprint(api)
    app.add_url_rule("/metrics", view_func=prometheus_route)
    return app


def main() -> None:
    p = argparse.ArgumentParser(description="Run Machine Access Control (MAC) server")
    p.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Debug mode",
    )
    args = p.parse_args(sys.argv[1:])
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    app: Quart = create_app()
    app.run(loop=loop, debug=args.debug, host="0.0.0.0")


if __name__ == "__main__":
    main()
