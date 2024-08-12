"""Decatur Makers Machine Access Control."""

from flask import Flask

from dm_mac.views.api import api
from dm_mac.views.machine import machineapi


# see: https://github.com/pallets/flask/issues/4786#issuecomment-1416354177
api.register_blueprint(machineapi)


def create_app() -> Flask:
    """Factory to create the app."""
    app: Flask = Flask("dm_mac")
    app.register_blueprint(api)
    return app
