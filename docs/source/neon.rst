.. _neon:

NeonOne Integration
===================

`Decatur Makers <https://decaturmakers.org/>`__ stores membership and training records
in our `Neon One CRM <https://www.neoncrm.com/>`__ account. We store machine access
rights (really, trainings / safety checks) as custom fields on members' Accounts.

Support for this is provided by the ``neongetter`` entrypoint (:py:mod:`dm_mac.neongetter`),
which will use the Neon One API to generate :ref:`configuration.users-json`.

.. _neon.config:

Configuration
-------------

First, export the name of your Neon organization as the ``NEON_ORG`` environment variable
and your Neon API key as the ``NEON_KEY`` environment variable.

You will then need to generate a ``neon.config.json`` configuration file. An example configuration file can be dumped to STDOUT by running ``neongetter --dump-example-config`` and a description of the fields can be seen in the below `JSON Schema <http://json-schema.org/>`__. In some cases you will need to know the names of fields and custom fields set up for Accounts in your Neon instance. This information can be
obtained by running ``neongetter --dump-fields``.

.. _neon.config.schema:

Configuration Schema
++++++++++++++++++++

.. jsonschema:: dm_mac.neongetter.CONFIG_SCHEMA

.. _neon.running:

Usage
-----

TBD.
