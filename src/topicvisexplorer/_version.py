"""Single source of truth for the package version.

Kept in a tiny separate module so it can be read at install time without
importing the whole package (which would pull in heavy NLP deps).
"""

from __future__ import annotations

__version__ = "1.0.0"
