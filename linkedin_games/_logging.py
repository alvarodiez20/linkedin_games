"""
Centralised logging configuration for linkedin-games.

Call ``setup_logging()`` once at process startup (in each ``__main__.py``).
Every other module obtains its own logger with ``logging.getLogger(__name__)``.

Log levels:
    DEBUG    — internal solver steps, DOM query details.
    INFO     — user-facing progress (connecting, extracting, solving, playing).
    WARNING  — non-fatal anomalies (sparse board, cell already set, etc.).
    ERROR    — fatal failures that precede SystemExit.

Environment:
    LOG_LEVEL   Override the default level (e.g. ``LOG_LEVEL=DEBUG sudoku``).
    LOG_FORMAT  Override the log-record format string.
"""

from __future__ import annotations

import logging
import os
import sys

_DEFAULT_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DEFAULT_DATE_FORMAT = "%H:%M:%S"


def setup_logging(
    level: str | None = None,
    fmt: str | None = None,
    date_fmt: str | None = None,
) -> None:
    """Configure the root logger for the linkedin-games CLI.

    Installs a single ``StreamHandler`` on *stderr* so that progress output
    is kept separate from any stdout data.  Safe to call multiple times — the
    second call is a no-op because ``basicConfig`` skips if handlers are
    already present.

    Args:
        level: Log level string (``"DEBUG"``, ``"INFO"``, …).  Defaults to
            the ``LOG_LEVEL`` env-var, or ``"INFO"`` if unset.
        fmt: ``logging`` format string.  Defaults to ``LOG_FORMAT`` env-var or
            the package default (timestamp + level + logger name + message).
        date_fmt: ``strftime`` format for the timestamp.  Defaults to
            ``"%H:%M:%S"``.

    Example:
        >>> from linkedin_games._logging import setup_logging
        >>> setup_logging()
        >>> import logging
        >>> logging.getLogger(__name__).info("ready")
    """
    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_fmt = fmt or os.getenv("LOG_FORMAT", _DEFAULT_FORMAT)
    resolved_date_fmt = date_fmt or _DEFAULT_DATE_FORMAT

    logging.basicConfig(
        level=getattr(logging, resolved_level, logging.INFO),
        format=resolved_fmt,
        datefmt=resolved_date_fmt,
        stream=sys.stderr,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger.

    Thin wrapper around ``logging.getLogger`` provided for convenience so that
    modules do not need to import ``logging`` directly.

    Args:
        name: Logger name — pass ``__name__`` from the calling module.

    Returns:
        A ``logging.Logger`` instance for *name*.
    """
    return logging.getLogger(name)
