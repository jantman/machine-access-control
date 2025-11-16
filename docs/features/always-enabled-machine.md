# Always-Enabled Machine

## Feature Description

Right now, Machines can be configured to accept a list of authorizations and optionally set to `unauthorized_warn_only` mode. I would like to now add another `always_enabled` boolean to the Machine configuration which, if True, causes the machine to ALWAYS be authorized/enabled unless it is Oopsed. When in this state, the display of the machine should read "Always On". Please be sure to update the Machine CONFIG_SCHEMA, the Machine model itself, the MachineState model, all other relevant code, and all relevant documentation.

Please be sure to add unit tests for this new functionality for AT LEAST the following cases:

1. A machine with `always_enabled` True always has `Always On` on its display and always has its relay output turned on, unless Oopsed.
2. A machine with `always_enabled` True exhibits the same Oops behavior as existing tests.
3. A machine with `always_enabled` True does not change state when an RFID card is inserted or removed.
4. A machine with `always_enabled` True becomes enabled immediately when it contacts the server, unless Oopsed.

## Implementation Plan

### Overview

The implementation will add a new `always_enabled` boolean configuration option to machines. When enabled, the machine will:
- Always have its relay on (unless Oopsed or Locked)
- Display "Always On" text on the LCD (unless Oopsed or Locked)
- Ignore RFID card insertions/removals (no user authentication required)
- Be immediately enabled when it first contacts the server

Key files to modify:
- `src/dm_mac/models/machine.py`: Machine model, CONFIG_SCHEMA, and MachineState logic
- `tests/models/test_machine.py`: Model tests
- `tests/views/test_machine.py`: Integration tests for `/machine/update` endpoint
- Documentation files as needed

### Milestone 1: Configuration and Model Updates

**Commit prefix:** `always-enabled - 1.1` through `always-enabled - 1.3`

#### Task 1.1: Update CONFIG_SCHEMA
- Add `always_enabled` boolean property to CONFIG_SCHEMA in `src/dm_mac/models/machine.py`
- Set as optional field with clear description
- Ensure schema validation works correctly

#### Task 1.2: Update Machine class
- Add `always_enabled: bool` attribute to Machine class `__init__` method
- Default value should be `False` for backward compatibility
- Update type hints appropriately

#### Task 1.3: Update Machine.as_dict property
- Include `always_enabled` in the dictionary returned by `as_dict` property
- Add basic model test to verify `always_enabled` appears in `as_dict` output

**Milestone completion criteria:**
- Machine model can be instantiated with `always_enabled=True`
- CONFIG_SCHEMA validates configurations with `always_enabled` field
- All existing tests still pass

### Milestone 2: State Logic Updates

**Commit prefix:** `always-enabled - 2.1` through `always-enabled - 2.3`

#### Task 2.1: Add ALWAYS_ON_DISPLAY_TEXT constant
- Add constant `ALWAYS_ON_DISPLAY_TEXT = "Always On"` to MachineState class
- Position it near other display text constants (lines 184-188)

#### Task 2.2: Update MachineState.update() for always-enabled logic
- Modify `MachineState.update()` method (currently lines 364-408)
- After handling Oops/Lockout states, check if `machine.always_enabled` is True
- If always-enabled and not Oopsed/Locked:
  - Set `self.relay_desired_state = True`
  - Set `self.display_text = self.ALWAYS_ON_DISPLAY_TEXT`
  - Skip RFID processing (return early before RFID insert/remove handlers)
- Ensure Oops and Lockout states still override always-enabled behavior

#### Task 2.3: Handle initial state for always-enabled machines
- Ensure that when an always-enabled machine first contacts the server (with no RFID), it:
  - Gets `relay_desired_state = True`
  - Gets `display_text = "Always On"`
  - Has status LED set to green (0.0, 1.0, 0.0)
- This should happen in the "no RFID change" code path

**Milestone completion criteria:**
- Always-enabled machines show "Always On" and relay=True when not Oopsed
- Always-enabled machines respect Oops and Lockout states
- RFID cards are ignored when machine is always-enabled
- All existing tests still pass

### Milestone 3: Unit Tests

**Commit prefix:** `always-enabled - 3.1` through `always-enabled - 3.4`

Add comprehensive test coverage in `tests/views/test_machine.py`:

#### Task 3.1: Test always-enabled basic behavior
- Create test class `TestAlwaysEnabledMachine`
- Test: `test_always_enabled_basic()`
  - Machine with `always_enabled: true` in config
  - POST to `/machine/update` with no RFID
  - Assert response: `relay=True`, `display="Always On"`, green LED
  - Verify state persisted to disk

#### Task 3.2: Test always-enabled with Oops
- Test: `test_always_enabled_oopsed()`
  - Machine with `always_enabled: true`
  - POST with `oops=true`
  - Assert response: `relay=False`, display=OOPS_DISPLAY_TEXT, red LED
  - POST with `oops=false` after Oops cleared
  - Assert returns to: `relay=True`, `display="Always On"`, green LED

#### Task 3.3: Test always-enabled ignores RFID
- Test: `test_always_enabled_ignores_rfid_insert()`
  - Machine with `always_enabled: true`
  - POST with RFID value (authorized user)
  - Assert response: `relay=True`, `display="Always On"` (NOT welcome message)
- Test: `test_always_enabled_ignores_rfid_remove()`
  - Machine with `always_enabled: true`, RFID already present
  - POST with empty RFID value
  - Assert response: `relay=True`, `display="Always On"` (no change)

#### Task 3.4: Test always-enabled immediate enable
- Test: `test_always_enabled_first_contact()`
  - Fresh machine state (no previous contact)
  - POST with no RFID, no Oops
  - Assert response: `relay=True`, `display="Always On"`, green LED immediately

**Milestone completion criteria:**
- All 5+ new tests pass
- Tests cover all 4 required cases from feature spec
- All existing tests still pass
- Coverage for always-enabled code paths

### Milestone 4: Acceptance Criteria

**Commit prefix:** `always-enabled - 4.1` through `always-enabled - 4.4`

#### Task 4.1: Update documentation
- Update `CLAUDE.md`: Add `always_enabled` to configuration options description
- Update `README.md` (if configuration section exists): Document `always_enabled` option
- Update `docs/source/` Sphinx docs (if applicable): Add to machine configuration reference
- Ensure documentation style matches existing docs (concise, technical)

#### Task 4.2: Verify unit test coverage
- Run `nox -s coverage -- report` to check coverage
- Ensure new code has appropriate test coverage (aim for >80% of new lines)
- Add any missing tests if gaps are identified

#### Task 4.3: Verify all nox sessions pass
- Run `nox -s tests` - must be 100% passing
- Run `nox -s mypy` - must pass with no errors
- Run `nox -s pre-commit` - must pass all checks
- Run `nox -s safety` - must pass
- Fix any issues that arise

#### Task 4.4: Move feature to completed
- Move `docs/features/always-enabled-machine.md` to `docs/features/completed/always-enabled-machine.md`
- Commit with message: "always-enabled - 4.4: feature complete"

**Milestone completion criteria:**
- All documentation updated
- All nox sessions passing
- Feature file moved to completed/
- Feature fully implemented and validated

## Implementation Status

**Status:** Planning complete, awaiting approval to begin implementation

**Current Milestone:** None (planning phase)

**Completed Milestones:** None
