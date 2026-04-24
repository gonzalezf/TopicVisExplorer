"""Internal utility helpers (JSON encoding, type coercion).

Kept tiny and dependency-free so it can be imported from anywhere
including from inside the front-end serialization path.
"""

from __future__ import annotations

import json
import math
import os
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


def sanitize_for_json(obj: Any) -> Any:
    """Recursively replace NaN / +Inf / -Inf with ``None``.

    FastAPI's :class:`fastapi.responses.JSONResponse` defaults to
    ``allow_nan=False`` (strict RFC-8259), so any NaN or infinity that
    survives down to the response serializer raises
    ``ValueError: Out of range float values are not JSON compliant``.
    The paper's downstream legacy JS already special-cases ``null``
    where it expects "no value" (e.g. relevance scoring after a term
    is removed via ``remove_word`` zeros the row, leaving ``loglift =
    log(0/.) = -inf``), so converting at the egress point is both
    safe and the smallest-blast-radius fix.

    Used by every endpoint that re-emits a ``PreparedData`` payload
    (``Topic_Splitting_Document_Based``, ``get_new_topic_vector``,
    ``Add_Remove_Word``, ``Exclude_Document``).
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    return obj


def tve_merge_timing_enabled() -> bool:
    """True when ``TVE_MERGE_TIMING`` requests merge/split hot-path timing logs.

    Set to ``1`` (or any non-empty value except ``0`` / ``false`` / ``no``) to
    log phase durations in :func:`topicvisexplorer.server.app._do_merge` and
    per-topic progress during embedding :meth:`EmbeddingSimilarity.precompute`.
    """
    v = (os.environ.get("TVE_MERGE_TIMING") or "").strip().lower()
    return v not in ("", "0", "false", "no")
