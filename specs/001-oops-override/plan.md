# Implementation Plan: Oops/Lockout Override Login

**Branch**: `001-oops-override` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-oops-override/spec.md`

## Summary

Designated repair members need to activate oopsed or locked-out machines without clearing those states. The approach adds an `oops_override` boolean to the User model (sourced from a configurable NeonOne field), and an `is_override_login` flag to MachineState. When an override-authorized user inserts their RFID on an oopsed/locked machine, the system activates the relay while preserving the underlying oops/lockout flags. On card removal, the machine returns to its previous oopsed/locked state. Override logins post to the Slack control channel only (not oops channel) and are exposed via a new Prometheus metric.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Quart (async Flask), slack-bolt, prometheus-client, jsonschema, filelock, humanize
**Storage**: JSON config files (users.json, machines.json), pickle state files with file locking
**Testing**: pytest with pytest-asyncio (auto mode), pytest-blockage (no network), freeze_time, responses library for HTTP mocking
**Target Platform**: Linux server (Raspberry Pi / Docker)
**Project Type**: Web service (async HTTP API for ESP32 MCUs)
**Performance Goals**: <2 second response time for MCU update requests
**Constraints**: Must not break existing MCU protocol; must be backward-compatible with existing config files and pickled state
**Scale/Scope**: ~5-10 machines, ~50-200 users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety & Reliability | PASS | Override activates relay only while card is present; fail-safe default (relay off) preserved. Card removal restores oops/lockout state. No new failure modes introduced. |
| II. Testing Discipline | PASS | Plan includes comprehensive unit and integration tests for all override scenarios, edge cases, and Slack notification behavior. Uses existing fixtures pattern. |
| III. Simplicity & YAGNI | PASS | Minimal new fields (one boolean per user, one boolean + method per machine state). No new abstractions. Direct, linear code additions to existing handlers. |
| IV. Backward Compatibility | PASS | `oops_override` is optional in users.json (defaults to false). Pickle `_load_from_cache` uses `hasattr` so missing field is handled. No MCU protocol changes. `oops_override_field` is optional in neongetter config. |
| V. Documentation | PASS | Plan includes updates to admin.rst (metrics), configuration.rst (schemas), slack.rst (notifications), neon.rst (override field), and CLAUDE.md. |

**Post-Phase 1 Re-check**: All gates still pass. No new abstractions, dependencies, or breaking changes introduced in the design.

## Project Structure

### Documentation (this feature)

```text
specs/001-oops-override/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── machine-update-response.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/dm_mac/
├── models/
│   ├── machine.py       # MachineState: add is_override_login, modify _handle_rfid_insert/_remove
│   └── users.py         # User: add oops_override field; CONFIG_SCHEMA update
├── views/
│   ├── machine.py       # No changes needed (delegates to Machine.update)
│   └── prometheus.py    # Add machine_override_login_state metric
├── slack_handler.py     # Add log_override_login() method
└── neongetter.py        # Add oops_override_field config; pull override flag per user

tests/
├── fixtures/
│   ├── users.json                  # Add oops_override field to test users
│   └── test_neongetter/            # Update fixtures for override field
├── models/
│   ├── test_machine_state.py       # Unit tests for override state transitions
│   └── test_users.py               # Schema validation tests with oops_override
├── views/
│   ├── test_machine.py             # Integration tests for override login flow
│   └── test_prometheus.py          # Metric exposure tests
├── test_neongetter.py              # Config schema and field extraction tests
└── test_slack_handler.py           # Override notification tests

docs/source/
├── admin.rst            # Add override metric to Prometheus docs
├── configuration.rst    # Document oops_override in users.json schema
├── slack.rst            # Document override notification behavior
└── neon.rst             # Document oops_override_field config option
```

**Structure Decision**: All changes fit within the existing project structure. No new files or directories are needed in `src/` -- only modifications to existing modules. The `contracts/` directory is new but only for planning documentation.

## Complexity Tracking

> No violations to justify. All changes are minimal additions to existing modules.
