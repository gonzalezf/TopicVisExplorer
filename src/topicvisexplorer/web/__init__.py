"""Front-end assets bundled in the wheel.

Two parallel front-end tracks ship in v1.0:

* ``web/legacy/`` -- the byte-identical pre-1.0 static blob (paper version).
  Always present; guarantees visual parity for reviewers regardless of
  whether the modern bundle was built.
* ``web/dist/``   -- the Vite + TypeScript output from ``frontend/``.
  Optional: present when the wheel was built from a source tree that ran
  ``npm install && npm run build`` first. The FastAPI server detects its
  presence at startup and switches the default template accordingly.

The dual-track design lets the wheel keep working in environments without
Node.js (e.g. minimal Docker images) while still preferring the modern
bundle whenever it is available.
"""

from __future__ import annotations

from pathlib import Path

LEGACY_STATIC: Path = Path(__file__).parent / "legacy" / "static"
LEGACY_TEMPLATES: Path = Path(__file__).parent / "legacy" / "templates"

#: Modern Vite + TypeScript bundle output. Path may not exist if the
#: wheel was built without running the frontend build first; callers
#: should check ``MODERN_DIST.is_dir()`` before mounting it.
MODERN_DIST: Path = Path(__file__).parent / "dist"


def has_modern_bundle() -> bool:
    """Return True iff the bundled Vite output is present and non-empty.

    Used by :mod:`topicvisexplorer.server.app` to decide whether to serve
    the legacy ``index.html`` template (paper-version <script> soup) or
    the modern ``index_v1.html`` template (single bundled tve.js).
    """
    if not MODERN_DIST.is_dir():
        return False
    return (MODERN_DIST / "tve.js").is_file()


__all__ = ["LEGACY_STATIC", "LEGACY_TEMPLATES", "MODERN_DIST", "has_modern_bundle"]
