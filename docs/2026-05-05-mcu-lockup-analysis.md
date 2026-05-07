# MCU Heartbeat Lockup Analysis — 2026-05-05

## Incident summary

On **2026-05-05 14:18:53 ET**, four ESPHome-based MAC ESP32 units —
**Bronte**, **Grizzly Metal Lathe**, **Metal Mill**, and **Resaw** — all
stopped checking in to `mac-server` within **31 seconds of one another**.
The trigger was a server-side disk hang: one POST to
`/api/machine/update` took **30.6 s** to return **HTTP 200**.

After that single slow-but-successful request, all four MCUs sat
locked up — still WiFi-associated to their UniFi APs (confirmed via
per-MAC `unpoller_client_uptime_seconds`, zero drops across 23 h) but
doing no application work — until each was power-cycled
**~22 h 57 m later**.

This document analyzes the ESPHome configs at
`esphome-configs/2025.11.2/` to determine which component sends the
heartbeat, why a single delayed-but-200 response leaves the firmware
permanently locked up, and what concrete config or component changes
would close the failure mode.

## What sends the heartbeat

`esphome-configs/2025.11.2/no-current-input.yaml`, the `interval:`
block at **lines 377–430**, fires every 10 s (after a 30 s startup
delay) and POSTs JSON to `mac_url`. The same `http_request.post` body
is also duplicated in four other places:

- `wifi.on_connect` (line 54)
- `card_present.on_release` (line 161)
- `oops_button.on_press` (line 228)
- `wiegand.on_tag` (line 318)

All five blocks share the same problematic shape: no `timeout`, no
`on_error`, no failure counter, and a synchronous `http_request.post`
that runs on the main loop task.

## Timeout / retry / blocking behavior — as written

