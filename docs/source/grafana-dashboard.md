# Grafana Dashboard Documentation

## Overview

This document provides comprehensive information about the Grafana dashboard for the Decatur Makers Machine Access Control (dm-mac) system. This dashboard visualizes metrics exposed by the `/metrics` Prometheus endpoint on the control server.

**Dashboard File**: `docs/source/grafana-dashboard.json`
**GitHub URL**: https://github.com/jantman/machine-access-control/blob/main/docs/source/grafana-dashboard.json
**Documentation**: `docs/source/admin.rst` (includes embedded dashboard JSON)

## Purpose

The dashboard provides real-time monitoring and historical visualization of:
- Machine operational status (relay state, usage)
- User authentication and RFID presence
- Machine health (WiFi connectivity, temperature, uptime)
- System health (server uptime, configuration state)
- Maintenance issues (oops button states, lockouts)

## Dashboard Configuration

### Basic Settings

- **Default Time Range**: 24 hours (`now-24h` to `now`)
- **Refresh Rate**: 5 seconds (adjustable)
- **UID**: `dm-mac-dashboard`
- **Title**: "Decatur Makers Machine Access Control"
- **Description**: GitHub URL to source file
- **Datasource**: Prometheus (uses variable `${DS_PROMETHEUS}`)

### Template Variables

- **`$machine`**: Machine selector variable
  - Query: `label_values(machine_relay_state, display_name)`
  - Used in the "Machine Details" section for per-machine drill-down
  - Auto-populated from Prometheus labels
  - Uses `display_name` (machine alias if set, otherwise machine name)

## Dashboard Sections

### 1. System Status Row (Top)

**Panel ID 1: Server Uptime**
- **Type**: Stat
- **Metric**: `app_start_timestamp * 1000`
- **Display**: Time since server started (shown as "X ago")
- **Position**: Top left (gridPos: {h: 4, w: 6, x: 0, y: 0})

**Panel ID 2: Users**
- **Type**: Stat with sparkline
- **Metric**: `user_count`
- **Display**: Current count with area graph showing trend
- **Position**: {h: 4, w: 3, x: 6, y: 0}
- **Note**: Shows historical changes to detect config updates

**Panel ID 3: RFID Fobs**
- **Type**: Stat with sparkline
- **Metric**: `fob_count`
- **Display**: Current count with area graph showing trend
- **Position**: {h: 4, w: 3, x: 9, y: 0}

**Panel ID 4: Machine Connectivity (5min)**
- **Type**: Stat
- **Metric**: `machine_last_checkin_timestamp > (time() - 300)`
- **Display**: Shows "Online" (green) or "Offline" (red) per machine
- **Position**: {h: 4, w: 6, x: 12, y: 0}
- **Logic**: Machines that checked in within last 5 minutes are online

**Panel ID 5: Machine Lockout Status**
- **Type**: Stat
- **Metric**: `machine_lockout_state`
- **Display**: "Available" (green) or "LOCKED OUT" (red)
- **Position**: {h: 4, w: 6, x: 18, y: 0}

### 2. Machine Usage Overview Row

**Panel ID 6: Machine Relay Status**
- **Type**: Stat
- **Metric**: `machine_relay_state`
- **Display**: "Idle" (blue) or "IN USE" (green) per machine
- **Position**: {h: 6, w: 8, x: 0, y: 5}

**Panel ID 7: RFID Presence**
- **Type**: Stat
- **Metric**: `machine_rfid_present`
- **Display**: "No RFID" (blue) or "RFID Present" (green)
- **Position**: {h: 6, w: 8, x: 8, y: 5}

**Panel ID 8: Machine Status (Oops Button)**
- **Type**: Stat
- **Metric**: `machine_oops_state == 0` (inverted logic)
- **Display**:
  - Value 1 (not oopsed): "OK" with **dark-gray** background
  - Value 0 (oopsed): "OOPS!" with **red** background
- **Position**: {h: 6, w: 8, x: 16, y: 5}
- **Design Note**: Gray for normal state keeps it visually quiet; red draws attention to problems

**Panel ID 9: Machine Relay State Over Time**
- **Type**: Timeseries
- **Metric**: `machine_relay_state`
- **Display**: Line graph showing 0 (off) or 1 (on) over time
- **Position**: {h: 8, w: 12, x: 0, y: 11}
- **Scale**: Linear (0-1 range)
- **Interpolation**: Step-after (shows discrete state changes)

**Panel ID 10: Time Since Last Check-In (Log Scale)**
- **Type**: Timeseries
- **Metric**: `time() - machine_last_checkin_timestamp`
- **Display**: Seconds since last check-in per machine
- **Position**: {h: 8, w: 12, x: 12, y: 11}
- **Scale**: **Logarithmic (base-10)**
- **Thresholds**:
  - Green: 0-60s (healthy)
  - Yellow: 60-300s (1-5 min, slightly delayed)
  - Orange: 300-600s (5-10 min, concerning)
  - Red: 600+ s (10+ min, connectivity issue)
