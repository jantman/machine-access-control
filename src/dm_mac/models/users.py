"""Models for users and tools for loading users config."""

import logging
import os
from time import time
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
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
            "full_name": {"type": "string", "description": "Full name of user."},
            "first_name": {"type": "string", "description": "First name of user."},
            "last_name": {"type": "string", "description": "Last name of user."},
            "preferred_name": {
                "type": "string",
                "description": "Preferred name of user.",
            },
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
            "full_name",
            "first_name",
            "last_name",
            "preferred_name",
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
        full_name: str,
        first_name: str,
        last_name: str,
        preferred_name: str,
        email: str,
        expiration_ymd: str,
        authorizations: List[str],
    ):
        """Initialize one user."""
        self.fob_codes: List[str] = fob_codes
        self.account_id: str = account_id
        self.full_name: str = full_name
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.preferred_name: str = preferred_name
        self.email: str = email
        self.expiration_ymd: str = expiration_ymd
        self.authorizations: List[str] = authorizations

    def __eq__(self, other: Any) -> bool:
        """Check equality between Users."""
        if not isinstance(other, User):
            return NotImplemented
        return self.account_id == other.account_id

    def __repr__(self) -> str:
        """Return a string representation of the user."""
        return f"User(account_id={self.account_id}, full_name={self.full_name})"

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Return a dict representation of this user."""
        return {
            "account_id": self.account_id,
            "authorizations": self.authorizations,
            "email": self.email,
            "expiration_ymd": self.expiration_ymd,
            "fob_codes": self.fob_codes,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "preferred_name": self.preferred_name,
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
        self.load_time: float = time()
        self.file_mtime: float = os.path.getmtime(self._get_config_path())

    def _get_config_path(self) -> str:
        """Get the path to the users config file."""
        if "USERS_CONFIG" in os.environ:
            return os.environ["USERS_CONFIG"]
        return "users.json"

    def _load_and_validate_config(self) -> List[Dict[str, Any]]:
        """Load and validate the config file."""
        config: List[Dict[str, Any]] = cast(
            List[Dict[str, Any]],
            # if changing, be sure to also update _get_config_path()
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

    def reload(self) -> Tuple[int, int, int]:
        """Reload configuration from config file on disk.

        Returns a 3-tuple of counts of users removed, updated, and added.
        """
        logger.info("Reloading users config.")
        try:
            nconf: UsersConfig = UsersConfig()
        except Exception as ex:
            logger.error("Error reloading users config: %s", ex, exc_info=True)
            raise
        added: int = 0
        updated: int = 0
        removed: int = 0
        nusers: Dict[str, User] = {x.account_id: x for x in nconf.users}
        users: Dict[str, User] = {x.account_id: x for x in self.users}
        user: User
        nuser: User
        for acctid, user in users.items():
            if acctid not in nusers:
                logger.warning("Removing user: %s", user)
                for fc in user.fob_codes:
                    self.users_by_fob.pop(fc)
                self.users.remove(user)
                removed += 1
                continue
            nuser = nusers[acctid]
            if user.as_dict != nuser.as_dict:
                updated += 1
                for k in [
                    "full_name",
                    "first_name",
                    "last_name",
                    "preferred_name",
                    "email",
                    "expiration_ymd",
                    "authorizations",
                ]:
                    if getattr(user, k) != getattr(nuser, k):
                        logger.warning(
                            "Updating user: %s %s from %s to %s",
                            user,
                            k,
                            getattr(user, k),
                            getattr(nuser, k),
                        )
                        setattr(user, k, getattr(nuser, k))
                if user.fob_codes != nuser.fob_codes:
                    logger.warning(
                        "Updating user: %s fob codes from %s to %s",
                        user,
                        getattr(user, k),
                        getattr(nuser, k),
                    )
                    for fc in user.fob_codes:
                        self.users_by_fob.pop(fc)
                    user.fob_codes = nuser.fob_codes
                    for fob in nuser.fob_codes:
                        self.users_by_fob[fob] = nuser
        for acctid, nuser in nusers.items():
            if acctid not in users:
                logger.warning("Adding new user: %s", nuser)
                self.users.append(nuser)
                for fob in nuser.fob_codes:
                    self.users_by_fob[fob] = nuser
                added += 1
        logger.info("Done reloading users config.")
        self.load_time = time()
        self.file_mtime = os.path.getmtime(self._get_config_path())
        return removed, updated, added
