"""Tests for dm_mac.utils module."""

from unittest.mock import call
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

from dm_mac.utils import load_json_config


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
