"""Tests for dm_mac.neongetter module."""

import json
import os
from base64 import b64encode
from pathlib import Path
from typing import Any
from typing import List
from typing import Tuple
from typing import cast
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest
import responses
from _pytest.capture import CaptureFixture
from jsonschema.exceptions import ValidationError
from requests.exceptions import HTTPError
from responses.registries import OrderedRegistry

from dm_mac.neongetter import NeonUserUpdater
from dm_mac.neongetter import logger
from dm_mac.neongetter import main


pbm = "dm_mac.neongetter"
pb = f"{pbm}.NeonUserUpdater"

NOX_CREDS: Tuple[str, str] = ("test", "12345")
NOX_AUTH: str = "Basic " + b64encode(":".join(NOX_CREDS).encode("ascii")).decode(
    "ascii"
)


class TestInit:
    """Test the class init() method."""

    def test_happy_path(self) -> None:
        """Happy path test."""
        with patch(f"{pb}._load_and_validate_config", autospec=True) as m_load:
            with patch(f"{pb}._dump_fields", autospec=True) as m_df:
                with patch(f"{pbm}.env_var_or_die") as m_evod:
                    m_evod.return_value = ["ORGID", "TKN"]
                    m_load.return_value = {"foo": "bar"}
                    cls = NeonUserUpdater()
        assert cls._config == {"foo": "bar"}
        assert m_load.mock_calls == [call(cls)]
        assert m_df.mock_calls == []
        assert m_evod.mock_calls == [
            call("NEON_ORG", "your Neon organization ID"),
            call("NEON_KEY", "your Neon API key"),
        ]

    def test_dump_fields(self) -> None:
        """Test with dump_fields True."""
        with patch(f"{pb}._load_and_validate_config", autospec=True) as m_load:
            with patch(f"{pb}._dump_fields", autospec=True) as m_df:
                with patch(f"{pbm}.env_var_or_die") as m_evod:
                    m_evod.return_value = ["ORGID", "TKN"]
                    m_load.return_value = {"foo": "bar"}
                    cls = NeonUserUpdater(dump_fields=True)
        assert m_load.mock_calls == []
        assert m_df.mock_calls == [call(cls)]
        assert m_evod.mock_calls == [
            call("NEON_ORG", "your Neon organization ID"),
            call("NEON_KEY", "your Neon API key"),
        ]


class TestLoadAndValidateConfig:
    """Test NeonUserUpdater._load_and_validate_config()."""

    @patch.dict("os.environ", {"NEON_ORG": "o", "NEON_KEY": "k"})
    def test_happy_path(self) -> None:
        """Test happy path."""
        with patch(f"{pb}._load_and_validate_config") as m_load_conf:
            m_load_conf.return_value = {}
            cls = NeonUserUpdater()
        assert cls._config == {}
        with patch(f"{pbm}.load_json_config", autospec=True) as m_load:
            with patch(f"{pb}.validate_config") as m_validate:
                m_load.return_value = {"foo": "bar"}
                m_validate.return_value = None
                res = cls._load_and_validate_config()
        assert m_load.mock_calls == [call("NEONGETTER_CONFIG", "neon.config.json")]
        assert m_validate.mock_calls == [call({"foo": "bar"})]
        assert res == {"foo": "bar"}


