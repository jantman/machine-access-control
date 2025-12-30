"""Tool to add RFID fobs to NeonOne accounts via API."""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from typing import cast

from requests import Response
from requests import Session
from requests.adapters import HTTPAdapter

from dm_mac.cli_utils import env_var_or_die
from dm_mac.cli_utils import set_log_debug
from dm_mac.cli_utils import set_log_info
from dm_mac.utils import load_json_config


logging.basicConfig(
    level=logging.WARNING, format="[%(asctime)s %(levelname)s] %(message)s"
)
logger: logging.Logger = logging.getLogger()

# suppress noisy urllib3 logging
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3").propagate = True

# Module-level constant for FobCSV field name
FOB_CSV_FIELD: str = "FobCSV"


class NeonFobUpdater:
    """Class to add RFID fobs to NeonOne accounts via API."""

    BASE_URL: str = "https://api.neoncrm.com/v2/"

    def __init__(self) -> None:
        """Initialize NeonFobUpdater."""
        self._orgid: str = env_var_or_die("NEON_ORG", "your Neon organization ID")
        self._token: str = env_var_or_die("NEON_KEY", "your Neon API key")
        self._sess: Session = Session()
        self._sess.mount("https://", HTTPAdapter(max_retries=3))
        self._sess.auth = (self._orgid, self._token)
        self._sess.headers.update({"NEON-API-VERSION": "2.11"})
        logger.debug(
            "Will authenticate to Neon API using Username (organization ID) "
            "%s and password (token) of length %d: %s...",
            self._orgid,
            len(self._token),
            self._token[:3],
        )
        self._timeout: int = 10
        self._config: Dict[str, Union[str, List[str]]] = cast(
            Dict[str, Union[str, List[str]]],
            load_json_config("NEONGETTER_CONFIG", "neon.config.json"),
        )
        # Cache for FobCSV field ID to avoid repeated API calls
        self._fobcsv_field_id: Optional[int] = None
        # Cache for update logger
        self._update_logger: Optional[logging.Logger] = None

    def _setup_update_logger(self, timestamp: str) -> logging.Logger:
        """
        Set up a logger for writing fob update records to file.

        Args:
            timestamp: Timestamp string for log filename (format: YYYYmmddHHMMSS)

        Returns:
            Configured logger instance
        """
        if self._update_logger is not None:
            return self._update_logger

        # Create logger
        update_logger = logging.getLogger(f"neon_fob_adder.updates.{timestamp}")
        update_logger.setLevel(logging.INFO)
        update_logger.propagate = False  # Don't propagate to root logger

        # Create file handler
        log_filename = f"neon_fob_adder_{timestamp}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)

        # Create formatter
        # Format: timestamp - Account <id> (<name>) - Previous: [list]
        #         - Added: <code> - Updated: <csv>
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add handler to logger
        update_logger.addHandler(file_handler)

        # Cache the logger
        self._update_logger = update_logger

        logger.info("Created update log file: %s", log_filename)
        return update_logger

    def _get_custom_fields_raw(self) -> List[Dict[str, Any]]:
        """Return the raw API response for custom fields."""
        url: str = self.BASE_URL + "customFields?category=Account"
        logger.debug("GET %s", url)
        r: Response = self._sess.get(url, timeout=self._timeout)
        logger.debug(
            "Neon returned HTTP %d with %d byte content", r.status_code, len(r.content)
        )
        try:
            r.raise_for_status()
        except Exception:
            logger.error(
                "HTTP GET of %s returned HTTP %d headers=%s body=%s",
                url,
                r.status_code,
                r.headers,
                r.text,
            )
            raise
        return cast(List[Dict[str, Any]], r.json())

    def _get_fobcsv_field_id(self) -> int:
        """Get the field ID for the FobCSV custom field, with caching."""
        # Return cached value if available
        if self._fobcsv_field_id is not None:
            logger.debug("Using cached FobCSV field ID: %d", self._fobcsv_field_id)
            return self._fobcsv_field_id

        # Get all custom fields
        custom_fields: List[Dict[str, Any]] = self._get_custom_fields_raw()
        logger.debug("Neon API returned %d custom fields", len(custom_fields))

        # Find the FobCSV field
        for field in custom_fields:
            if field.get("name") == FOB_CSV_FIELD:
                field_id: int = int(field["id"])
                logger.debug("Found FobCSV field with ID: %d", field_id)
                # Cache the result
                self._fobcsv_field_id = field_id
                return field_id

        # Field not found
        raise RuntimeError(
            f"Custom field '{FOB_CSV_FIELD}' not found in Neon account. "
            f"Available fields: {[f.get('name') for f in custom_fields]}"
        )

    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """
        Retrieve account information including all fob codes.

        Returns dict with keys: account_id, full_name, preferred_name, email, fob_codes
        """
        url: str = f"{self.BASE_URL}accounts/{account_id}"
        logger.debug("GET %s", url)
        r: Response = self._sess.get(url, timeout=self._timeout)
        logger.debug(
            "Neon returned HTTP %d with %d byte content", r.status_code, len(r.content)
        )
        try:
            r.raise_for_status()
        except Exception:
            logger.error(
                "HTTP GET of %s returned HTTP %d headers=%s body=%s",
                url,
                r.status_code,
                r.headers,
                r.text,
            )
            raise

        # Parse response
        response_data: Dict[str, Any] = r.json()
        account_data: Dict[str, Any] = response_data.get("individualAccount", {})

        # Extract primary contact info
        primary_contact: Dict[str, Any] = account_data.get("primaryContact", {})

        # Build a flat dict for easier field access
        # Combine top-level account fields and custom fields
        flat_account: Dict[str, Any] = {}

        # Add standard fields from primaryContact
        flat_account["First Name"] = primary_contact.get("firstName", "")
        flat_account["Email 1"] = primary_contact.get("email1", "")
        flat_account["Preferred Name"] = primary_contact.get("preferredName", "")

        # Build full name from firstName and lastName
        first_name = primary_contact.get("firstName", "")
        last_name = primary_contact.get("lastName", "")
        flat_account["Full Name (F)"] = f"{first_name} {last_name}".strip()

        # Add account ID
        flat_account["Account ID"] = account_data.get("accountId", account_id)

        # Add custom fields
        custom_fields: List[Dict[str, Any]] = account_data.get(
            "accountCustomFields", []
        )
        for field in custom_fields:
            field_name = field.get("name")
            field_value = field.get("value")
            if field_name and field_value is not None:
                flat_account[field_name] = field_value

        # Extract the fields we need using config
        result: Dict[str, Any] = {
            "account_id": flat_account.get(
                cast(str, self._config["account_id_field"]), account_id
            ),
            "full_name": flat_account.get(
                cast(str, self._config["full_name_field"]), ""
            ),
            "preferred_name": flat_account.get(
                cast(str, self._config["preferred_name_field"]), ""
            ),
            "email": flat_account.get(cast(str, self._config["email_field"]), ""),
            "fob_codes": [],
        }

        # Extract fob codes from all fob fields in config
        all_fobs: List[str] = []
        for fob_field in cast(List[str], self._config["fob_fields"]):
            if fob_value := flat_account.get(fob_field):
                # Handle CSV format - split and strip whitespace
                fob_codes = [code.strip() for code in str(fob_value).split(",")]
                all_fobs.extend([code for code in fob_codes if code])

        result["fob_codes"] = all_fobs
        logger.debug(
            "Retrieved account %s (%s) with %d fob codes",
            result["account_id"],
            result["full_name"],
            len(all_fobs),
        )
        return result

    def update_account_fob(self, account_id: str, new_fob_code: str) -> str:
        """
        Update account by appending new fob code to FobCSV field.

        Args:
            account_id: Neon account ID
            new_fob_code: New fob code to add (will be left-padded to 10 digits)

        Returns:
            Updated FobCSV value

        Raises:
            ValueError: If fob code is invalid or duplicate
            RuntimeError: If API call fails
        """
        # Left-pad to 10 digits
        padded_fob = new_fob_code.strip().zfill(10)

        # Validate it's numeric
        if not padded_fob.isdigit():
            raise ValueError(
                f"Fob code must be numeric. Got: '{new_fob_code}' "
                f"(padded: '{padded_fob}')"
            )

        # Validate length after padding
        if len(padded_fob) != 10:
            raise ValueError(
                f"Fob code must be 10 digits after padding. Got: '{padded_fob}' "
                f"({len(padded_fob)} digits)"
            )

        # Get current account info
        account_info: Dict[str, Any] = self.get_account_info(account_id)

        # Check for duplicate
        if padded_fob in account_info["fob_codes"]:
            raise ValueError(
                f"Fob code '{padded_fob}' already exists on account "
                f"{account_id} ({account_info['full_name']})"
            )

        # Get FobCSV field ID
        field_id: int = self._get_fobcsv_field_id()

        # Get current FobCSV value (need to re-fetch from flat_account)
        # We'll fetch it from the raw account data
        url: str = f"{self.BASE_URL}accounts/{account_id}"
        r: Response = self._sess.get(url, timeout=self._timeout)
        r.raise_for_status()
        response_data: Dict[str, Any] = r.json()
        account_data: Dict[str, Any] = response_data.get("individualAccount", {})
        custom_fields: List[Dict[str, Any]] = account_data.get(
            "accountCustomFields", []
        )

        current_fobcsv: str = ""
        for field in custom_fields:
            if field.get("name") == FOB_CSV_FIELD:
                current_fobcsv = field.get("value", "")
                break

        # Build new FobCSV value (append to existing)
        if current_fobcsv:
            new_fobcsv = f"{current_fobcsv},{padded_fob}"
        else:
            new_fobcsv = padded_fob

        # Build PATCH payload
        patch_data: Dict[str, Any] = {
            "individualAccount": {
                "accountCustomFields": [
                    {"id": str(field_id), "name": FOB_CSV_FIELD, "value": new_fobcsv}
                ]
            }
        }

        # PATCH the account
        patch_url: str = f"{self.BASE_URL}accounts/{account_id}"
        logger.debug(
            "PATCH %s with data: %s",
            patch_url,
            json.dumps(patch_data, sort_keys=True, indent=4),
        )
        r = self._sess.patch(patch_url, timeout=self._timeout, json=patch_data)
        logger.debug(
            "Neon returned HTTP %d with %d byte content", r.status_code, len(r.content)
        )
        try:
            r.raise_for_status()
        except Exception:
            logger.error(
                "HTTP PATCH of %s returned HTTP %d headers=%s body=%s",
                patch_url,
                r.status_code,
                r.headers,
                r.text,
            )
            raise

        logger.info(
            "Successfully updated account %s (%s): added fob %s to FobCSV",
            account_id,
            account_info["full_name"],
            padded_fob,
        )
        return new_fobcsv

    def add_fob_to_account(self, account_id: str) -> None:
        """
        Interactive method to add a fob to an account.

        Displays account information, prompts for new fob code, validates,
        and updates if confirmed.

        Args:
            account_id: Neon account ID to process
        """
        # Get account info
        try:
            account_info = self.get_account_info(account_id)
        except Exception as e:
            print(f"\nError retrieving account {account_id}: {e}")
            logger.error("Failed to retrieve account %s: %s", account_id, e)
            return

        # Display account information
        print("\n" + "=" * 70)
        print(f"Account ID: {account_info['account_id']}")
        print(f"Full Name: {account_info['full_name']}")
        print(f"Preferred Name: {account_info['preferred_name']}")
        print(f"Email: {account_info['email']}")
        print(
            f"Current Fob Codes ({len(account_info['fob_codes'])}): {account_info['fob_codes']}"
        )
        print("=" * 70)

        # Prompt for new fob code
        new_fob = input("\nEnter new fob code (or 's' to skip): ").strip()

        # Check if user wants to skip
        if new_fob.lower() in ("s", "skip"):
            print("Skipped")
            return

        # Pad to 10 digits
        padded_fob = new_fob.zfill(10)

        # Validate numeric
        if not padded_fob.isdigit():
            print(
                f"Error: Fob code must be numeric. Got: '{new_fob}' (padded: '{padded_fob}')"
            )
            return

        # Validate length
        if len(padded_fob) != 10:
            print(
                f"Error: Fob code must be 10 digits. Got: '{padded_fob}' ({len(padded_fob)} digits)"
            )
            return

        # Check for duplicate
        if padded_fob in account_info["fob_codes"]:
            print(f"Error: Fob code '{padded_fob}' already exists on this account")
            return

        # Display proposed change
        print("\nProposed change:")
        print(f"   Will add fob code: {padded_fob}")
        print(
            f"   To account: {account_info['account_id']} ({account_info['full_name']})"
        )

        # Confirm
        confirmation = input("\nConfirm addition? [y/N]: ").strip().lower()

        if confirmation != "y":
            print("Cancelled")
            return

        # Perform update
        try:
            new_fobcsv = self.update_account_fob(account_id, padded_fob)
            print(f"Success! Updated FobCSV: {new_fobcsv}")

            # Log to update file
            # Create timestamp if logger not yet set up
            if self._update_logger is None:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                self._setup_update_logger(timestamp)

            # Log the update
            self._update_logger.info(
                "Account %s (%s) - Previous: %s - Added: %s - Updated FobCSV: %s",
                account_info["account_id"],
                account_info["full_name"],
                account_info["fob_codes"],
                padded_fob,
                new_fobcsv,
            )

        except Exception as e:
            print(f"\nError updating account: {e}")
            logger.error("Failed to update account %s: %s", account_id, e)


