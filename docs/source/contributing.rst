.. _contributing:

Contributing and Development
============================

Thank you for your interest in improving this project. This project is
open-source under the `MIT
license <https://opensource.org/licenses/MIT>`__ and welcomes
contributions in the form of bug reports, feature requests, and pull
requests.

Here is a list of important resources for contributors:

-  `Source Code <https://github.com/jantman/machine_access_control>`__
-  `Documentation <https://github.com/jantman/machine_access_control>`__
-  `Issue
   Tracker <https://github.com/jantman/machine_access_control/issues>`__

Tooling in use
--------------

-  `Poetry <https://python-poetry.org/>`__ for dependency management.
-  `Nox <https://nox.thea.codes/>`__ for running tests, building docs, etc.
-  GitHub Actions for CI/CD and building the GitHub Pages documentation site.
-  `Sphinx <https://www.sphinx-doc.org/en/master/>`__ for writing the documentation
   in `rST <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#rst-primer>`__,
   mainly chosen for its excellent support for auto-generating Python API docs.
-  `pre-commit <https://pre-commit.com/>`__ for faster feedback on your changes.

How to set up your development environment
------------------------------------------

You need Python 3.12+ and the following tools:

-  `Poetry <https://python-poetry.org/>`__ for dependency management
-  `Nox <https://nox.thea.codes/>`__ for running tests, building docs, etc.
-  `nox-poetry <https://nox-poetry.readthedocs.io/>`__

Install the package with development requirements:

.. code:: console

   $ python3 -mvenv venv
   $ source venv/bin/activate
   $ pip install poetry
   $ poetry install

Finally, install and set up pre-commit:

.. code:: console

   $ nox --session=pre-commit -- install

Running Locally
---------------

.. code:: console

   $ flask --app dm_mac run

The app will now be available at http://127.0.0.1:5000

How to test the project
-----------------------

Run the full test suite:

.. code:: console

   $ nox

List the available Nox sessions:

.. code:: console

   $ nox --list-sessions

You can also run a specific Nox session. For example, invoke the unit
test suite like this:

.. code:: console

   $ nox --session=tests

To manually run the pre-commit tests:

.. code:: console

   $ nox --session=pre-commit

Unit tests are located in the `tests/ <tests/>`__ directory, and are
written using the `pytest <https://pytest.readthedocs.io/>`__ testing
framework.

How to build docs
-----------------

To build docs, serve them locally, and rebuild as they change:

.. code:: console

   $ DOCS_REBUILD=true nox --session=docs

To just build docs to `docs/build/ <docs/build/>`__:

.. code:: console

   $ nox --session=docs

How to submit changes
---------------------

Open a `pull
request <https://github.com/jantman/machine_access_control/pulls>`__ to
submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

-  The Nox test suite must pass without errors and warnings.
-  Include unit tests. This project maintains 100% code coverage.
-  If your changes add functionality, update the documentation
   accordingly.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before committing your change,
you can install pre-commit as a Git hook by running the following
command:

.. code:: console

   $ nox --session=pre-commit -- install

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate
your approach.
