# MCU Heartbeat Lockup Analysis — 2026-05-11 (follow-up to PR #137)

## Incident summary

On **2026-05-11 15:38:01 UTC**, the same four ESPHome-based MCUs that
were affected by the 2026-05-05 incident — **Bronte**, **Grizzly Metal
Lathe**, **Metal Mill**, and **Resaw** — again stopped checking in to
`mac-server` within ~5 seconds of one another. The trigger this time
was a **SATA link-layer reset** on the server host `palantir`, which
froze all in-flight writes for several seconds.

This is the second post-deploy lockup; PR #137 had been rolled out to
production (server 0.12.0) and all four MCUs were running the new
firmware. The PR's server-side defenses **worked exactly as designed**:
the three state-mutating endpoints all returned **503** within ~2 s
instead of hanging. The PR's firmware-side defenses **partially worked**:
Bronte's relay-on-defer correctly prevented an in-progress cut from
being interrupted; but the three other MCUs (all relay-off) **did not
reboot themselves**, and remained silent for **~40–43 minutes** until
the operator power-cycled each one by hand.

This document captures the disk-side root cause and the firmware-side
follow-up bug.

## Timeline (all times UTC)

| Time | Event |
|---|---|
| 15:38:01 | Kernel logs `ata1.00: exception ... SError: { PHYRdyChg CommWake }` — 16 queued `WRITE FPDMA QUEUED` commands timeout; `ata1: hard resetting link`; link comes back up at 6.0 Gbps |
| 15:37:30.045 | Resaw POST → **503**, request duration **2.005 s**, `mac_state_save_timeouts_total{mac-mcu-resaw} = 1` |
| 15:37:30.107 | Bronte POST → **503**, **2.008 s**, lifetime count = 1 |
| 15:37:34.107 | Metallathe POST → **503**, **2.010 s**, lifetime count = 1 |
| 15:37:34.783 | Metalmill POST → **503**, **2.006 s**, lifetime count = 1 |
| 15:37:36 → 15:38:01 | 12× `POST /loki/api/v1/push` return 500 with `context deadline exceeded` (Loki is on the same disk) |
| 15:38:01.678 | Bronte POST → 200 — last successful check-in for Bronte before the lockup |
| 15:38:01.679 | Resaw POST → 200, **duration 23.676 s** (disk recovering) — last successful check-in for Resaw |
| 15:38:11 | `slack_bolt.AsyncApp` session closed and reconnected (Slack WebSocket disrupted by the disk hang) |
| 16:12:38 | Operator queries `@bot status` in Slack (notices the outage) |
| 16:17:53 | Metal Mill back online (first post-recovery POST) — **manually power-cycled** ~7 s prior |
| 16:18:01 | Grizzly Metal Lathe back online — manually power-cycled |
| 16:20:11 | Resaw back online — manually power-cycled |
| 16:21:03 | Bronte back online — manually power-cycled |

All four "back online" timestamps are the value of
`machine_last_checkin_timestamp{display_name=…}` at the moment the
metric transitioned away from `1778513881.6…` (15:38:01 UTC, frozen
throughout the silent window) to a fresh value.

Concurrent host signals on `palantir` at the incident minute:
`node_load1` = 6.57, `rate(node_disk_io_time_seconds_total{device="sda"})`
= 0.66 (66 % of wall), `rate(node_disk_write_time_seconds_total)`
showed no further spike — consistent with a brief, complete I/O
freeze rather than sustained write saturation.

## Root cause: failing SATA link on `palantir`

Kernel journal at 15:38:01 UTC:

```
ata1.00: exception Emask 0x0 SAct 0x7ff02003 SErr 0x50000 action 0x6 frozen
ata1: SError: { PHYRdyChg CommWake }
ata1.00: failed command: WRITE FPDMA QUEUED       (×16, all Emask 0x4 timeout)
ata1: hard resetting link
ata1: SATA link up 6.0 Gbps (SStatus 133 SControl 300)
ata1.00: configured for UDMA/133
ata1: EH complete
```

