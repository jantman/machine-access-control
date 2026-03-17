# Tasks: Oops/Lockout Override Login

**Input**: Design documents from `/specs/001-oops-override/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included -- the feature spec explicitly requires "comprehensive test updates."

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: User model changes and test fixture updates that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T001 Add `oops_override` boolean field to User class `__init__()`, `as_dict` property, and update CONFIG_SCHEMA to include optional `oops_override` boolean in `src/dm_mac/models/users.py`
- [ ] T002 Add `oops_override` field to test user fixtures -- set `true` for one existing user (e.g., Jason Antman / account_id "4") and `false` or omit for others in `tests/fixtures/users.json`
- [ ] T003 Add unit tests for User model with `oops_override` field: test schema validation accepts with and without field, test User instantiation with `oops_override=True` and default `False`, test `as_dict` includes field in `tests/models/test_users.py`

**Checkpoint**: User model accepts `oops_override` field; test fixtures updated; all existing tests still pass

---

## Phase 2: User Stories 1 & 2 - Override Login on Oopsed and Locked-Out Machines (Priority: P1) MVP

**Goal**: Override-authorized users can activate oopsed or locked-out machines without clearing those states. Card removal restores the previous oopsed/locked state.

**Independent Test**: Insert override user's RFID on oopsed machine -> relay activates, display shows "OVERRIDE BY [name]", oops state preserved. Remove card -> machine returns to oopsed state. Repeat for locked-out machine.

**Note**: US1 (oopsed) and US2 (locked-out) are combined because they modify the exact same code paths in `_handle_rfid_insert()` and `_handle_rfid_remove()`.

### Tests for User Stories 1 & 2

- [ ] T004 [P] [US1] Add unit tests for override login on oopsed machine in `tests/models/test_machine_state.py`: test `_handle_rfid_insert` with override user on oopsed machine sets `is_override_login=True`, `relay_desired_state=True`, display="OVERRIDE BY\n{name}", `is_oopsed` remains `True`
- [ ] T005 [P] [US2] Add unit tests for override login on locked-out machine in `tests/models/test_machine_state.py`: test `_handle_rfid_insert` with override user on locked-out machine sets `is_override_login=True`, `relay_desired_state=True`, display="OVERRIDE BY\n{name}", `is_locked_out` remains `True`
- [ ] T006 [P] [US1] Add unit tests for override card removal on oopsed machine in `tests/models/test_machine_state.py`: test `_handle_rfid_remove` when `is_override_login=True` and `is_oopsed=True` restores oops display/LED, clears override flag, turns off relay
- [ ] T007 [P] [US2] Add unit tests for override card removal on locked-out machine in `tests/models/test_machine_state.py`: test `_handle_rfid_remove` when `is_override_login=True` and `is_locked_out=True` restores lockout display/LED, clears override flag, turns off relay
- [ ] T008 [P] [US1] Add unit test for normal user on oopsed machine (no override) in `tests/models/test_machine_state.py`: verify existing behavior unchanged -- login is rejected, oops state remains
- [ ] T009 [P] [US1] Add unit test for override user on non-oopsed/non-locked machine in `tests/models/test_machine_state.py`: verify normal login behavior occurs (override has no effect)
- [ ] T010 [P] [US1] Add unit test for override on machine that is both oopsed AND locked out in `tests/models/test_machine_state.py`: verify both states preserved during override and restored on card removal
- [ ] T011 [P] [US1] Add unit test for reboot during override login in `tests/models/test_machine_state.py`: verify `_handle_reboot` clears `is_override_login`, oops/lockout state preserved
- [ ] T012 [P] [US1] Add unit test for `_save_cache` and `_load_from_cache` with `is_override_login` field in `tests/models/test_machine_state.py`: verify state persistence and backward-compatible loading from old pickle without field
- [ ] T013 [P] [US1] Add integration tests for override login via `/machine/update` endpoint in `tests/views/test_machine.py`: test full request/response cycle for override insert on oopsed machine, verify response has `relay=True`, `oops_led=True`, display="OVERRIDE BY\n{name}"
- [ ] T014 [P] [US2] Add integration tests for override login via `/machine/update` endpoint on locked-out machine in `tests/views/test_machine.py`: test full request/response cycle for override insert on locked-out machine
- [ ] T015 [P] [US1] Add integration test for override card removal via `/machine/update` in `tests/views/test_machine.py`: test full cycle -- insert override RFID on oopsed machine, then remove RFID, verify machine returns to oopsed state
- [ ] T016 [P] [US1] Add integration test verifying admin clearing oops during active override in `tests/views/test_machine.py`: override login active, admin clears oops via API, card removed, machine returns to normal idle state
- [ ] T017 [P] [US1] Add integration test for admin oopsing machine during active override in `tests/views/test_machine.py`: override login active, admin oopses via API, verify relay turns off immediately; then card removed, verify machine stays in oopsed state and `is_override_login` is cleared

### Implementation for User Stories 1 & 2

- [ ] T018 [US1] Add `is_override_login: bool = False` field to `MachineState.__init__()` in `src/dm_mac/models/machine.py`
- [ ] T019 [US1] Add `is_override_login` to `_save_cache()` data dict in `src/dm_mac/models/machine.py`
- [ ] T020 [US1] Modify `_handle_rfid_insert()` in `src/dm_mac/models/machine.py`: before the oopsed/locked-out early-return blocks, check if user has `oops_override=True` and machine is oopsed or locked out. If so, set `is_override_login=True`, `relay_desired_state=True`, `current_user=user`, `display_text=f"OVERRIDE BY\n{user.preferred_name}"`, green LED, and return (skip oops/lockout rejection). If user has override but machine is NOT oopsed/locked, fall through to normal login flow.
- [ ] T021 [US1] Modify `_handle_rfid_remove()` in `src/dm_mac/models/machine.py`: if `is_override_login` is True, clear `is_override_login=False`, turn off relay, and restore display/LED based on current `is_oopsed`/`is_locked_out` flags (oops display if oopsed, lockout display if locked out, default display if neither). Skip normal display reset path.
- [ ] T022 [US1] Modify `_handle_reboot()` in `src/dm_mac/models/machine.py`: add `self.is_override_login = False` to reset override state on reboot

**Checkpoint**: Override login works for both oopsed and locked-out machines. Card removal restores previous state. All existing tests still pass.

---

## Phase 3: User Story 3 - Slack Notification for Override Login (Priority: P2)

**Goal**: Override logins post to Slack control channel only (not oops channel). No un-oops/unlock notifications on card removal from override session.

**Independent Test**: Perform override login, verify Slack control channel receives notification, verify oops channel receives nothing.

### Tests for User Story 3

- [ ] T023 [P] [US3] Add unit tests for `log_override_login()` method in `tests/test_slack_handler.py`: verify message posted to `control_channel_id` only, not `oops_channel_id`, with correct message format including machine name and user name
- [ ] T024 [P] [US3] Add integration test in `tests/views/test_machine.py` verifying Slack mock calls during override login: `log_override_login` called on insert, `admin_log` called on remove, no `log_unoops`/`log_unlock` calls at any point

### Implementation for User Story 3

- [ ] T025 [US3] Add `log_override_login(machine, user_name)` method to SlackHandler in `src/dm_mac/slack_handler.py`: post "Override login on {display_name} by {user_name}." to `control_channel_id` only, using fire-and-forget `create_task()` pattern
- [ ] T026 [US3] Wire up Slack notifications in `_handle_rfid_insert()` override path in `src/dm_mac/models/machine.py`: call `slack.log_override_login()` when override login occurs
- [ ] T027 [US3] Update `_handle_rfid_remove()` override path in `src/dm_mac/models/machine.py`: call `slack.admin_log()` with "(override session)" suffix in logout message, ensure no `log_unoops`/`log_unlock` calls

**Checkpoint**: Override logins generate control-channel-only Slack notifications. Card removal logs session with override indication. No oops channel notifications.

---

## Phase 4: User Story 4 - NeonOne CRM Integration (Priority: P2)

**Goal**: Neongetter pulls override authorization from a configurable Neon checkbox field and includes it in users.json output.

**Independent Test**: Configure neongetter with override field, run against test fixtures, verify users.json includes `oops_override` for appropriate users.

### Tests for User Story 4

- [ ] T028 [P] [US4] Add unit tests for neongetter CONFIG_SCHEMA with `oops_override_field` in `tests/test_neongetter.py`: test schema validates with and without the optional field, test default value behavior
- [ ] T029 [P] [US4] Add unit tests for neongetter `fields_to_get()` with override field in `tests/test_neongetter.py`: verify override checkbox field ID is included in retrieval list when configured
- [ ] T030 [P] [US4] Add unit tests for neongetter `run()` with override field in `tests/test_neongetter.py`: verify `oops_override=True` set for users with matching field value, `oops_override=False` for others
- [ ] T031 [P] [US4] Add unit test for static_fobs with `oops_override` field in `tests/test_neongetter.py`: verify static users can have `oops_override` set, defaults to `False` when omitted

### Implementation for User Story 4

- [ ] T032 [US4] Add `oops_override_field` as optional string property (default `"OOPS_OVERRIDE"`) to neongetter CONFIG_SCHEMA in `src/dm_mac/neongetter.py`
- [ ] T033 [US4] Update `fields_to_get()` in `src/dm_mac/neongetter.py`: if `oops_override_field` is in config, find the matching Neon checkbox custom field and add its ID to the retrieval list
- [ ] T034 [US4] Update `run()` in `src/dm_mac/neongetter.py`: for each user, check if the override field value equals `authorized_field_value` and set `oops_override: True/False` accordingly in the output user dict
- [ ] T035 [US4] Update static_fobs processing in `run()` in `src/dm_mac/neongetter.py`: read optional `oops_override` boolean from each static user entry, default to `False`
- [ ] T036 [US4] Add optional `oops_override` boolean to static_fobs schema within CONFIG_SCHEMA in `src/dm_mac/neongetter.py`
- [ ] T037 [US4] Update neongetter test fixtures in `tests/fixtures/test_neongetter/`: add `OOPS_OVERRIDE` checkbox field to recorded API response YAML, add `oops_override_field` to test neon.config.json fixture

**Checkpoint**: Neongetter produces users.json with `oops_override` field populated from Neon. Static fobs support override. Config schema accepts `oops_override_field`.

---

## Phase 5: User Story 5 - Prometheus Metrics (Priority: P3)

**Goal**: Override login state exposed as a per-machine Prometheus metric.

**Independent Test**: Perform override login, scrape `/metrics`, verify `machine_override_login_state` is 1 for the overridden machine.

### Tests for User Story 5

- [ ] T038 [P] [US5] Add test for `machine_override_login_state` metric in `tests/views/test_prometheus.py`: verify metric present for all machines, reads 0 by default, reads 1 when `is_override_login=True`

### Implementation for User Story 5

- [ ] T039 [US5] Add `machine_override_login_state` gauge metric to `PromCustomCollector.collect()` in `src/dm_mac/views/prometheus.py`: create `LabeledGaugeMetricFamily` with labels `machine_name` and `display_name`, value from `m.state.is_override_login`

**Checkpoint**: Override login state visible in Prometheus metrics endpoint.

---

## Phase 6: User Story 6 - Documentation Updates (Priority: P2)

**Goal**: All affected documentation updated for administrators, users, and developers.

**Independent Test**: Review each doc page for completeness and accuracy.

- [ ] T040 [P] [US6] Update `docs/source/admin.rst`: add `machine_override_login_state` metric to the Prometheus metrics example output, add description of override login state to the monitoring section
- [ ] T041 [P] [US6] Update `docs/source/configuration.rst`: document that users.json schema now includes optional `oops_override` boolean field; note backward compatibility
- [ ] T042 [P] [US6] Update `docs/source/slack.rst`: document that override logins generate control-channel-only notifications, describe the notification message format, note that no oops channel messages are sent for override events
- [ ] T043 [P] [US6] Update `docs/source/neon.rst`: document `oops_override_field` config option with default value "OOPS_OVERRIDE", explain how the checkbox field works, document `oops_override` support in static_fobs entries

**Checkpoint**: All documentation pages accurately reflect the override login feature.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, cleanup, and final validation

- [ ] T044 Run `nox -s pre-commit` and fix any linting/formatting issues across all modified files
- [ ] T045 Run `nox -s mypy` and fix any type checking errors in modified files
- [ ] T046 Run `nox -s tests` and verify all tests pass with no failures
- [ ] T047 Run `nox -s coverage -- report` and verify coverage has not decreased
- [ ] T048 Run `nox -s safety` and verify no new high/critical vulnerabilities in dependencies
- [ ] T049 Run `nox -s docs` and verify documentation builds without warnings

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies - can start immediately. BLOCKS all user stories.
- **US1+US2 (Phase 2)**: Depends on Phase 1 completion (User model with `oops_override` field)
- **US3 (Phase 3)**: Depends on Phase 2 (override login logic must exist to wire up notifications)
- **US4 (Phase 4)**: Depends on Phase 1 only (User model schema). Can run in parallel with Phase 2.
- **US5 (Phase 5)**: Depends on Phase 2 (needs `is_override_login` field on MachineState)
- **US6 (Phase 6)**: Depends on Phases 2-5 (must document implemented behavior)
- **Polish (Phase 7)**: Depends on all previous phases

### User Story Dependencies

- **US1+US2 (P1)**: Depends on Foundational only. MVP.
- **US3 (P2)**: Depends on US1+US2 (adds Slack calls to override code paths)
- **US4 (P2)**: Independent of US1+US2. Can be implemented in parallel. Only depends on Foundational.
- **US5 (P3)**: Depends on US1+US2 (reads `is_override_login` from MachineState)
- **US6 (P2)**: Depends on all other stories being complete

### Within Each User Story

- Tests written FIRST, verified to FAIL before implementation
- Model/schema changes before logic changes
- Core implementation before integration/wiring
- Story complete and passing before moving to next priority

### Parallel Opportunities

- T004-T017: All US1/US2 test tasks can run in parallel (different test classes/methods)
- T023-T024: US3 test tasks can run in parallel
- T028-T031: US4 test tasks can run in parallel
- T040-T043: All documentation tasks can run in parallel (different files)
- Phase 4 (US4/NeonGetter) can run in parallel with Phase 2 (US1+US2/MachineState) since they modify different files

---

## Parallel Example: User Stories 1 & 2

```bash
# Launch all unit tests in parallel (different test methods, same file):
Task: T004 - Override insert on oopsed machine test
Task: T005 - Override insert on locked-out machine test
Task: T006 - Override remove on oopsed machine test
Task: T007 - Override remove on locked-out machine test
Task: T008 - Normal user on oopsed machine test
Task: T009 - Override user on normal machine test
Task: T010 - Both oopsed and locked out test
Task: T011 - Reboot during override test
Task: T012 - State persistence test

# Launch integration tests in parallel:
Task: T013 - Override login endpoint test (oopsed)
Task: T014 - Override login endpoint test (locked-out)
Task: T015 - Override card removal endpoint test
Task: T016 - Admin clear during override test
Task: T017 - Admin oops during override test
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Foundational (User model + fixtures)
2. Complete Phase 2: US1+US2 (core override login logic)
3. **STOP and VALIDATE**: Override login works for oopsed and locked-out machines
4. Run `nox -s tests` to verify all tests pass

### Incremental Delivery

1. Phase 1 (Foundational) -> User model ready
2. Phase 2 (US1+US2) -> Core override works (MVP!)
3. Phase 3 (US3) -> Slack notifications added
4. Phase 4 (US4) -> NeonGetter integration (can run alongside Phase 2)
5. Phase 5 (US5) -> Prometheus metrics
6. Phase 6 (US6) -> Documentation complete
7. Phase 7 (Polish) -> Quality gates pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 are combined into a single phase since they modify identical code paths
- US4 (NeonGetter) is the only story that can truly run in parallel with US1+US2
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
