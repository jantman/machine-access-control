HTTP API
========

This page documents the HTTP API exposed by the MAC server.

The OpenAPI spec is also available at ``/openapi.json`` on a running server,
with interactive documentation at ``/docs`` (Swagger UI) and ``/redocs`` (ReDoc).

.. openapi:: openapi.json

State Save Timeout (HTTP 503)
-----------------------------

The endpoints that mutate machine state — ``POST /api/machine/update``,
``POST/DELETE /api/machine/oops/<machine_name>``, and
``POST/DELETE /api/machine/locked_out/<machine_name>`` — bound the time
spent persisting state to disk to ``STATE_SAVE_TIMEOUT_SEC`` (2.0
seconds). If the underlying disk hangs and the write exceeds this
budget, the handler returns:

::

    HTTP/1.1 503 Service Unavailable
    Content-Type: application/json

    {"error": "state save timeout"}

This is the recommended path for the firmware to recover from a stuck
disk on the server: the MCU sees a clean error, leaves its current
relay state alone, and retries on its next 10-second heartbeat. Without
this bound, a slow-but-eventually-successful 200 response can wedge the
firmware via ESPHome ``http_request`` issues such as `#6677
<https://github.com/esphome/issues/issues/6677>`_.

Each timeout increments the per-machine ``mac_state_save_timeouts_total``
Prometheus counter. When the lifetime per-machine count reaches 2 or
more, a notification is posted to ``SLACK_CONTROL_CHANNEL_ID``; a single
transient timeout is logged and counted but does not page.

Second Relay Protocol Additions
-------------------------------

``POST /api/machine/update`` accepts an optional additive request field and emits
an additive response field to support the per-machine ``second_relay``
configuration (see :ref:`configuration.machines-json.second_relay`):

* Request — ``second_relay_state`` (boolean, optional): The actual current
  state of the second relay as known to the MCU. Reported by firmware that
  drives a second relay; older firmware omits this field. The server uses
  this for observability only and never for authorization decisions.
* Response — ``second_relay`` (boolean, always emitted, defaults to
  ``false``): Desired state of the second relay. For machines without
  ``second_relay`` configured this is always ``false``. Firmware that does
  not know about this field simply ignores it.

The ``display`` field is byte-identical between pre-feature and post-feature
servers for any given (machine, operator, machine state) tuple. ``second_relay``
configuration never causes LCD changes.

Prometheus Metrics
------------------

``GET /metrics``

Returns Prometheus-compatible metrics in ``text/plain`` format. This endpoint
is not included in the OpenAPI spec as it does not return JSON.

For machines with ``second_relay`` configured, the following additional
metrics are emitted (one sample per machine, with labels ``machine_name``,
``display_name``, and ``second_relay_alias``):

* ``machine_second_relay_state`` — whether the second relay is currently
  energized (0/1)
* ``machine_second_relay_configured`` — always ``1`` for machines with a
  ``second_relay`` block
* ``machine_second_relay_unauth_warn_only`` — the ``unauthorized_warn_only``
  config flag (0/1)
* ``machine_second_relay_always_enabled`` — the ``always_enabled`` config
  flag (0/1)

These metrics are not emitted at all for machines without ``second_relay``,
keeping cardinality minimal.

The ``mac_state_save_timeouts_total`` counter (one sample per machine)
exposes the lifetime count of writes to the per-machine pickle that
exceeded ``STATE_SAVE_TIMEOUT_SEC``. See `State Save Timeout (HTTP 503)`_
above for the firmware-facing behavior.

See :py:mod:`dm_mac.views.prometheus` for details on the available metrics.