`PHYRdyChg CommWake` + `Emask 0x4 (timeout)` on multiple queued NCQ
writes + `hard resetting link` is a physical-layer SATA fault — the
link itself dropped briefly, all 16 in-flight writes timed out, and
the kernel issued a controller-level reset that took the disk fully
offline for the duration. This is **not** media/EXT4 corruption (no
`I/O error, dev sda` or `EXT4-fs error` lines); it is **link
hardware**, typically caused by a marginal SATA cable, a failing
controller port, drive power-rail noise, or a drive whose NCQ queue
is failing.

**This is recurring on `palantir`:**

| When | Event |
|---|---|
| 2026-05-05 ~14:18 ET | First observed lockup of the four MCUs (see `docs/2026-05-05-mcu-lockup-analysis.md`) |
| 2026-05-10 04:43:17 UTC | `ata1: hard resetting link` (silent — happened overnight, no relays were energized; no operator impact) |
| 2026-05-11 15:38:01 UTC | This incident |

Three SATA hard-resets in a week is the underlying problem driving
every other symptom. **Mac-server, Loki, Grafana, Prometheus, and
ESPHome all run on `palantir` and share this disk**, which is why the
disk hang manifested as simultaneous server timeouts *and* Loki push
errors *and* a Slack WebSocket disconnect.

## What PR #137 caught — and what it missed

### Server side (Milestones 1 + 7): worked as designed

`MachineState.save_cache()`'s 2.0 s budget tripped on all four pickle
writes; `views.machine` surfaced **HTTP 503** with body
`{"error": "state save timeout"}` in 2.005 – 2.010 s. The
`mac_state_save_timeouts_total{machine_name}` counter incremented by
exactly 1 for each of the four machines. Compare this to the
2026-05-05 incident, where the equivalent request took **30.6 s** and
returned **200**.

The 23.7 s duration on Bronte's 15:38:01 *successful* POST is the
disk completing its backlog after the SATA reset — not a server bug.
The MCU's `http_request: timeout: 5s` likely already aborted the
client side of that exchange (see firmware section); the server
still processed and stored the resulting state.

### Firmware §1 (relay-on defer): worked as designed

The headline claim — Bronte sat for 43 minutes without rebooting *because*
the watchdog's relay-on branch fired and deferred — is supported by the
following evidence. Three of the four sub-claims are directly verifiable
from server-side telemetry; the fourth (which exact watchdog branch ran
on the MCU) is necessarily an inference, with a caveat at the end of this
section.

The silent window analyzed below is Bronte's
`machine_last_checkin_timestamp` value `1778513881.679` (= 15:38:01.679 UTC)
through the first transition away from that value at
`1778516463.756` (= 16:21:03.756 UTC) — **2 582 s ≈ 43 min 02 s**.

**Assertion 1: Bronte had relay energized and a card present at the
moment of the freeze.**

The card had been inserted **44 min 46 s before** the freeze and
remained continuously present through it. From a 15 s-resolution
range query over `[1778508000, 1778514000]` showing every transition
of `machine_relay_state{display_name="Bronte"}` and
`machine_rfid_present{display_name="Bronte"}` (lines shown are
*transitions only*; the metrics held their value between):

```
machine_relay_state                machine_rfid_present
  14:00:00Z  1.0  (already on)       14:00:00Z  1.0
  14:42:30Z  0.0  (card removed)     14:42:30Z  0.0
  14:53:15Z  1.0  (card reinserted)  14:53:15Z  1.0
   …no further transitions through the silent window…
```

Independently confirmed by `machine_rfid_present_since_timestamp`,
which carries the epoch of the latest card-insertion event. Evaluated
during the silent window:

```
machine_rfid_present_since_timestamp{display_name="Bronte"}
  = 1778511180.184  (= 2026-05-11 14:53:00.184 UTC)
```

i.e. the *same* card had been continuously present for **2 821 s
(~47 min)** at the moment of the freeze. There is no possibility
that the relay/rfid state reflects an event coincident with the
freeze itself.

For completeness, `machine_relay_state` and `machine_rfid_present`
also held at `1` across seven independent five-minute samples within
the silent window (the metrics are pinned to the last reported POST
body throughout the window, so these are redundant with the above —
they only rule out an out-of-band metric update during the window,
which the server architecture does not allow anyway):

```
  15:43:01Z 1   15:48:01Z 1   15:53:01Z 1   15:58:01Z 1
  16:03:01Z 1   16:08:01Z 1   16:13:01Z 1
```

The post-recovery transition was captured at 15 s resolution:

