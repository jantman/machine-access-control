# Bulk Fob Update

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to implement a new module in the `dm_mac` project, called `neon_fob_adder`. This module will provide both a `NeonFobUpdater` class with appropriate methods, as well as a command line interface accessible via a `neon-fob-adder` entrypoint. Its purpose is to automate adding new RFID fob/card codes to Neon CRM accounts, using the [Account PATCH API](https://developer.neoncrm.com/api-v2/#/Accounts/patchUsingPATCH). The [dm_mac.neongetter](/src/dm_mac/neongetter.py) module already contains code to retrieve account/fob information from Neon, and we should leverage its existing configuration file. The new Fob Adder module will need methods to retrieve information for a given account ID (full name, preferred name, email, full list of fob codes) as well as a method to update (PATCH) a user account by appending a new fob code to a custom field (`FobCSV` - this should be a module-level constant) which contains a CSV list of fob codes. All fob codes must be ten-digit numeric strings, left-padded with zeroes if needed.

The `NeonFobUpdater` class should include an interactive helper method `add_fob_to_account`, which takes an account ID as its argument. This method retrieves and displays the account information (account number, full name, preferred name, email, full list of all current fob codes in both `Fob10Digit` and `FobCSV` fields), prompts the user to interactively enter a new fob code (or the string `s` or `skip` to skip this account), validates that the code is a 10-digit numeric and not already present on the user account, and then prompts the user to confirm the addition (y/N); if confirmed, it PATCHes the account to append the new code to the `FobCSV` CSV field and outputs the updated `FobCSV` value. This script should also write a log file, `neon_fob_adder_<YYYYmmddHHMMSS>.log`, containing the account ID, previous fob list, and new fob list, of all accounts that are updated.

For the CLI interface, the script can either be called with one or more account IDs on the command line, in which case the previously-explained `NeonFobUpdater.add_fob_to_account()` method will be called for each argument, or it can be called with `-c` / `--csv` and `-f` / `--field` options, in which case it will load the CSV file at the path specified by `-c` and call `NeonFobUpdater.add_fob_to_account()` with the value of the `-f` field for each row in the file other than the first row (headers).

Comprehensive unit tests should be added under `tests/` for all functionality, with all API calls/requests mocked out.

Finally, the documentation at `docs/source/neon.rst` must be updated with a detailed user guide for this new module/CLI.
