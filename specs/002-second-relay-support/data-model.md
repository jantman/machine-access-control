# Phase 1 Data Model: Second Relay Support

**Feature**: Second Relay Support
**Branch**: `002-second-relay-support`
**Date**: 2026-04-26

This document describes the entities affected by this feature, their fields, validation rules, and state transitions.

---

## Entity: `SecondRelayConfig` (NEW)

Holds the authorization rules governing a machine's second relay. Constructed during `MachinesConfig._load_and_validate_config()` from a `second_relay` block in `machines.json`.

### Fields

| Field | Type | Required | Default | Notes |
| ----- | ---- | -------- | ------- | ----- |
| `authorizations_or` | `List[str]` | Yes | — | Non-empty list. Operator must hold ≥1 of these to energize the second relay (subject to `unauthorized_warn_only` / `always_enabled` overrides). |
| `unauthorized_warn_only` | `bool` | No | `False` | If true, energize the second relay even for primary-authorized operators lacking secondary auth, but emit a warning log + Slack message. |
| `always_enabled` | `bool` | No | `False` | If true, second relay tracks primary relay's energized state regardless of secondary authorization. Per-user secondary auth is not evaluated. |
| `alias` | `Optional[str]` | No | `None` | Human-readable name used in Slack/log lines that refer specifically to the second relay (e.g., "Laser Cutter — Rotary Attachment"). |

### Validation rules

- `authorizations_or` MUST be a list of at least one string when `always_enabled` is `false`. (Same rule as root machine config.)
- When `always_enabled` is `true`, `authorizations_or` MUST still be present and non-empty (consistency with root config; the list is unused at decision time but kept for symmetry and future flexibility).
- `alias`, if present, MUST be a non-empty string.
- The `second_relay` block MUST NOT itself contain a nested `second_relay` (no recursion). Schema enforces via explicit `additionalProperties: false`.
- Unknown fields MUST be rejected at config load time (`additionalProperties: false`).

### Relationships

- Owned 0:1 by a `Machine`. A machine has at most one `SecondRelayConfig`. A `SecondRelayConfig` belongs to exactly one machine.

---

## Entity: `Machine` (EXISTING — extended)

### New fields

| Field | Type | Default | Notes |
| ----- | ---- | ------- | ----- |
| `second_relay` | `Optional[SecondRelayConfig]` | `None` | Set during construction if the `second_relay` block is present in this machine's `machines.json` entry. |

### Existing fields

`name`, `authorizations_or`, `unauthorized_warn_only`, `always_enabled`, `alias`, `state` — unchanged.

### `as_dict` (used by `/machine/<name>` admin views and tests)

Add `second_relay` key with the dict-ified `SecondRelayConfig` when present, or omit the key entirely when absent (preserves byte-identical output for single-relay machines).

---

## Entity: `MachineState` (EXISTING — extended)

Tracks frozen state at a point in time, including the current operator, primary-relay desired state, oops/lockout, and now second-relay state.

### New fields

| Field | Type | Default | Notes |
| ----- | ---- | ------- | ----- |
| `second_relay_desired_state` | `bool` | `False` | Whether the server wants the second relay energized. Sent to the MCU in the response payload. |
| `second_relay_authorization` | `Optional[str]` | `None` | One of `"granted"`, `"denied"`, `"warn"`, `"always_enabled"`, or `None` (no `second_relay` configured). Used by Slack/logs/metrics. |

### Existing fields

`last_checkin`, `last_update`, `rfid_value`, `rfid_present_since`, `current_user`, `relay_desired_state`, `is_oopsed`, `is_locked_out`, `is_override_login`, `current_amps`, `display_text`, `uptime`, `status_led_rgb`, `status_led_brightness`, `wifi_signal_db`, `wifi_signal_percent`, `internal_temperature_c` — unchanged.

### Pickle serialization

`_save_cache()` adds the two new fields to its dict literal. `_load_from_cache()` is unchanged in structure — its existing `hasattr(self, k)` guard means missing keys (older pickle files) leave the `__init__` defaults in place, and unknown keys (newer pickle files than this code) are silently ignored.