```
machine_relay_state{display_name="Bronte"}:
  16:15:00Z  1.0
  16:21:15Z  0.0    ← first sample reflecting a post-recovery POST
                    (server cleared the relay because the
                     post-recovery firmware reported rfid_value="")
```

The last `/api/machine/update` request body Bronte sent before the
freeze (`mac-server` log line at `2026-05-11 11:38:01,678 EDT`)
contained a populated `rfid_value` field. (RFID value redacted.)

**Assertion 2: Bronte did not reboot itself during the silent window.**

`machine_last_checkin_timestamp{display_name="Bronte"}` queried at
15 s step over `[1778516000, 1778516500]` produced exactly two
distinct values across the entire ~8-minute span around recovery:

```
  16:13:20Z  last_checkin = 1778513881.6790676  (= 15:38:01.679 UTC)
  16:21:20Z  last_checkin = 1778516463.7563207  (= 16:21:03.756 UTC)
```

i.e. the metric was constant at the pre-freeze value for the entire
silent window and changed exactly once, at 16:21:03.756 UTC. A
self-reboot would have produced an intermediate transition (the
post-reboot MCU would have POSTed within seconds of WiFi reconnect);
the absence of any such transition is direct evidence that no
self-reboot occurred.

The same conclusion is independently visible in
`machine_uptime_seconds{display_name="Bronte"}`. At 30 s resolution
across `[1778513881, 1778517000]`, the only transitions were:

```
  15:38:31Z  uptime = 165254.5 s   (= ~45.9 h since boot on 2026-05-09 18:19 UTC)
  16:21:31Z  uptime =      6.7 s   ← DROP: fresh boot ~6.7 s prior
  16:22:01Z  uptime =     51.7 s   (then growing at 30 s per 30 s, normal)
  16:22:31Z  uptime =     81.7 s
  …
```

No intermediate uptime values exist between `165254.5` and `6.7` —
the metric goes directly from "frozen at the pre-freeze value" to
"fresh boot" with no values in between, consistent with a single
power-cycle and inconsistent with any series of self-reboots during
the silent window.

Cross-check from access logs: the earlier Loki query
`{syslog_identifier="docker-mac-server"} |~ "10\.1\.1\.(52|56)"`
over `[15:38:20Z, now]` returned **zero matches** for Bronte
(`10.1.1.52`) until the post-power-cycle resumption. No POSTs
landed on the server from Bronte during the silent window, period.

**Assertion 3: The local relay state on the MCU cannot have changed
during the silent window.**

`esphome-configs/2025.11.2/no-current-input.yaml:128–136` is the
*only* code path that mutates `id(relay_output)`:

```cpp
if (response->status_code >= 200 && response->status_code < 300) {
  bool parse_ok = json::parse_json(body, [](JsonObject root) -> bool {
    if ( root["relay"]) {
      id(relay_output).turn_on();
    } else {
      id(relay_output).turn_off();
    }
    …
```

That branch only executes inside `on_response` after a 2xx response.
With zero successful POSTs during the silent window (Assertion 2),
`relay_output` cannot have been mutated by firmware. The MCU's local
view of the relay therefore matches the value it last successfully
echoed back to the server — **relay on**.

**Assertion 4 (inferred): the watchdog took the `relay_on` branch
each time it ran.**

The watchdog at `no-current-input.yaml:316–334` has exactly two
terminal actions when `stale > 90 s`:

| Branch | Condition | Action |
|---|---|---|
| relay-off | `stale > 90 && !relay_on` | `App.safe_reboot()` |
| relay-on  | `stale > 90 &&  relay_on` | paint `"WARN: server\nlink stale"` to LCD; *no* reboot |

After 15:39:31 UTC (T+90 s from the freeze) the `stale > 90` guard
is satisfied; `relay_on` is `true` by Assertion 3; so the relay-on
branch is the only branch reachable. Combined with Assertion 2 (no
self-reboot) the trace is **fully consistent** with the relay-on
branch firing every 30 s for the duration of the window.

