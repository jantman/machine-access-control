"""Tests for dm_mac.cli_utils module."""

from unittest.mock import patch

import pytest

from dm_mac.cli_utils import env_var_or_die


class TestEnvVarOrDie:
    """Tests for env_var_or_die() function."""

    @patch.dict("os.environ", {"VNAME": "vval"})
    def test_success(self) -> None:
        """Test success condition."""
        assert env_var_or_die("VNAME", "foo") == "vval"

    @patch.dict("os.environ", {})
    def test_failure(self) -> None:
        """Test failure condition."""
        with pytest.raises(RuntimeError) as exc:
            env_var_or_die("VNAME", "foo")
        assert exc.value.args[0] == (
            "ERROR: Please set the VNAME environment " "variable to foo."
        )
