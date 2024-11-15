"""Nox sessions."""

import os
import shlex
import shutil
import sys
from pathlib import Path
from textwrap import dedent

import nox


try:
    from nox_poetry import Session
    from nox_poetry import session
except ImportError:
    message = f"""\
    Nox failed to import the 'nox-poetry' package.

    Please install it using the following command:

    {sys.executable} -m pip install nox-poetry"""
    raise SystemExit(dedent(message)) from None


package = "dm_mac"
python_versions = ["3.12"]
nox.needs_version = ">= 2024.4.15"
nox.options.sessions = (
    "pre-commit",
    "safety",
    "mypy",
    "tests",
    "typeguard",
    "docs",
)

TEST_ENV = {
    "NEON_ORG": "test",
    "NEON_KEY": "12345",
    "NEONGETTER_CONFIG": "tests/fixtures/neon.config.json",
}


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    assert session.bin is not None  # noqa: S101

    # Only patch hooks containing a reference to this session's bindir. Support
    # quoting rules for Python and bash, but strip the outermost quotes so we
    # can detect paths within the bindir, like <bindir>/python.
    bindirs = [
        bindir[1:-1] if bindir[0] in "'\"" else bindir
        for bindir in (repr(session.bin), shlex.quote(session.bin))
    ]

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    headers = {
        # pre-commit < 2.16.0
        "python": f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """,
        # pre-commit >= 2.16.0
        "bash": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
        # pre-commit >= 2.17.0 on Windows forces sh shebang
        "/bin/sh": f"""\
            VIRTUAL_ENV={shlex.quote(virtualenv)}
            PATH={shlex.quote(session.bin)}"{os.pathsep}$PATH"
            """,
    }

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        if not hook.read_bytes().startswith(b"#!"):
            continue

        text = hook.read_text()

        if not any(
            Path("A") == Path("a") and bindir.lower() in text.lower() or bindir in text
            for bindir in bindirs
        ):
            continue

        lines = text.splitlines()

        for executable, header in headers.items():
            if executable in lines[0].lower():
                lines.insert(1, dedent(header))
                hook.write_text("\n".join(lines))
                break


@session(name="pre-commit", python=python_versions[0])
def precommit(session: Session) -> None:
    """Lint using pre-commit."""
    args = session.posargs or [
        "run",
        "--all-files",
        "--hook-stage=manual",
        "--show-diff-on-failure",
    ]
    session.install(
        "black",
        "darglint",
        "flake8",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "isort",
        "pep8-naming",
        "pre-commit",
        "pre-commit-hooks",
        "pyupgrade",
    )
    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@session(python=python_versions[0])
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    requirements = session.poetry.export_requirements()
    session.install("safety")
    ignored = ",".join(
        [
            "70612",  # CVE-2019-8341 in Jinja2, no fix as of 3.1.4
        ]
    )
    session.run(
        "safety",
        "check",
        "--full-report",
        f"--file={requirements}",
        f"--ignore={ignored}",
    )


@session(python=python_versions)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or ["src", "tests"]
    session.install(".")
    session.install(
        "mypy",
        "pytest",
        "types-jsonschema",
        "types-requests",
        "responses",
        "freezegun",
    )
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")
    else:
        session.run("mypy", *args)


@session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install(
        "coverage[toml]",
        "pytest",
        "pygments",
        "pytest-blockage",
        "responses",
        "pytest-html",
        "freezegun",
        "pytest-asyncio",
    )
    try:
        session.run(
            "coverage",
            "run",
            "--parallel",
            "-m",
            "pytest",
            "--blockage",
            "--asyncio-mode=auto",
            "--capture=tee-sys",
            "--junitxml=pytest.xml",
            "--html=pytest.html",
            "--self-contained-html",
            "--log-level=DEBUG",
            "--log-format=%(asctime)s [%(levelname)s %(filename)s:"  # continue
            "%(lineno)s - %(name)s.%(funcName)s() ] %(message)s",
            "-v",
            *session.posargs,
            env=TEST_ENV,
        )
    finally:
        session.notify("coverage", posargs=[])


@session(python=python_versions[0])
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    session.install("coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)
    session.run("coverage", "html")
    session.run("coverage", "xml")


@session(python=python_versions[0])
def typeguard(session: Session) -> None:
    """Runtime type checking using Typeguard."""
    session.install(".")
    session.install(
        "pytest",
        "typeguard",
        "pygments",
        "responses",
        "freezegun",
    )
    session.run(
        "pytest",
        f"--typeguard-packages={package}",
        *session.posargs,
        env=TEST_ENV,
    )


@session(python=python_versions[0], reuse_venv=True)
def docs(session: Session) -> None:
    """Build the documentation."""
    session.install(".")
    args = session.posargs or ["-b", "html", "docs/source", "docs/build", "-E", "-W"]

    if os.environ.get("DOCS_REBUILD") == "true" and not session.posargs:
        args = ["-a", "--watch=docs/source/_static", "--open-browser", *args]

    builddir = Path("docs", "build")
    if builddir.exists():
        shutil.rmtree(builddir)

    session.install("-r", "docs/requirements.txt")

    session.run(
        "sphinx-apidoc",
        "src/dm_mac",
        "-o",
        "docs/source",
        "-e",
        "-f",
        "-M",
        "--private",
    )
    if os.environ.get("DOCS_REBUILD") == "true":
        session.run("sphinx-autobuild", *args)
    else:
        session.run("sphinx-build", *args)