class TestDumpFields:
    """Test NeonUserUpdater._dump_fields() method."""

    @responses.activate(registry=OrderedRegistry)
    def test_happy_path(self, fixtures_path: str, capsys: CaptureFixture[Any]) -> None:
        """Test happy path of method."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "dump_fields.yaml")
        )
        # store the responses; they're removed from the registry as called
        resp: List[responses.BaseResponse] = [x for x in responses.registered()]
        NeonUserUpdater(dump_fields=True)
        captured = capsys.readouterr()
        assert resp[0].call_count == 1
        assert resp[0].calls[0].request.headers["Authorization"] == NOX_AUTH
        assert resp[0].calls[0].request.headers["NEON-API-VERSION"] == "2.8"
        assert resp[1].call_count == 1
        assert resp[1].calls[0].request.headers["Authorization"] == NOX_AUTH
        assert resp[1].calls[0].request.headers["NEON-API-VERSION"] == "2.8"
        # get the responses from the fixture data
        std: Any = json.loads(cast(str, resp[0].body))
        custom: Any = json.loads(cast(str, resp[1].body))
        assert (
            captured.out
            == "Account fields:\n"
            + json.dumps(std, sort_keys=True, indent=4)
            + "\n"
            + "Custom fields:\n"
            + json.dumps(custom, sort_keys=True, indent=4)
            + "\n"
        )

    @responses.activate(registry=OrderedRegistry)
    def test_account_fields_500(self, fixtures_path: str) -> None:
        """Test when endpoint returns HTTP 500."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "dump_fields.yaml")
        )
        # exfiltrate the registered responses
        resp: List[responses.BaseResponse] = [x for x in responses.registered()]
        # clear all registered responses
        responses.reset()
        # add back a response so the first request fails
        responses.add(
            responses.GET,
            "https://api.neoncrm.com/v2/accounts/search/outputFields?searchKey=1",
            body="Some error.",
            status=503,
        )
        # just for completeness, add back the second OK response
        responses.add(resp[1])
        with pytest.raises(HTTPError):
            NeonUserUpdater(dump_fields=True)

    @responses.activate(registry=OrderedRegistry)
    def test_custom_fields_500(
        self, fixtures_path: str, capsys: CaptureFixture[Any]
    ) -> None:
        """Test when endpoint returns HTTP 500."""
        # NOTE: capsys is only here to keep STDOUT from polluting pytest console
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "dump_fields.yaml")
        )
        # exfiltrate the registered responses
        resp: List[responses.BaseResponse] = [x for x in responses.registered()]
        # clear all registered responses
        responses.reset()
        # add back the first response
        responses.add(resp[0])
        # add back a response so the first request fails
        responses.add(
            responses.GET,
            "https://api.neoncrm.com/v2/customFields?category=Account",
            body="Some error.",
            status=503,
        )
        # just for completeness, add back the second OK response
        with pytest.raises(HTTPError):
            NeonUserUpdater(dump_fields=True)
        capsys.readouterr()


class TestValidateConfig:
    """Tests for neongetter.validate_config()."""

    def test_example_validates(self) -> None:
        """Ensure example config is valid."""
        NeonUserUpdater.validate_config(NeonUserUpdater.example_config())

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


