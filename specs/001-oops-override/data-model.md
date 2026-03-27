# Data Model: Oops/Lockout Override Login

**Feature**: 001-oops-override | **Date**: 2026-03-16

## Entity Changes

### User (src/dm_mac/models/users.py)

**New field**:

| Field | Type | Default | Required in Schema | Description |
|-------|------|---------|-------------------|-------------|
| `oops_override` | `bool` | `False` | No (optional) | Whether user can perform override logins on oopsed/locked-out machines |

**Schema change** (users.json CONFIG_SCHEMA):
- Add `oops_override` as optional boolean property to user object schema
- Existing users.json files without this field remain valid (backward compatible)

**Impact on User class**:
- Add `oops_override` parameter to `__init__()` with default `False`
- Add to `as_dict` property
- Add to `__eq__` / comparison logic if applicable

**Impact on UsersConfig**:
- No changes needed -- `users_by_fob` lookup returns User objects which will have the new field

### MachineState (src/dm_mac/models/machine.py)

**New field**:

| Field | Type | Default | Persisted | Description |
|-------|------|---------|-----------|-------------|
| `is_override_login` | `bool` | `False` | Yes (pickle) | Whether machine is currently in override login state |

**State transitions**:

```
Normal state (not oopsed/locked) + override user inserts RFID:
  → Normal login (override has no effect)

Oopsed/locked state + override user inserts RFID:
  → is_override_login = True
  → relay = True
  → display = "OVERRIDE BY\n{name}"
  → LED = green
  → is_oopsed/is_locked_out remain unchanged

Override login active + RFID removed:
  → is_override_login = False
  → relay = False
  → Restore oops/lockout display and LED state
  → No oops/lockout Slack notifications

Override login active + machine reboots:
  → is_override_login = False
  → relay = False (reboot handler)
  → Oops/lockout state preserved

Override login active + admin clears oops/lockout via Slack/API:
  → Override login continues (relay stays on)
  → On card removal: is_override_login = False, normal idle state restored
```

**Persistence**:
- Add `is_override_login` to `_save_cache()` data dict
- `_load_from_cache()` handles missing field gracefully via existing `hasattr` pattern (defaults to `False`)

### NeonGetter Config (src/dm_mac/neongetter.py)

**New config field**:

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `oops_override_field` | `str` | `"OOPS_OVERRIDE"` | No (optional) | Neon custom field name for override authorization checkbox |

**Impact on CONFIG_SCHEMA**:
- Add as optional string property with default value

**Impact on static_fobs schema**:
- Add optional `oops_override` boolean field to static fob user objects

**Impact on run() flow**:
1. In `fields_to_get()`: If `oops_override_field` is configured, find matching checkbox custom field and add its ID to the retrieval list
2. In `run()`: For each user, check if the override field value equals `authorized_field_value`. Set `oops_override: True/False` accordingly.
3. In static_fobs processing: Read optional `oops_override` field, default to `False`

## Prometheus Metrics

**New metric**:

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `machine_override_login_state` | Gauge | `machine_name`, `display_name` | Whether machine is in override login state (1/0) |

## Slack Messages

**New SlackHandler method**: `log_override_login(machine, user_name)`

| Channel | Message Format |
|---------|---------------|
| `control_channel_id` | `"Override login on {display_name} by {user_name}."` |
| `oops_channel_id` | (no message) |

**Override card removal**: Uses existing `admin_log()` method

| Channel | Message Format |
|---------|---------------|
| `control_channel_id` | `"RFID logout on {display_name} by {user_name}; session duration {duration} (override session)"` |
| `oops_channel_id` | (no message) |
