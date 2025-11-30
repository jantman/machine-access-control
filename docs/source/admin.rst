.. _admin:

Administration
==============

.. _admin.monitoring:

Monitoring
----------

The control server exposes a `Prometheus <https://prometheus.io/>`__-compatible metrics server endpoint at ``/metrics``. These metrics can be used to monitor the system's health, machine status, and usage patterns.

A pre-built :ref:`Grafana dashboard <admin.grafana_dashboard>` is provided for visualizing these metrics.

An example response from the metrics endpoint is:

::

    # HELP python_gc_objects_collected_total Objects collected during gc
    # TYPE python_gc_objects_collected_total counter
    python_gc_objects_collected_total{generation="0"} 11253.0
    python_gc_objects_collected_total{generation="1"} 23526.0
    python_gc_objects_collected_total{generation="2"} 4120.0
    # HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
    # TYPE python_gc_objects_uncollectable_total counter
    python_gc_objects_uncollectable_total{generation="0"} 0.0
    python_gc_objects_uncollectable_total{generation="1"} 0.0
    python_gc_objects_uncollectable_total{generation="2"} 0.0
    # HELP python_gc_collections_total Number of times this generation was collected
    # TYPE python_gc_collections_total counter
    python_gc_collections_total{generation="0"} 248.0
    python_gc_collections_total{generation="1"} 22.0
    python_gc_collections_total{generation="2"} 2.0
    # HELP python_info Python platform information
    # TYPE python_info gauge
    python_info{implementation="CPython",major="3",minor="12",patchlevel="7",version="3.12.7"} 1.0
    # HELP process_virtual_memory_bytes Virtual memory size in bytes.
    # TYPE process_virtual_memory_bytes gauge
    process_virtual_memory_bytes 8.1723392e+07
    # HELP process_resident_memory_bytes Resident memory size in bytes.
    # TYPE process_resident_memory_bytes gauge
    process_resident_memory_bytes 7.1622656e+07
    # HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
    # TYPE process_start_time_seconds gauge
    process_start_time_seconds 1.73115012004e+09
    # HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
    # TYPE process_cpu_seconds_total counter
    process_cpu_seconds_total 3.79
    # HELP process_open_fds Number of open file descriptors.
    # TYPE process_open_fds gauge
    process_open_fds 6.0
    # HELP process_max_fds Maximum number of open file descriptors.
    # TYPE process_max_fds gauge
    process_max_fds 1024.0
    # HELP machine_config_load_timestamp The timestamp when the machine config was loaded
    # TYPE machine_config_load_timestamp gauge
    machine_config_load_timestamp 1.689477248e+09
    # HELP user_config_load_timestamp The timestamp when the users config was loaded
    # TYPE user_config_load_timestamp gauge
    user_config_load_timestamp 1.689477248e+09
    # HELP app_start_timestamp The timestamp when the server app started
    # TYPE app_start_timestamp gauge
    app_start_timestamp 1.689477248e+09
    # HELP user_count The number of users configured
    # TYPE user_count gauge
    user_count 4.0
    # HELP fob_count The number of fobs configured
    # TYPE fob_count gauge
    fob_count 4.0
    # HELP machine_relay_state The state of the machine relay
    # TYPE machine_relay_state gauge
    machine_relay_state{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_relay_state{display_name="hammer",machine_name="hammer"} 0.0
    machine_relay_state{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_relay_state{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_relay_state{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_oops_state The Oops state of the machine
    # TYPE machine_oops_state gauge
    machine_oops_state{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_oops_state{display_name="hammer",machine_name="hammer"} 0.0
    machine_oops_state{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_oops_state{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_oops_state{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_lockout_state The lockout state of the machine
    # TYPE machine_lockout_state gauge
    machine_lockout_state{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_lockout_state{display_name="hammer",machine_name="hammer"} 0.0
    machine_lockout_state{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_lockout_state{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_lockout_state{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_unauth_warn_only_state The unauthorized_warn_only state of the machine
    # TYPE machine_unauth_warn_only_state gauge
    machine_unauth_warn_only_state{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_unauth_warn_only_state{display_name="hammer",machine_name="hammer"} 1.0
    machine_unauth_warn_only_state{display_name="permissive-lathe",machine_name="permissive-lathe"} 1.0
    machine_unauth_warn_only_state{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_unauth_warn_only_state{display_name="esp32test",machine_name="esp32test"} 1.0
    # HELP machine_last_checkin_timestamp The last checkin timestamp for the machine
    # TYPE machine_last_checkin_timestamp gauge
    machine_last_checkin_timestamp{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_last_checkin_timestamp{display_name="hammer",machine_name="hammer"} 0.0
    machine_last_checkin_timestamp{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_last_checkin_timestamp{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_last_checkin_timestamp{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_last_update_timestamp The last update timestamp of the machine
    # TYPE machine_last_update_timestamp gauge
    machine_last_update_timestamp{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_last_update_timestamp{display_name="hammer",machine_name="hammer"} 0.0
    machine_last_update_timestamp{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_last_update_timestamp{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_last_update_timestamp{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_rfid_present Whether a RFID fob is present in the machine
    # TYPE machine_rfid_present gauge
    machine_rfid_present{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_rfid_present{display_name="hammer",machine_name="hammer"} 0.0
    machine_rfid_present{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_rfid_present{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_rfid_present{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_rfid_present_since_timestamp The timestamp since the RFID was inserter into the machine
    # TYPE machine_rfid_present_since_timestamp gauge
    machine_rfid_present_since_timestamp{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_rfid_present_since_timestamp{display_name="hammer",machine_name="hammer"} 0.0
    machine_rfid_present_since_timestamp{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_rfid_present_since_timestamp{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_rfid_present_since_timestamp{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_current_amps The amperage being used by the machine if applicable
    # TYPE machine_current_amps gauge
    machine_current_amps{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_current_amps{display_name="hammer",machine_name="hammer"} 0.0
    machine_current_amps{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_current_amps{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_current_amps{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_known_user Whether a known user RFID is inserted into the machine
    # TYPE machine_known_user gauge
    machine_known_user{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_known_user{display_name="hammer",machine_name="hammer"} 0.0
    machine_known_user{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_known_user{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_known_user{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_uptime_seconds The machine uptime seconds
    # TYPE machine_uptime_seconds gauge
    machine_uptime_seconds{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_uptime_seconds{display_name="hammer",machine_name="hammer"} 0.0
    machine_uptime_seconds{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_uptime_seconds{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_uptime_seconds{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_wifi_signal_db The machine WiFi signal in dB
    # TYPE machine_wifi_signal_db gauge
    machine_wifi_signal_db{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_wifi_signal_db{display_name="hammer",machine_name="hammer"} 0.0
    machine_wifi_signal_db{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_wifi_signal_db{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_wifi_signal_db{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_wifi_signal_percent The machine WiFi signal in percent
    # TYPE machine_wifi_signal_percent gauge
    machine_wifi_signal_percent{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_wifi_signal_percent{display_name="hammer",machine_name="hammer"} 0.0
    machine_wifi_signal_percent{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_wifi_signal_percent{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_wifi_signal_percent{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_esp_temperature_c The machine ESP32 internal temperature in °C
    # TYPE machine_esp_temperature_c gauge
    machine_esp_temperature_c{display_name="Metal Mill",machine_name="metal-mill"} 0.0
    machine_esp_temperature_c{display_name="hammer",machine_name="hammer"} 0.0
    machine_esp_temperature_c{display_name="permissive-lathe",machine_name="permissive-lathe"} 0.0
    machine_esp_temperature_c{display_name="restrictive-lathe",machine_name="restrictive-lathe"} 0.0
    machine_esp_temperature_c{display_name="esp32test",machine_name="esp32test"} 0.0
    # HELP machine_status_led The machine status LED state
    # TYPE machine_status_led gauge
    machine_status_led{display_name="Metal Mill",led_attribute="red",machine_name="metal-mill"} 0.0
    machine_status_led{display_name="Metal Mill",led_attribute="green",machine_name="metal-mill"} 0.0
    machine_status_led{display_name="Metal Mill",led_attribute="blue",machine_name="metal-mill"} 0.0
    machine_status_led{display_name="Metal Mill",led_attribute="brightness",machine_name="metal-mill"} 0.0
    machine_status_led{display_name="hammer",led_attribute="red",machine_name="hammer"} 0.0
    machine_status_led{display_name="hammer",led_attribute="green",machine_name="hammer"} 0.0
    machine_status_led{display_name="hammer",led_attribute="blue",machine_name="hammer"} 0.0
    machine_status_led{display_name="hammer",led_attribute="brightness",machine_name="hammer"} 0.0
    machine_status_led{display_name="permissive-lathe",led_attribute="red",machine_name="permissive-lathe"} 0.0
    machine_status_led{display_name="permissive-lathe",led_attribute="green",machine_name="permissive-lathe"} 0.0
    machine_status_led{display_name="permissive-lathe",led_attribute="blue",machine_name="permissive-lathe"} 0.0
    machine_status_led{display_name="permissive-lathe",led_attribute="brightness",machine_name="permissive-lathe"} 0.0
    machine_status_led{display_name="restrictive-lathe",led_attribute="red",machine_name="restrictive-lathe"} 0.0
    machine_status_led{display_name="restrictive-lathe",led_attribute="green",machine_name="restrictive-lathe"} 0.0
    machine_status_led{display_name="restrictive-lathe",led_attribute="blue",machine_name="restrictive-lathe"} 0.0
    machine_status_led{display_name="restrictive-lathe",led_attribute="brightness",machine_name="restrictive-lathe"} 0.0
    machine_status_led{display_name="esp32test",led_attribute="red",machine_name="esp32test"} 0.0
    machine_status_led{display_name="esp32test",led_attribute="green",machine_name="esp32test"} 0.0
    machine_status_led{display_name="esp32test",led_attribute="blue",machine_name="esp32test"} 0.0
    machine_status_led{display_name="esp32test",led_attribute="brightness",machine_name="esp32test"} 0.0

.. _admin.grafana_dashboard:

Grafana Dashboard
-----------------

A pre-built Grafana dashboard is provided to visualize the metrics exposed by the Prometheus endpoint. The dashboard provides comprehensive monitoring and visualization of the machine access control system.

Dashboard Features
~~~~~~~~~~~~~~~~~~

The Grafana dashboard includes the following visualizations:

**System Status**

* Server uptime tracking
* User and RFID fob counts with historical trends
* Machine connectivity monitoring (5-minute check-in status)
* Machine lockout status overview

**Machine Usage Overview**

* Real-time relay state visualization (which machines are powered on)
* RFID presence indicators
* Oops button status monitoring
* Machine relay state timeline

**Machine Health & Connectivity**

* WiFi signal strength monitoring (both percentage and dB)
* ESP32 internal temperature tracking
* Machine controller uptime

**Usage Analytics**

* Current session duration tracking
* 24-hour usage distribution by machine
* Known user presence indicators

**Machine Details**

* Per-machine drill-down view with detailed metrics
* Selectable via dashboard variable dropdown

Importing the Dashboard
~~~~~~~~~~~~~~~~~~~~~~~

To import the dashboard into Grafana:

1. In Grafana, navigate to **Dashboards** → **Import**
2. Click **Upload JSON file** and select the dashboard JSON file
3. Select your Prometheus datasource when prompted
4. Click **Import**

The dashboard is configured with:

* 5-second auto-refresh rate (adjustable)
* 24-hour default time range
* Machine selector variable for detailed views

Dashboard JSON
~~~~~~~~~~~~~~

The complete Grafana dashboard JSON is available below:

.. literalinclude:: grafana-dashboard.json
   :language: json
   :linenos:
