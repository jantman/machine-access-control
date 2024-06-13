"""Decatur Makers Machine Access Control."""

from flask import Flask


def create_app() -> Flask:
    """Factory to create the app."""
    app: Flask = Flask("dm_mac")

    from dm_mac.views.api import api

    app.register_blueprint(api)

    return app
