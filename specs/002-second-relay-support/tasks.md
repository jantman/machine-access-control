---

description: "Task list for Second Relay Support"
---

# Tasks: Second Relay Support

**Input**: Design documents from `/specs/002-second-relay-support/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are REQUIRED (Constitution §II Testing Discipline). Test tasks are included in every user-story phase and parametrized to cover the authorization decision matrix per `research.md` R9.

**Organization**: Tasks are grouped by user story (US1, US2, US3, US4) so each is independently implementable and testable. The user-story order in spec.md is US1, US2, US3, US4 — we process them in that order here, with US3 (P2) deferred after the three P1 stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1, US2, US3, US4) — only on user-story phase tasks
- All paths absolute or relative to `/home/jantman/GIT/machine-access-control/`

## Path Conventions

Single-project Python web service plus YAML firmware configs (per plan.md). Server code under `src/dm_mac/`, tests under `tests/`, firmware under `esphome-configs/2025.11.2/`, docs under `docs/source/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the test fixtures that every user-story phase will reuse. No production code changes.

- [ ] T001 [P] Create fixture `tests/fixtures/machines-second-relay.json` containing one single-relay machine, one machine with `second_relay` requiring distinct authorizations, one machine with `second_relay.unauthorized_warn_only=true`, one machine with `second_relay.always_enabled=true`, and one machine with `second_relay.alias` set; cover the cases the contract docs in `specs/002-second-relay-support/contracts/machines-config-schema.md` enumerate.
- [ ] T002 [P] Extend `tests/fixtures/users.json` (or add `tests/fixtures/users-second-relay.json` if simpler) with three users: one with primary auth only, one with secondary auth only (negative-case operator), one with both. Reuse existing user fixture conventions; do NOT modify existing user records that other tests depend on.
- [ ] T003 [P] Capture a pre-feature `/machine/update` golden response for a representative single-relay machine in `tests/fixtures/golden-single-relay-response.json` for use by the US4 byte-identity regression tests. Run the existing test suite once on `main` to extract canonical values, then commit the fixture.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema, model, persistence, and protocol scaffolding required by every user story. The auth-decision function lives here so all user-story phases can test it from different angles.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [ ] T004 Extend `CONFIG_SCHEMA` in `src/dm_mac/models/machine.py` to accept an optional `second_relay` property whose object schema mirrors the per-machine option subset (`authorizations_or` required, `unauthorized_warn_only`/`always_enabled`/`alias` optional) and forbids nested `second_relay` plus all unknown fields (`additionalProperties: false`, `minItems: 1` on `authorizations_or`). Schema must match `specs/002-second-relay-support/contracts/machines-config-schema.md` exactly.
- [ ] T005 Add a `SecondRelayConfig` class to `src/dm_mac/models/machine.py` (above the existing `Machine` class) with fields `authorizations_or: List[str]`, `unauthorized_warn_only: bool = False`, `always_enabled: bool = False`, `alias: Optional[str] = None`, plus an `as_dict` property mirroring `Machine.as_dict`'s style.
- [ ] T006 Extend `Machine.__init__` in `src/dm_mac/models/machine.py` to accept and store `second_relay: Optional[SecondRelayConfig] = None`; update `MachinesConfig._load_and_validate_config` flow so the dict from JSON is converted to a `SecondRelayConfig` instance when present (and passed to `Machine(**mdict)` accordingly). Update `Machine.as_dict` to include `"second_relay": self.second_relay.as_dict` when set, omit the key entirely when `None` (preserves byte-identical output for single-relay machines).
- [ ] T007 [P] Extend `MachineUpdateResponse` in `src/dm_mac/models/api_schemas.py` to include `second_relay: bool = Field(default=False, description="Desired state of the second relay (V1 hardware GPIO14). Always emitted; firmware that does not know about this field ignores it.")`.
- [ ] T008 [P] Extend `MachineUpdateRequest` in `src/dm_mac/models/api_schemas.py` to include `second_relay_state: Optional[bool] = Field(default=None, description="Actual current state of the second relay as known to the MCU; reported for observability only and never used in authorization decisions. Older firmware omits this field.")`.
- [ ] T009 Extend `MachineState.__init__` in `src/dm_mac/models/machine.py` to add `self.second_relay_desired_state: bool = False` and `self.second_relay_authorization: Optional[str] = None` with safe defaults BEFORE the `_load_from_cache()` call so older pickle files load correctly.
- [ ] T010 Extend `MachineState._save_cache` in `src/dm_mac/models/machine.py` to add `second_relay_desired_state` and `second_relay_authorization` to the persisted dict. `_load_from_cache` does NOT need to change — its existing `hasattr` guard already tolerates missing-and-extra keys.
- [ ] T011 Add a private `_user_is_second_authorized(self, user: User, slack: Optional["SlackHandler"]) -> bool` method on `MachineState` in `src/dm_mac/models/machine.py` that mirrors the structure of the existing `_user_is_authorized` but reads `self.machine.second_relay.authorizations_or` and respects `self.machine.second_relay.unauthorized_warn_only`. Defensively returns `False` if `self.machine.second_relay is None`.
- [ ] T012 Add a private `async def _resolve_second_relay(self, slack: Optional["SlackHandler"]) -> None` method on `MachineState` in `src/dm_mac/models/machine.py` that sets `self.second_relay_desired_state` and `self.second_relay_authorization` per the decision tree in `specs/002-second-relay-support/data-model.md` (no second_relay → False/None; primary off → False/None; `always_enabled` → True/"always_enabled"; granted → True/"granted"; warn → True/"warn"; denied → False/"denied"). Wrap the body in `try/except` so any unexpected error fails closed (`False`/`"denied"`).
- [ ] T013 Wire `_resolve_second_relay` into `MachineState.update`: call it AFTER all primary-relay-state mutations are settled (i.e., after the `_handle_rfid_insert` / `_handle_rfid_remove` / `_handle_reboot` / always-enabled branches and before `_save_cache()`).
- [ ] T014 Wire `_resolve_second_relay` into `MachineState.lockout`, `MachineState.unlock`, `MachineState.oops`, `MachineState.unoops`, and `MachineState._handle_reboot` so the second-relay state is recomputed (and zeroed where appropriate) on every primary-state change. For `lockout`/`oops` the result MUST be `False`/`None`; for `unlock`/`unoops`/`_handle_reboot` with the root machine `always_enabled=true`, the result depends on whether `second_relay.always_enabled` is also true.
- [ ] T015 Extend `MachineState.machine_response` in `src/dm_mac/models/machine.py` to include `"second_relay": self.second_relay_desired_state` in the returned dict. Always emit the key (consistent with the trade-off documented in `data-model.md`).

