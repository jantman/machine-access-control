"""Helpers for testing the Flask app."""

import os
from pathlib import Path
from typing import Tuple
from unittest.mock import patch

from flask import Flask
from flask.testing import FlaskClient

from dm_mac import create_app


def app_and_client(
    tmp_path: Path, user_conf: str = "users.json", machine_conf: str = "machines.json"
) -> Tuple[Flask, FlaskClient]:
    """Test App - app instance configured for testing.

    Doing this as a pytest fixture is a complete pain in the ass because I want
    keyword arguments with defaults, and fixtures don't do that. We also don't
    need any cleanup code.
    """
    testdir: str = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")
    )
    with patch.dict(
        "os.environ",
        {
            "USERS_CONFIG": os.path.join(testdir, user_conf),
            "MACHINES_CONFIG": os.path.join(testdir, machine_conf),
            "MACHINE_STATE_DIR": str(os.path.join(tmp_path, "machine_state")),
        },
    ):
        app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )
    return app, app.test_client()
