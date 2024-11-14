Decatur Makers Machine Access Control (dm-mac)
==============================================

.. image:: https://www.repostatus.org/badges/latest/concept.svg
   :alt: Project Status: Concept – Minimal or no implementation has been done yet, or the repository is only intended to be a limited example, demo, or proof-of-concept.
   :target: https://www.repostatus.org/#concept
.. image:: https://github.com/jantman/machine-access-control/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/jantman/machine-access-control/actions/workflows/tests.yml

This is a software and hardware project for using RFID cards/fobs to
control use of various power tools and equipment in the `Decatur
Makers <https://decaturmakers.org/>`__ makerspace. It is made up of
custom ESP32-based hardware (machine control units) controlling power to
each enabled machine and running ESPHome, and a central access
control/management/logging server application written in Python/Quart.
Like our `“glue” server <https://github.com/decaturmakers/glue>`__ that
powers the RFID-based door access control to the makerspace, dm-mac uses
the `Neon CRM <https://www.neoncrm.com/>`__ as its source for user data,
though that is completely optional and pluggable.

For full documentation, see:
https://jantman.github.io/machine-access-control/

License
-------

Distributed under the terms of the `MIT
license <https://github.com/jantman/machine_access_control/blob/main/LICENSE>`__,
*Machine_Access_Control* (``dm_mac``) is free and open source software.
