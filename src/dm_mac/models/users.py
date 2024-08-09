"""Models for users and tools for loading users config."""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import cast

from jsonschema import validate

from dm_mac.utils import load_json_config


logging.basicConfig(
    level=logging.WARNING, format="[%(asctime)s %(levelname)s] %(message)s"
)
logger: logging.Logger = logging.getLogger()


CONFIG_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {"/": {}},
    "patternProperties": {
        "^([0-9]+)$": {
            "type": "object",
            "properties": {
                "fob_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "List of fob codes for user.",
                },
                "account_id": {
                    "type": "string",
                    "description": "Unique Account ID for user.",
                },
                "name": {"type": "string", "description": "Name of user."},
                "email": {"type": "string", "description": "User email address."},
                "expiration_ymd": {
                    "type": "string",
                    "description": "User membership expiration in YYYY-MM-DD format.",
                },
                "authorizations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of authorized field names for user.",
                },
            },
            "required": [
                "fob_codes",
                "account_id",
                "name",
                "email",
                "expiration_ymd",
                "authorizations",
            ],
            "additionalProperties": False,
        }
    },
    "additionalProperties": False,
}


class UsersConfig:
    """Class representing users configuration file."""

    def __init__(self) -> None:
        """Initialize UsersConfig."""
        self._config: Dict[str, Union[str, List[str]]] = (
            self._load_and_validate_config()
        )

    def _load_and_validate_config(self) -> Dict[str, Union[str, List[str]]]:
        """Load and validate the config file."""
        config: Dict[str, Union[str, List[str]]] = cast(
            Dict[str, Union[str, List[str]]],
            load_json_config("USERS_CONFIG", "users.config.json"),
        )
        UsersConfig.validate_config(config)
        return config

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """Validate configuration via jsonschema."""
        logger.debug("Validating Users config")
        validate(config, CONFIG_SCHEMA)
        logger.debug("Users is valid")
