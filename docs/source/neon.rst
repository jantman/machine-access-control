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

You can either save your configuration file to ``neon.config.json`` in the directory that you run ``neongetter`` from, or specify the full path to the file in the ``NEONGETTER_CONFIG`` environment variable.

.. _neon.config.schema:

Configuration Schema
++++++++++++++++++++

.. jsonschema:: dm_mac.neongetter.CONFIG_SCHEMA

.. _neon.running:

Usage
-----

TBD.

.. _neon.development:

Development
-----------

Testing of neongetter is slightly different, as it makes external API calls to an API that presumably returns sensitive personal information. The process for testing API calls to neon uses the `responses <https://github.com/getsentry/responses>`__ library for testing HTTP requests, and specifically uses the (as of v0.25.3) beta feature of recording actual HTTP responses to a file.

1. In :py:mod:`~.dm_mac.neongetter` add an ``from responses import _recorder`` import.
2. Decorate the method in question (generally :py:meth:`~.dm_mac.neongetter.NeonUserUpdater.run`) with ``@_recorder.record(file_path="tests/fixtures/test_neongetter/run-raw.yaml")`` (or a similar decorator for other methods).
3. Run neongetter with your actual real credentials. **DO NOT commit anything to git until instructed!**.
4. Assuming that it finished successfully and created/updated the responses YAML file, remove the import and decorator added in steps 1 and 2.
5. **IMPORTANT** Currently, only data in the fields enumerated in ``neon.config.json`` are sanitized in the following step!
6. Run ``NEONGETTER_CONFIG=tests/fixtures/neon.config.json tests/fixtures/test_neongetter/sanitizer.py tests/fixtures/test_neongetter/run-raw.yaml tests/fixtures/test_neongetter/run.yaml``
7. Examine the generated ``tests/fixtures/test_neongetter/run.yaml`` file and ensure it appears sanitized.
8. **IMPORTANT** Delete the original ``tests/fixtures/test_neongetter/run-raw.yaml`` file.
9. Add and commit to git.
