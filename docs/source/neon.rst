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

In order to activate the newly-updated users config immediately (i.e. without restarting the machine-access-control server), set the ``MAC_USER_RELOAD_URL`` environment variable to the full URL to the ``/api/reload-users`` endpoint. If you are running MAC in a Docker container and neongetter in the same container (i.e. via ``docker exec``), you could set ``MAC_USER_RELOAD_URL=http://localhost:5000/api/reload-users`` on the container itself.

.. _neon.config.schema:

Configuration Schema
++++++++++++++++++++

.. jsonschema:: dm_mac.neongetter.CONFIG_SCHEMA

.. _neon.config.static_fobs:

Static User Entries
+++++++++++++++++++

The configuration file supports an optional ``static_fobs`` field that allows you to specify user entries that will be added directly to the generated ``users.json`` file without querying the NeonOne API. This is useful for:

* Administrative/emergency access fobs to be used if there are problems with NeonOne
* Fobs for group events where multiple people may share access
* Temporary fobs for users who do not already have their own fob

The ``static_fobs`` field is an array of user objects with the following required fields:

* ``fob_codes``: Array of RFID fob codes for this user
* ``account_id``: Unique account identifier
* ``email``: Email address
* ``full_name``: Full name of the user
* ``first_name``: First name
* ``last_name``: Last name
* ``preferred_name``: Preferred name
* ``expiration_ymd``: Membership expiration date in YYYY-MM-DD format
* ``authorizations``: Array of authorization/training field names

**Example:**

.. code-block:: json

    {
      "full_name_field": "Full Name (F)",
      "first_name_field": "First Name",
      "last_name_field": "Last Name",
      "preferred_name_field": "Preferred Name",
      "email_field": "Email 1",
      "expiration_field": "Membership Expiration Date",
      "account_id_field": "Account ID",
      "fob_fields": ["Fob10Digit"],
      "authorized_field_value": "Training Complete",
      "static_fobs": [
        {
          "fob_codes": ["9999999999"],
          "account_id": "admin-1",
          "email": "admin@example.com",
          "full_name": "Admin User",
          "first_name": "Admin",
          "last_name": "User",
          "preferred_name": "Admin",
          "expiration_ymd": "2099-12-31",
          "authorizations": ["Woodshop 101", "CNC Router"]
        }
      ]
    }

**Important Notes:**

* Static users are merged with NeonOne users in the final ``users.json`` file
* Duplicate fob codes between static users and NeonOne users will cause an error
* Duplicate fob codes within static users themselves will also cause an error
* Static users follow the same validation rules as NeonOne users

.. _neon.config.fields:

Authorization and Custom Fields
+++++++++++++++++++++++++++++++

This script uses custom fields on users' Neon Accounts to store whether or not they've received the training required for specific machines. The custom fields must be "checkbox" type and must use the same option name to indicate that an account has completed the training; the examples in this project use "Training Complete" as the option name, but that is configurable using the "authorized_field_value" configuration file option.

For each user, their list of authorizations will be made up of the custom field names, which on their account have a value matching the "authorized_field_value".

.. _neon.running:

Usage
-----

Set up your configuration file and environment variables as described above, then run ``neongetter``. If all goes well, it will write a ``users.json`` file in the current directory; a different output path can be specified with the ``-o`` option.

.. _neon.fob-adder:

Neon Fob Adder
--------------

The ``neon-fob-adder`` tool (:py:mod:`dm_mac.neon_fob_adder`) provides an interactive command-line interface for adding RFID fob codes to member accounts in Neon One CRM. This tool simplifies the process of bulk-adding fobs by displaying account information, validating fob codes, and updating the ``FobCSV`` custom field via the Neon API.

Prerequisites
+++++++++++++

The ``neon-fob-adder`` tool uses the same environment variables and configuration file as ``neongetter``:

* ``NEON_ORG`` - Your Neon organization ID
* ``NEON_KEY`` - Your Neon API key
* ``NEONGETTER_CONFIG`` - Path to your ``neon.config.json`` file (optional, defaults to ``./neon.config.json``)

Ensure these are set up as described in :ref:`neon.config` before using ``neon-fob-adder``.

Usage Modes
+++++++++++

The tool supports two modes of operation:

**Account IDs Mode** - Process a list of account IDs provided as command-line arguments:

.. code-block:: bash

    neon-fob-adder 123 456 789

**CSV File Mode** - Process accounts from a CSV file:

.. code-block:: bash

    neon-fob-adder --csv members.csv --field account_id

The CSV file should have a header row, and you specify which column contains the Neon account IDs using the ``--field`` option.

Interactive Workflow
++++++++++++++++++++

For each account, the tool will:

1. Retrieve and display the account information including:

   * Account ID
   * Full name and preferred name
   * Email address
   * All current fob codes (from both ``Fob10Digit`` and ``FobCSV`` fields)

2. Prompt you to enter a new fob code, or type ``s`` / ``skip`` to skip this account

3. Validate the fob code:

   * Auto-pads to 10 digits with leading zeros
   * Checks that it's numeric
   * Checks for duplicates across all existing fob fields

4. Display the proposed change and ask for confirmation (y/N, defaults to No)

5. If confirmed, update the account and log the change

**Example interaction:**

.. code-block:: text

    ========================================
    Account ID: 123
    Name: John Doe (preferred: Johnny)
    Email: john@example.com
    Current fobs: 1234567890
    ========================================

    Enter new fob code (or 's' to skip): 555

    Will add fob: 0000000555
    Current fobs: 1234567890
    Updated fobs: 1234567890,0000000555

    Confirm update? (y/N): y

    ✓ Successfully updated account 123

Logging
+++++++

All fob additions are logged to a timestamped file in the current directory:

.. code-block:: text

    neon_fob_adder_20251230143022.log

Each log entry includes:

* Timestamp
* Account ID and name
* Previous fob codes
* New fob code added
* Updated fob codes list

Command-Line Options
++++++++++++++++++++

.. code-block:: text

    usage: neon-fob-adder [-h] [-c CSV] [-f FIELD] [-v] [account_ids ...]

    positional arguments:
      account_ids           Neon account IDs to process

    options:
      -h, --help            show this help message and exit
      -c CSV, --csv CSV     Path to CSV file containing account IDs
      -f FIELD, --field FIELD
                            Field name in CSV for account IDs
      -v, --verbose         Enable verbose (debug) logging

**Note:** You cannot use both positional account IDs and CSV mode in the same invocation.

Error Handling
++++++++++++++

The tool will display clear error messages for common issues:

* **Invalid fob code** - Non-numeric or wrong length after padding
* **Duplicate fob** - Fob already exists on this account
* **Account not found** - Invalid account ID
* **API errors** - Network or authentication issues

When an error occurs, the tool will display the error and continue to the next account.

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