- **Design Note**: Log scale allows seeing changes across machines with vastly different check-in intervals

### 3. Machine Health & Connectivity Row

**Panel ID 11: WiFi Signal Strength (%)**
- **Type**: Timeseries
- **Metric**: `machine_wifi_signal_percent`
- **Position**: {h: 8, w: 12, x: 0, y: 20}
- **Unit**: Percent
- **Legend**: Shows mean and min values

**Panel ID 14: WiFi Signal Strength (dB)**
- **Type**: Timeseries
- **Metric**: `machine_wifi_signal_db`
- **Position**: {h: 8, w: 12, x: 12, y: 20}
- **Unit**: dB
- **Legend**: Shows mean and min values
- **Note**: Both WiFi panels on same row for easy comparison

**Panel ID 12: ESP32 Temperature**
- **Type**: Timeseries
- **Metric**: `machine_esp_temperature_c`
- **Position**: {h: 8, w: 12, x: 0, y: 28}
- **Unit**: Celsius
- **Legend**: Shows mean and max values

**Panel ID 13: Machine Controller Uptime (Log Scale)**
- **Type**: Timeseries
- **Metric**: `machine_uptime_seconds`
- **Position**: {h: 8, w: 12, x: 12, y: 28}
- **Unit**: Seconds
- **Scale**: **Logarithmic (base-10)**
- **Design Note**: Log scale allows seeing changes for machines with both short and long uptimes
- **Use Case**: Some machines run forever, others reboot frequently; log scale makes all changes visible

### 4. Usage Analytics Row

**Panel ID 15: Current Session Duration**
- **Type**: Bar gauge
- **Metric**: `(time() - machine_rfid_present_since_timestamp) * on() (machine_rfid_present > 0)`
- **Display**: Horizontal bars showing active session length
- **Position**: {h: 8, w: 12, x: 0, y: 37}
- **Unit**: Duration

**Panel ID 16: Machine Usage (24h)**
- **Type**: Pie chart
- **Metric**: `sum(increase(machine_relay_state[24h])) by (machine_name)`
- **Display**: Donut chart showing relative usage distribution
- **Position**: {h: 8, w: 6, x: 12, y: 37}

**Panel ID 17: Known User Present**
- **Type**: Bar gauge
- **Metric**: `machine_known_user`
- **Display**: Shows Yes/No per machine
- **Position**: {h: 8, w: 6, x: 18, y: 37}

### 5. Machine Details Row (Variable-Driven)

This section uses the `$machine` template variable to show detailed stats for a selected machine.

**Panel IDs 18-28**: Individual stat panels showing:
- Relay State (18)
- Oops State (24)
- Lockout State (25)
- Temperature (26)
- WiFi Signal (27)
- Uptime (28)

**Note**: Current Draw panel (previously ID 29) was removed as the feature is not currently in use.

## Key Metrics Reference

### Prometheus Metrics Used

| Metric Name | Type | Description | Labels |
|------------|------|-------------|--------|
| `app_start_timestamp` | Gauge | Server start time (Unix timestamp) | None |
| `user_count` | Gauge | Total configured users | None |
| `fob_count` | Gauge | Total configured RFID fobs | None |
| `machine_config_load_timestamp` | Gauge | When machine config was loaded | None |
| `user_config_load_timestamp` | Gauge | When user config was loaded | None |
| `machine_relay_state` | Gauge | Machine relay on (1) or off (0) | display_name, machine_name |
| `machine_oops_state` | Gauge | Oops button pressed (1) or not (0) | display_name, machine_name |
| `machine_lockout_state` | Gauge | Machine locked out (1) or not (0) | display_name, machine_name |
| `machine_unauth_warn_only_state` | Gauge | Warn-only mode enabled (1) or not (0) | display_name, machine_name |
| `machine_last_checkin_timestamp` | Gauge | Last check-in time (Unix timestamp) | display_name, machine_name |
| `machine_last_update_timestamp` | Gauge | Last state update time (Unix timestamp) | display_name, machine_name |
| `machine_rfid_present` | Gauge | RFID fob present (1) or not (0) | display_name, machine_name |
| `machine_rfid_present_since_timestamp` | Gauge | When RFID was inserted (Unix timestamp) | display_name, machine_name |
| `machine_current_amps` | Gauge | Current amperage draw (if applicable) | display_name, machine_name |
| `machine_known_user` | Gauge | Known user RFID present (1) or not (0) | display_name, machine_name |
| `machine_uptime_seconds` | Gauge | Machine controller uptime in seconds | display_name, machine_name |
| `machine_wifi_signal_db` | Gauge | WiFi signal strength in dB | display_name, machine_name |
| `machine_wifi_signal_percent` | Gauge | WiFi signal strength as percentage | display_name, machine_name |
| `machine_esp_temperature_c` | Gauge | ESP32 internal temperature (°C) | display_name, machine_name |
| `machine_status_led` | Gauge | LED RGB values and brightness | display_name, led_attribute, machine_name |

