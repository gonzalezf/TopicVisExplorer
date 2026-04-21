"""Fixtures for the API-contract test layer.

A fresh ``TestClient`` is created per test so the in-memory session
store is isolated and tests can run in parallel.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from topicvisexplorer.server import ServerConfig, build_app


@pytest.fixture
def client() -> TestClient:
    """A FastAPI TestClient with the bundled tiny demo scenarios registered."""
    app = build_app(ServerConfig(register_demo=True, max_sessions=4))
    return TestClient(app)
