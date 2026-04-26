# Feature Specification: Second Relay Support

**Feature Branch**: `002-second-relay-support`
**Created**: 2026-04-25
**Status**: Implemented
**Input**: GitHub Issue #129 — "Second Relay Support"

## Summary

Some machines in the makerspace have accessories or modes that require additional training beyond what is required to operate the machine itself. Today, the access control system can gate exactly one output relay per machine, which forces an all-or-nothing decision: either everyone authorized on the machine can use the accessory, or nobody can. We want to allow a single machine to control a second, independently-gated output relay so that an additional authorization can be required to enable the accessory while still allowing primary-authorized users to operate the base machine.

The hardware foundation already exists: V1 Machine Control Unit (MCU) boards expose connector pin 6 wired to GPIO14, currently reserved for future use. This feature wires that pin up as a second controllable output and adds the configuration, authorization logic, and observability needed to use it safely. The operator-facing LCD is intentionally NOT changed by this feature; whether the second relay is energized is communicated to the operator only by the physical state of the accessory itself.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator with primary authorization only operates base machine (Priority: P1)

A makerspace member who is trained and authorized on a machine taps their RFID fob and operates the machine normally. The base machine relay energizes; the second-relay accessory remains disabled because the member does not have the additional authorization required for it. The member can still use the machine for everything that does not require the accessory.

**Why this priority**: This is the most common case once second-relay machines exist. The system must NOT regress behavior for primary-only users — they continue to operate exactly as they do today, just without access to the accessory.

**Independent Test**: Configure one machine with a `second_relay` block requiring an authorization the test user does not hold. Have the test user (with primary authorization only) tap their fob; verify the primary relay activates and the second relay stays de-energized. The LCD must show the same content it would show today for an authorized operator (no second-relay information rendered).

**Acceptance Scenarios**:

1. **Given** a machine configured with a `second_relay` requiring authorization "X" and a primary `authorizations_or` of "Y", **When** a user authorized only for "Y" taps their fob, **Then** the primary relay activates, the second relay does not activate, and the LCD content is identical to what an authorized operator on a single-relay machine would see today.
2. **Given** the same machine and user from scenario 1, **When** the user releases the machine (taps out), **Then** both the primary and the second relay are de-energized.

---

### User Story 2 - Operator with both primary and secondary authorization operates base machine plus accessory (Priority: P1)

A member who is authorized on both the machine and its restricted accessory taps their fob. The system grants both authorizations, energizing both the primary and the second relay so the member can use the machine and the accessory in the same session.

**Why this priority**: This is the entire point of the feature — without it, the second relay never activates and the work is meaningless. P1 alongside Story 1 because the two together form the minimum viable behavior.

