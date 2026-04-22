"""Backwards-compatibility shim for the original ``demo_20ng`` module.

Prefer :mod:`topicvisexplorer.server.demo_fixtures`.  This module only
re-exports the legacy symbols so existing import sites keep working.
"""

from __future__ import annotations

from .demo_fixtures import (
    build_20ng_tiny,
    build_scenario_from_fixture,
    build_scenario_from_topic_model,
    demo_page_contains_real_terms,
)

__all__ = [
    "build_20ng_tiny",
    "build_scenario_from_fixture",
    "build_scenario_from_topic_model",
    "demo_page_contains_real_terms",
]
