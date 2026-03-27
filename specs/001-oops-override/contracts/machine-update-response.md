# Contract: Machine Update Response

**Feature**: 001-oops-override | **Date**: 2026-03-16

## Endpoint: POST /machine/update

### Response Schema (unchanged)

The response schema does NOT change. The existing fields are sufficient to represent override login state:

```json
{
  "relay": true,
  "display": "OVERRIDE BY\nJohn",
  "oops_led": true,
  "status_led_rgb": [0.0, 1.0, 0.0],
  "status_led_brightness": 0.5
}
```

**Key observation**: During an override login, `relay` is `true` (machine powered) AND `oops_led` is `true` (oops LED remains lit). This combination does not occur during normal operation and visually signals to other members that the machine is still oopsed despite being powered on.

### Request Schema (unchanged)

No changes to the request payload. The override is determined server-side based on the user's RFID lookup, not by any MCU-sent flag.

### Backward Compatibility

- No new fields added to request or response
- No existing fields removed or re-typed
- MCUs do not need firmware updates

## Config Schema: users.json

### Change: Optional `oops_override` field

**Before**:
```json
{
  "fob_codes": ["1234567890"],
  "account_id": "123",
  "full_name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "preferred_name": "Johnny",
  "email": "john@example.com",
  "expiration_ymd": "2026-12-31",
  "authorizations": ["Woodshop 101"]
}
```

**After** (field is optional, defaults to false):
```json
{
  "fob_codes": ["1234567890"],
  "account_id": "123",
  "full_name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "preferred_name": "Johnny",
  "email": "john@example.com",
  "expiration_ymd": "2026-12-31",
  "authorizations": ["Woodshop 101"],
  "oops_override": true
}
```

**Backward compatibility**: Existing users.json files without `oops_override` remain valid. All users default to `oops_override: false`.

## Config Schema: neon.config.json

### Change: Optional `oops_override_field` setting

**Before** (all required fields):
```json
{
  "full_name_field": "Full Name (F)",
  "first_name_field": "First Name",
  "last_name_field": "Last Name",
  "preferred_name_field": "Preferred Name",
  "email_field": "Email 1",
  "expiration_field": "Membership Expiration Date",
  "account_id_field": "Account ID",
  "fob_fields": ["Fob10Digit"],
  "authorized_field_value": "Training Complete"
}
```

**After** (new optional field):
```json
{
  "full_name_field": "Full Name (F)",
  "first_name_field": "First Name",
  "last_name_field": "Last Name",
  "preferred_name_field": "Preferred Name",
  "email_field": "Email 1",
  "expiration_field": "Membership Expiration Date",
  "account_id_field": "Account ID",
  "fob_fields": ["Fob10Digit"],
  "authorized_field_value": "Training Complete",
  "oops_override_field": "OOPS_OVERRIDE"
}
```

**Backward compatibility**: Field is optional. When absent, no users receive override authorization.

## Prometheus Endpoint: GET /metrics

### New metric: machine_override_login_state

```
# HELP machine_override_login_state The override login state of the machine
# TYPE machine_override_login_state gauge
machine_override_login_state{display_name="Metal Mill",machine_name="metal-mill"} 0.0
machine_override_login_state{display_name="hammer",machine_name="hammer"} 1.0
```

**Labels**: Same as all other per-machine metrics (`machine_name`, `display_name`).
**Values**: `0.0` (no override login) or `1.0` (override login active).
