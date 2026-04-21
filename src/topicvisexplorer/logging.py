"""Logging configuration for the topicvisexplorer namespace.

We expose a single named logger ``topicvisexplorer`` and *do not* attach a
handler by default, in keeping with `Python logging best practices for
libraries
<https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library>`_.
End-user applications opt in via :func:`configure_logging` or by attaching
their own handler::

    import logging
    logging.basicConfig(level=logging.INFO)

Internal modules acquire their child logger via::

    from topicvisexplorer.logging import get_logger
    logger = get_logger(__name__)

This namespacing lets users selectively raise/lower the log level for
TopicVisExplorer without touching root logging::

    logging.getLogger("topicvisexplorer").setLevel(logging.DEBUG)
"""

from __future__ import annotations

import logging
import sys
from typing import Final, TextIO

_PACKAGE_LOGGER_NAME: Final[str] = "topicvisexplorer"
_DEFAULT_FORMAT: Final[str] = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger inside the ``topicvisexplorer`` namespace.

    Pass ``__name__`` from a submodule to get a properly nested logger
    (e.g. ``topicvisexplorer.similarity.embedding``). Passing ``None``
    returns the root package logger.
    """
    if name is None or name == _PACKAGE_LOGGER_NAME:
        return logging.getLogger(_PACKAGE_LOGGER_NAME)
    if name.startswith(_PACKAGE_LOGGER_NAME + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_PACKAGE_LOGGER_NAME}.{name}")


def configure_logging(level: int = logging.INFO, *, stream: TextIO | None = None) -> None:
    """Attach a single stderr handler to the package logger.

    This is a convenience for scripts and notebooks; library users are
    expected to configure logging from the application side instead.

    The function is idempotent: calling it twice does not double-attach
    handlers. Call ``logging.getLogger("topicvisexplorer").handlers.clear()``
    if you need to fully reset.
    """
    logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    logger.setLevel(level)
    if any(getattr(h, "_topicvisexplorer_managed", False) for h in logger.handlers):
        return
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    handler._topicvisexplorer_managed = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    logger.propagate = False
