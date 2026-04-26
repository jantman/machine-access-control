# Implementation Plan: Second Relay Support

**Branch**: `002-second-relay-support` | **Date**: 2026-04-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-second-relay-support/spec.md`

## Summary

Add an optional `second_relay` block to each machine's entry in `machines.json` that gates an additional output relay (driven by GPIO14, V1 connector pin 6) on a separate authorization. The second relay only energizes when (a) the primary relay is already energized for the current operator AND (b) the operator additionally holds at least one of the `second_relay.authorizations_or` (with `unauthorized_warn_only` and `always_enabled` honored on the second relay independently of the primary). The LCD is intentionally unchanged; observability lands in structured logs, Slack messages, and Prometheus metrics. The MCU↔server JSON protocol gains additive optional fields so existing firmware/server combinations keep working.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Quart (async Flask), slack-bolt, prometheus-client, jsonschema, filelock, humanize, pydantic (existing)
**Storage**: JSON config files (`machines.json`, `users.json`); per-machine pickle state under `MACHINE_STATE_DIR` (default `./machine_state/`) protected by `filelock`
**Testing**: pytest, pytest-asyncio, pytest-blockage, fixtures under `tests/fixtures/`; nox sessions `tests`, `typeguard`, `mypy`, `pre-commit`, `safety`
**Target Platform**: Linux server (server-side); ESP32 running ESPHome 2025.11.2 (firmware side)
**Project Type**: Single-project Python web service plus YAML firmware configs
**Performance Goals**: No new latency budget — second relay decision is computed in the same `/machine/update` request path as the primary decision (sub-100ms typical)
**Constraints**:
  - Backward-compatible `/machine/update` request and response schemas — new fields are additive and optional (Constitution §IV)
  - Pickle state files MUST load when the new `second_*` keys are absent (older state) AND when present (newer state) (Constitution §IV)
  - Fail-closed: if the second-relay authorization decision raises, the response MUST set the second relay state to `false` (Constitution §I)
  - LCD content/strings MUST NOT change for any operator on any machine (FR-009)
**Scale/Scope**: ~50 machines in production, ~500 users; expect <10 machines to adopt `second_relay` in the first year

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Safety & Reliability | ✅ Pass | Second relay defaults to off whenever primary is off, on lockout, on oops, on server-restart-without-state, and whenever the second-relay authorization check returns false or raises. New tests will explicitly cover fail-closed behavior. |
| II. Testing Discipline | ✅ Pass | Plan adds fixtures for second-relay machines under `tests/fixtures/`; new unit and integration tests for the authorization decision, MCU update flow, Slack/log/metric paths. No network calls. |
| III. Simplicity & YAGNI | ✅ Pass | We add exactly one optional schema block (`second_relay`) using the same options as the existing root config, one new internal entity (`SecondRelayConfig`), four new state fields on `MachineState`, two new optional fields each on the MCU request and response, and a small set of new metrics. No new dependencies, no new abstractions or extension points. |
| IV. Backward Compatibility | ✅ Pass | `machines.json` change is additive; absence of `second_relay` reproduces today's behavior byte-for-byte. MCU request/response gain optional additive fields with safe defaults. Pickle state load is tolerant of missing/extra fields (already true; we extend by setting defaults in `__init__` and keeping `_load_from_cache` `hasattr` guard). |
| V. Documentation | ✅ Pass | `CLAUDE.md`, `README.rst`, `docs/source/configuration.rst`, `docs/source/http-api.rst`, `docs/source/slack.rst`, `docs/source/grafana-dashboard.md`, and the ESPHome configs under `esphome-configs/2025.11.2/` will all be updated as part of Phase 2 implementation tasks. Quickstart in `specs/002-second-relay-support/quickstart.md` documents the admin workflow. |

**Result**: PASS. No complexity violations to track.

## Project Structure

### Documentation (this feature)

```text
specs/002-second-relay-support/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (/speckit.specify)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── machines-config-schema.md     # JSON schema additions for second_relay
│   └── mcu-update-protocol.md        # MCU /machine/update request/response additions
├── checklists/
│   └── requirements.md  # Spec quality checklist (already created)
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this command)
```

### Source Code (repository root)

```text
src/dm_mac/
├── models/
│   ├── machine.py                # EXTEND: CONFIG_SCHEMA gets second_relay block;
│   │                             # Machine grows .second_relay: Optional[SecondRelayConfig];
│   │                             # MachineState grows second_relay_desired_state, second_current_user,
│   │                             # second_authorization_status; helpers _user_is_second_authorized,
│   │                             # _resolve_second_relay; pickle save/load adds new fields
│   ├── api_schemas.py            # EXTEND: MachineUpdateRequest gains optional relay2 reporting;
│   │                             # MachineUpdateResponse gains optional second_relay field
│   └── users.py                  # NO CHANGE
├── views/
│   ├── machine.py                # NO CHANGE in routing; works through Machine.update()
│   └── prometheus.py             # EXTEND: add machine_second_relay_state,
│                                 # machine_second_relay_configured,
│                                 # machine_second_relay_unauth_warn_only,
│                                 # machine_second_relay_always_enabled metrics
├── slack_handler.py              # EXTEND: status renderer includes second relay info;
│                                 # admin_log/oops/lock messages name accessory by second_relay.alias
├── __init__.py                   # NO CHANGE
└── ...

tests/
├── fixtures/
│   ├── machines.json             # ADD second-relay machine entries to existing fixture
│   └── machines-second-relay.json # NEW: dedicated fixture for second-relay edge cases
└── test_*.py                     # ADD unit tests for SecondRelayConfig validation,
                                  # second-auth decision, MCU update flow, Slack/log/metrics paths

esphome-configs/2025.11.2/
└── no-current-input.yaml         # EXTEND: add output relay on GPIO14 (relay2_output);
                                  # POST request unchanged (or adds optional relay2 field);
                                  # response handler reads optional `second_relay` field

docs/source/
├── configuration.rst             # Document second_relay block in machines.json
├── http-api.rst                  # Document optional new request/response fields
├── slack.rst                     # Document second-relay phrasing in Slack messages
└── grafana-dashboard.md          # Note new Prometheus metrics

CLAUDE.md                          # Add second_relay to the Configuration System section
README.rst                         # No change expected unless we add a feature blurb
```

**Structure Decision**: Single-project layout (Option 1). All server-side code lives under `src/dm_mac/`, mirrored by `tests/`. Firmware lives under `esphome-configs/2025.11.2/` and is updated in lockstep. No new top-level packages; the feature lands as additive changes to existing modules.

## Complexity Tracking

> Constitution Check passed with no violations. No entries here.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
