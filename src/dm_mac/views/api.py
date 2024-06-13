"""API Views."""

from flask import Blueprint


api: Blueprint = Blueprint("api", __name__, url_prefix="/api")


@api.route("/")
def index():
    """Main API index route - placeholder."""
    return "Hello, World!"