class TestRun:
    """Test the full run() path."""

    @responses.activate(registry=OrderedRegistry)
    def test_happy_path(self, fixtures_path: str, tmp_path: Path) -> None:
        """Happy path test."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "run.yaml")
        )
        # get config fixture path
        conf_path: str = os.path.join(fixtures_path, "neon.config.json")
        # temporary directory to write output to
        os.chdir(tmp_path)
        # overwrite noxfile default NEONGETTER_CONFIG
        with patch.dict(os.environ, {"NEONGETTER_CONFIG": conf_path}):
            NeonUserUpdater().run(output_path="users.json")
        with open("users.json") as fh:
            result: str = json.load(fh)
        with open(
            os.path.join(fixtures_path, "test_neongetter", "users-happy.json")
        ) as fh:
            expected: str = json.load(fh)
        assert result == expected

    @responses.activate(registry=OrderedRegistry)
    def test_config_reload(self, fixtures_path: str, tmp_path: Path) -> None:
        """Happy path test."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "run-config-reload.yaml")
        )
        # get config fixture path
        conf_path: str = os.path.join(fixtures_path, "neon.config.json")
        # temporary directory to write output to
        os.chdir(tmp_path)
        # overwrite noxfile default NEONGETTER_CONFIG
        with patch.dict(
            os.environ,
            {
                "NEONGETTER_CONFIG": conf_path,
                "MAC_USER_RELOAD_URL": "http://localhost:5000/api/reload-users",
            },
        ):
            NeonUserUpdater().run(output_path="users.json")
        with open("users.json") as fh:
            result: str = json.load(fh)
        with open(
            os.path.join(fixtures_path, "test_neongetter", "users-happy.json")
        ) as fh:
            expected: str = json.load(fh)
        assert result == expected

    @responses.activate(registry=OrderedRegistry)
    def test_config_reload_error(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test API returns HTTP error."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(
                fixtures_path, "test_neongetter", "run-config-reload-error.yaml"
            )
        )
        # get config fixture path
        conf_path: str = os.path.join(fixtures_path, "neon.config.json")
        # temporary directory to write output to
        os.chdir(tmp_path)
        # overwrite noxfile default NEONGETTER_CONFIG
        with patch.dict(
            os.environ,
            {
                "NEONGETTER_CONFIG": conf_path,
                "MAC_USER_RELOAD_URL": "http://localhost:5000/api/reload-users",
            },
        ):
            with pytest.raises(HTTPError):
                NeonUserUpdater().run(output_path="users.json")

    @responses.activate(registry=OrderedRegistry)
    def test_duplicate_fob(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test exception raised for duplicate fob."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "run-dupe-fob.yaml")
        )
        # get config fixture path
        conf_path: str = os.path.join(fixtures_path, "neon.config.json")
        # temporary directory to write output to
        os.chdir(tmp_path)
        # overwrite noxfile default NEONGETTER_CONFIG
        with patch.dict(os.environ, {"NEONGETTER_CONFIG": conf_path}):
            with pytest.raises(RuntimeError) as exc:
                NeonUserUpdater().run(output_path="users.json")
        assert exc.value.args[0] == (
            "ERROR: Duplicate fob fields: fob 0476421226 is present in user "
            "Victoria Jones (17) as well as Joshua Adams (586); fob 3706638933"
            " is present in user Adam Duarte (449) as well as Lisa Padilla "
            "(587)"
        )

    @responses.activate(registry=OrderedRegistry)
    def test_search_api_error(self, fixtures_path: str, tmp_path: Path) -> None:
        """Test API returns HTTP error."""
        # load recoreded fixture from file
        responses._add_from_file(
            os.path.join(fixtures_path, "test_neongetter", "run-search-api-error.yaml")
        )
        # get config fixture path
        conf_path: str = os.path.join(fixtures_path, "neon.config.json")
        # temporary directory to write output to
        os.chdir(tmp_path)
        # overwrite noxfile default NEONGETTER_CONFIG
        with patch.dict(os.environ, {"NEONGETTER_CONFIG": conf_path}):
            with pytest.raises(HTTPError):
                NeonUserUpdater().run(output_path="users.json")


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
            assert mock_nuu.mock_calls == [call(), call().run(output_path="users.json")]

    def test_run_output_path(
        self, mock_debug: Mock, mock_info: Mock, mock_nuu: Mock
    ) -> None:
        """Test with no arguments."""
        with patch(f"{pbm}.sys.argv", ["neongetter", "-o", "/foo/bar.json"]):
            main()
            assert mock_debug.mock_calls == []
            assert mock_info.mock_calls == [call(logger)]
            assert mock_nuu.mock_calls == [
                call(),
                call().run(output_path="/foo/bar.json"),
            ]

    def test_run_debug(self, mock_debug: Mock, mock_info: Mock, mock_nuu: Mock) -> None:
        """Test with verbose argument."""
        with patch(f"{pbm}.sys.argv", ["neongetter", "-v"]):
            main()
            assert mock_debug.mock_calls == [call(logger)]
            assert mock_info.mock_calls == []
            assert mock_nuu.mock_calls == [call(), call().run(output_path="users.json")]

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
