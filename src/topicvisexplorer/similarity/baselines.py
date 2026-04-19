"""Baseline topic-similarity metrics named in the paper, Section 2.3.

These exist for two reasons:

1. Direct head-to-head comparison in benchmarks (Phase 5 docs),
   strengthening the paper's empirical claim.
2. Letting users override the default embedding metric with a
   distribution-only metric (cheaper, no embedding needed).

All five conform to :class:`SimilarityMetric` and return a ``(K_a, K_b)``
matrix in ``[0, 1]`` (1 = identical).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..logging import get_logger

if TYPE_CHECKING:
    from ..embeddings.protocol import EmbeddingBackend
    from ..prepare import PreparedData

logger = get_logger(__name__)


def _topic_term_matrix(prepared: PreparedData) -> np.ndarray:
    """Reconstruct ``(K, V)`` topic-term distribution from a PreparedData.

    The PreparedData object stores ``topic_info`` in long form; we
    reshape it back to a dense matrix for distribution-based metrics.
    """
    by_topic: dict[str, dict[str, float]] = {}
    for _, row in prepared.topic_info.iterrows():
        cat = row["Category"]
        if not cat.startswith("Topic"):
            continue
        by_topic.setdefault(cat, {})[row["Term"]] = float(row["Freq"])
    K = len(by_topic)
    vocab = sorted({term for d in by_topic.values() for term in d})
    term_index = {t: i for i, t in enumerate(vocab)}
    M = np.zeros((K, len(vocab)), dtype=np.float64)
    for k_idx in range(K):
        cat = f"Topic{k_idx + 1}"
        if cat not in by_topic:
            continue
        for term, freq in by_topic[cat].items():
            M[k_idx, term_index[term]] = freq
    row_sums = M.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return M / row_sums


class JensenShannonSimilarity:
    """``1 - sqrt(JSD)`` mapped into ``[0, 1]``."""

    name = "jensen_shannon"

    def __call__(self, prepared_a: PreparedData, prepared_b: PreparedData, /) -> np.ndarray:
        from scipy.spatial.distance import jensenshannon

        a = _topic_term_matrix(prepared_a)
        b = _topic_term_matrix(prepared_b)
        if a.shape[1] != b.shape[1]:
            a, b = _align_vocab(a, b)
        K_a, K_b = a.shape[0], b.shape[0]
        out = np.zeros((K_a, K_b), dtype=np.float64)
        for i in range(K_a):
            for j in range(K_b):
                out[i, j] = 1.0 - jensenshannon(a[i], b[j], base=2)
        return out


class HellingerSimilarity:
    """Hellinger-distance similarity: ``1 - H(p, q)``."""

    name = "hellinger"

    def __call__(self, prepared_a: PreparedData, prepared_b: PreparedData, /) -> np.ndarray:
        a = _topic_term_matrix(prepared_a)
        b = _topic_term_matrix(prepared_b)
        if a.shape[1] != b.shape[1]:
            a, b = _align_vocab(a, b)
        sa, sb = np.sqrt(a), np.sqrt(b)
        diff = sa[:, None, :] - sb[None, :, :]
        h = np.sqrt(0.5 * np.sum(diff * diff, axis=-1))
        return 1.0 - h


class CosineSimilarity:
    """Cosine similarity over topic-term distribution vectors."""

    name = "cosine"

    def __call__(self, prepared_a: PreparedData, prepared_b: PreparedData, /) -> np.ndarray:
        a = _topic_term_matrix(prepared_a)
        b = _topic_term_matrix(prepared_b)
        if a.shape[1] != b.shape[1]:
            a, b = _align_vocab(a, b)
        return cosine_similarity(a, b)


class JaccardSimilarity:
    """Jaccard similarity over the top-N keyword sets per topic.

    Parameters
    ----------
    n_terms:
        How many top keywords to compare per topic (default 10).
    lambda_:
        pyLDAvis relevance lambda for keyword selection (default 0.6).
    """

    name = "jaccard"

    def __init__(self, *, n_terms: int = 10, lambda_: float = 0.6) -> None:
        self.n_terms = n_terms
        self.lambda_ = lambda_

    def __call__(self, prepared_a: PreparedData, prepared_b: PreparedData, /) -> np.ndarray:
        sets_a = self._sets(prepared_a)
        sets_b = self._sets(prepared_b)
        out = np.zeros((len(sets_a), len(sets_b)), dtype=np.float64)
        for i, sa in enumerate(sets_a):
            for j, sb in enumerate(sets_b):
                u = sa | sb
                out[i, j] = len(sa & sb) / len(u) if u else 0.0
        return out

    def _sets(self, prepared: PreparedData) -> list[set[str]]:
        return [
            set(prepared.topic_top_terms(k + 1, n=self.n_terms, lambda_=self.lambda_))
            for k in range(len(prepared.topic_order))
        ]


class WordEmbeddingSpaceSimilarity:
    """Word-Embedding-Space similarity (WES, He et al. 2017).

    Each topic is represented by the *unweighted* mean of the embedding
    vectors of its top-N keywords. This is the simplest embedding-based
    baseline and is the one explicitly compared against the paper's
    metric in Section 5.2.
    """

    name = "wes"

    def __init__(self, embedding: EmbeddingBackend, *, n_terms: int = 10, lambda_: float = 0.6):
        self.embedding = embedding
        self.n_terms = n_terms
        self.lambda_ = lambda_

    def _vec(self, prepared: PreparedData) -> np.ndarray:
        K = len(prepared.topic_order)
        out = np.zeros((K, self.embedding.vector_size), dtype=np.float64)
        for k in range(K):
            terms = prepared.topic_top_terms(k + 1, n=self.n_terms, lambda_=self.lambda_)
            in_vocab = [t for t in terms if t in self.embedding]
            if not in_vocab:
                continue
            stacked = np.asarray([self.embedding[t] for t in in_vocab], dtype=np.float64)
            out[k] = stacked.mean(axis=0)
        return out

    def __call__(self, prepared_a: PreparedData, prepared_b: PreparedData, /) -> np.ndarray:
        a = self._vec(prepared_a)
        b = self._vec(prepared_b)
        if not np.any(a) or not np.any(b):
            return np.zeros((a.shape[0], b.shape[0]))
        return cosine_similarity(a, b)


def _align_vocab(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Pad two topic-term matrices to a common (concat) vocabulary."""
    width = max(a.shape[1], b.shape[1])
    a2 = np.zeros((a.shape[0], width))
    b2 = np.zeros((b.shape[0], width))
    a2[:, : a.shape[1]] = a
    b2[:, : b.shape[1]] = b
    return a2, b2
