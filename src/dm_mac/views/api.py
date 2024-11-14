"""API Views."""

from logging import Logger
from logging import getLogger
from typing import Tuple

from quart import Blueprint
from quart import Response
from quart import current_app
from quart import jsonify

from dm_mac.models.users import UsersConfig


logger: Logger = getLogger(__name__)

api: Blueprint = Blueprint("api", __name__, url_prefix="/api")


@api.route("/")
async def index() -> str:
    """Main API index route - placeholder."""
    return "Nothing to see here..."


@api.route("/reload-users", methods=["POST"])
async def reload_users() -> Tuple[Response, int]:
    """Reload users config."""
    added: int
    updated: int
    removed: int
    try:
        users: UsersConfig = current_app.config["USERS"]  # noqa
        removed, updated, added = users.reload()
        return jsonify({"removed": removed, "updated": updated, "added": added}), 200
    except Exception as ex:
        logger.error("Error reloading users config: %s", ex, exc_info=True)
        return jsonify({"error": str(ex)}), 500