### Calculated Metrics

Some panels use PromQL expressions rather than direct metrics:

- **Time Since Check-In**: `time() - machine_last_checkin_timestamp`
  - Returns seconds since last check-in
  - Higher values indicate connectivity problems

- **Machine Connectivity**: `machine_last_checkin_timestamp > (time() - 300)`
  - Returns 1 if checked in within last 5 minutes, 0 otherwise
  - Boolean check for online status

- **Oops State (Inverted)**: `machine_oops_state == 0`
  - Returns 1 if NOT oopsed, 0 if oopsed
  - Used because mappings work better with this logic

- **Current Session Duration**: `(time() - machine_rfid_present_since_timestamp) * on() (machine_rfid_present > 0)`
  - Shows duration only when RFID is present
  - Filters out machines with no active session

## Design Decisions & Rationale

### Logarithmic Scales

Two panels use logarithmic (base-10) scales:

1. **Machine Controller Uptime**
   - **Problem**: Some machines run for weeks (millions of seconds), others reboot frequently (hundreds of seconds)
   - **Solution**: Log scale makes proportional changes visible regardless of absolute values
   - **Example**: A machine going from 100s→200s shows similar visual change as 10,000s→20,000s

2. **Time Since Last Check-In**
   - **Problem**: Normal check-ins are ~5-30 seconds, but failed machines can go hours/days
   - **Solution**: Log scale allows seeing both normal variations and long outages
   - **Benefit**: Easy to spot when a machine transitions from normal to problem state

### Color Schemes

**Oops Button Panel**:
- Normal (OK): Dark gray background
- Problem (OOPS!): Red background
- **Rationale**: "Good news should be quiet, bad news should be loud" - gray keeps normal state visually neutral, red immediately draws attention to problems

**Connectivity Panel**:
- Online: Green
- Offline: Red
- **Rationale**: Clear binary state, green = good, red = needs attention

**Relay State Panel**:
- Idle: Blue
- In Use: Green
- **Rationale**: Both are normal states; blue for idle (passive), green for active (energy)

### Removed Features

**Machine Current Draw (Amperage)**:
- **Original Location**: Timeseries in Machine Usage Overview row
- **Removed**: Feature not currently implemented in hardware
- **Panel ID**: 10 was freed up and reused for "Time Since Last Check-In"
- **Future**: If amperage monitoring is added, restore as timeseries with thresholds for over-current detection

### Panel Layout Philosophy

