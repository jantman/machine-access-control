# Quickstart: Oops/Lockout Override Login

**Feature**: 001-oops-override | **Date**: 2026-03-16

## What This Feature Does

Allows designated repair members to activate machines that are oopsed or locked out without clearing those states. When the repair member removes their card, the machine returns to oopsed/locked state.

## Files to Modify

### Core Logic (in order of implementation)

1. **src/dm_mac/models/users.py** — Add `oops_override: bool` field to User class and CONFIG_SCHEMA
2. **src/dm_mac/neongetter.py** — Add `oops_override_field` config option; pull override flag from Neon
3. **src/dm_mac/models/machine.py** — Add `is_override_login` to MachineState; modify `_handle_rfid_insert()`, `_handle_rfid_remove()`, `_handle_reboot()`, `_save_cache()`
4. **src/dm_mac/slack_handler.py** — Add `log_override_login()` method
5. **src/dm_mac/views/prometheus.py** — Add `machine_override_login_state` metric

### Test Files

6. **tests/fixtures/users.json** — Add `oops_override` field to test users (one user with `true`)
7. **tests/models/test_users.py** — Schema validation tests with new field
8. **tests/models/test_machine_state.py** — Unit tests for override state transitions
9. **tests/views/test_machine.py** — Integration tests for full override login flow
10. **tests/views/test_prometheus.py** — Metric exposure tests
11. **tests/test_neongetter.py** — Config schema and field extraction tests
12. **tests/test_slack_handler.py** — Override notification tests

### Documentation

13. **docs/source/configuration.rst** — Document `oops_override` in users.json schema
14. **docs/source/neon.rst** — Document `oops_override_field` config option and static fob support
15. **docs/source/slack.rst** — Document override notification behavior
16. **docs/source/admin.rst** — Add override metric to Prometheus docs
17. **CLAUDE.md** — Update Architecture section if needed

## Key Implementation Pattern

The override login intercepts the normal oops/lockout rejection flow in `_handle_rfid_insert()`:

```
Normal flow:
  RFID insert → user lookup → oopsed? → REJECT (early return)
                             → locked?  → REJECT (early return)
                             → auth check → grant/deny

Override flow:
  RFID insert → user lookup → oopsed/locked? → user.oops_override?
                                                → YES: activate with override
                                                → NO: REJECT (existing behavior)
```

On card removal, `_handle_rfid_remove()` checks `is_override_login` and restores the oopsed/locked display state instead of resetting to default.

## Quick Validation

```bash
# Run all tests
nox -s tests

# Run just machine state tests (fastest feedback loop)
nox -s tests -- tests/models/test_machine_state.py

# Run integration tests for override
nox -s tests -- tests/views/test_machine.py

# Full quality gates
nox -s pre-commit
nox -s mypy
```
