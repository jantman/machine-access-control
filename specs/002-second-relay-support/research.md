# Phase 0 Research: Second Relay Support

**Feature**: Second Relay Support
**Branch**: `002-second-relay-support`
**Date**: 2026-04-26

This document records the research and decisions that resolve open implementation questions before Phase 1 design begins. The spec at [spec.md](./spec.md) has zero `[NEEDS CLARIFICATION]` markers; the items below address technical-context unknowns that surfaced while drafting the plan.

---

## R1. How is the existing `Machine` config validated and instantiated?

**Decision**: Extend the existing `CONFIG_SCHEMA` in `src/dm_mac/models/machine.py` by adding an optional `second_relay` property whose schema is a `$ref` to the same per-machine option set already used at the root, with the exception of the recursive `second_relay` itself (i.e., a `second_relay` cannot itself contain a nested `second_relay`).

**Rationale**: The existing schema uses `jsonschema.validate` against `patternProperties` on `^[a-z0-9_-]+$`. Adding `second_relay` as an additional property with a sibling object schema is a one-line addition. The "second_relay accepts the same options" rule from the spec (Q1 → Option C) is most cleanly expressed by a shared `$defs` entry referenced from both the root and `second_relay`.

**Alternatives considered**:
- *Inline-duplicate the option list in two places* — rejected as duplicative; risks drift if the root schema gains a new option later.
- *Separate top-level config file for second-relay overrides* — rejected as a violation of YAGNI; the issue specifically asks for this in `machines.json`.

---

## R2. How is the per-machine state persisted, and what backwards-compat invariants apply?

**Decision**: Add the new state fields (`second_relay_desired_state: bool`, `second_relay_authorization: Optional[str]` capturing the granted/denied/warn/always_enabled outcome, and `second_relay_alias_at_auth: Optional[str]`) to `MachineState.__init__` with safe defaults. Add them to the `_save_cache` dict. Rely on the existing `_load_from_cache` `hasattr` guard so older pickle files load cleanly with the defaults from `__init__`. Any unknown extra keys in the pickle (e.g., from a future version) are already silently ignored by the same `hasattr` check.

**Rationale**: This pattern is exactly how the existing codebase already handles state evolution (see `is_override_login` added in feature 001). It satisfies Constitution §IV (backward compatibility) and §I (safe defaults — second relay defaults to off whenever loaded from older state).

**Alternatives considered**:
- *Bump a version field in the pickle* — rejected as unnecessary complexity; the project has no precedent for it and `hasattr` already guarantees forward and backward read tolerance.
- *Migrate pickle files at startup* — rejected; the existing approach already converges on the desired state on the first MCU update after restart.

---

## R3. How should the MCU↔server JSON protocol be extended without breaking older firmware?

**Decision**: Add two optional fields with safe defaults:
- **Response**: `second_relay` (boolean, default `false`). MCU firmware that does not know about this field simply ignores it; modern firmware drives GPIO14 from it.
- **Request**: `second_relay_state` (boolean, optional). Reported by modern firmware as the actual GPIO14 state for parity-checking and metrics. Older firmware omits it entirely. The server uses the field for observability only and never as input to authorization decisions.

`MachineUpdateRequest` and `MachineUpdateResponse` (pydantic models in `src/dm_mac/models/api_schemas.py`) get the new fields as optional with defaults. Existing tests for the schemas continue to pass.

**Rationale**: Constitution §IV mandates additive, optional protocol changes. The default of `false` for the response field guarantees that firmware that does drive GPIO14 from this field will leave it off whenever the server doesn't explicitly enable it (fail-closed — Constitution §I).

**Alternatives considered**:
- *Bump an API version* — rejected; the protocol is semver-implicit and no other features have ever bumped a version.
- *Add new endpoints `/machine/update2`* — rejected as duplicative and brittle.

---

## R4. How are Prometheus metrics structured today, and how do we add second-relay metrics without breaking dashboards?

**Decision**: Add four new metric families, each emitting only for machines with `second_relay` configured:
1. `machine_second_relay_state` (gauge, 0/1) — whether the second relay is currently energized.
2. `machine_second_relay_configured` (gauge, 0/1) — whether the machine has a `second_relay` block at all (so dashboards can `or` this with the state to count adoption).
3. `machine_second_relay_unauth_warn_only` (gauge, 0/1) — config flag.
4. `machine_second_relay_always_enabled` (gauge, 0/1) — config flag.

Labels reuse the existing `machine_name` and `display_name` and add an optional `second_relay_alias` label (empty string when not configured).

For machines without `second_relay`, none of the four metrics emit a sample. This keeps cardinality minimal and avoids zero-padding existing dashboards with new-but-empty series for single-relay machines (FR-006, FR-012).

**Rationale**: The current `PromCustomCollector` emits one sample per metric per machine for shared metrics. Restricting the new metrics to `second_relay`-equipped machines is the smallest change that satisfies Constitution §IV (no new series for single-relay machines) and FR-006 (byte-identical behavior).

**Alternatives considered**:
- *Reuse the existing `machine_relay_state` with a `relay_index` label* — rejected; would change the label schema for the existing metric, breaking existing Grafana dashboards and PromQL queries.
- *Always emit second-relay metrics with `0` for single-relay machines* — rejected; doubles the metric count for many machines that don't need it and produces "configured=0, state=0" series that look like real signals to dashboards.