**Checkpoint**: Schema accepts `second_relay`; `Machine` parses it; `MachineState` tracks it; `_resolve_second_relay` produces correct values; pickle round-trips it; MCU response includes it. User stories can begin.

---

## Phase 3: User Story 1 - Primary-only Operator Operates Base Machine (Priority: P1) 🎯 MVP

**Goal**: A primary-authorized operator gets the base machine relay but the second relay stays off; LCD content is unchanged.

**Independent Test**: Tap a primary-only user's fob against a machine with `second_relay` configured; verify response has `relay=true`, `second_relay=false`, and `display` byte-identical to today's "Welcome,\n…" string.

### Tests for User Story 1

- [ ] T016 [P] [US1] Unit test in `tests/test_machine.py` (or `tests/test_models_machine.py`) for `_resolve_second_relay` with a machine configured with `second_relay`, primary-authorized user, no secondary auth → asserts `second_relay_desired_state=False`, `second_relay_authorization="denied"`. Parametrize over `unauthorized_warn_only=False` only.
- [ ] T017 [P] [US1] Unit test in `tests/test_machine.py` covering the negative edge case: user has secondary auth but NOT primary → `_resolve_second_relay` short-circuits because primary relay is off, asserts `second_relay_desired_state=False`, `second_relay_authorization=None`.
- [ ] T018 [P] [US1] Integration test in `tests/test_views_machine.py` (or `tests/test_machine_api.py`) using the Quart test client: POST `/machine/update` with `rfid_value` of a primary-only user against a `second_relay`-equipped machine fixture; assert response 200, `relay=true`, `second_relay=false`, `display` matches the existing "Welcome,\n<preferred_name>" string exactly.
- [ ] T019 [P] [US1] Integration test asserting that after the primary-only operator taps out (sends update with empty `rfid_value`), the response has `relay=false` and `second_relay=false`.

### Implementation for User Story 1

(All implementation lives in Phase 2 Foundational — `_resolve_second_relay` already covers the `denied` branch. No new code is required for US1; only the tests above.)

**Checkpoint**: US1 fully testable. Primary-only authorization path produces correct second-relay-off behavior.

