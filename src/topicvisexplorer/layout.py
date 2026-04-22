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
from scipy.linalg import orthogonal_procrustes
from scipy.spatial import procrustes

from .logging import get_logger
from .prepare import _pcoa

if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy.typing import NDArray

logger = get_logger(__name__)


def circle_positions(
    topic_similarity_matrix: Mapping[float, np.ndarray],
) -> dict[float, list[list[float]]]:
    """Compute Procrustes-aligned circle positions across the omega slider.

    Parameters
    ----------
    topic_similarity_matrix:
        Mapping from omega in ``{0.00, 0.01, ..., 1.00}`` to a square
        ``(K, K)`` cosine-similarity matrix between topics.

    Returns
    -------
    dict[float, list[list[float]]]
        Mapping ``{omega: [[x, y], ...]}``. JSON-encode at the boundary
        if you need to ship it to the front end.
    """
    new_positions: dict[float, list[list[float]]] = {}
    for raw_step in range(101):
        omega = raw_step / 100.0
        sim = np.asarray(topic_similarity_matrix[omega], dtype=np.float64)
        if sim.shape[0] < 2:
            new_positions[omega] = np.zeros((sim.shape[0], 2)).tolist()
            continue
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

    return standardized


def get_circle_positions(topic_similarity_matrix: Mapping[float, np.ndarray]) -> str:
    """Legacy alias: returns the layout already JSON-encoded.

    Prefer :func:`circle_positions` in new code.
    """
    return json.dumps(circle_positions(topic_similarity_matrix))


def _procrustes_align(
    a_full: np.ndarray,
    b_full: np.ndarray,
    correspondence: list[tuple[int, int]] | None,
) -> np.ndarray:
    """Return ``b_full`` rotated+translated to match ``a_full`` on the paired rows.

    ``correspondence`` is a list of ``(old_row, new_row)`` index pairs. Rows
    without a correspondence (a new child topic after a split, or the dropped
    topic after a merge) are excluded from the fit but still rotated along
    with the rest of the scene so they stay in a visually consistent frame.

    Falls back to min(Ka, Kb) position-wise pairing with a logger warning if
    ``correspondence`` is None (legacy path).
    """
    ka, kb = a_full.shape[0], b_full.shape[0]
    if ka == 0 or kb == 0:
        return b_full.copy()
    if correspondence is None:
        logger.warning(
            "procrustes: no correspondence map (ka=%d kb=%d); "
            "falling back to position-wise pairing",
            ka,
            kb,
        )
        n = min(ka, kb)
        pairs: list[tuple[int, int]] = [(i, i) for i in range(n)]
    else:
        pairs = [(i, j) for (i, j) in correspondence if 0 <= i < ka and 0 <= j < kb]
    if len(pairs) < 2:
        # Degenerate: nothing to fit on. Translate new centroid onto old centroid.
        logger.warning("procrustes: |pairs|=%d, centroid-only align", len(pairs))
        return b_full - b_full.mean(0, keepdims=True) + a_full.mean(0, keepdims=True)

    a_sub = np.asarray([a_full[i] for i, _ in pairs], dtype=np.float64)
    b_sub = np.asarray([b_full[j] for _, j in pairs], dtype=np.float64)

    a_mean = a_sub.mean(0, keepdims=True)
    b_mean = b_sub.mean(0, keepdims=True)
    R, _s = orthogonal_procrustes(a_sub - a_mean, b_sub - b_mean)
    # Apply to the *full* new layout: centre, rotate, re-centre on A's centroid.
    result: np.ndarray = (b_full - b_mean) @ R + a_mean
    logger.debug(
        "procrustes align: ka=%d kb=%d pairs=%d disparity=%.4f",
        ka,
        kb,
        len(pairs),
        float(_s),
    )
    return result


def split_correspondence(k_old: int, parent_idx: int, k_new: int) -> list[tuple[int, int]]:
    """Old-row -> new-row mapping for a split of ``parent_idx`` into ``k_new`` children.

    The parent row is deliberately dropped from the map — its children are
    new identities, so they should not constrain the rotation.
    """
    before = [(i, i) for i in range(parent_idx)]
    after = [(j, j + k_new - 1) for j in range(parent_idx + 1, k_old)]
    return before + after


def merge_correspondence(k_old: int, a_idx: int, b_idx: int) -> list[tuple[int, int]]:
    """Old-row -> new-row mapping for merging (a_idx, b_idx) with a_idx < b_idx.

    Rows strictly between ``a_idx`` and ``b_idx`` stay at their old index
    (deletion at ``b_idx`` is to their right). Rows after ``b_idx`` shift
    left by one. Row ``b_idx`` is dropped (absorbed into ``a_idx``).
    """
    if a_idx > b_idx:
        a_idx, b_idx = b_idx, a_idx
    before = [(i, i) for i in range(a_idx)]
    keep_a = [(a_idx, a_idx)]
    middle = [(j, j) for j in range(a_idx + 1, b_idx)]
    after = [(j, j - 1) for j in range(b_idx + 1, k_old)]
    return before + keep_a + middle + after


def circle_positions_from_old_matrix(
    old_circle_positions: Mapping[str, list[list[float]]],
    topic_similarity_matrix: Mapping[float, np.ndarray],
    *,
    correspondence: list[tuple[int, int]] | None = None,
) -> dict[str, list[list[float]]]:
    """Re-align PCoA layouts for a new (K_new) topic set to a prior (K_old) layout.

    ``correspondence`` is an ordered list of ``(old_row, new_row)`` pairs
    describing which topic identities survived the edit. Callers must build
    this from the edit's shape:

      - For splits: :func:`split_correspondence(K_old, parent_idx, k_new)`.
      - For merges: :func:`merge_correspondence(K_old, a_idx, b_idx)`.

    When ``correspondence is None`` the function falls back to position-wise
    pairing of ``min(K_old, K_new)`` rows with a logger warning. This matches
    the previous (buggy) behaviour so that existing call sites do not silently
    regress, but new call sites MUST pass an explicit map.
    """
    new_positions: dict[str, np.ndarray] = {}
    for raw_step in range(101):
        omega = raw_step / 100.0
        sim = np.asarray(topic_similarity_matrix[omega], dtype=np.float64)
        if sim.shape[0] < 2:
            logger.warning("PCoA with K=%d: returning origin layout", sim.shape[0])
            new_positions[str(omega)] = np.zeros((sim.shape[0], 2))
            continue
        dist = 1.0 - sim
        np.fill_diagonal(dist, 0.0)
        new_positions[str(omega)] = _pcoa(dist, n_components=2)

    standardized: dict[str, list[list[float]]] = {}
    for key, a_list in old_circle_positions.items():
        a_full = np.asarray(a_list, dtype=np.float64)
        b_full = new_positions[key]
        b_aligned = _procrustes_align(a_full, b_full, correspondence)
        standardized[key] = b_aligned.tolist()
    return standardized


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
    return json.dumps(
        circle_positions_from_old_matrix(old_circle_positions, topic_similarity_matrix)
    )