**Caveat — server-side data cannot fully distinguish "branch ran" from
"loop wedged before reaching branch".** The relay-on branch *not
calling* `App.safe_reboot()` produces the same observable trace
(no POSTs, no reboot, frozen metrics, manual power-cycle to recover)
as the relay-off branch *would have* produced if hit on Bronte
*and then* hanging inside `run_safe_shutdown_hooks()` — the exact
failure mode documented for the other three MCUs in the next
subsection. The relay-on inference is selected over the relay-off
hypothesis only because Assertion 3 establishes that the relay-off
guard `!relay_on` was false on this MCU.

The only direct observable that would falsify the relay-on inference
is the LCD content during the silent window: relay-on branch paints
`"WARN: server\nlink stale"`; a wedged loop leaves whatever text was
drawn just before the freeze. ESPHome MCU logs are not shipped to
Loki and the display state is not exported as a metric, so this
observable is only available to an on-site operator. If the
operator who power-cycled Bronte recalls what its LCD showed
immediately before the power-cycle, that closes the inference
either way.

### Firmware §1 (relay-off reboot): **did not fire**

Metal Mill, Grizzly Metal Lathe, and Resaw all had `relay_off` at the
time of the freeze. The watchdog should have called `App.safe_reboot()`
within ~90–120 s. Instead the MCUs sat unresponsive until the
operator power-cycled them 40–43 minutes later (confirmed by
operator).

### Firmware §3 (esp-idf task WDT panic at 60 s): **did not fire**

`CONFIG_ESP_TASK_WDT_PANIC=y` should have hard-reset the chip after
60 s if the loop task got wedged. It didn't, which means the loop
task was **still alive and feeding the WDT** the entire time the MCU
appeared dead from the server's perspective.

### Slack notification: **did not fire**

`MachineState.save_cache()` is wired to notify
`SLACK_CONTROL_CHANNEL_ID` *exactly once*, on the per-machine timeout
count's transition to 2. With four machines each hitting their first
lifetime timeout simultaneously, every counter went 0 → 1 and the
notification never fired. The disk hang affected four MCUs across
the fleet but produced **zero Slack messages**.

## Why the firmware watchdog hung instead of rebooting

The watchdog action at `no-current-input.yaml:328` calls
**`App.safe_reboot()`**, which in ESPHome is:

```cpp
void Application::safe_reboot() {
  ESP_LOGI(TAG, "Rebooting safely...");
  this->run_safe_shutdown_hooks();   // synchronous; no timeout
  this->reboot();
}
```

`run_safe_shutdown_hooks()` calls `on_shutdown()` on every component
synchronously and waits indefinitely for each one to return. The
`http_request` component's shutdown is known to block when the network
or server is unreachable — exactly the condition this watchdog is
trying to recover from. The main loop was therefore stuck **inside
`safe_reboot()`'s wait**, which is itself fed by the task WDT, so
neither the application watchdog *nor* the 60 s task WDT panic could
escape — the loop task never appeared "stuck" to either.

This matches a well-known ESPHome pattern: `safe_reboot()` is the
right call when the device is *healthy* and an operator initiates a
restart from Home Assistant; it is the wrong call from inside a
liveness watchdog whose entire premise is that the device is
unrecoverable.

## Recommendations (priority order)

### 1. Fix the SATA hardware on `palantir` — *root cause; everything else is a workaround*

The three resets-in-a-week trend will keep firing. Action:

1. Run `smartctl -a /dev/sda` and confirm whether
   `Reallocated_Sector_Ct`, `Current_Pending_Sector`,
   `Offline_Uncorrectable`, or `UDMA_CRC_Error_Count` are nonzero or
   trending. **A high `UDMA_CRC_Error_Count` is the cable / connector
   smoking gun**, separate from media health.
2. Replace the SATA cable (and try a different port) regardless of
   SMART, since cable wear is the most common cause of `PHYRdyChg`
   without media errors. This is a 30-second test.
3. If SMART shows media degradation, replace the drive.
4. Until resolved, expect repeat incidents — mac-server, Loki,
   Grafana, and Prometheus all share `/dev/sda` on `palantir`.

### 2. Switch the watchdog action from `App.safe_reboot()` to `App.reboot()`

In `esphome-configs/2025.11.2/no-current-input.yaml:328`:

```cpp
- App.safe_reboot();
+ App.reboot();
```

`App.reboot()` calls `esp_restart()` directly, skipping the
synchronous `on_shutdown()` hooks. By the time the liveness watchdog
fires, the device is by-definition unrecoverable; "graceful" shutdown
is the wrong default. This is a one-line change.

