"""Topic-similarity metrics.

The package provides:

* :class:`SimilarityMetric` -- the Protocol every metric implements.
* :class:`EmbeddingSimilarity` -- the **paper metric** (Eq. 7-9), with
  the ``omega`` blend and ``lambda_`` term-relevance parameters
  *explicitly untangled* (the legacy code conflated both into one
  ``lambda_`` argument; see ``EmbeddingSimilarity.__init__`` for the
  mapping).
* :class:`JensenShannonSimilarity`, :class:`HellingerSimilarity`,
  :class:`CosineSimilarity`, :class:`JaccardSimilarity`,
  :class:`WordEmbeddingSpaceSimilarity` -- baselines named in Section
  2.3 of the paper for direct head-to-head comparison.

Use them via :func:`topicvisexplorer.similarity.compute_omega_grid`
which returns the omega-keyed dict consumed by the layout module.
"""

from __future__ import annotations

from .baselines import (
    CosineSimilarity,
    HellingerSimilarity,
    JaccardSimilarity,
    JensenShannonSimilarity,
    WordEmbeddingSpaceSimilarity,
)
from .embedding import EmbeddingSimilarity, compute_omega_grid
from .protocol import SimilarityMetric

__all__ = [
    "CosineSimilarity",
    "EmbeddingSimilarity",
    "HellingerSimilarity",
    "JaccardSimilarity",
    "JensenShannonSimilarity",
    "SimilarityMetric",
    "WordEmbeddingSpaceSimilarity",
    "compute_omega_grid",
]
