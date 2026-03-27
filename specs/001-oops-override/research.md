# Research: Oops/Lockout Override Login

**Feature**: 001-oops-override | **Date**: 2026-03-16

## R1: Override State Representation in MachineState

**Decision**: Add a single `is_override_login: bool` field to MachineState (default `False`). The underlying `is_oopsed` and `is_locked_out` flags remain unchanged during an override login.

**Rationale**: The existing oops/lockout flags already track the machine's "true" state. The override login is a transient overlay -- the relay is activated and display shows "OVERRIDE BY" text, but the oops/lockout booleans stay True. On card removal, restoring the previous state is trivial: just turn off the relay and re-apply the oops/lockout display/LED settings, since the flags were never cleared.

**Alternatives considered**:
- *Snapshot/restore pattern* (save pre-override state separately): Unnecessary complexity since the oops/lockout flags are already preserved in-place.
- *New compound state enum*: Over-engineered for a boolean flag. The existing boolean pattern (`is_oopsed`, `is_locked_out`) is consistent and works well.

## R2: Override Authorization on the User Model

**Decision**: Add `oops_override: bool` field to User class, defaulting to `False`. Add as optional field in users.json CONFIG_SCHEMA.

**Rationale**: A simple boolean per-user is sufficient. The override capability is global (applies to all machines), so no per-machine mapping is needed. Making it optional in the schema preserves backward compatibility -- existing users.json files without the field will work, and users default to no override capability.

**Alternatives considered**:
- *Add to authorizations list*: Would conflate training/machine authorizations with an administrative capability. Override is fundamentally different from "trained on machine X".
- *Separate override_machines list*: YAGNI -- the spec explicitly states override applies to all machines.

## R3: NeonOne Field Integration

**Decision**: Add optional `oops_override_field` to neongetter CONFIG_SCHEMA, defaulting to `"OOPS_OVERRIDE"`. The field is treated as a checkbox custom field in Neon, identical to how authorization fields work -- if the field value equals `authorized_field_value` (e.g., "Training Complete"), the user gets `oops_override: True`.

**Rationale**: Follows the exact same pattern as existing authorization checkbox fields. The default field name "OOPS_OVERRIDE" is consistent with the Neon custom field naming convention used in the project. Making it optional means neongetter works without it configured.

**Alternatives considered**:
- *Hardcode field name*: Less flexible, inconsistent with the configurable pattern used for all other fields.
- *Use a different field type (dropdown, text)*: Checkbox is the established pattern for boolean authorization flags in this project.

## R4: Slack Notification Strategy

**Decision**: Add a `log_override_login()` method to SlackHandler that posts only to `control_channel_id` (not `oops_channel_id`). Use `admin_log()` for override card-removal events.

**Rationale**: The spec requires control-channel-only notification for override logins. A dedicated method (rather than reusing `admin_log()`) allows the message to clearly identify override events with structured information (machine name, user, override reason). Card removal during override uses `admin_log()` since it's just informational.

**Alternatives considered**:
- *Reuse admin_log()*: Would work but loses the ability to have a structured, distinctive message format for override events.
- *Post to oops channel too*: Explicitly rejected by spec -- the whole point is to avoid confusing oops-channel notifications.

## R5: Pickle State Backward Compatibility

**Decision**: No migration needed. The `_load_from_cache()` method uses `hasattr(self, k)` to only restore known fields. New `is_override_login` field defaults to `False` in `__init__`, so old pickle files without this field will load correctly with the field defaulting to `False`.

**Rationale**: The existing code already handles missing fields gracefully. A server upgrade with active machines will correctly see `is_override_login=False` for all machines, which is the correct state.

**Alternatives considered**:
- *Pickle migration script*: Unnecessary given the existing graceful handling.
- *Switch to JSON state files*: Out of scope and violates YAGNI.

## R6: _handle_rfid_insert Modification Strategy

**Decision**: In `_handle_rfid_insert()`, add an override check *before* the existing oops/lockout early-return blocks. When the user has `oops_override=True` and the machine is oopsed or locked out:
1. Set `is_override_login = True`
2. Set `relay_desired_state = True`
3. Set `display_text = f"OVERRIDE BY\n{user.preferred_name}"`
4. Set status LED to green (same as normal authorized login)
5. Set `current_user = user`
6. Log to Slack via `log_override_login()`
7. Return (skip the normal oops/lockout early-return)

When the user has `oops_override=True` but the machine is NOT oopsed or locked out, fall through to normal login behavior.

**Rationale**: Inserting the check before the oops/lockout blocks is the minimal change. The oops/lockout flags remain True, so `machine_response` still reports `oops_led: True` (matching the physical state). The override user sees the machine work, other members see the oops LED stays on.

## R7: _handle_rfid_remove Modification Strategy

**Decision**: In `_handle_rfid_remove()`, check `is_override_login` before resetting display/LED state. If `is_override_login` is True:
1. Clear `is_override_login = False`
2. Turn off relay
3. Restore oops/lockout display state based on current flags:
   - If `is_oopsed`: display = OOPS_DISPLAY_TEXT, LED = red
   - Elif `is_locked_out`: display = LOCKOUT_DISPLAY_TEXT, LED = orange
   - Else: display = DEFAULT_DISPLAY_TEXT, LED = off (handles case where admin cleared during override)
4. Log via `admin_log()` (no oops/unlock notifications)

**Rationale**: The restore logic is straightforward since the oops/lockout flags were never modified. The else branch handles the edge case where an admin cleared the oops/lockout via Slack/API during the override session.

## R8: Reboot During Override Login

**Decision**: The existing `_handle_reboot()` method already clears `current_user` and resets relay/display. Add clearing of `is_override_login = False` to `_handle_reboot()`. The oops/lockout flags survive the reboot (they're persisted), so the machine will show oops/lockout state after reboot.

**Rationale**: Consistent with existing reboot behavior -- reboot resets the active session but preserves machine configuration state.
