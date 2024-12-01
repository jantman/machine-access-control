"""Tests for dm_mac.utils module."""

import logging
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from dm_mac.utils import load_json_config
from dm_mac.utils import set_log_debug
from dm_mac.utils import set_log_info
from dm_mac.utils import set_log_level_format


pbm = "dm_mac.utils"


class TestLoadJsonConfig:
    """Tests for load_json_config() function."""

    @patch.dict("os.environ", {})
    def test_success_default(self) -> None:
        """Test success condition."""
        data = '{"foo": "bar"}'
        with patch(f"{pbm}.os.path.exists") as m_ope:
            with patch(f"{pbm}.open", mock_open(read_data=data)) as m_open:
                m_ope.return_value = True
                res = load_json_config("VNAME", "default.json")
        assert res == {"foo": "bar"}
        assert m_ope.mock_calls == [call("default.json")]
        assert m_open.mock_calls == [
            call("default.json"),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
        ]

    @patch.dict("os.environ", {"VNAME": "fname.json"})
    def test_success_env_var(self) -> None:
        """Test success condition."""
        data = '{"foo": "bar"}'
        with patch(f"{pbm}.os.path.exists") as m_ope:
            with patch(f"{pbm}.open", mock_open(read_data=data)) as m_open:
                m_ope.return_value = True
                res = load_json_config("VNAME", "default.json")
        assert res == {"foo": "bar"}
        assert m_ope.mock_calls == [call("fname.json")]
        assert m_open.mock_calls == [
            call("fname.json"),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
        ]

    @patch.dict("os.environ", {})
    def test_does_not_exist(self) -> None:
        """Test success condition."""
        data = '{"foo": "bar"}'
        with patch(f"{pbm}.os.path.exists") as m_ope:
            with patch(f"{pbm}.open", mock_open(read_data=data)) as m_open:
                m_ope.return_value = False
                with pytest.raises(RuntimeError) as exc:
                    load_json_config("VNAME", "default.json")
        assert m_ope.mock_calls == [call("default.json")]
        assert m_open.mock_calls == []
        expected: str = (
            "ERROR: Config file does not exist at default.json; "
            "please either save your config file at ./default.json"
            " or set the VNAME environment variable to the full "
            "path to your config file."
        )
        assert exc.value.args[0] == expected


class TestLogHelpers:

    def test_set_log_info(self) -> None:
        mock_log = Mock(spec_set=logging.Logger)
        with patch("%s.set_log_level_format" % pbm, autospec=True) as mock_set:
            set_log_info(mock_log)
        assert mock_set.mock_calls == [
            call(
                mock_log, logging.INFO, "%(asctime)s %(levelname)s:%(name)s:%(message)s"
            )
        ]

    def test_set_log_debug(self) -> None:
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
