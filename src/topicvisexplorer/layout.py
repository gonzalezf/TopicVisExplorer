"""Topic-circle 2D layout via PCoA + Procrustes alignment.

Ported from the legacy ``_get_new_circle_positions.py``. The algorithm
is unchanged - we recompute one PCoA per omega step (101 steps from 0
to 1 inclusive) on the cosine-distance matrix, then chain-align
neighboring layouts with Procrustes so the topic circles "morph"
smoothly when the user drags the omega slider.

Vectorized speedups (no algorithmic change):

* PCoA inputs/outputs stay as float64 NumPy arrays end-to-end.
* The legacy code rebuilt distance matrices via Python-level fills; we
  rely on :func:`numpy.fill_diagonal` instead.

Numerical equivalence to the legacy implementation is enforced by a
golden test in ``tests/golden/test_layout_golden.py``.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import numpy as np
from scipy.spatial import procrustes

from .logging import get_logger
from .prepare import _pcoa

if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy.typing import NDArray

logger = get_logger(__name__)


def get_circle_positions(topic_similarity_matrix: Mapping[float, np.ndarray]) -> str:
    """Compute Procrustes-aligned circle positions across the omega slider.

    Parameters
    ----------
    topic_similarity_matrix:
        Mapping from omega in ``{0.00, 0.01, ..., 1.00}`` to a square
        ``(K, K)`` cosine-similarity matrix between topics.

    Returns
    -------
    str
        JSON-encoded mapping ``{omega: [[x, y], ...]}`` ready to ship to
        the front end.
    """
    new_positions: dict[float, list[list[float]]] = {}
    for raw_step in range(101):
        omega = raw_step / 100.0
        sim = np.asarray(topic_similarity_matrix[omega], dtype=np.float64)
        dist = 1.0 - sim
        np.fill_diagonal(dist, 0.0)
        new_positions[omega] = _pcoa(dist, n_components=2).tolist()

    omegas = list(new_positions.keys())
    standardized: dict[float, list[list[float]]] = {}
    disparities: dict[float, float] = {}
    original_a: NDArray[np.float64] = np.asarray(new_positions[0.0], dtype=np.float64)

    last_b: NDArray[np.float64] = original_a
    for i in range(len(omegas) - 1):
        original_b = np.asarray(new_positions[omegas[i + 1]], dtype=np.float64)
        mtx1, mtx2, disparity = procrustes(original_a, original_b)
        disparities[omegas[i]] = disparity
        standardized[omegas[i]] = mtx1.tolist()
        original_a = mtx2
        last_b = mtx2
    standardized[omegas[-1]] = last_b.tolist()
    disparities[omegas[-1]] = disparities.get(omegas[-2], 0.0)

    return json.dumps(standardized)


def get_circle_positions_from_old_matrix(
    old_circle_positions: Mapping[str, list[list[float]]],
    topic_similarity_matrix: Mapping[float, np.ndarray],
) -> str:
    """Re-align newly computed positions to a previous omega-keyed layout.

    Used after a topic split or merge: we already know the layout the
    user is currently looking at and want the new layout to be visually
    *close* to it (so circles don't teleport on screen).

    Parameters
    ----------
    old_circle_positions:
        Mapping from omega (string-keyed, as JSON-deserialized) to the
        previously-shown ``[[x, y], ...]`` layout.
    topic_similarity_matrix:
        Mapping from omega (float-keyed) to the new ``(K, K)`` cosine
        similarity matrix.
    """
    new_positions: dict[str, list[list[float]]] = {}
    for raw_step in range(101):
        omega = raw_step / 100.0
        sim = np.asarray(topic_similarity_matrix[omega], dtype=np.float64)
        dist = 1.0 - sim
        np.fill_diagonal(dist, 0.0)
        new_positions[str(omega)] = _pcoa(dist, n_components=2).tolist()

    standardized: dict[str, list[list[float]]] = {}
    for current_omega in old_circle_positions:
        original_a = np.asarray(old_circle_positions[current_omega], dtype=np.float64)
        original_b = np.asarray(new_positions[current_omega], dtype=np.float64)
        _mtx1, mtx2, _disparity = procrustes(original_a, original_b)
        standardized[current_omega] = mtx2.tolist()

    return json.dumps(standardized)
