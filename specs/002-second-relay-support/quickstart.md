# Quickstart: Adding a Second Relay to a Machine

**Feature**: Second Relay Support
**Branch**: `002-second-relay-support`
**Date**: 2026-04-26

This is the administrator-facing walk-through for enabling a second, independently-gated output relay on an existing machine. It corresponds to **SC-004** in the spec ("administrator can configure end-to-end in under 10 minutes").

---

## Prerequisites

1. The MCU for the target machine must be running V1 hardware (connector pin 6 / GPIO14 wired and available).
2. The MCU must be flashed with the post-feature ESPHome firmware from `esphome-configs/2025.11.2/no-current-input.yaml` (or a derivative). Older firmware will accept the new server response but will not physically drive GPIO14.
3. The dm-mac server must be running a version that includes this feature.
4. You have shell/SSH access to the host running the dm-mac server, and the ability to restart it.

---

## Step 1: Identify the secondary authorization name

Check `users.json` (or your NeonOne sync output) for the `authorizations` field and pick the string that represents the additional training required for the accessory. Examples in this codebase use values like `laser_rotary`, `cnc_advanced`, etc. The exact spelling MUST match what is set on user records.

---

## Step 2: Edit `machines.json`

Add a `second_relay` block to the machine's existing entry:

```jsonc
{
  "laser_cutter": {
    "authorizations_or": ["laser_basic"],
    "alias": "Laser Cutter",
    "second_relay": {
      "authorizations_or": ["laser_rotary"],
      "alias": "Rotary Attachment"
    }
  }
}
```

Available options inside `second_relay`:

- `authorizations_or` (REQUIRED, non-empty list of strings)
- `unauthorized_warn_only` (optional bool, default false) — primary-authorized operators without secondary auth still get the second relay, but a warning is logged and Slacked.
- `always_enabled` (optional bool, default false) — second relay tracks the primary relay's state regardless of secondary auth.
- `alias` (optional string) — used in Slack and log lines that refer to the accessory.

Validate the JSON:

```bash
poetry run python -c "import json; json.load(open('machines.json'))"
```

---

## Step 3: Restart the dm-mac server

```bash
sudo systemctl restart dm-mac   # or however you run the server
```

The server validates `machines.json` at startup and will refuse to start if the `second_relay` block is malformed (e.g., empty `authorizations_or`, unknown field). Watch the logs for validation errors:

```bash
journalctl -u dm-mac -f
```

A successful start logs `Validating Users config` and `Users is valid` (existing log lines).

---

## Step 4: Verify in Slack

Tap your fob with full authorizations against the target machine. The Slack `admin_log` should read something like:

```
RFID login on Laser Cutter by authorized user Alice; Rotary Attachment authorized
```

Tap your fob with primary-only authorization (or borrow a member with that profile):

```
RFID login on Laser Cutter by authorized user Alice; Rotary Attachment NOT authorized — relay off
```

If the second relay is configured with `unauthorized_warn_only: true` and the operator lacks the secondary auth:

```
RFID login on Laser Cutter by authorized user Alice; Rotary Attachment WARN-ONLY override — relay on
```

If the second relay is configured with `always_enabled: true`:

```
RFID login on Laser Cutter by authorized user Alice; Rotary Attachment always-enabled — relay on
```

The token after `;` resolves to `second_relay.alias` if set, otherwise the literal string `second relay`.

---

## Step 5: Verify in Prometheus / Grafana

Query the new metrics:

```promql
machine_second_relay_configured{machine_name="laser_cutter"}
machine_second_relay_state{machine_name="laser_cutter"}
```

Both should be `1` while a fully-authorized operator's session is active. After tap-out, `machine_second_relay_state` returns to `0` while `machine_second_relay_configured` stays at `1`.

The existing `machine_relay_state` metric is unaffected.

---

## Step 6: Verify physical accessory behavior

The LCD does not change to indicate accessory state — by design. Test physically:

1. Tap in with primary-only auth → power-cycle / try the accessory → it should NOT operate.
2. Tap in with both auths → try the accessory → it SHOULD operate.
3. Press the oops button mid-session → both relays de-energize together.
4. Lock out the machine via Slack `lock <machine_name>` → both relays de-energize.

---

## Rolling back

To remove second-relay enforcement on a machine, delete the `second_relay` block from that machine's entry in `machines.json` and restart the server. The MCU's GPIO14 will be commanded off on the next checkin and the machine reverts to single-relay behavior.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| Server fails to start, error mentions `additionalProperties` | Typo in `second_relay` field name | Check spelling against the schema in [contracts/machines-config-schema.md](./contracts/machines-config-schema.md). |
| Server fails to start, error mentions `authorizations_or` | Missing or empty list | Provide at least one authorization string. |
| `machine_second_relay_state` is always 0 even for fully authorized users | Old firmware on the MCU is not driving GPIO14 | Flash modern firmware to the MCU. |
| Accessory works for users without the secondary auth | `unauthorized_warn_only: true` set, or `always_enabled: true` set | Check the config block. Remove the override if unintended. |
| LCD shows new wording about the accessory | Should not happen — file a bug | LCD is contractually unchanged (FR-009). |
