.. _configuration:

Configuration
=============

TBD.

.. _configuration.users-json:

users.json
----------

Users are configured via a ``users.json`` file in the current directory, or another file name/path specified in the ``USERS_CONFIG`` environment variable. This file defines all of the users and their contact information, as well as their RFID fob code(s) and the authorizations/trainings they have. If using the Neon One CRM, this file can be auto-generated from your CRM Accounts via the :ref:`neon`.

The schema of this file is as follows:

.. jsonschema:: dm_mac.models.users.CONFIG_SCHEMA

.. _configuration.machines-json:

machines.json
-------------

Machines are configured via a ``machines.json`` file in the current directory, or another file name/path specified in the ``MACHINES_CONFIG`` environment variable. This file lists all of the supported/configured machines and which authorization(s) are required to use them. Note that the names in this file must match the names configured in your ESPHome :ref:`hardware`. Machine names must be unqiue and can only contain alphanumeric characters, underscores, and dashes. No spaces, no dots.

The schema of this file is as follows:

.. jsonschema:: dm_mac.models.machine.CONFIG_SCHEMA

.. _configuration.machine-state-dir:

Machine State Directory
-----------------------

During operation, the state of each machine is cached on disk every time it's updated; this is done to ensure that a restart of the server will not affect running machines. As of this time, state is saved to a separate file for each machine. By default, these are saved in a ``machine_state`` subdirectory of the current directory, which is created if it does not exist. An alternate directory to save machine state to can be specified via the ``MACHINE_STATE_DIR`` environment variable.