def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Add RFID fob codes to NeonOne accounts")
    p.add_argument(
        "account_ids",
        nargs="*",
        help="Account IDs to process (cannot be used with --csv)",
    )
    p.add_argument(
        "-c",
        "--csv",
        dest="csv_path",
        action="store",
        type=str,
        default=None,
        help="Path to CSV file containing account IDs",
    )
    p.add_argument(
        "-f",
        "--field",
        dest="field_name",
        action="store",
        type=str,
        default=None,
        help="Field name in CSV file containing account IDs (required with --csv)",
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

    # Validation: cannot use both modes
    if args.account_ids and args.csv_path:
        p.error("Cannot specify both account IDs and --csv option")

    # Validation: CSV mode requires both -c and -f
    if args.csv_path and not args.field_name:
        p.error("--csv requires --field to be specified")
    if args.field_name and not args.csv_path:
        p.error("--field requires --csv to be specified")

    # Validation: must specify one mode
    if not args.account_ids and not args.csv_path:
        p.error("Must specify either account IDs or --csv option")

    return args


def main() -> None:
    """Main entrypoint for CLI script."""
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose:
        set_log_debug(logger)
    else:
        set_log_info(logger)

    # Create updater instance
    updater = NeonFobUpdater()

    # Route to appropriate mode
    if args.account_ids:
        # Account IDs mode
        for account_id in args.account_ids:
            updater.add_fob_to_account(account_id)
    else:
        # CSV mode
        process_csv_file(args.csv_path, args.field_name, updater)


def process_csv_file(csv_path: str, field_name: str, updater: "NeonFobUpdater") -> None:
    """Process a CSV file and add fobs to accounts."""
    logger.info("Processing CSV file: %s", csv_path)
    with open(csv_path) as fh:
        reader = csv.DictReader(fh)

        # Validate field exists in CSV
        if reader.fieldnames is None or field_name not in reader.fieldnames:
            raise ValueError(
                f"Field '{field_name}' not found in CSV. "
                f"Available fields: {reader.fieldnames}"
            )

        # Process each row
        for row in reader:
            account_id = row[field_name]
            if account_id:  # Skip empty values
                updater.add_fob_to_account(account_id)