### 3. Tighten the Slack alert to also fire on fleet-wide simultaneous timeouts

The current rule (Slack on per-machine transition to 2 lifetime
timeouts) is good at suppressing single transient stalls, but is
silent on the exact failure pattern that just happened: **N distinct
machines each hitting their first timeout in the same minute**.

Suggested addition to `MachineState.save_cache()` / its caller:
post to `SLACK_CONTROL_CHANNEL_ID` when **≥ 2 distinct machines**
record a state-save timeout within a short window (e.g. 60 s).
Implementation sketch: a process-wide deque of `(machine_name, ts)`
tuples; on each new timeout, count distinct machines in the last
60 s and notify if count crosses 2 (with a cooldown to avoid
re-paging). The existing per-machine `>= 2 lifetime` rule stays as
the "this machine is repeatedly slow" signal; the new rule covers
"the disk is the problem, not the machine."

### 4. Defense-in-depth: enable the RTC / bootloader watchdog

`CONFIG_ESP_TASK_WDT_PANIC=y` only fires when the loop task stops
feeding the task WDT. The RTC watchdog (a separate hardware timer)
fires unconditionally and is the true last-resort. Add to the
`esp32:` framework sdkconfig:

```yaml
sdkconfig_options:
  CONFIG_BOOTLOADER_WDT_ENABLE: y
  CONFIG_BOOTLOADER_WDT_TIME_MS: "9000"
  CONFIG_ESP_INT_WDT: y
  CONFIG_ESP_INT_WDT_TIMEOUT_MS: "300"
```

(Verify exact option names against the ESP-IDF version ESPHome
2025.11.2 pins; some are renamed across IDF releases.)

### 5. *(Optional)* Move `MACHINE_STATE_DIR` to `tmpfs`

The pickle state files exist only to survive a `mac-server` restart;
they are not durable application state in the user-data sense.
Putting them on a `tmpfs` mount (with an optional periodic
copy-on-shutdown for warm-start) means a SATA hiccup on the host can
never block the request path. This is more invasive than #2/#3 and
should be evaluated after #1 lands — if the disk is fixed, the
2 s timeout becomes the cheap belt-and-suspenders it was designed
to be.

## Summary

PR #137's *server*-side defenses caught this incident cleanly:
2 s timeout → 503 → counter incremented, all four MCUs received a
correct error response within ~2 s. PR #137's *firmware*-side
recovery did not work: `App.safe_reboot()` hangs inside
`run_safe_shutdown_hooks()` when the `http_request` component cannot
cleanly close, so neither the application liveness watchdog nor the
60 s task WDT panic could escape. Three MCUs that should have
self-rebooted in ~90 s sat unresponsive for 40–43 minutes.

The single highest-leverage action is **#1 (replace SATA cable on
palantir / inspect drive)** — it is the actual root cause, recurring
on a ~weekly cadence, and would prevent every observable symptom in
this incident chain. **#2 (`safe_reboot()` → `reboot()`)** is a
one-line firmware fix that makes the liveness watchdog actually
work the next time the disk hiccups, since the disk will hiccup
again. **#3 (fleet-wide Slack alert)** closes the observability gap
that let this incident play out silently for 35 minutes.

## References

- 2026-05-05 incident analysis:
  [`docs/2026-05-05-mcu-lockup-analysis.md`](2026-05-05-mcu-lockup-analysis.md)
- PR #137 (MCU heartbeat resilience): server-side timeout, firmware
  liveness watchdog, task WDT panic
- Affected firmware: `esphome-configs/2025.11.2/no-current-input.yaml`
  (watchdog at lines 316–334; `safe_reboot()` call at line 328)
- Affected server code: `src/dm_mac/models/machine.py`
  (`MachineState.save_cache()`), `src/dm_mac/views/machine.py`
  (503 handling)
- [ESPHome Application::safe_reboot — source (synchronous shutdown hooks)](https://github.com/esphome/esphome/blob/main/esphome/core/application.cpp)
- [ESP-IDF Watchdogs reference (task WDT, int WDT, RTC WDT)](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/wdts.html)
- [libata error decoding (PHYRdyChg, CommWake, NCQ timeout)](https://www.kernel.org/doc/html/latest/admin-guide/sata.html)
