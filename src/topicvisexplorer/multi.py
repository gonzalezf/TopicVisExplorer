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
    """Compute similarity grid + aligned layout for one pair of corpora."""
    logger.info(
        "Computing cross-corpus similarity (K_a=%d, K_b=%d).",
        len(prepared_a.topic_order),
        len(prepared_b.topic_order),
    )
    omega_grid = compute_omega_grid(
        metric,
        prepared_a,
        prepared_b,
        doc_topic_a=doc_topic_a,
        doc_topic_b=doc_topic_b,
        raw_texts_a=raw_texts_a,
        raw_texts_b=raw_texts_b,
        n_steps=n_omega_steps,
    )
    aligned = get_circle_positions(omega_grid)
    return CrossCorpusBundle(
        omega_to_similarity=dict(omega_grid),
        aligned_positions_json=aligned,
        corpus_a=prepared_a,
        corpus_b=prepared_b,
    )
