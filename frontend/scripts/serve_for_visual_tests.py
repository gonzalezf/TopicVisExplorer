#!/usr/bin/env python3
"""Launch a TopicVisExplorer FastAPI server for Playwright visual tests.

Used by ``frontend/playwright.config.ts`` as the ``webServer.command``.
Forces the modern frontend track (so a missing Vite bundle fails fast
instead of silently rendering the legacy template) and pins a
deterministic port so the test base URL stays stable.

Environment variables
---------------------

``TVE_E2E_PORT``
    Port to bind to. Defaults to 8765.
``TVE_E2E_FRONTEND``
    ``"modern"`` (default) or ``"legacy"`` -- lets the same script also
    capture legacy screenshots when generating side-by-side diffs.
"""

from __future__ import annotations

import os
import sys

import uvicorn

from topicvisexplorer.server import ServerConfig, build_app


def main() -> int:
    port = int(os.environ.get("TVE_E2E_PORT", "8765"))
    frontend = os.environ.get("TVE_E2E_FRONTEND", "modern")
    app = build_app(
        ServerConfig(
            register_demo=True,
            frontend=frontend,
            max_sessions=8,
        )
    )
    print(
        f"[visual-tests] serving on http://127.0.0.1:{port} "
        f"(frontend={frontend})",
        flush=True,
    )
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
