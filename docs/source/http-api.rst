HTTP API
========

This page documents the HTTP API exposed by the MAC server.

The OpenAPI spec is also available at ``/openapi.json`` on a running server,
with interactive documentation at ``/docs`` (Swagger UI) and ``/redocs`` (ReDoc).

.. openapi:: openapi.json

Prometheus Metrics
------------------

``GET /metrics``

Returns Prometheus-compatible metrics in ``text/plain`` format. This endpoint
is not included in the OpenAPI spec as it does not return JSON.

See :py:mod:`dm_mac.views.prometheus` for details on the available metrics.
