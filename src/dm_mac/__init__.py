"""Decatur Makers Machine Access Control."""

import logging

from flask import Flask
from flask import has_request_context
from flask import request
from flask.logging import default_handler

from dm_mac.models.machine import MachinesConfig
from dm_mac.models.users import UsersConfig
from dm_mac.views.api import api
from dm_mac.views.machine import machineapi


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

# see: https://github.com/pallets/flask/issues/4786#issuecomment-1416354177
api.register_blueprint(machineapi)


def create_app() -> Flask:
    """Factory to create the app."""
    app: Flask = Flask("dm_mac")
    app.config.update({"MACHINES": MachinesConfig()})
    app.config.update({"USERS": UsersConfig()})
    app.register_blueprint(api)
    return app
