"""Tests for dm_mac.cli_utils module."""

import logging
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest

from dm_mac.cli_utils import env_var_or_die
from dm_mac.cli_utils import set_log_debug
from dm_mac.cli_utils import set_log_info
from dm_mac.cli_utils import set_log_level_format


pbm: str = "dm_mac.cli_utils"


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


class TestLogFunctions:
    """Test the log level setting functions."""

    def test_set_log_info(self) -> None:
        """Test set_log_info()."""
        mock_log = Mock(spec_set=logging.Logger)
        with patch("%s.set_log_level_format" % pbm, autospec=True) as mock_set:
            set_log_info(mock_log)
        assert mock_set.mock_calls == [
            call(
                mock_log, logging.INFO, "%(asctime)s %(levelname)s:%(name)s:%(message)s"
            )
        ]

    def test_set_log_debug(self) -> None:
        """Test set_log_debug()."""
        mock_log = Mock(spec_set=logging.Logger)
        with patch("%s.set_log_level_format" % pbm, autospec=True) as mock_set:
            set_log_debug(mock_log)
        assert mock_set.mock_calls == [
            call(
                mock_log,
                logging.DEBUG,
                "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
                "%(name)s.%(funcName)s() ] %(message)s",
            )
        ]

    def test_set_log_level_format(self) -> None:
        """Test set_log_level_format()."""
        mock_log = Mock(spec_set=logging.Logger)
        mock_handler = Mock(spec_set=logging.Handler)
        type(mock_log).handlers = [mock_handler]
        with patch("%s.logging.Formatter" % pbm, autospec=True) as mock_formatter:
            set_log_level_format(mock_log, 5, "foo")
        assert mock_formatter.mock_calls == [call(fmt="foo")]
        assert mock_handler.mock_calls == [
            call.setFormatter(mock_formatter.return_value)
        ]
        assert mock_log.mock_calls == [call.setLevel(5)]