---

## R5. How does the Slack handler currently render machine state, and how should second-relay events be rendered?

**Decision**:
- For login events (`_handle_rfid_insert`): emit a single Slack `admin_log` message describing both relays in one line — e.g., `"RFID login on Laser by Alice; primary authorized; accessory (Rotary) authorized"`, or `"... primary authorized; accessory (Rotary) NOT authorized — relay off"`, or `"... primary authorized; accessory (Rotary) WARN-ONLY override — relay on"`.
- For logout events (`_handle_rfid_remove`): the existing single line is sufficient because both relays de-energize together — extend the line to mention "both relays off" only when `second_relay` is configured.
- For oops/lock/unlock: messages already act on the machine as a whole; no Slack-text changes beyond clarifying that "both relays" are affected when `second_relay` is configured.
- The accessory's human-readable name comes from `second_relay.alias` if set, otherwise the literal phrase "second relay".

**Rationale**: Single-message-per-tap-in keeps Slack noise low (FR-010) and matches the existing administrator-facing tone. Using `second_relay.alias` in the message text is the only reason we kept `alias` in scope (Q1 → Option C).

**Alternatives considered**:
- *Two separate Slack messages, one per relay* — rejected; doubles Slack volume and is harder to correlate.
- *Skip Slack changes for single-relay events* — rejected; admins want a clear signal whether the accessory was authorized for the session, even when authorization was implicit.

---

## R6. ESPHome firmware: how is GPIO14 wired and how should it be driven?

**Decision**: Add a second `output.gpio` plus `switch.output` pair to `esphome-configs/2025.11.2/no-current-input.yaml` bound to GPIO14, identified as `relay2_output`. The existing `on_response` lambda is extended to read the optional `second_relay` field from the JSON response; if present and `true`, call `id(relay2_output).turn_on()`, otherwise `turn_off()`. If the field is missing entirely (server has no opinion / older server), default to `turn_off()` for fail-closed semantics.

**Rationale**: Mirrors how the primary relay is already driven from the `relay` field. Default-off when the field is missing is consistent with Constitution §I (safe defaults).

**Alternatives considered**:
- *Drive GPIO14 directly from a different network call* — rejected; doubles MCU↔server traffic and breaks atomicity.
- *Make GPIO14 an inversion of the primary relay* — rejected; not what the issue asks for and physically dangerous (could energize an accessory the operator isn't authorized for).

---

## R7. How should `always_enabled` semantics on `second_relay` be implemented?

**Decision**: When `second_relay.always_enabled` is true, the second relay's desired state in `machine_response` mirrors the primary relay's `relay_desired_state` exactly — no per-user authorization check is performed for the second relay, but the second relay still de-energizes whenever the primary does (oops, lockout, no operator, server reboot without persisted active state). This is implemented in `_resolve_second_relay` by short-circuiting on `always_enabled` to copy the primary state.

**Rationale**: Edge case in spec already specifies this. It is the only sane meaning of "always enabled" in the context of a relay that physically depends on the primary one.

**Alternatives considered**:
- *Reject `always_enabled: true` on `second_relay` at config-validation time* — rejected because the user (Q1 → Option C) explicitly chose to keep it accepted.
- *Treat `always_enabled` on `second_relay` as decoupled from the primary relay* — rejected; would let the second relay energize while the primary is off, which is unsafe and contradicts FR-004.

---

## R8. Does this feature change the `/api/reload-users` or `/api/reload-machines` (if any) flow?

**Decision**: No. There is no `reload-machines` endpoint today. Adding `second_relay` to `machines.json` requires a server restart, same as all other machine-config changes. This is an explicit non-goal for this feature.

**Rationale**: YAGNI (Constitution §III). Hot-reloading machine config is not requested in the issue.

**Alternatives considered**:
- *Add `/api/reload-machines` as part of this feature* — rejected as scope creep.

---

## R9. How are tests for the new behavior structured?

**Decision**:
- Unit tests for `Machine` / `MachineState` covering:
  - Config validation (positive: minimal, all-options, alias-only; negative: empty `authorizations_or`, unknown field, deeply-nested `second_relay`).
  - Authorization decision matrix: (primary auth y/n) × (second auth y/n) × (`unauthorized_warn_only` y/n) × (`always_enabled` y/n) — driven by parametrized fixtures.
  - State persistence: save → restart → load round-trip preserves second-relay state; loading old-format pickle (without second-relay keys) yields safe defaults.
- Integration tests via the Quart test client hitting `/machine/update`:
  - End-to-end tap-in / tap-out / oops / lockout sequences for second-relay-equipped machines.
  - Backwards-compat regression: a machine without `second_relay` must produce byte-identical responses to a fixture captured pre-feature.
- Slack-handler tests using the existing `tests/test_slack_handler.py` patterns for the new messages.
- Prometheus-collector tests verifying that the four new metrics emit only for second-relay machines.

**Rationale**: Constitution §II demands automated tests for all new logic; the parametrized matrix is the cheapest way to cover the authorization decision exhaustively.

**Alternatives considered**:
- *Single end-to-end test only* — rejected; would not exercise the auth decision matrix at the unit level and would leave coverage gaps.

---

## Summary

All technical-context items are resolved. Phase 1 (data model, contracts, quickstart) can proceed.
