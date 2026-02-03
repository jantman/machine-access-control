# Always Enabled Config Change Bug

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Earlier today we had a number of machines with `always_enabled` set to true in the `machines.json` configuration, which resulted in them always having their LED green and relay enabled. I changed the `machines.json` config to remove `always_enabled` (default false) to enable proper RFID-based authorization on these machines, but they stayed in the enabled state until an RFID card change was made. We need to fix this behavior, including adding unit tests to ensure we don't have a regression.

## Root Cause Analysis

The bug is in `src/dm_mac/models/machine.py` in the `MachineState.update()` method (lines 425-483).

When `always_enabled` is true, the update method sets the machine to enabled state and saves it to the pickle cache:
```python
if (
    self.machine.always_enabled
    and not self.is_oopsed
    and not self.is_locked_out
):
    self.relay_desired_state = True
    self.display_text = self.ALWAYS_ON_DISPLAY_TEXT
    ...
elif rfid_value != self.rfid_value:
    # Handle RFID changes
```

When `always_enabled` is changed to false in the config:
1. The `Machine.always_enabled` attribute becomes false
2. On subsequent updates, the first `if` branch is skipped
3. If no RFID change occurs, the `elif` branch is also skipped
4. The cached state (relay on, "Always On" display, green LED) persists incorrectly

## Implementation Plan

### Milestone 1: Fix the Bug

**Prefix:** `AEC-1`

**Task 1.1:** Add logic to reset machine state when `always_enabled` is false but machine has stale enabled state

In `MachineState.update()`, after the existing `always_enabled` and RFID handling blocks, add a final check:
- If `always_enabled` is false AND no RFID is present AND not oopsed AND not locked AND relay is currently on
- This indicates stale state from a previously always-enabled machine
- Reset to default disabled state (relay off, default display text, LED off)

The logic should be added after line 481 (after the `self.last_update = time()` in the elif block), before `self._save_cache()`.

**Task 1.2:** Add unit test for config change from always_enabled to not always_enabled

Create a new test in `tests/views/test_machine_always_enabled.py` that:
1. Sets up a machine with `always_enabled: true`
2. Sends an update to establish the enabled state
3. Modifies the machine config to set `always_enabled: false`
4. Sends another update with no RFID change
5. Verifies the machine returns to default disabled state

### Milestone 2: Acceptance Criteria

**Prefix:** `AEC-2`

**Task 2.1:** Verify all tests pass with `nox -s tests`

**Task 2.2:** Verify all nox sessions pass (linting, type checking, etc.)

**Task 2.3:** Update documentation if needed (CLAUDE.md, README.md, docs/)

**Task 2.4:** Move feature document to `docs/features/completed/`

## Progress

- [x] Milestone 1: Fix the Bug
  - [x] Task 1.1: Add state reset logic (commit 190b026)
  - [x] Task 1.2: Add unit test (commit 6976e77)
- [x] Milestone 2: Acceptance Criteria
  - [x] Task 2.1: Verify all tests pass (194 tests, 99% coverage)
  - [x] Task 2.2: Verify all nox sessions pass (7 sessions)
  - [x] Task 2.3: Update documentation (no changes needed - bug fix only)
  - [x] Task 2.4: Move feature document
