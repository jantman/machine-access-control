"""Utility functions for this package."""

import json
import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


def load_json_config(env_var: str, default_path: str) -> Any:
    """Try to load a JSON config file."""
    path: str
    if env_var in os.environ:
        path = os.environ[env_var]
        logger.debug("Loading config file from %s; path from env var %s", path, env_var)
    else:
        path = default_path
        logger.debug(
            "Env var %s not set; loading config from default path %s", env_var, path
        )
    if not os.path.exists(path):
        raise RuntimeError(
            f"ERROR: Config file does not exist at {path}; please either "
            f"save your config file at ./{default_path} or set the "
            f"{env_var} environment variable to the full path to "
            "your config file."
        )
    config: Any
    with open(path) as fh:
        config = json.load(fh)
    logger.debug(
        "Loaded config of type %s with length %d", type(config).__name__, len(config)
    )
    return config
