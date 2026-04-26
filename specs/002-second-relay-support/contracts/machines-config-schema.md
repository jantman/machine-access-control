# Contract: `machines.json` Configuration Schema

**Feature**: Second Relay Support
**Branch**: `002-second-relay-support`
**Date**: 2026-04-26

This document specifies the additions to the `machines.json` JSON Schema that ship with this feature. It is the authoritative description of the configuration contract; the implementation in `src/dm_mac/models/machine.py::CONFIG_SCHEMA` MUST match.

---

## Top-level shape

```jsonc
{
  // existing: per-machine entries keyed by machine name (^[a-z0-9_-]+$)
  "laser_cutter": {
    "authorizations_or": ["laser_basic"],
    "alias": "Laser Cutter",
    "unauthorized_warn_only": false,
    "always_enabled": false,
    "second_relay": { /* SecondRelayConfig — see below */ }
  }
}
```

---

## New: `second_relay` property

`second_relay` is an OPTIONAL property on each per-machine entry. Its value is an object with the following schema:

```yaml
type: object
required: ["authorizations_or"]
additionalProperties: false
properties:
  authorizations_or:
    type: array
    minItems: 1
    items:
      type: string
    description: |-
      List of authorizations any one of which is sufficient to energize the
      second relay. Must be non-empty. Even when always_enabled is true, this
      list is required for schema consistency.
  unauthorized_warn_only:
    type: boolean
    description: |-
      If true, the second relay energizes for primary-authorized operators
      lacking secondary auth, with a warning emitted to logs and Slack.
  always_enabled:
    type: boolean
    description: |-
      If true, the second relay tracks the primary relay's energized state
      regardless of operator's secondary authorization. The second relay
      never energizes while the primary is de-energized.
  alias:
    type: string
    minLength: 1
    description: |-
      Human-readable name for the accessory governed by the second relay.
      Used in Slack messages and structured logs that refer specifically
      to second-relay events.
```

### Implementation note

The full project schema lives in `src/dm_mac/models/machine.py::CONFIG_SCHEMA`. The current schema declares the per-machine option set inline under `patternProperties`. The implementation should be refactored so the per-machine option subset (without `second_relay` itself, to prevent recursion) is referenced from BOTH the root machine entry AND from inside `second_relay`, OR — to keep the diff minimal — duplicate the relevant subset inside the `second_relay` schema. Either is acceptable; the contract is the shape above.

---

## Validation behavior

| Input | Result |
| ----- | ------ |
| `second_relay` absent | Valid. Machine has no second relay; behavior is byte-identical to today. |
| `second_relay: {}` | INVALID. Missing required `authorizations_or`. |
| `second_relay: { "authorizations_or": [] }` | INVALID. `minItems: 1`. |
| `second_relay: { "authorizations_or": ["x"], "unknown_key": true }` | INVALID. `additionalProperties: false`. |
| `second_relay: { "authorizations_or": ["x"], "second_relay": {...} }` | INVALID. Nested `second_relay` not allowed (no recursion). |
| `second_relay: { "authorizations_or": ["x"], "always_enabled": true }` | Valid. Second relay tracks primary regardless of operator. |
| `second_relay: { "authorizations_or": ["x"], "alias": "Rotary" }` | Valid. Alias used in Slack/log messages. |
| `second_relay: { "authorizations_or": ["x"], "unauthorized_warn_only": true }` | Valid. Warn-only for second relay. |

---

## Error message contract

When validation fails, the error message MUST identify (at minimum):
1. The offending machine name (i.e., the parent key under the root object), AND
2. The offending field name within `second_relay` (e.g., `authorizations_or` or `unknown_key`).

The exact message wording is left to the `jsonschema` library's default formatter; we MUST NOT swallow or rewrite the validation error in a way that loses these two pieces of information.
