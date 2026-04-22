"""FastAPI server replacing the legacy Flask app.

The server exposes the same JSON contract the legacy front end already
expects (so Phase 2 ships **without** any JavaScript change and keeps
the visualization byte-identical for paper review). The Vite + TS
rewrite lands in Phase 3.

Key differences from ``topicvisexplorer.py`` (the old Flask app):

* **No IP-based ``MaxClientQueue``.** Sessions are tracked via a signed
  cookie (`tve_session`); the server holds at most ``max_sessions``
  in-memory entries with LRU eviction (configurable via
  :class:`ServerConfig`).
* **No paper-era user-study server routes** (e.g. ``/redirect_with_user_study_code``,
  ``previous_users.txt``). The browser **export** of topic snapshots is
  entirely client-side (JSON file download) — not an HTTP upload.
* **No global mutable state.** Per-session storage lives in
  :class:`SessionStore` and is dependency-injected.
* **Pydantic-validated requests.** Every endpoint uses
  :mod:`topicvisexplorer.server.schemas` so contract drift is caught at
  PR time, not in production.
* **Structured logging.** Each request gets a request id and is logged
  through the package logger.

Public API:

* :func:`build_app` -- return a configured :class:`fastapi.FastAPI`.
* :func:`serve` -- programmatically launch uvicorn (used by
  :func:`topicvisexplorer.show` and :func:`topicvisexplorer.demo`).
"""

from __future__ import annotations

from .app import ServerConfig, build_app
from .runner import serve

__all__ = ["ServerConfig", "build_app", "serve"]