- **No `timeout:` set** at the `http_request:` component (line 119 is
  empty) and none on the action. ESPHome's default is **4.5 s**, but
  per esp-idf / ESPHome docs and bug history this is the per-recv
  socket timeout, not a true total-request bound — if the server
  trickles bytes (or a TCP keepalive arrives) the timer keeps resetting
  and the request can run far longer than 4.5 s. See ESPHome issues
  [#4103](https://github.com/esphome/issues/issues/4103),
  [#13669](https://github.com/esphome/esphome/issues/13669),
  [#6682](https://github.com/esphome/issues/issues/6682).
- **No `watchdog_timeout:` set.** On esp-idf this is what feeds (or
  stops feeding) the task WDT during the transfer phase; without it
  set, the WDT is fed throughout the whole HTTP exchange.
- **No `on_error:` handler** on any of the five posts — only
  `on_response`. A request that fails silently does nothing; nothing
  increments a failure counter, nothing reboots.
- **`http_request.post` is synchronous and runs on the main loop
  task.** While the request is in flight the entire ESPHome `loop()`
  is blocked — sensors don't update, the LCD doesn't refresh, no other
  automations run. WiFi keeps its association because `wifi`/`lwIP`
  runs in its own esp-idf task on the other core, which is exactly why
  the UniFi `unpoller_client_uptime_seconds` saw zero drops.
- **No application-level liveness watchdog.**
  `wifi.reboot_timeout: 1min` only fires on a *disconnect*, and
  `api.reboot_timeout: 0s` explicitly disables the native-API liveness
  reboot. Nothing is configured to reboot the ESP32 if `loop()` stops
  or if heartbeats stop succeeding while WiFi remains associated.
- **No `CONFIG_ESP_TASK_WDT_*` sdkconfig overrides.** The esp-idf task
  watchdog defaults to monitoring only the IDLE tasks; the loop task
  is not subscribed, and the panic handler is not enabled.

## Why a slow-but-200 response wedged the firmware

Three failures stack to produce the 23-hour lockup:

1. **30.6 s blocked loop.** The server stalled on disk but trickled
   enough bytes that esp-idf's recv timeout never tripped, so
   `esp_http_client_perform()` blocked the loop task for ~30 s.
   Espressif explicitly documents this:
   *"esp_http_client_perform blocks the task… when the server is down,
   the HTTP request blocks the rest of the task for a very long time"*
   (esp-idf [#12578](https://github.com/espressif/esp-idf/issues/12578)).
2. **The "trickle" path is worse than a clean error.** Because the
   response eventually returned **200** with a real body, no error
   path ran and no reset was triggered — the firmware happily processed
   the response and considered the cycle "successful." A 4.5 s clean
   timeout would have surfaced via `on_error`… except there is no
   `on_error` handler either.
3. **Component left in a wedged state after the long exchange.** This
   is the well-known symptom in ESPHome
   [#6677](https://github.com/esphome/issues/issues/6677)
   ("Device partially stops responding after HTTP Request failed") and
   [#2501](https://github.com/esphome/issues/issues/2501)
   ("http_request leaves ESP stuck"): display freezes, sensors stop
   updating, ping/WiFi keep working, only a hard reboot restores it.
   Maintainers' analysis: the http_request component sets an internal
   error flag without recovering; in newer versions there is also an
   unbounded read loop when `Content-Length` is missing or
   `max_response_buffer_size` is set
   ([#13669](https://github.com/esphome/esphome/issues/13669),
   [#6682](https://github.com/esphome/issues/issues/6682)).
   Once wedged, no watchdog kicks because (a) WiFi never disconnected,
   (b) `api.reboot_timeout: 0s`, (c) the task WDT isn't watching the
   loop. The device stays in this state indefinitely — exactly the
   22 h 57 m observation.

The "all four within 31 s" pattern is consistent with this: the
server's single 30.6 s stall delivered the same poisoned response to
all four units that happened to be in the middle of a heartbeat cycle,
wedging each one.

## Recommended changes (in priority order)

### 1. Add an application-level liveness watchdog *(highest leverage; closes the failure mode)*

Track the timestamp of the last successful POST, and reboot if it
grows stale. Add new globals plus a watchdog interval:

```yaml
globals:
  - id: last_ok_post_uptime
    type: uint32_t
    restore_value: false
    initial_value: '0'
  - id: consecutive_post_failures
    type: uint32_t
    restore_value: false
    initial_value: '0'

interval:
  - interval: 30s
    startup_delay: 120s
    then:
      - lambda: |-
          uint32_t now = (uint32_t) id(uptime_sensor).state;
          uint32_t last = id(last_ok_post_uptime);
          if (last == 0 || (now - last) > 90) {
            ESP_LOGE("WDOG", "No successful POST in %us; rebooting", now - last);
            App.safe_reboot();
          }
```

In every `on_response` (where the body is parsed today) set
`id(last_ok_post_uptime) = (uint32_t) id(uptime_sensor).state;` and
reset `consecutive_post_failures` to 0. Add `on_error:` blocks (see §4)
that increment `consecutive_post_failures` and call `App.safe_reboot()`
once the count crosses a small threshold (e.g. `>= 3`).

### 2. Bound any single POST to a few seconds

```yaml
http_request:
  timeout: 5s
  watchdog_timeout: 8s   # esp-idf only; caps the WDT-feed window during transfer
```

The `timeout` is the per-socket recv/send timeout (not bulletproof,
see issues above) but is still strictly better than the 4.5 s default
at correlated thresholds, because pairing it with `watchdog_timeout`
provides a real ceiling: when transfer exceeds `watchdog_timeout` the
task WDT stops being fed and (with the panic option below) will reset
the chip.

### 3. Enable the esp-idf task watchdog with panic

```yaml
esp32:
  board: esp32dev
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_ESP_TASK_WDT_TIMEOUT_S: "15"
      CONFIG_ESP_TASK_WDT_EN: y
      CONFIG_ESP_TASK_WDT_INIT: y
      CONFIG_ESP_TASK_WDT_CHECK_IDLE_TASK_CPU0: y
      CONFIG_ESP_TASK_WDT_CHECK_IDLE_TASK_CPU1: y
      CONFIG_ESP_TASK_WDT_PANIC: y
```

With `..._PANIC: y` the device resets instead of just logging when the
WDT fires. Combined with `watchdog_timeout: 8s`, a 15 s+ stuck
transfer reboots automatically.

### 4. Add `on_error` to every `http_request.post`

```yaml
on_error:
  then:
    - lambda: |-
        id(consecutive_post_failures) += 1;
        ESP_LOGW("HTTP", "POST failed; consec=%u", id(consecutive_post_failures));
    - if:
        condition:
          lambda: 'return id(consecutive_post_failures) >= 3;'
        then:
          - lambda: 'App.safe_reboot();'
```

### 5. Eliminate the duplicated POST blocks

The same ~50-line POST/parse block is copy-pasted five times. Move it
into a `script:` (with `mode: restart` so a new event preempts a stuck
one) and replace each occurrence with `script.execute: post_to_mac`.
This dramatically reduces the chance that future fixes drift between
the five copies.

### 6. Re-enable a real ESPHome-API reboot fallback (or remove API entirely)

`api.reboot_timeout: 0s` is fine *only* because there is no Home
Assistant. Consider either:

- removing the `api:` block entirely (one fewer task, one fewer thing
  to wedge), or
- keeping it but accepting that it is not a heartbeat watchdog for
  *this* server — the application-level watchdog in §1 is the one that
  matters.

### 7. Server-side defensive change

Independent of firmware: the original disk hang served a 30.6 s
**200**. If the server detects that a write to its state directory
exceeds e.g. 2 s, it should fail the request with a 503 instead of
returning 200, so even the current firmware would hit `on_error` and
(after fix §4) reboot.

## Summary of root cause

The firmware is missing every layer of defense that would have caught
this:

- no real total-request timeout,
- no `on_error` handler,
- no consecutive-failure reboot,
- no liveness-of-loop watchdog,
- no esp-idf task watchdog panic enabled,
- and the only existing reboots (WiFi disconnect / API disconnect)
  require the very signals that didn't fire in this incident.

A 30 s response that returns **200** is therefore the worst possible
outcome: it bypasses every error path that was available, and the
http_request component has known wedge bugs
([#6677](https://github.com/esphome/issues/issues/6677),
[#2501](https://github.com/esphome/issues/issues/2501))
that turn a one-time slow exchange into a permanent application
lockup. Adding §1 + §2 + §3 + §4 above is the minimum change set that
closes this.

## References

- [ESPHome #6677 — Device partially stops responding after "HTTP Request failed"](https://github.com/esphome/issues/issues/6677)
- [ESPHome #2501 — http_request leaves ESP stuck if there is no internet connection](https://github.com/esphome/issues/issues/2501)
- [ESPHome #6682 — http_request stucks on infinite loop when HTTP server does not send Content-Length](https://github.com/esphome/issues/issues/6682)
- [ESPHome #4103 — Timeout on http_request not respected in all cases](https://github.com/esphome/issues/issues/4103)
- [ESPHome #13669 — http_request read until timeout when max_response_buffer_size is set](https://github.com/esphome/esphome/issues/13669)
- [ESPHome #6493 — watchdog non functional during stuck http request](https://github.com/esphome/issues/issues/6493)
- [esp-idf #12578 — esp_http_client_perform slow / non connect](https://github.com/espressif/esp-idf/issues/12578)
- [esp-idf #6364 — httpclient unhandled error causes call to not return](https://github.com/espressif/esp-idf/issues/6364)
- [HTTP Request component docs (timeout / watchdog_timeout / on_error)](https://esphome.io/components/http_request/)
- [ESP-IDF Watchdogs reference (CONFIG_ESP_TASK_WDT_*)](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/wdts.html)
- [ESP HTTP Client API (esp_http_client_perform blocking semantics)](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html)