- **Top row**: High-level system health at a glance
- **Second row**: Current machine states (what's happening now)
- **Third row**: Time series graphs for usage patterns
- **Fourth row**: Health monitoring (connectivity, temperature)
- **Fifth row**: Usage analytics and statistics
- **Bottom row**: Detailed per-machine view with variable selector

## Common Modifications

### Adding a New Metric Panel

1. **Choose Panel ID**: Find highest existing ID and increment
2. **Determine Position**: Use `gridPos` to specify location
   - Grid is 24 units wide
   - Common widths: 12 (half), 8 (third), 6 (quarter)
   - y-coordinate increases down the page
3. **Set Datasource**: Use `"uid": "${DS_PROMETHEUS}"`
4. **Configure Metric**: Add to `targets` array with PromQL expression
5. **Set Display Options**: Choose panel type (stat, timeseries, gauge, etc.)
6. **Add Color/Thresholds**: Define mappings or thresholds as needed

### Changing Time Range

Edit the `time` section near the end of the JSON:
```json
"time": {
  "from": "now-24h",  // Change this
  "to": "now"
}
```

Common values: `now-6h`, `now-12h`, `now-24h`, `now-7d`, `now-30d`

### Changing Refresh Rate

Edit the `refresh` field:
```json
"refresh": "5s"
```

Options: `"5s"`, `"10s"`, `"30s"`, `"1m"`, `"5m"`, `""` (disabled)

### Adding Thresholds/Colors

For stat panels, edit the `thresholds` section:
```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    {"color": "green", "value": null},  // Default
    {"color": "yellow", "value": 60},   // Above 60
    {"color": "red", "value": 300}      // Above 300
  ]
}
```

For value mappings (discrete states):
```json
"mappings": [
  {
    "options": {
      "0": {"color": "red", "text": "OFF"},
      "1": {"color": "green", "text": "ON"}
    },
    "type": "value"
  }
]
```

### Changing to/from Log Scale

In timeseries panels, edit `scaleDistribution`:

**Linear**:
```json
"scaleDistribution": {
  "type": "linear"
}
```

**Logarithmic**:
```json
"scaleDistribution": {
  "type": "log",
  "log": 10  // Base-10, can also use 2
}
```

## File Integration

### Location

The dashboard JSON is stored in `docs/source/grafana-dashboard.json` for two reasons:
1. It's documentation that should be versioned with the code
2. It can be embedded in the Sphinx documentation

### Documentation Integration

The file is embedded in `docs/source/admin.rst` using the `literalinclude` directive:

```rst
.. literalinclude:: grafana-dashboard.json
   :language: json
   :linenos:
```

This automatically includes the full JSON in the built documentation, ensuring docs always match the actual file.

### Updating Process

When modifying the dashboard:

1. Edit `docs/source/grafana-dashboard.json`
2. Test by importing into Grafana
3. Adjust as needed
4. Commit the JSON file
5. Documentation will auto-update on next Sphinx build

**Note**: The dashboard description field contains the GitHub URL, so users can always find the latest version.

## Import Instructions

### First-Time Import

1. In Grafana: **Dashboards** → **Import**
2. Click **Upload JSON file**
3. Select `docs/source/grafana-dashboard.json`
4. Choose your Prometheus datasource
5. Click **Import**

### Updating Existing Dashboard

**Option 1 - Overwrite (Recommended)**:
1. Note your current dashboard UID: `dm-mac-dashboard`
2. Import as above
3. Grafana will detect matching UID and offer to overwrite
4. Confirm overwrite

**Option 2 - Manual**:
1. Open existing dashboard settings (gear icon)
2. Go to **JSON Model**
3. Copy entire contents of `grafana-dashboard.json`
4. Paste and save

## Troubleshooting

### Panels Show "No Data"

- **Check**: Prometheus datasource is configured and accessible
- **Check**: `/metrics` endpoint is reachable from Prometheus
- **Check**: Machines are checking in (metrics are being generated)
- **Debug**: Try metric in Grafana's Explore view

### Template Variable Not Populating

- **Check**: Query `label_values(machine_relay_state, machine_name)` returns values
- **Check**: At least one machine has reported `machine_relay_state` metric
- **Fix**: Refresh dashboard or wait for metrics to appear

### Log Scale Shows Unexpected Results

- **Issue**: Log scales cannot display zero or negative values
- **Check**: Ensure metric never reaches exactly zero
- **Note**: For uptime, this is fine (uptime is always positive)
- **Note**: For time-since-checkin, zero is handled properly

### Colors Not Showing Correctly

- **Check**: `colorMode` in panel options is set to `"background"` or `"value"`
- **Check**: Mappings or thresholds match expected metric values
- **Debug**: View actual metric values in Explore view

## Future Enhancements

### Potential Additions

1. **Amperage Monitoring**: Restore current draw graphs when hardware supports it
2. **Alert Annotations**: Mark dashboard with Grafana alerts for offline machines
3. **Usage Heatmap**: Show which hours/days machines are used most
4. **User Statistics**: Track which users operate which machines (if data available)
5. **Maintenance Windows**: Annotate scheduled maintenance periods
6. **Cost Tracking**: If power monitoring is added, calculate energy costs
7. **Trend Analysis**: Add panels showing usage trends (week-over-week, etc.)

### Monitoring Best Practices

1. **Set up alerts**: Use Grafana alerting for:
   - Machines offline > 10 minutes
   - Temperature > threshold
   - WiFi signal < threshold
   - Oops state active > threshold time

2. **Regular review**: Check dashboard weekly for:
   - Machines with frequent oops events (maintenance needed)
   - WiFi connectivity issues (network problems)
   - Unusual usage patterns

3. **Capacity planning**: Use 24h usage pie chart to:
   - Identify heavily-used machines (may need backup/replacement)
   - Identify rarely-used machines (may need training/promotion)
   - Balance machine allocation in makerspace

## Version History

- **v1**: Initial dashboard creation
  - Basic metrics visualization
  - System status, machine usage, health monitoring
  - 24-hour default view
  - Auto-refresh every 5 seconds
  - Log scales for uptime and check-in time
  - Gray/red color scheme for oops button
  - Removed current draw panels (feature not in use)
  - Added time-since-checkin visualization

## References

- **Grafana Documentation**: https://grafana.com/docs/grafana/latest/
- **Prometheus Querying**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **PromQL Functions**: https://prometheus.io/docs/prometheus/latest/querying/functions/
- **Grafana Panel Types**: https://grafana.com/docs/grafana/latest/panels-visualizations/
- **Project Repository**: https://github.com/jantman/machine-access-control
- **Metrics Implementation**: `src/dm_mac/views/prometheus.py`
