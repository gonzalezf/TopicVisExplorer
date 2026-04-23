"""Cross-corpus helpers powering the multi-corpus Sankey view.

Given two or more :class:`PreparedData` objects (one per corpus), we
compute the omega-grid of similarity matrices and the aligned circle
positions needed by the Sankey + topic-map panels. This is a thin
orchestration layer over :mod:`topicvisexplorer.similarity` and
:mod:`topicvisexplorer.layout` so the FastAPI server (Phase 2) can
ship one JSON blob per pair of corpora.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .layout import get_circle_positions
from .logging import get_logger
from .similarity.embedding import EmbeddingSimilarity, compute_omega_grid

if TYPE_CHECKING:
    from .prepare import PreparedData

logger = get_logger(__name__)


@dataclass
class CrossCorpusBundle:
    """Bundle of everything the front end needs for two corpora."""

    omega_to_similarity: dict[float, np.ndarray]
    aligned_positions_json: str
    corpus_a: PreparedData
    corpus_b: PreparedData


def cross_corpus(
    prepared_a: PreparedData,
    prepared_b: PreparedData,
    *,
    metric: EmbeddingSimilarity,
    doc_topic_a: pd.DataFrame,
    doc_topic_b: pd.DataFrame,
    raw_texts_a: Sequence[str],
    raw_texts_b: Sequence[str],
    n_omega_steps: int = 101,
) -> CrossCorpusBundle:
    """Compute similarity grid + aligned layout for one pair of corpora.

    Returns the rectangular ``(K_a, K_b)`` cross-corpus similarity per
    omega (for the Sankey view) AND an aligned ``(K_a + K_b, 2)`` layout
    computed from the combined block similarity
    ``[[A_A, A_B], [B_A, B_B]]`` so both corpora share a single
    omega-varying topic map.
    """
    logger.info(
        "Computing cross-corpus similarity (K_a=%d, K_b=%d).",
        len(prepared_a.topic_order),
        len(prepared_b.topic_order),
    )
    pa = metric.precompute(prepared_a, doc_topic_a, raw_texts_a)
    pb = metric.precompute(prepared_b, doc_topic_b, raw_texts_b)

    omega_grid: dict[float, np.ndarray] = {}
    combined_grid: dict[float, np.ndarray] = {}
    for step in range(n_omega_steps):
        omega = round(step / (n_omega_steps - 1), 2) if n_omega_steps > 1 else 0.0
        ab = metric.matrix_for_omega(pa, pb, omega)
        aa = metric.matrix_for_omega(pa, pa, omega)
        bb = metric.matrix_for_omega(pb, pb, omega)
        omega_grid[omega] = ab
        combined_grid[omega] = np.block([[aa, ab], [ab.T, bb]])

    aligned = get_circle_positions(combined_grid)
    return CrossCorpusBundle(
        omega_to_similarity=omega_grid,
        aligned_positions_json=aligned,
        corpus_a=prepared_a,
        corpus_b=prepared_b,
    )
