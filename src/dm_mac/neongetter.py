"""Tool to update users.json from NeonOne API."""

import argparse
import json
import logging
import sys

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
        url: str = self.BASE_URL + "customFields?category=Account"
        logger.debug("GET %s", url)
        r: Response = self._sess.get(url, timeout=self._timeout)
        logger.debug(
            "Neon returned HTTP %d with %d byte content", r.status_code, len(r.content)
        )
        r.raise_for_status()
        print(json.dumps(r.json(), sort_keys=True, indent=4))

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
        help="Just dump Neon API fields and then exit",
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


def main():
    """Main entrypoint for CLI script."""
    args = parse_args(sys.argv[1:])
    # set logging level
    if args.verbose:
        set_log_debug(logger)
    else:
        set_log_info(logger)
    if args.dump_fields:
        NeonUserUpdater(dump_fields=True)
        return
    NeonUserUpdater().run()


if __name__ == "__main__":
    main()
