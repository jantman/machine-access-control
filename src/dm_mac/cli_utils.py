"""Utility functions for command-line tools."""

import logging
import os


def set_log_info(lgr: logging.Logger) -> None:
    """Set logger level to INFO."""
    set_log_level_format(
        lgr, logging.INFO, "%(asctime)s %(levelname)s:%(name)s:%(message)s"
    )


def set_log_debug(lgr: logging.Logger) -> None:
    """Set logger level to DEBUG, and debug-level output format."""
    set_log_level_format(
        lgr,
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s",
    )


def set_log_level_format(lgr: logging.Logger, level: int, fmt: str) -> None:
    """Set logger level and format."""
    formatter = logging.Formatter(fmt=fmt)
    lgr.handlers[0].setFormatter(formatter)
    lgr.setLevel(level)


def env_var_or_die(varname: str, content: str) -> str:
    """Return the value of an env var, or raise exception if not set."""
    try:
        return os.environ[varname]
    except KeyError as ex:
        raise RuntimeError(
            f"ERROR: Please set the {varname} environment variable to {content}."
        ) from ex
