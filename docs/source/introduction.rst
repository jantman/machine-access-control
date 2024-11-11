.. _introduction:

Introduction
============

This is a software and hardware project for using RFID cards/fobs to
control use of various power tools and equipment in the `Decatur
Makers <https://decaturmakers.org/>`__ makerspace. It is made up of
custom ESP32-based hardware (machine control units) controlling power to
each enabled machine and running ESPHome, and a central access
control/management/logging server application written in Python/Flask.
Like our `“glue” server <https://github.com/decaturmakers/glue>`__ that
powers the RFID-based door access control to the makerspace, dm-mac uses
the `Neon CRM <https://www.neoncrm.com/>`__ as its source for user data,
though that is completely optional and pluggable.

.. _introduction.software:

Software Components
-------------------

At a high level, the system is made up of the central control server and
the ESPHome configuration for the ESP32’s.

.. _introduction.control-server:

Control Server
~~~~~~~~~~~~~~

This is a Python/Flask application that provides authentication and
authorization for users via RFID credentials, control of the ESP32-based
machine control units;, and logging and monitoring as well as basic
management capabilities.

**Why not use the Glue server?** First, because the glue server is
currently running in a cloud hosting provider. That makes sense for its
purpose, but less so for direct control of physical machines in our
space. We want the machine access control system to always function,
regardless of the state of our Internet connection, with low latency. We
also aren’t concerned about reliability through a power outage, as that
will also prevent the controlled machines from working. Secondly, having
the business logic contained in a central server with relatively “dumb”
machine control units on the machines allows for simpler management of
the system.

.. _introduction.mcu-software:

Machine Control Unit Software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The machine control units run ESPHome, because it is well-supported with
an active community, requires minimal programming (just a YAML
configuration), and allows updating and managing many devices wirelessly
from a central point. The machine control units (and their ESPHome
configuration) are relatively simple - they just react to events (RFID
card insertion or removal, button press, or a timer ticking), send their
current state to the control server via a HTTP POST, and receive a
response with the intended state of their outputs (control relay, LCD
screen, LEDs). All of the logic of the system is contained in the
central control server.

In the event of an extended control server outage, special event, or
other exigent circumstance, the machine control unit software is
configured with a list of permanently-authorized RFID cards that will
enable the machine without requiring authorization from the control
server.

.. _introduction.hardware:

Hardware Components
-------------------

The hardware (see :ref:`hardware` for details) is made up of a main Machine Control Unit (MCU) that houses the RFID reader, display, buttons, processor, and a 10A control relay. The MCU has a GX16-8 connector that takes +5VDC power in and provides a dry contact connection to the relay output to control machine power. This can be connected to separate dedicated enclosure controlling AC mains power to a machine, or to something such as a VFD as needed.
