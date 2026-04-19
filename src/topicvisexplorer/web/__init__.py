"""Front-end assets bundled in the wheel.

Only the legacy track is shipped at this point; the modern Vite bundle
will land in Phase 3 alongside the ``frontend/`` project.

* ``web/legacy/`` -- the byte-identical pre-1.0 static blob (paper version).
  Always present; guarantees visual parity for reviewers regardless of
  whether a modern bundle is built later.
"""

from __future__ import annotations

from pathlib import Path

LEGACY_STATIC: Path = Path(__file__).parent / "legacy" / "static"
LEGACY_TEMPLATES: Path = Path(__file__).parent / "legacy" / "templates"

__all__ = ["LEGACY_STATIC", "LEGACY_TEMPLATES"]