### State transitions for `second_relay_desired_state`

The second-relay state is computed at the end of every `update()` call (and on lockout/unlock/oops/unoops/reboot) by `_resolve_second_relay`:

```
if machine.second_relay is None:
    second_relay_desired_state = False
    second_relay_authorization = None
elif primary relay is off (no operator, oops, lockout, etc.):
    second_relay_desired_state = False
    second_relay_authorization = None
elif machine.second_relay.always_enabled:
    second_relay_desired_state = True
    second_relay_authorization = "always_enabled"
elif user holds any of second_relay.authorizations_or:
    second_relay_desired_state = True
    second_relay_authorization = "granted"
elif machine.second_relay.unauthorized_warn_only:
    second_relay_desired_state = True
    second_relay_authorization = "warn"
else:
    second_relay_desired_state = False
    second_relay_authorization = "denied"
```

If `_resolve_second_relay` raises for any reason (defensive guard), it MUST set `second_relay_desired_state = False` and `second_relay_authorization = "denied"` (Constitution §I, fail-closed).

### State transitions for primary-de-energizing events

| Event | Primary effect | Second-relay effect |
| ----- | -------------- | ------------------- |
| RFID removed (`_handle_rfid_remove`) | relay off, user cleared | `second_relay_desired_state = False`, `second_relay_authorization = None` |
| Oops (`oops`) | relay off, user cleared, display = OOPS | same as RFID removed |
| Lockout (`lockout`) | relay off, user cleared, display = LOCKOUT | same as RFID removed |
| Reboot detected (`_handle_reboot`) | relay off (or restored if `always_enabled`), user cleared | always reset to `False` / `None`; if root `always_enabled` AND `second_relay.always_enabled`, set both to `True` / `"always_enabled"` |
| Unlock / unoops with `always_enabled` root | relay on (always-on) | if `second_relay.always_enabled`, mirror; otherwise off |

---

## Entity: `MachineUpdateRequest` (EXISTING pydantic — extended)

### New optional field

| Field | Type | Default | Notes |
| ----- | ---- | ------- | ----- |
| `second_relay_state` | `Optional[bool]` | `None` | Reported by modern firmware as the actual GPIO14 state. Server uses for observability only; does not feed authorization decisions. Older firmware omits this field entirely (pydantic optional with default). |

---

## Entity: `MachineUpdateResponse` (EXISTING pydantic — extended)

### New optional field

| Field | Type | Default | Notes |
| ----- | ---- | ------- | ----- |
| `second_relay` | `bool` | `False` | The desired state of the second relay. Always present in the response, defaulting to `False` for machines without `second_relay` configured (firmware that does not know about this field ignores it). |

We deliberately ALWAYS emit `second_relay` (even for single-relay machines) with value `False` because pydantic's response serialization is positional/keyed and the cost is one boolean per response. This avoids a conditional path in firmware that would otherwise need to distinguish "field absent" from "field false".

> **Trade-off note**: This means single-relay machines' response payloads gain one new key. FR-006 says behavior "for events not related to the second relay" must be identical; we read this as functional behavior rather than literal byte-identity of the response. If a stricter byte-identity reading is required, we can flip to "omit the field unless `second_relay` is configured" — see [contracts/mcu-update-protocol.md](./contracts/mcu-update-protocol.md). The single-relay response gaining one key is consistent with how `oops_led` etc. are always present today.

---

## Configuration file: `machines.json`

A machine entry with `second_relay`:

```json
{
  "laser_cutter": {
    "authorizations_or": ["laser_basic", "laser_advanced"],
    "alias": "Laser Cutter",
    "second_relay": {
      "authorizations_or": ["laser_rotary"],
      "alias": "Rotary Attachment",
      "unauthorized_warn_only": false
    }
  }
}
```

A machine entry without `second_relay` (unchanged from today):

```json
{
  "drill_press": {
    "authorizations_or": ["drill_press_basic"]
  }
}
```

---

## Persisted state file: `machine_state/<machine_name>-state.pickle`

After this feature, the persisted dict has the additional keys `second_relay_desired_state` and `second_relay_authorization`. Existing files load with these defaulted.
