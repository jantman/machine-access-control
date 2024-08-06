"""Tool to update users.json from NeonOne API."""

import argparse
import json
import logging
import sys

from jsonschema import validate
from requests import Response
from requests import Session
from requests.adapters import HTTPAdapter

from dm_mac.cli_utils import env_var_or_die
from dm_mac.cli_utils import set_log_debug
from dm_mac.cli_utils import set_log_info


logging.basicConfig(
    level=logging.WARNING, format="[%(asctime)s %(levelname)s] %(message)s"
)
logger: logging.Logger = logging.getLogger()


class NeonUserUpdater:
    """Class to update users.json from Neon One API."""

    BASE_URL: str = "https://api.neoncrm.com/v2/"

    def __init__(self, dump_fields: bool = False):
        """Initialize NeonUserUpdater."""
        self._orgid: str = env_var_or_die("NEON_ORG", "your Neon organization ID")
        self._token: str = env_var_or_die("NEON_KEY", "your Neon API key")
        self._sess: Session = Session()
        self._sess.mount("https://", HTTPAdapter(max_retries=3))
        self._sess.auth = (self._orgid, self._token)
        self._sess.headers.update({"NEON-API-VERSION": "2.8"})
        self._timeout: int = 10
        if dump_fields:
            self._dump_fields()
            return
        # @TODO load config

    def _get_custom_fields_raw(self) -> dict:
        """Return the raw API response for custom fields."""
        url: str = self.BASE_URL + "customFields?category=Account"
        logger.debug("GET %s", url)
        r: Response = self._sess.get(url, timeout=self._timeout)
        logger.debug(
            "Neon returned HTTP %d with %d byte content", r.status_code, len(r.content)
        )
        r.raise_for_status()
        return r.json()

    def _dump_fields(self):
        print("Account fields:")
        url: str = self.BASE_URL + "accounts/search/outputFields?searchKey=1"
        logger.debug("GET %s", url)
        r: Response = self._sess.get(url, timeout=self._timeout)
        logger.debug(
            "Neon returned HTTP %d with %d byte content", r.status_code, len(r.content)
        )
        r.raise_for_status()
        print(json.dumps(r.json(), sort_keys=True, indent=4))
        print("Custom fields:")
        print(json.dumps(self._get_custom_fields_raw(), sort_keys=True, indent=4))

    @staticmethod
    def validate_config(config: dict):
        """Validate configuration via jsonschema."""
        schema = {
            "type": "object",
            "properties": {
                "name_field": {
                    "type": "string",
                    "description": "Neon field name containing member name.",
                },
                "email_field": {
                    "type": "string",
                    "description": "Neon field name containing member email "
                    "address.",
                },
                "expiration_field": {
                    "type": "string",
                    "description": "Neon field name containing membership "
                    "expiration date.",
                },
                "account_id_field": {
                    "type": "string",
                    "description": "Neon field name containing account ID.",
                },
                "fob_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "List of Neon field names containing RFID "
                    "fob codes.",
                },
                "authorized_field_value": {
                    "type": "string",
                    "description": "Value for name of option indicating that "
                    "member is authorized / training complete.",
                },
            },
            "required": [
                "name_field",
                "email_field",
                "expiration_field",
                "account_id_field",
                "fob_fields",
                "authorized_field_value",
            ],
        }
        validate(config, schema)

    @staticmethod
    def example_config() -> dict:
        """Return an example configuration."""
        return {
            "name_field": "Full Name (F)",
            "email_field": "Email 1",
            "expiration_field": "Membership Expiration Date",
            "account_id_field": "Account ID",
            "fob_fields": ["Fob10Digit"],
            "authorized_field_value": "Training Complete",
        }

    def run(self):
        """Run the update."""
        pass


def parse_args(argv):
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Update users.json from Neon API")
    p.add_argument(
        "--dump-fields",
        dest="dump_fields",
        action="store_true",
        default=False,
        help="Just dump Neon API fields to STDOUT and then exit",
    )
    p.add_argument(
        "--dump-example-config",
        dest="dump_example_config",
        action="store_true",
        default=False,
        help="Just dump example config file to STDOUT and then exit",
    )
    p.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="verbose output",
    )
    args = p.parse_args(argv)
    return args


def main() -> None:
    """Main entrypoint for CLI script."""
    args = parse_args(sys.argv[1:])
    # set logging level
    if args.verbose:
        set_log_debug(logger)
    else:
        set_log_info(logger)
    if args.dump_fields:
        NeonUserUpdater(dump_fields=True)
    elif args.dump_example_config:
        print(json.dumps(NeonUserUpdater.example_config(), sort_keys=True, indent=4))
    else:
        NeonUserUpdater().run()