---

## Phase 4: User Story 2 - Operator with Both Auths Operates Machine + Accessory (Priority: P1)

**Goal**: An operator with both primary and secondary auth gets both relays energized; primary-de-energizing events also de-energize the second relay.

**Independent Test**: Tap a user with both auths; verify `relay=true` AND `second_relay=true`. Then trigger oops/lockout/tap-out and verify both go to `false`.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test in `tests/test_machine.py` for `_resolve_second_relay` with primary-authorized operator + secondary auth → `second_relay_desired_state=True`, `second_relay_authorization="granted"`.
- [ ] T021 [P] [US2] Unit test for `_resolve_second_relay` with `second_relay.unauthorized_warn_only=true`, primary-authorized operator without secondary auth → `True`/`"warn"`.
- [ ] T022 [P] [US2] Unit test for `_resolve_second_relay` with `second_relay.always_enabled=true` and ANY operator (primary-authorized) → `True`/`"always_enabled"`. Also assert that when primary relay is off (no operator), the second relay is `False`/`None` regardless of `always_enabled`.
- [ ] T023 [P] [US2] Integration test in `tests/test_views_machine.py`: POST with both-auth user fob → response `relay=true`, `second_relay=true`.
- [ ] T024 [P] [US2] Integration test: with both-auth user logged in, send a follow-up `/machine/update` with `oops=true` → response `relay=false`, `second_relay=false`, `display` matches OOPS_DISPLAY_TEXT.
- [ ] T025 [P] [US2] Integration test: with both-auth user logged in, call `POST /machine/locked_out/<name>`, then `/machine/update` → response `relay=false`, `second_relay=false`, `display` matches LOCKOUT_DISPLAY_TEXT.
- [ ] T026 [P] [US2] Integration test: with both-auth user logged in, send update with empty `rfid_value` (tap out) → response `relay=false`, `second_relay=false`.
- [ ] T027 [P] [US2] Integration test: machine with `second_relay.always_enabled=true`, primary-only user (no secondary) taps in → response `relay=true`, `second_relay=true`. Tap out → both `false`.
- [ ] T027a [P] [US2] Edge-case integration test in `tests/test_views_machine.py`: machine where `authorizations_or` and `second_relay.authorizations_or` share a common authorization (e.g., both lists contain `"laser_rotary"`); user holding only that shared auth taps in → response `relay=true`, `second_relay=true`. Verifies the spec edge case "same authorization in both lists."
- [ ] T027b [P] [US2] User-swap integration test in `tests/test_views_machine.py`: with userA (both auths) tapped in (response `relay=true`, `second_relay=true`), send a `/machine/update` whose `rfid_value` switches to userB (primary only) WITHOUT an intervening empty-rfid update — assert response transitions to `relay=true`, `second_relay=false`, with no leaked second-relay state from userA's session. (This may surface as two updates if the firmware sends a tap-out first; test both single-update and tap-out-then-tap-in sequences.)

### Implementation for User Story 2

(All implementation lives in Phase 2 Foundational — `_resolve_second_relay` covers `granted`/`warn`/`always_enabled` branches; the wiring into oops/lockout/etc. was completed in T014.)

**Checkpoint**: US2 fully testable. Dual-authorization path works; primary-de-energizing events correctly cascade.

---

## Phase 5: User Story 4 - Backwards Compatibility for Single-Relay Machines (Priority: P1)

**Goal**: Machines without a `second_relay` block behave identically to today (excluding the always-emitted `second_relay: false` key in the response, per the documented trade-off).

**Independent Test**: Run the existing test suite on a machines.json that contains no `second_relay` blocks; assert no regressions and that the response (modulo `second_relay: false`) matches the captured pre-feature golden response.

### Tests for User Story 4

