# Bulk Fob Update

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to implement a new module in the `dm_mac` project, called `neon_fob_adder`. This module will provide both a `NeonFobUpdater` class with appropriate methods, as well as a command line interface accessible via a `neon-fob-adder` entrypoint. Its purpose is to automate adding new RFID fob/card codes to Neon CRM accounts, using the [Account PATCH API](https://developer.neoncrm.com/api-v2/#/Accounts/patchUsingPATCH). The [dm_mac.neongetter](/src/dm_mac/neongetter.py) module already contains code to retrieve account/fob information from Neon, and we should leverage its existing configuration file. The new Fob Adder module will need methods to retrieve information for a given account ID (full name, preferred name, email, full list of fob codes) as well as a method to update (PATCH) a user account by appending a new fob code to a custom field (`FobCSV` - this should be a module-level constant) which contains a CSV list of fob codes. All fob codes must be ten-digit numeric strings, left-padded with zeroes if needed.

The `NeonFobUpdater` class should include an interactive helper method `add_fob_to_account`, which takes an account ID as its argument. This method retrieves and displays the account information (account number, full name, preferred name, email, full list of all current fob codes in both `Fob10Digit` and `FobCSV` fields), prompts the user to interactively enter a new fob code (or the string `s` or `skip` to skip this account), validates that the code is a 10-digit numeric and not already present on the user account, and then prompts the user to confirm the addition (y/N); if confirmed, it PATCHes the account to append the new code to the `FobCSV` CSV field and outputs the updated `FobCSV` value. This script should also write a log file, `neon_fob_adder_<YYYYmmddHHMMSS>.log`, containing the account ID, previous fob list, and new fob list, of all accounts that are updated.

For the CLI interface, the script can either be called with one or more account IDs on the command line, in which case the previously-explained `NeonFobUpdater.add_fob_to_account()` method will be called for each argument, or it can be called with `-c` / `--csv` and `-f` / `--field` options, in which case it will load the CSV file at the path specified by `-c` and call `NeonFobUpdater.add_fob_to_account()` with the value of the `-f` field for each row in the file other than the first row (headers).

Comprehensive unit tests should be added under `tests/` for all functionality, with all API calls/requests mocked out.

Finally, the documentation at `docs/source/neon.rst` must be updated with a detailed user guide for this new module/CLI.

## Implementation Plan

### Key Design Decisions

1. **Module-level constant**: `FOB_CSV_FIELD = "FobCSV"` for the custom field name
2. **Configuration reuse**: Leverage existing `NEONGETTER_CONFIG` and `neon.config.json` for field mappings
3. **API endpoints**:
   - `GET /accounts/{accountId}` - Retrieve account info with all custom fields
   - `GET /customFields?category=Account` - Get custom field IDs (cached)
   - `PATCH /accounts/{accountId}` - Update account with new FobCSV value
4. **Fob code handling**:
   - Display fobs from both `Fob10Digit` and `FobCSV` fields (read from config `fob_fields`)
   - Only update `FobCSV` field (append to CSV string)
   - Auto-pad input to 10 digits with leading zeroes
5. **Logging**: Write `neon_fob_adder_<YYYYmmddHHMMSS>.log` to current directory

### Implementation Milestones

#### Milestone 1: Core NeonFobUpdater Class
**Status**: ✅ Complete (2025-12-30)
**Commit prefix**: `bulk-fob-adder - M1.{task}`

**Tasks**:
1. **M1.1**: ✅ Create module structure with `FOB_CSV_FIELD` constant and `NeonFobUpdater.__init__()`
2. **M1.2**: ✅ Implement `_get_fobcsv_field_id() -> int`
3. **M1.3**: ✅ Implement `get_account_info(account_id: str) -> Dict[str, Any]`
4. **M1.4**: ✅ Implement `update_account_fob(account_id: str, new_fob_code: str) -> str`
5. **M1.5**: ✅ Run tests and commit M1

**Summary**: Created core NeonFobUpdater class with methods to retrieve account info, get FobCSV field ID, and update accounts with new fob codes. All existing tests passing.

#### Milestone 2: Interactive Helper and Logging
**Status**: ✅ Complete (2025-12-30)
**Commit prefix**: `bulk-fob-adder - M2.{task}`

**Tasks**:
1. **M2.1**: ✅ Implement `_setup_update_logger(timestamp: str) -> logging.Logger`
2. **M2.2**: ✅ Implement `add_fob_to_account(account_id: str) -> None`
3. **M2.3**: ✅ Run tests and commit M2

**Summary**: Implemented interactive fob addition workflow with account info display, user prompts, validation, and logging to timestamped log files. All existing tests passing.

#### Milestone 3: CLI Implementation
**Status**: Not started
**Commit prefix**: `bulk-fob-adder - M3.{task}`

**Tasks**:
1. **M3.1**: Implement `parse_args(argv: List[str]) -> argparse.Namespace`
2. **M3.2**: Implement `process_csv_file(csv_path: str, field_name: str, updater: NeonFobUpdater) -> None`
3. **M3.3**: Implement `main() -> None`
4. **M3.4**: Add entrypoint to `pyproject.toml`
5. **M3.5**: Run tests and commit M3

#### Milestone 4: Comprehensive Testing
**Status**: Not started
**Commit prefix**: `bulk-fob-adder - M4.{task}`

**Tasks**:
1. **M4.1**: Create test fixtures
2. **M4.2**: Test `__init__` and basic setup
3. **M4.3**: Test `get_account_info()`
4. **M4.4**: Test `update_account_fob()`
5. **M4.5**: Test `add_fob_to_account()`
6. **M4.6**: Test CLI
7. **M4.7**: Run tests and commit M4

#### Milestone 5: Acceptance Criteria
**Status**: Not started
**Commit prefix**: `bulk-fob-adder - M5.{task}`

**Tasks**:
1. **M5.1**: Update `docs/source/neon.rst`
2. **M5.2**: Update `CLAUDE.md`
3. **M5.3**: Verify test coverage
4. **M5.4**: Run all nox sessions
5. **M5.5**: Move feature to completed
