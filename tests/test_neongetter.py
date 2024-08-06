"""Tests for dm_mac.neongetter module."""

import json
from typing import Any
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture
from jsonschema.exceptions import ValidationError

from dm_mac.neongetter import NeonUserUpdater
from dm_mac.neongetter import logger
from dm_mac.neongetter import main


pbm = "dm_mac.neongetter"
pb = f"{pbm}.NeonUserUpdater"


class TestValidateConfig:
    """Tests for neongetter.validate_config()."""

    def test_example_validates(self) -> None:
        """Ensure example config is valid."""
        res = NeonUserUpdater.validate_config(NeonUserUpdater.example_config())
        assert res is None

    def test_invalid_raises_exception(self) -> None:
        """Ensure invalid config raises an exception."""
        config = {
            "name_field": "Full Name (F)",
            "email_field": "Email 1",
            "expiration_field": "Membership Expiration Date",
            "account_id_field": "Account ID",
            "fob_fields": ["Fob10Digit"],
            # "authorized_field_value": "Training Complete",
            "invalid_field": "foo",
        }
        with pytest.raises(ValidationError):
            NeonUserUpdater.validate_config(config)


@patch(pb)
@patch(f"{pbm}.set_log_info")
@patch(f"{pbm}.set_log_debug")
class TestMain:
    """Tests for main method."""

    def test_run(self, mock_debug: Mock, mock_info: Mock, mock_nuu: Mock) -> None:
        """Test with no arguments."""
        with patch(f"{pbm}.sys.argv", ["neongetter"]):
            main()
            assert mock_debug.mock_calls == []
            assert mock_info.mock_calls == [call(logger)]
            assert mock_nuu.mock_calls == [call(), call().run()]

    def test_run_debug(self, mock_debug: Mock, mock_info: Mock, mock_nuu: Mock) -> None:
        """Test with verbose argument."""
        with patch(f"{pbm}.sys.argv", ["neongetter", "-v"]):
            main()
            assert mock_debug.mock_calls == [call(logger)]
            assert mock_info.mock_calls == []
            assert mock_nuu.mock_calls == [call(), call().run()]

    def test_dump_fields(
        self, mock_debug: Mock, mock_info: Mock, mock_nuu: Mock
    ) -> None:
        """Test with --dump-fields argument."""
        with patch(f"{pbm}.sys.argv", ["neongetter", "--dump-fields"]):
            main()
            assert mock_debug.mock_calls == []
            assert mock_info.mock_calls == [call(logger)]
            assert mock_nuu.mock_calls == [call(dump_fields=True)]

    def test_dump_example_config(
        self,
        mock_debug: Mock,
        mock_info: Mock,
        mock_nuu: Mock,
        capsys: CaptureFixture[Any],
    ) -> None:
        """Test with --dump-example-config argument."""
        type(mock_nuu).example_config = Mock(return_value={"my": "config"})
        with patch(f"{pbm}.sys.argv", ["neongetter", "--dump-example-config"]):
            main()
            assert mock_debug.mock_calls == []
            assert mock_info.mock_calls == [call(logger)]
            assert mock_nuu.mock_calls == []
            captured = capsys.readouterr()
            assert (
                captured.out
                == json.dumps({"my": "config"}, sort_keys=True, indent=4) + "\n"
            )
