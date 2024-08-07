"""Utility functions for this package."""

import json
import os
from typing import Any


def load_json_config(env_var: str, default_path: str) -> Any:
    """Try to load a JSON config file."""
    path = os.environ.get(env_var, default_path)
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
    return config