- [ ] T028 [P] [US4] Regression test in `tests/test_views_machine.py`: load `tests/fixtures/machines.json` (single-relay only, untouched from main), drive a tap-in/tap-out cycle, and assert each response equals the captured `tests/fixtures/golden-single-relay-response.json` plus the new `second_relay: false` key.
- [ ] T029 [P] [US4] Pickle backwards-compat test in `tests/test_machine.py`: write a pickle file using only the pre-feature dict shape (no `second_relay_desired_state` or `second_relay_authorization` keys), then construct a `MachineState` and assert `second_relay_desired_state == False` and `second_relay_authorization is None`.
- [ ] T030 [P] [US4] MCU forward-compat test in `tests/test_views_machine.py`: POST `/machine/update` with a request body that omits `second_relay_state` entirely; assert 200 and a valid response.
- [ ] T031 [P] [US4] LCD invariant test in `tests/test_views_machine.py`: across all parametrized scenarios from US1 and US2, assert that the `display` field matches the value the same scenario produced before the feature (use the captured golden file or hard-coded expected strings — explicitly NEVER include any second-relay reference in `display`).
- [ ] T032 [P] [US4] Slack/log non-emission test in `tests/test_views_machine.py` (or `tests/test_machine.py`): for a single-relay machine, drive a normal tap-in/tap-out cycle and assert (a) no log line text references "second relay", "accessory", or any `second_relay.alias`, AND (b) no AUTH log record carries any structured field/extra key whose name relates to second-relay decisions (covers FR-011's omission half explicitly).
- [ ] T032a [P] [US4] Deconfigured-relay forward-compat test in `tests/test_views_machine.py`: POST `/machine/update` with `second_relay_state: true` against a machine that has NO `second_relay` block configured; assert response 200, `second_relay: false`, no exception raised, and at most a DEBUG-level log entry. Covers FR-015's "MCU reports state for a removed second relay" clause.

### Implementation for User Story 4

(No new production code. This phase is regression-protection via tests only. If any test fails, fix the production code in the appropriate Phase 2 / 6 task.)

**Checkpoint**: US4 verified. Single-relay deployments are unaffected by the feature.

---

## Phase 6: User Story 3 - Maintainer Configures and Observes (Priority: P2)

**Goal**: Slack messages, Prometheus metrics, structured logs, and ESPHome firmware all expose second-relay state coherently. Configuration validation produces actionable errors.

**Independent Test**: Add a `second_relay` block to a fixture machine; drive a session through both auth paths plus oops/lockout; verify Slack messages name the accessory, Prometheus exposes the four new metrics only for second-relay machines, structured logs include the auth decision, and the ESPHome YAML drives GPIO14 from the response field.

### Tests for User Story 3

- [ ] T033 [P] [US3] Config validation positive tests in `tests/test_machine_config.py` (or wherever `MachinesConfig.validate_config` is currently tested): `second_relay` minimal (only `authorizations_or`), with all four options, with alias only.
- [ ] T034 [P] [US3] Config validation negative tests in the same file: missing `authorizations_or`, empty `authorizations_or`, unknown field inside `second_relay`, nested `second_relay` inside `second_relay`. Each must raise `jsonschema.ValidationError` with a message that mentions both the offending machine name and the offending field.
- [ ] T035 [P] [US3] Slack handler tests in `tests/test_slack_handler.py` covering: tap-in with both auths emits a single admin_log line naming the alias and "authorized"; tap-in with primary-only emits a single admin_log line naming the alias and "NOT authorized"; tap-in with `unauthorized_warn_only` emits a "WARN-ONLY" line; oops/lockout messages mention "both relays" only when `second_relay` is configured.
- [ ] T036 [P] [US3] Prometheus collector tests in `tests/test_views_prometheus.py`: emit metrics, assert `machine_second_relay_state`, `machine_second_relay_configured`, `machine_second_relay_unauth_warn_only`, `machine_second_relay_always_enabled` exist for second-relay machines and DO NOT emit any sample for single-relay machines.
- [ ] T037 [P] [US3] Structured log tests in `tests/test_machine.py`: assert that the AUTH logger emits a record per second-relay decision (granted/denied/warn/always_enabled) with the operator name, machine name, alias (if set), and decision keyword.

### Implementation for User Story 3

- [ ] T038 [US3] Update Slack admin_log message generation in `src/dm_mac/models/machine.py::_handle_rfid_insert` (and helpers) to compose a single coherent line. Use these EXACT templates (where `<accessory>` resolves to `second_relay.alias` if set, else the literal string `"second relay"`):
  - granted (both auths): `"RFID login on {machine} by authorized user {user}; <accessory> authorized"`
  - denied (primary only, second relay denied): `"RFID login on {machine} by authorized user {user}; <accessory> NOT authorized — relay off"`
  - warn (primary only, second relay warn-only override): `"RFID login on {machine} by authorized user {user}; <accessory> WARN-ONLY override — relay on"`
  - always_enabled: `"RFID login on {machine} by authorized user {user}; <accessory> always-enabled — relay on"`
  Only include the second clause when `self.machine.second_relay is not None`. The single-relay phrasing (`"RFID login on {machine} by authorized user {user}"`) MUST remain byte-identical to today.
- [ ] T039 [US3] Update `_handle_rfid_remove` admin_log line to mention "both relays off" only when `self.machine.second_relay is not None`. Single-relay machines retain today's exact phrasing (verified by US4 T032).
- [ ] T040 [US3] Update Slack lockout/unlock/oops/unoops log messages in `src/dm_mac/slack_handler.py` (methods `log_lock`, `log_unlock`, `log_oops`, `log_unoops`) to include "(both relays)" only when the machine has `second_relay` configured.
- [ ] T041 [US3] Add four new metrics to `src/dm_mac/views/prometheus.py::PromCustomCollector.collect`: `machine_second_relay_state`, `machine_second_relay_configured`, `machine_second_relay_unauth_warn_only`, `machine_second_relay_always_enabled`. Each emits one sample per machine ONLY when `m.second_relay is not None`. Labels: `machine_name`, `display_name`, plus `second_relay_alias` (empty string when alias is unset).
- [ ] T042 [US3] Add structured log emission in `MachineState._resolve_second_relay`: log to the `AUTH` logger one of "User X authorized for accessory Y on machine Z" / "User X UNAUTHORIZED for accessory Y on machine Z" / "User X authorized for accessory Y on machine Z (warn-only override)" / "Accessory Y on machine Z always-enabled" using `display_name` for machine and `second_relay.alias` (or "second relay") for accessory.
- [ ] T043 [US3] Update ESPHome firmware in `esphome-configs/2025.11.2/no-current-input.yaml`: add an `output.gpio` on GPIO14 with id `relay2_output_pin` and a `switch.output` with id `relay2_output`; extend the `on_response` lambda to read `root["second_relay"]` (defaulting to `false` if absent) and call `id(relay2_output).turn_on()` / `turn_off()` accordingly. Document GPIO14 / connector pin 6 in the file's header comment block.
- [ ] T044 [US3] Verify `esphome-configs/2025.11.2/hardware-test.yaml` requires no second-relay changes. (Confirmed during /speckit.analyze: hardware-test.yaml only exercises GPIO33/RFID/oops button; second-relay/GPIO14 hardware testing is out of scope for this feature.) This task is a no-op verification — record the finding in the PR description and move on.

**Checkpoint**: All observability surfaces and the firmware now expose and act on second-relay state.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates, full test-suite green-up, manual quickstart validation, and feature closeout.

- [ ] T045 [P] Update `CLAUDE.md` Configuration System section to document the `second_relay` block and its options. Match the bullet style already used for `authorizations_or` / `unauthorized_warn_only` / `always_enabled` / `alias`.
- [ ] T046 [P] Update `docs/source/configuration.rst` with a new `second_relay` subsection under the machines.json documentation. Include a code example matching `quickstart.md`.
- [ ] T047 [P] Update `docs/source/http-api.rst` to document the new optional `second_relay_state` request field and the new always-emitted `second_relay` response field. Reference `specs/002-second-relay-support/contracts/mcu-update-protocol.md`.
- [ ] T048 [P] Update `docs/source/slack.rst` to describe the new Slack message phrasing for second-relay machines. Reference the alias usage.
- [ ] T049 [P] Update `docs/source/grafana-dashboard.md` to mention the four new Prometheus metrics and how to filter dashboard panels by `machine_second_relay_configured == 1`.
- [ ] T050 [P] Update `docs/source/dm_mac.models.machine.rst` and `docs/source/dm_mac.models.api_schemas.rst` autodoc references if necessary (typically no change needed since `automodule` picks up new classes/fields automatically — verify by running `nox -s docs` and checking for autodoc warnings).
- [ ] T051 Run the full nox suite from repo root: `nox -s tests typeguard mypy pre-commit safety` and resolve any failures. All sessions MUST pass.
- [ ] T052 Run `nox -s coverage -- report` and confirm coverage has not decreased relative to `main` (Constitution §II).
- [ ] T053 Manually validate `specs/002-second-relay-support/quickstart.md` end-to-end against a local server with a fixture `machines.json` containing `second_relay`. Capture timing to confirm SC-004 (under 10 minutes).
- [ ] T054 Update `specs/002-second-relay-support/spec.md` Status from `Draft` to `Implemented` and append a brief implementation note to the bottom of the file.
- [ ] T055 Close GitHub issue #129 with a comment linking to the merged PR and the spec directory.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies — start immediately.
- **Phase 2 Foundational**: Depends on Phase 1 completion. **BLOCKS all user stories.**
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2. Independent of US1 (different test scenarios).
- **Phase 5 (US4)**: Depends on Phase 2. Independent of US1/US2.
- **Phase 6 (US3)**: Depends on Phase 2. Tests in this phase depend on the implementation tasks below them, but US3 is otherwise independent of US1/US2/US4.
- **Phase 7 Polish**: Depends on all desired user stories. T051 (full nox) MUST run after every previous task.

### User Story Dependencies

All four user stories share the foundational `_resolve_second_relay` implementation in Phase 2. They are otherwise independent and can be tested independently. The MVP is **US1 + US2 + US4** (all P1) — US3 (P2) can ship later.

### Within Each User Story

- Test tasks ([P]) write tests that MUST pass against the Phase 2 implementation. If a test fails, the bug is in Phase 2 and we fix it there.
- US3 implementation tasks (T038–T044) are mostly NOT parallelizable with each other since several touch the same files (`models/machine.py`, `slack_handler.py`).

### Parallel Opportunities

- **Phase 1**: T001, T002, T003 all parallel.
- **Phase 2**: T007 and T008 (separate sections of `api_schemas.py`) parallel. T004–T006 sequential within `models/machine.py`. T009–T015 sequential (all in `models/machine.py`, dependent edits).
- **Phase 3**: T016, T017, T018, T019 parallel.
- **Phase 4**: T020–T027b all parallel.
- **Phase 5**: T028–T032a all parallel.
- **Phase 6 Tests**: T033–T037 parallel.
- **Phase 6 Impl**: T038/T039 sequential (same file). T040, T041, T042, T043 parallel with each other and with T038/T039 once those land. T044 parallel with T043.
- **Phase 7 Docs**: T045–T050 all parallel. T051 / T052 sequential after all docs.

---

## Parallel Example: User Story 2

```bash
# Launch all unit tests for US2 together:
Task: "T020 Unit test for _resolve_second_relay granted branch"
Task: "T021 Unit test for _resolve_second_relay warn branch"
Task: "T022 Unit test for _resolve_second_relay always_enabled branch"

# Launch all integration tests for US2 together:
Task: "T023 Integration test: both-auth user tap-in"
Task: "T024 Integration test: oops mid-session"
Task: "T025 Integration test: lockout mid-session"
Task: "T026 Integration test: tap-out"
Task: "T027 Integration test: always_enabled second_relay"
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US4 — all P1)

1. Phase 1 Setup (T001–T003).
2. Phase 2 Foundational (T004–T015).
3. Phase 3 US1 tests (T016–T019). Run; expect green.
4. Phase 4 US2 tests (T020–T027). Run; expect green.
5. Phase 5 US4 regression tests (T028–T032). Run; expect green.
6. **STOP and VALIDATE**: feature is functionally complete and regression-safe. Could ship to production-with-second-relay-machines if observability is acceptable.

### Incremental Delivery

1. Setup + Foundational → Foundation ready.
2. + US1 + US2 + US4 → Functional + regression-safe MVP. Demo-able.
3. + US3 (Slack/metrics/logs/firmware) → Production-ready observability. Ship.
4. + Polish → Documentation/full nox green. Merge.

### Parallel Team Strategy

With multiple developers:

1. One developer drives Phase 2 (Foundational is mostly sequential within `models/machine.py`).
2. Once Phase 2 is done, three developers can work US1, US2, US4 test phases in parallel; a fourth can start US3 implementation tasks.
3. Polish phase docs (T045–T050) parallel across the team.

---

## Notes

- **Test-first within each user-story phase**: Phase 2 implements; user-story tests verify. If a test reveals a bug, fix it in Phase 2 — do NOT add new code in user-story phases.
- **No new abstractions**: Constitution §III. Don't introduce a `RelayConfig` base class for `Machine` and `SecondRelayConfig` to share — keep them parallel and concrete.
- **Fail closed**: Any unexpected condition in `_resolve_second_relay` MUST result in `False`/`"denied"` — verified by US1's negative tests.
- **No git commits inside individual tasks**: commit at logical-group boundaries (end of Phase 2, end of each user-story phase, end of Phase 7).
- **`docs/features/` move-on-completion rule**: not applicable here — this feature was initiated from GitHub issue #129, not from a `docs/features/*.md` file. T055 closes the issue instead.
