# Contributor Guide

Thank you for your interest in improving this project.
This project is open-source under the [MIT license](https://opensource.org/licenses/MIT) and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- [Source Code](https://github.com/jantman/machine_access_control)
- [Documentation](https://github.com/jantman/machine_access_control)
- [Issue Tracker](https://github.com/jantman/machine_access_control/issues)

## How to set up your development environment

You need Python 3.12+ and the following tools:

- [Poetry](https://python-poetry.org/)
- [Nox](https://nox.thea.codes/)
- [nox-poetry](https://nox-poetry.readthedocs.io/)

Install the package with development requirements:

```console
$ python3 -mvenv venv
$ source venv/bin/activate
$ pip install poetry
$ poetry install
```

Finally, install and set up pre-commit:

```console
$ nox --session=pre-commit -- install
```

## Running Locally

```console
$ flask --app dm_mac run
```

The app will now be available at [http://127.0.0.1:5000](http://127.0.0.1:5000)

## How to test the project

Run the full test suite:

```console
$ nox
```

List the available Nox sessions:

```console
$ nox --list-sessions
```

You can also run a specific Nox session.
For example, invoke the unit test suite like this:

```console
$ nox --session=tests
```

To manually run the pre-commit tests:

```console
$ nox --session=pre-commit
```

Unit tests are located in the [tests/](tests/) directory,
and are written using the [pytest](https://pytest.readthedocs.io/) testing framework.

## How to submit changes

Open a [pull request](https://github.com/jantman/machine_access_control/pulls) to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The Nox test suite must pass without errors and warnings.
- Include unit tests. This project maintains 100% code coverage.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early, though—we can always iterate on this.

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

```console
$ nox --session=pre-commit -- install
```

It is recommended to open an issue before starting work on anything.
This will allow a chance to talk it over with the owners and validate your approach.
