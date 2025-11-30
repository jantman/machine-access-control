# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Decatur Makers Machine Access Control (dm-mac)**: a software and hardware project for using RFID cards/fobs to control access to power tools and equipment in the Decatur Makers makerspace. The system consists of:

1. **Central Control Server**: Python/Quart (async Flask) application that handles authentication/authorization, machine control, and logging
2. **Machine Control Units (MCUs)**: ESP32-based hardware running ESPHome that communicate with the server

The system integrates with NeonOne CRM for user data (optional and pluggable).

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtualenv (if needed)
poetry shell

# Install pre-commit hooks
nox -s pre-commit -- install
```

### Testing
```bash
# Run all tests with coverage
nox -s tests

# Run a single test file
nox -s tests -- tests/test_utils.py

# Run a specific test
nox -s tests -- tests/test_utils.py::test_specific_function

# Run tests with typeguard runtime type checking
nox -s typeguard
```

### Code Quality
```bash
# Run all linting/formatting checks
nox -s pre-commit

# Run type checking
nox -s mypy

# Run security checks
nox -s safety

# Check coverage report
nox -s coverage -- report
nox -s coverage -- html  # generates htmlcov/index.html
```

### Documentation
```bash
# Build docs
nox -s docs

# Build docs with auto-rebuild and browser
DOCS_REBUILD=true nox -s docs
```

### Running the Server
```bash
# Run the MAC server (default port 5000)
poetry run mac-server

# Run with debug mode
poetry run mac-server --debug

# Run with verbose logging
poetry run mac-server --verbose

# Run on custom port
poetry run mac-server --port 8080
```

### NeonGetter Tool
```bash
# Update users.json from NeonOne CRM
poetry run neongetter
```

## Architecture

### Core Components

**Application Factory Pattern**: The Quart app is created via `create_app()` in `src/dm_mac/__init__.py`. The app configuration includes:
- `MACHINES`: MachinesConfig instance managing all machine configurations
- `USERS`: UsersConfig instance managing all user data
- `SLACK_HANDLER`: Optional SlackHandler for Slack integration
- `START_TIME`: Server start timestamp for uptime tracking

**Configuration System**:
- Machines: `machines.json` (schema in `models/machine.py::CONFIG_SCHEMA`)
  - `authorizations_or`: List of authorizations, any one sufficient to operate
  - `unauthorized_warn_only`: (optional) Allow operation but log warning for unauthorized users
  - `always_enabled`: (optional) Machine always enabled without RFID authentication, displays "Always On"
  - `alias`: (optional) Human-friendly name used in Slack messages and logs instead of machine name
- Users: `users.json` (schema in `models/users.py::CONFIG_SCHEMA`)
- Machine names must match ESPHome configs and can only contain `[a-z0-9_-]`
- Machines can be looked up by either name or alias in Slack commands

**State Persistence**:
- Machine state is persisted to disk on every update using pickle
- Default location: `./machine_state/` (configurable via `MACHINE_STATE_DIR` env var)
- File locking via `filelock` ensures thread-safe state updates
- Enables server restarts without affecting running machines

### Request Flow

1. **MCU Update Request**: ESP32 POSTs to `/machine/update` with current state (RFID value, oops button, uptime, WiFi signal, temperature, optional amperage)
2. **Authentication**: Server looks up user by RFID fob code (zero-padded to 10 chars)
3. **Authorization**: Checks if user has any of the required authorizations from `machines.json::authorizations_or` list
4. **State Update**: Updates machine state, persists to disk, optionally logs to Slack
5. **Response**: Returns JSON with desired MCU outputs (relay state, LCD text, LED colors)

### Key Models

**Machine** (`models/machine.py`):
- `name`: Unique machine identifier
- `authorizations_or`: List of authorizations, any one sufficient to operate
- `unauthorized_warn_only`: If true, log warning but allow operation for unauthorized users
- `state`: MachineState instance tracking current operator, session timing, lockout status

**User** (`models/users.py`):
- `fob_codes`: List of RFID fob codes (10-digit strings)
- `account_id`: Unique account identifier
- `authorizations`: List of training/authorization field names
- `expiration_ymd`: Membership expiration in YYYY-MM-DD format

### API Endpoints

**Machine APIs** (`/machine/*`):
- `POST /machine/update`: Main endpoint for MCU state updates
- `POST /machine/lock/<machine_name>`: Lock out a machine
- `POST /machine/unlock/<machine_name>`: Unlock a machine

**Admin APIs** (`/api/*`):
- `POST /api/reload-users`: Hot-reload users.json without restart
- `GET /metrics`: Prometheus metrics endpoint

### Logging

Custom `RequestFormatter` adds request context (`remote_addr`, `url`) to all logs when available. The `AUTH` logger is used specifically for authentication/authorization decisions.

## Environment Variables

Required for NeonGetter:
- `NEON_ORG`: NeonOne organization name
- `NEON_KEY`: NeonOne API key
- `NEONGETTER_CONFIG`: Path to neon config JSON

Optional for MAC server:
- `USERS_CONFIG`: Path to users.json (default: `./users.json`)
- `MACHINES_CONFIG`: Path to machines.json (default: `./machines.json`)
- `MACHINE_STATE_DIR`: State persistence directory (default: `./machine_state`)
- `SLACK_BOT_TOKEN`: Slack Bot User OAuth Token
- `SLACK_APP_TOKEN`: Slack Socket OAuth Token
- `SLACK_SIGNING_SECRET`: Slack Signing Secret
- `SLACK_CONTROL_CHANNEL_ID`: Private admin channel ID
- `SLACK_OOPS_CHANNEL_ID`: Public channel for oops/maintenance notices

## Testing Notes

- Tests use fixtures in `tests/fixtures/` for config files
- Test environment variables are set in `noxfile.py::TEST_ENV`
- Async tests use `pytest-asyncio` with `--asyncio-mode=auto`
- Network blocking enforced via `pytest-blockage` to prevent accidental external calls
- Coverage threshold: 5% (intentionally low for early-stage project)

## Important Implementation Details

- RFID values from ESPHome have leading zeroes stripped; the server left-pads to 10 characters
- Machine state updates use both in-memory caching and disk persistence
- All machine state operations are protected by file locks to prevent race conditions
- The server uses asyncio event loop with custom exception handler
- Slack integration uses Socket Mode (bidirectional WebSocket)
- Machines can be configured with `unauthorized_warn_only: true` for training/soft-enforcement mode

## Feature Development

We have a special process for developing features. When asked to begin work on a feature, you MUST read and understand all of `docs/features/README.md` which outlines our feature development process. Once you have read and understood that document, ask the user which of the `docs/features/*.md` Features they want to begin work on; once one is chosen, begin work on the feature development process.
