"""Unit tests for :mod:`topicvisexplorer.logging`."""

from __future__ import annotations

import logging

from topicvisexplorer.logging import configure_logging, get_logger


def test_get_logger_namespacing() -> None:
    assert get_logger().name == "topicvisexplorer"
    assert get_logger("foo").name == "topicvisexplorer.foo"
    assert get_logger("topicvisexplorer.bar").name == "topicvisexplorer.bar"


def test_configure_logging_idempotent() -> None:
    configure_logging(level=logging.DEBUG)
    n_after_first = len(logging.getLogger("topicvisexplorer").handlers)
    configure_logging(level=logging.INFO)
    assert len(logging.getLogger("topicvisexplorer").handlers) == n_after_first