**Independent Test**: Configure a machine as in Story 1. Have a test user who holds *both* the primary authorization and the secondary authorization tap their fob; verify both relays energize and Slack/logs/metrics reflect that both relays are active for the named operator. The LCD must show its normal authorized content (unchanged from today's behavior).

**Acceptance Scenarios**:

1. **Given** a machine with primary authorization "Y" and `second_relay` authorization "X", **When** a user holding both "X" and "Y" taps their fob, **Then** both relays activate.
2. **Given** the situation in scenario 1, **When** the operator taps out, presses the oops button, or the machine is locked out via Slack/API, **Then** both relays de-energize.

---

### User Story 3 - Maintainer configures and observes second-relay machines (Priority: P2)

A makerspace administrator updates `machines.json` to add a `second_relay` block to an existing machine, restarts (or reloads) the server, and verifies the new behavior is in effect. They expect logs, Slack notifications, and Prometheus metrics to clearly distinguish second-relay status from primary-relay status so they can audit usage and troubleshoot issues without reading source code.

**Why this priority**: P2 because configuration and observability are essential for operating the feature in production but are independent of the core enforcement behavior in Stories 1 and 2.

**Independent Test**: Add a `second_relay` block to a fixture machine, start the server, drive the machine through the lifecycle (tap-in with primary-only, tap-in with both auths, oops, lockout). Verify that for every state transition the logs, Slack messages, and Prometheus metrics independently identify the primary relay state, the second relay state, and the operator's authorization to each.

**Acceptance Scenarios**:

1. **Given** a machine has a `second_relay` block configured, **When** an operator with both authorizations starts a session, **Then** the Slack notification, structured log entries, and Prometheus metrics all clearly indicate that both relays are active for the named operator.
2. **Given** the same configuration, **When** an operator with only primary authorization starts a session, **Then** Slack/logs/metrics indicate primary-relay active and second-relay inactive (with a reason such as "user not authorized for accessory").
3. **Given** an invalid `second_relay` block (e.g., missing required fields), **When** the server starts up, **Then** configuration validation fails with a clear error message naming the offending machine and field.

---

### User Story 4 - Backwards compatibility for single-relay machines (Priority: P1)

Existing machines without a `second_relay` block in `machines.json` continue to operate exactly as they do today, with no changes to their relay behavior, LCD content, log output, Slack notifications, or metric labels.

**Why this priority**: P1 because the deployed fleet has many single-relay machines that must keep working without configuration changes during and after rollout.

**Independent Test**: Take an unmodified `machines.json` from before this feature and run it against the post-change server. Drive a representative single-relay machine through its full lifecycle and verify behavior is identical to the pre-change baseline (same LCD content, same log lines, same Slack messages, same metric series).

**Acceptance Scenarios**:

1. **Given** a `machines.json` that contains no `second_relay` blocks anywhere, **When** the server starts and operators use the machines, **Then** behavior is byte-identical to the pre-feature behavior aside from any additive metric labels with safe defaults.
2. **Given** a machine without `second_relay`, **When** the MCU posts a state update, **Then** the response payload omits any new fields related to the second relay (or sets them to a documented safe default that the existing firmware ignores).

---

### Edge Cases

- An MCU running pre-feature firmware connects to a post-feature server controlling a machine that *does* have a `second_relay` configured. The server must continue to function (the second relay simply will not be physically driven by old firmware). Administrators are responsible for not deploying second-relay configuration against MCUs running pre-feature firmware in production, since old firmware cannot enforce the secondary gate.
- A user holds the secondary authorization but NOT the primary authorization. The second relay must remain de-energized — secondary access is meaningless without primary access.
- A machine has `second_relay.always_enabled` set to true. The second relay must follow the primary relay's energized state exactly (on whenever primary is on, off whenever primary is off), regardless of the operator's secondary authorizations. This is the natural meaning of `always_enabled` in the context of a relay that physically depends on the primary relay.
- The oops button is pressed mid-session while both relays are active. Both relays must de-energize together; the oops/maintenance flow must not leave one relay energized.
- A machine is locked out via Slack or API while both relays are active. Both relays must de-energize and remain de-energized until unlock.
- A user taps out and a different user taps in mid-session. The new operator's authorizations are evaluated independently for both the primary relay and the second relay.
- Configuration declares the same authorization for both `authorizations_or` and `second_relay.authorizations_or`. The system must accept this and treat it consistently (effectively any authorized operator gets both relays).
- Configuration declares an empty `authorizations_or` list inside `second_relay`. The system must reject this at load time with a clear error.
- A machine's `second_relay` has an `alias` set. That alias is used in second-relay-specific Slack messages and log lines so the accessory is identifiable by a human-readable name (e.g., "Laser Cutter — Rotary Attachment") distinct from the machine's own name/alias.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The machine configuration schema MUST support a new optional `second_relay` property on each machine. When present, this property declares the configuration governing a second, independently-gated output relay for that machine.
- **FR-002**: The `second_relay` property MUST accept the same set of options that the root machine config accepts: `authorizations_or` (required, non-empty list), `unauthorized_warn_only` (optional boolean, default false), `always_enabled` (optional boolean, default false), and `alias` (optional string).
- **FR-002a**: The `second_relay.alias`, when present, MUST be used in Slack messages and structured log entries that refer specifically to second-relay events, so administrators can identify the accessory by a human-readable name distinct from the machine name/alias.
- **FR-002b**: When `second_relay.always_enabled` is true, the second relay MUST follow the primary relay's energized state exactly (on whenever primary is on, off whenever primary is off), regardless of any operator's secondary authorization. `second_relay.always_enabled` MUST NOT cause the second relay to energize while the primary relay is de-energized.
- **FR-003**: When a machine has a `second_relay` configured (and `always_enabled` is not set on it), the second relay MUST be energized only if BOTH (a) the operator has at least one of the machine's primary `authorizations_or` AND (b) the operator has at least one of the `second_relay.authorizations_or` (subject to warn-only behavior described in FR-005).
- **FR-004**: When the primary relay de-energizes for any reason (operator taps out, oops, lockout, server restart restoring a non-active state), the second relay MUST also de-energize.
- **FR-005**: When `second_relay.unauthorized_warn_only` is true, the second relay MUST still activate for an operator with primary authorization but without secondary authorization, and the system MUST emit a warning log and Slack message naming the operator, the machine (and `second_relay.alias` if set), and the missing secondary authorization.
- **FR-006**: Machines without a `second_relay` block MUST behave identically to today in every operator-, admin-, and observability-facing way: identical LCD content, identical structured log output, identical Slack message content, and identical Prometheus metric series. The `/api/machine/update` JSON response payload gains exactly one additive field (`second_relay`, always `false` for unconfigured machines) for forward-compat with second-relay firmware; this is the only protocol-level deviation from byte-identity and is invisible to firmware that does not parse the field.
- **FR-007**: Configuration validation MUST reject `machines.json` files containing a `second_relay` block that fails the same structural validation rules applied to the root machine config (e.g., empty `authorizations_or`, unknown fields), with an error message identifying the offending machine and field.
- **FR-008**: The MCU update protocol MUST allow the server to instruct an MCU to set the second relay's state independently of the primary relay's state. Servers MUST continue to accept update requests from MCUs that do not yet support the second relay (older firmware) without error.
- **FR-009**: The operator-facing LCD MUST NOT be modified by this feature. LCD content for an authorized operator on a machine with `second_relay` configured MUST be identical to LCD content for the same authorized operator on a machine without `second_relay` configured. Operators learn the second relay's state only from the physical state of the accessory.
- **FR-010**: Slack notifications MUST distinguish between primary-relay state changes and second-relay state changes. A session in which both relays activate together SHOULD be communicated in a single coherent message rather than two independent messages, naming the `second_relay.alias` (or, if absent, the machine name) when referring to the accessory.
- **FR-011**: Structured logs MUST include the second relay's state (on/off) and the authorization decision (granted/denied/warn) for every machine state update on a machine with `second_relay` configured, and MUST omit second-relay fields entirely for machines without a `second_relay` configured.
- **FR-012**: Prometheus metrics MUST expose the second relay's state and recent activity in a way that allows dashboards to count and graph second-relay-specific events without breaking existing single-relay dashboards or producing extra metric series for single-relay machines.
- **FR-013**: The Slack lock/unlock and oops/unoops commands MUST act on the machine as a whole — locking a machine MUST de-energize both relays, and unlocking MUST restore the pre-lock state for both. There MUST NOT be a "lock only the second relay" command in this feature.
- **FR-014**: ESPHome firmware configuration MUST be updated to drive a second output relay on GPIO14 (V1 hardware connector pin 6) from the server's response payload, leaving GPIO14 inactive when the server's response indicates no second-relay configuration or no authorization for it.
- **FR-015**: The MCU update protocol MUST handle MCUs reporting state for a second relay that has been removed from configuration, and servers MUST handle MCUs that do not report second-relay state at all, without crashing or generating spurious authorization events.

### Key Entities

- **Machine**: Existing entity, now optionally containing a nested **SecondRelayConfig**. A machine has at most one second relay.
- **SecondRelayConfig**: New entity. Holds the authorization rules governing the second relay. Fields mirror the root-machine config: `authorizations_or` (required), `unauthorized_warn_only`, `always_enabled`, and `alias` (all optional).
- **MachineState**: Existing entity, extended to track the current energized/de-energized state of the second relay alongside the primary relay's state, plus the authorization decision that produced that state.
- **AuthorizationDecision**: Conceptual entity (may or may not be a literal type in code) describing, for a given operator and machine, the result for the primary relay AND for the second relay (granted / denied / warn-only / always-enabled). Used by Slack, logging, and metrics to render consistent messages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A machine configured with a `second_relay` correctly enforces the dual-authorization rule (primary AND secondary required) for 100% of operator tap-ins in acceptance testing — i.e., no test case where the second relay activates without both authorizations or fails to activate when both are held.
- **SC-002**: Operators can determine whether they have access to the accessory by attempting to use it — the LCD is intentionally unchanged, so the physical state of the accessory is the indicator. This means an operator without secondary authorization will know within seconds of trying to operate the accessory.
- **SC-003**: After this feature ships, an existing `machines.json` file that contains no `second_relay` blocks produces no observable behavior change versus the pre-feature server in regression testing — no new log lines, no new Slack messages, no new metric series for those machines. The `/api/machine/update` JSON response payload gains exactly one additive boolean key (`second_relay: false`); this protocol-level addition is the only deviation from byte-identity and does not affect operator, admin, or observability surfaces.
- **SC-004**: A makerspace administrator can add `second_relay` configuration to an existing machine, reload the configuration, and verify correct behavior end-to-end in under 10 minutes using only the project documentation.
- **SC-005**: Slack messages and Prometheus metrics for second-relay-equipped machines unambiguously identify whether the second relay was active during any given operator session, with zero ambiguity for users of those surfaces in feedback collected from at least one administrator.
- **SC-006**: Test coverage for the feature meets or exceeds the project's existing thresholds, and `nox -s tests`, `nox -s typeguard`, `nox -s mypy`, `nox -s pre-commit`, and `nox -s safety` all pass on the feature branch.

## Assumptions

- The hardware on deployed V1 MCUs has GPIO14 (connector pin 6) physically connected and available for use; no MCU hardware revision is needed.
- Older deployed MCU firmware that ignores the second relay output will continue to operate single-relay machines correctly; only machines with a `second_relay` configured need updated firmware to physically drive the second relay.
- The `second_relay` feature is opt-in per machine. Operators of single-relay machines never see any new behavior, log lines, Slack messages, or metric series.
- The LCD is intentionally not modified by this feature. The operator's signal that the second relay is or is not energized is the physical behavior of the accessory itself.
- The locking/oops/admin Slack commands continue to operate at the machine level (not per-relay). There is no anticipated need for second-relay-only administrative actions in this feature.
- Documentation for `machines.json`, MCU firmware, and operator behavior will be updated in step with the implementation; no separate documentation phase is required.
- The configuration property name `second_relay` (snake_case) is used to match the rest of the `machines.json` schema, despite the issue text using `secondRelay`. The issue's spelling is treated as descriptive, not prescriptive.

## Implementation Notes

- Implemented on branch `002-second-relay-support` (2026-04-26). All four user stories (US1, US2, US3, US4) ship together. See `tasks.md` for the task list and `quickstart.md` for the administrator-facing walkthrough.
- The MCU `/api/machine/update` response always emits `second_relay: false` for machines without `second_relay` configured (documented trade-off in `data-model.md`); this is the only protocol-level deviation from byte-identity for single-relay machines and is invisible to firmware that does not look at the field.
- Prometheus metrics for second-relay state are only emitted when at least one configured machine has a `second_relay` block, keeping single-relay deployments byte-identical at `/metrics`.
