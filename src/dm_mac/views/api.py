"""API Views."""

from flask import Blueprint


api: Blueprint = Blueprint("api", __name__, url_prefix="/api")


@api.route("/")
def index() -> str:
    """Main API index route - placeholder."""
    return "Nothing to see here..."
