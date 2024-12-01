.. _installation:

Installation
============

The only supported method of installing and running the Control Server is via Docker. Packages are published to the GitHub Container Registry.

For actual use, you will need to ensure that the Docker container is always running and restarts automatically; it's assumed that you'll use systemd or some configuration management / automation tool for that, but that's outside the scope of this documentation.

The `tests/fixtures directory of the source repository <https://github.com/jantman/machine-access-control/tree/main/tests/fixtures>`__ contains an example `docker-compose <https://docs.docker.com/compose/>`__ file that can be used as an example of how to run the container. By default, it will be accessible on port 5000 unless that file is changed.

**NOTE** that by default the container runs as root, and files written by it (i.e. the machine state directory) will be root-owned.

.. _installation.neongetter:

Running Neongetter
------------------

Using the :ref:`neon` integration is relatively straightforward:

1. Add an ``MAC_USER_RELOAD_URL=http://localhost:5000/api/reload-users`` environment variable on the container itself.
2. Set up your :ref:`neon.config` file and mount it into the container at ``/neon.config.json``
3. Via a job scheduler such as cron, at whatever interval you choose, update users from Neon with a docker exec command like ``docker exec -it -e NEON_ORG=yourOrg -e NEON_KEY=yourApiKey neongetter``
