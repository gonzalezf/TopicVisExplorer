"""Internal utility helpers (JSON encoding, type coercion).

Kept tiny and dependency-free so it can be imported from anywhere
including from inside the front-end serialization path.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np


class NumPyEncoder(json.JSONEncoder):
    """JSON encoder that handles NumPy scalar / array types.

    Used when serializing :class:`~topicvisexplorer.PreparedData` for the
    front end. Without this, ``np.int64`` topic ids and ``np.float64``
    coordinates would raise ``TypeError``.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)
