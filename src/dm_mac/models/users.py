"""Models for users and tools for loading users config."""

import logging
from typing import Any
from typing import Dict
from typing import List
from typing import cast

from jsonschema import validate

from dm_mac.utils import load_json_config


logger: logging.Logger = logging.getLogger(__name__)


CONFIG_SCHEMA: Dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "fob_codes": {
                "type": "array",
                "items": {"type": "string"},
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
    },
}


class User:
    """Class representing one user."""

    def __init__(
        self,
        fob_codes: List[str],
        account_id: str,
        name: str,
        email: str,
        expiration_ymd: str,
        authorizations: List[str],
    ):
        """Initialize one user."""
        self.fob_codes: List[str] = fob_codes
        self.account_id: str = account_id
        self.name: str = name
        self.email: str = email
        self.expiration_ymd: str = expiration_ymd
        self.authorizations: List[str] = authorizations

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Return a dict representation of this user."""
        return {
            "account_id": self.account_id,
            "authorizations": self.authorizations,
            "email": self.email,
            "expiration_ymd": self.expiration_ymd,
            "fob_codes": self.fob_codes,
            "name": self.name,
        }


class UsersConfig:
    """Class representing users configuration file."""

    def __init__(self) -> None:
        """Initialize UsersConfig."""
        logger.debug("Initializing UsersConfig")
        self.users_by_fob: Dict[str, User] = {}
        self.users: List[User] = []
        udict: Dict[str, Any]
        fob: str
        for udict in self._load_and_validate_config():
            user: User = User(**udict)
            self.users.append(user)
            for fob in user.fob_codes:
                self.users_by_fob[fob] = user

    def _load_and_validate_config(self) -> List[Dict[str, Any]]:
        """Load and validate the config file."""
        config: List[Dict[str, Any]] = cast(
            List[Dict[str, Any]],
            load_json_config("USERS_CONFIG", "users.json"),
        )
        UsersConfig.validate_config(config)
        return config

    @staticmethod
    def validate_config(config: List[Dict[str, Any]]) -> None:
        """Validate configuration via jsonschema."""
        logger.debug("Validating Users config")
        validate(config, CONFIG_SCHEMA)
        logger.debug("Users is valid")
