# Decatur Makers Machine Access Control (dm-mac)

[![Project Status: Concept – Minimal or no implementation has been done yet, or the repository is only intended to be a limited example, demo, or proof-of-concept.](https://www.repostatus.org/badges/latest/concept.svg)](https://www.repostatus.org/#concept)

This is a software and hardware project for using RFID cards/fobs to control use of various power tools and equipment in the [Decatur Makers](https://decaturmakers.org/ "‌") makerspace. It is made up of custom ESP32-based hardware (machine control units) controlling power to each enabled machine and running ESPHome, and a central access control/management/logging server application written in Python/Flask. Like our [“glue” server](https://github.com/decaturmakers/glue "‌") that powers the RFID-based door access control to the makerspace, dm-mac uses the [Neon CRM](https://www.neoncrm.com/ "‌") (or a local flat-file when in development mode) as its backend datastore.

## Software Components

At a high level, the system is made up of the central control server and the ESPHome configuration for the ESP32’s.

### Control Server

This is a Python/Flask application that provides authentication and authorization for users via RFID credentials, control of the ESP32-based machine control units;, and logging and monitoring as well as basic management capabilities.

**Why not use the Glue server?** First, because the glue server is currently running in a cloud hosting provider. That makes sense for its purpose, but less so for direct control of physical machines in our space. We want the machine access control system to always function, regardless of the state of our Internet connection, with low latency. We also aren’t concerned about reliability through a power outage, as that will also prevent the controlled machines from working. Secondly, having the business logic contained in a central server with relatively “dumb” machine control units on the machines allows for simpler management of the system.

### Machine Control Unit Software

The machine control units run ESPHome, because it is well-supported with an active community, requires minimal programming (just a YAML configuration), and allows updating and managing many devices wirelessly from a central point. The machine control units (and their ESPHome configuration) are relatively simple - they just react to events (RFID card insertion or removal, button press, or a timer ticking), send their current state to the control server via a HTTP POST, and receive a response with the intended state of their outputs (control relay, LCD screen, LEDs). All of the logic of the system is contained in the central control server.

In the event of an extended control server outage, special event, or other exigent circumstance, the machine control unit software is configured with a list of permanently-authorized RFID cards that will enable the machine without requiring authorization from the control server.

# Notes

## April 16th Notes

- 2 enclosures, one mains AC and one LV. Mains should ideally lock with a padlock, or else have tamper switch
  - mains relay should ideally have machine hard-wired to relay and then relay box plugs in to wall, or else machine plug is positively captured in enclosure. OR ELSE enclosure just has a clear label on it that bypassing the control by anyone other than DM Staff or an Area Technician will result in suspension of membership.
- AC enclosure - relay/contactor, 5V power supply for ESP32, [current clamp](https://esphome.io/components/sensor/ct_clamp "‌")
- ESP enclosure - wired up to it with a 6-conductor locking cable (power supply, current clamp, relay; maybe also tamper)
  - Has ESP32, fob reader ([wiegand](https://esphome.io/components/wiegand "‌")?), covered oops button, covered log out button, some sort of display, RGB or NeoPixel LED for status.
- software on ESPs - MicroPython or can this be done with ESPHome? Either way, need [central logging](https://esphome.io/components/logger#on-message "‌") and [Prometheus](https://esphome.io/components/prometheus "‌") stats
- ESP [calls ](https://esphome.io/components/http_request "‌")central auth server in space (SSL? encrypted? firewall? how to secure?) and receives boolean auth response; auth server handles caching the fob data from Glue
- user fobs-in, gets authenticated, machine turns on (buzzer/beeper and display feedback). Machine stays on for a configurable amount of time that counts down on display. Machine will not turn off if current clamp indicates it's still running (current draw above a specific level). When time expires AND machine is stopped (current clamp), or when user presses log out button, relay is shut off and user is logged out.
- oops button records a problem and posts to slack; user is prompted on display to post a photo and description to slack.

PS - Maybe the better, more-flexible plan is to just have the ESPs be relatively dumb interface units… they send input events (fob reads or button presses) back to a central server running on palantir ( [https://esphome.io/components/http_request](https://esphome.io/components/http_request "smartCard-inline") ) and receives a response that says what to put on the display, what the status LED should show, and what the relay state should be. Also every 1s while the relay is active, it makes a call with the reading from the current clamp, and gets back display/status LED/relay state values.

## May 28th Notes

Ok, I have the gist of the RFID card logic working as of [esphome-config.yaml](esphome-config.yaml) - it knows when an “authorized” card is scanned and then removed, and when an unauthorized or unknown card is scanned. That’s the very first rough PoC. Next steps are:

1. Minimal PoC local development auth server that takes a local JSON config listing fob codes that are known and what machines they’re authorized for; get the server to respond to the ESP with what to display on screen, and get the ESP to display that. ESP should send when a card is scanned or card sense changes to off.
2. Need a capacitor or similar on ESP, to ensure it doesn’t brown out when machine starts?
3. Add an LED output to the ESP to represent a relay output for the machine; update ESP and server so that’s also controlled properly.
4. Add an Oops button input to the ESP, and output for a LED on the button; send that input to the server, and have the server control the LED.
5. If Slack integration is enabled/secret is configured, post Oops to configurable channel.
6. Server exposes a Prometheus endpoint with information about each configured machine - status, user, etc.
7. Add current sensor input to ESP; if configured, significant changes in its value are reported back to the server. Server logs those changes and also reports them to Prometheus.
8. Server connects to Neon at bootup and every X minutes, pulls users from there and populates local database. This is cached on disk in event of connection issues.
9. Possibly a RGB LED on the control box for status information.
10. Web UI for controlling Oops/lockout status of machines.
11. Slack bot and status page for displaying machine status.

In terms of hardware, what I think makes the most sense is:

1. A main box that mounts near the user controls, with the ESP32, RFID reader, display, and LED. This is a standardized 3d-printed box design with the UI and RFID components on the front, a board inside, a connector on the back, and design provision for mounting with screws and a custom bracket on any side. The box halves would be secured with tamper-proof screws and an appropriate warning label over at least one screw.
2. A “power” box that would contain just:
   1. 120VAC (or 240VAC for special cases) to 5VDC power supply
   2. control relay*
   3. current sensor*
3. A 6-conductor cable connecting the two, likely shielded, using locking aircraft-style connectors

- The normal case we assume is a 120VAC power tool that’s essentially just a motor, where we want to control power to it and see if it’s running. For special cases, like the laser or other things that use lower-voltage (or at least lower-amperage) control circuits, we’d develop custom power boxes. It’s a simple enough interface - we have 2 wires for a relay control output from the ESP32 (which could be as simple as ground and a direct connection to an ESP32 pin, or could have an at-least-minimal relay in between), 2 wires that provide +5VDC and GND to the ESP32 and associated components in the control box, and 2 optional wires that provide output from a current clamp on the machine power input or some other method of sensing machine state.

Additional thoughts:

- We’ll need some people - I guess James and I at least, maybe a selection of Area Stewards - whose accounts can operate any tool. Should this just be a special check box? A hard-coded list?
- Need some way to display basic diagnostic data on the LCD screen, such as machine name, IP address, maybe version, etc. Maybe use some secret Oops button keypress, like 6 times in 3 seconds, or hold for 5 seconds, or something?

The server API should be dead-simple:

* On an event (card scan or removal or button press), POST to the server containing the event type, information (card ID) if applicable, machine name, current sensor value if applicable, and a shared secret string.
  * Aside from button presses or card changes, we’ll also have a timer event every X seconds that just updates the current sensor value, if applicable.
* Server responds with a simple JSON data structure containing what should be displayed on screen (written to global variable and printed to screen), desired state of the relay, and desired RGB LED state and/or Oops button LED state.

I would like the server to run on-premise within the building… (1) we want equipment authentication and logging to continue working even if the Internet is down, and (2) if the power is out this doesn’t matter anyway, so that’s not a concern.

Machine to server comm: card number or None, relay state (optional), oops button pressed, current draw (optional), machine name, maybe IP address and/or MAC address?

Server to machine reply: desired relay state, LCD message, LCD backlight state, status LED state.

Machine state representation, in database:

* machine name
* machine current IP
* relay state
* relay last state change time
* rfid_card_number (nullable)
* rfid card last state change time
* oopsed_since (nullable)
* current_draw (nullable; maybe integer? or maybe machine_is_on bool?)
* last_changed
