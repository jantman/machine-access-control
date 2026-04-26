# Contract: `/api/machine/update` Protocol Additions

**Feature**: Second Relay Support
**Branch**: `002-second-relay-support`
**Date**: 2026-04-26

This document specifies the additive changes to the MCU↔server JSON request/response on `POST /api/machine/update`. The pydantic models in `src/dm_mac/models/api_schemas.py` MUST match.

---

## Request: `MachineUpdateRequest`

### Existing fields (unchanged)

`machine_name`, `oops`, `rfid_value`, `uptime`, `wifi_signal_db`, `wifi_signal_percent`, `internal_temperature_c`, `amps`.

### New optional field

| Field | Type | Required | Default | Description |
| ----- | ---- | -------- | ------- | ----------- |
| `second_relay_state` | `bool` | No | `null` (omitted) | Actual current GPIO14 state as known to the MCU. Reported by firmware that drives a second relay; older firmware omits this field. **Server-side, this field MUST be used for observability only — it MUST NOT feed authorization decisions.** |

### Backwards-compat invariants

- A request with `second_relay_state` absent MUST be accepted exactly as today (no validation error, no log warning).
- A request with `second_relay_state` present but the machine has no `second_relay` configured MUST be accepted; the value is ignored beyond optional logging at DEBUG.

---

## Response: `MachineUpdateResponse`

### Existing fields (unchanged)

`relay`, `display`, `oops_led`, `status_led_rgb`, `status_led_brightness`.

### New field

| Field | Type | Required | Default | Description |
| ----- | ---- | -------- | ------- | ----------- |
| `second_relay` | `bool` | Yes (always emitted) | `false` | Desired state of the second relay. For machines without `second_relay` configured, this is always `false`. For machines with `second_relay` configured, this reflects the authorization decision computed in `_resolve_second_relay`. |

### Display field invariant

The `display` field MUST be byte-identical between the pre-feature server and the post-feature server for any given (machine, operator, machine state) tuple. FR-009 forbids any LCD change driven by second-relay configuration. Tests SHALL pin the existing `display` text values for representative scenarios and refuse to let them drift.

### Firmware-compat invariant

Firmware that does not know about the `second_relay` response field MUST continue to operate the primary relay correctly. The new field is parsed by modern firmware via `root["second_relay"]`; older firmware never reads this key and is unaffected.

---

## Backwards-compatibility test plan

Two regression tests SHALL be added:

1. `test_update_response_for_single_relay_machine_only_adds_second_relay_false`: send a typical request to a machine without `second_relay` configured; assert the response is identical to a captured pre-feature response with the addition of `"second_relay": false`. (This pins the trade-off note from `data-model.md`.)
2. `test_update_request_without_second_relay_state_is_accepted`: send a request omitting `second_relay_state` entirely; assert the server returns 200 and the response is correct.

---

## Example: machine with `second_relay`, operator authorized for both

**Request** (modern firmware):

```json
{
  "machine_name": "laser_cutter",
  "oops": false,
  "rfid_value": "0014916441",
  "uptime": 3600.0,
  "wifi_signal_db": -54,
  "wifi_signal_percent": 92,
  "internal_temperature_c": 53.9,
  "second_relay_state": false
}
```

**Response**:

```json
{
  "relay": true,
  "display": "Welcome,\nAlice",
  "oops_led": false,
  "status_led_rgb": [0.0, 1.0, 0.0],
  "status_led_brightness": 0.5,
  "second_relay": true
}
```

## Example: machine with `second_relay`, operator authorized for primary only

**Response** (note `display` is byte-identical to today's "Welcome" — FR-009):

```json
{
  "relay": true,
  "display": "Welcome,\nAlice",
  "oops_led": false,
  "status_led_rgb": [0.0, 1.0, 0.0],
  "status_led_brightness": 0.5,
  "second_relay": false
}
```

## Example: machine without `second_relay`

**Response**:

```json
{
  "relay": true,
  "display": "Welcome,\nAlice",
  "oops_led": false,
  "status_led_rgb": [0.0, 1.0, 0.0],
  "status_led_brightness": 0.5,
  "second_relay": false
}
```
