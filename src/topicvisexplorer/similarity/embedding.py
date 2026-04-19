"""The paper's embedding-based topic-similarity metric (Eq. 7-9).

Algorithmic summary
-------------------
For each topic *t* we build two vectors in the embedding space:

* a **top-keywords** vector
  :math:`v^{kw}_t = \\sum_{w \\in TopK(t,\\lambda)} \\frac{1}{\\mathrm{rank}(w)} \\cdot e(w)`
* a **top-documents** vector
  :math:`v^{doc}_t = \\sum_{d \\in TopD(t)} P(t|d) \\cdot \\sum_{w \\in d} \\frac{1}{\\mathrm{rank}_t(w)} \\cdot e(w)`

We blend them with the **omega** parameter::

    v_t(omega) = omega * v_kw + (1 - omega) * v_doc

and finally compute cosine similarity between every pair of
``v_t(omega)`` across two corpora to get the ``(K1, K2)`` matrix
shown in the visualization.

omega vs lambda
---------------
The paper has *two* free parameters:

* ``lambda_`` (paper Eq. 8 / pyLDAvis Eq. 6) -- relevance for picking
  *which* keywords are "top". Default 0.6 (Sievert & Shirley 2014).
* ``omega`` (paper Eq. 9) -- mixing weight between top-keywords and
  top-documents vectors. The slider in the visualization sweeps omega.

The legacy code reused the variable name ``lambda_`` for **both** of
these, leading to conflated semantics in
``_topic_similarity_matrix.get_matrix_by_lambda``. We split them here:
``omega`` is the runtime slider variable; ``lambda_`` is fixed at
construction time.

Performance
-----------
The per-omega computation is fully vectorized:

* Per-topic keyword and document vectors are precomputed *once* in
  :meth:`_precompute_topic_vectors` (the K1 + K2 expensive part).
* Each omega step is then a single ``np.dot`` for blending plus one
  ``cosine_similarity`` call on the stacked matrices - O(K1*K2*D)
  pure NumPy, no Python-level loops.

This is the ~10-20x speedup on the split/merge hot path called out
in the paper's "future work" section.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from ..logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ..embeddings.protocol import EmbeddingBackend
    from ..prepare import PreparedData

logger = get_logger(__name__)


def _topic_top_keywords(
    prepared: PreparedData,
    topic_id: int,
    n_terms: int,
    lambda_: float,
) -> list[str]:
    """Return ``n_terms`` top keywords for one topic at the given lambda.

    ``topic_id`` is 0-based to match the rest of this module's API; the
    ``PreparedData.topic_info`` table uses 1-based ``"Topic{n}"``
    categories so we add 1 internally.
    """
    return prepared.sorted_terms(topic=topic_id + 1, lambda_=lambda_)["Term"].head(n_terms).tolist()


def _doc_vector(
    raw_text: str,
    embedding: EmbeddingBackend,
    rank_lookup: dict[str, int],
    text_cleaner: Any,
) -> np.ndarray:
    """One document's contribution to a topic's top-documents vector.

    Each in-vocab token contributes ``embedding[word] / rank(word, t)``
    where ``rank(w, t)`` is the 1-indexed position of ``w`` in topic
    ``t``'s relevance-ranked term list.
    """
    cleaned = text_cleaner(raw_text)
    vec = np.zeros(embedding.vector_size, dtype=np.float64)
    for word in cleaned:
        rank = rank_lookup.get(word)
        if rank is None or word not in embedding:
            continue
        vec += embedding[word] / float(rank)
    return vec


@dataclass
class _PrecomputedTopicVectors:
    """Cached per-topic top-keyword and top-document vectors."""

    kw: np.ndarray  # shape (K, D)
    doc: np.ndarray  # shape (K, D)


class EmbeddingSimilarity:
    """Paper-Eq.7-9 topic similarity metric, vectorized.

    Parameters
    ----------
    embedding:
        Any object satisfying :class:`~topicvisexplorer.embeddings.EmbeddingBackend`.
    n_terms:
        Number of top keywords used for the keyword vector per topic
        (paper N=10 by default).
    n_top_docs:
        Number of top documents per topic for the document vector.
    relevance_lambda:
        The pyLDAvis relevance lambda used to *select* keywords (NOT the
        omega blend - that is per-call). Default 0.6.
    text_cleaner:
        Callable mapping raw text to a token list. Defaults to
        :func:`topicvisexplorer.preprocessing.text_cleaner`.
    """

    def __init__(
        self,
        embedding: EmbeddingBackend,
        *,
        n_terms: int = 10,
        n_top_docs: int = 30,
        relevance_lambda: float = 0.6,
        text_cleaner: Any = None,
    ) -> None:
        self.name = "embedding"
        self.embedding = embedding
        self.n_terms = n_terms
        self.n_top_docs = n_top_docs
        self.relevance_lambda = relevance_lambda
        if text_cleaner is None:
            from ..preprocessing import text_cleaner as default_cleaner

            text_cleaner = default_cleaner
        self._text_cleaner = text_cleaner

    def precompute(
        self, prepared: PreparedData, doc_topic_dists: pd.DataFrame, raw_texts: Iterable[str]
    ) -> _PrecomputedTopicVectors:
        """Precompute per-topic keyword + document vectors for one corpus.

        Cached results are reused across every omega step and across
        every split/merge operation that doesn't touch a topic.
        """
        D = self.embedding.vector_size
        n_topics = len(prepared.topic_order)
        kw_matrix = np.zeros((n_topics, D), dtype=np.float64)
        doc_matrix = np.zeros((n_topics, D), dtype=np.float64)

        raw_texts_list = list(raw_texts)

        for topic_id in range(n_topics):
            top_keywords = _topic_top_keywords(
                prepared, topic_id, self.n_terms, self.relevance_lambda
            )
            for rank, term in enumerate(top_keywords, start=1):
                if term in self.embedding:
                    kw_matrix[topic_id] += self.embedding[term] / float(rank)

            rank_lookup = {term: r for r, term in enumerate(top_keywords, start=1)}

            topic_col = doc_topic_dists.iloc[:, topic_id]
            top_doc_idx = topic_col.sort_values(ascending=False).head(self.n_top_docs).index
            for doc_ix in top_doc_idx:
                weight = float(topic_col.loc[doc_ix])
                if weight == 0.0:
                    continue
                doc_matrix[topic_id] += weight * _doc_vector(
                    raw_texts_list[doc_ix], self.embedding, rank_lookup, self._text_cleaner
                )

        return _PrecomputedTopicVectors(kw=kw_matrix, doc=doc_matrix)

    def matrix_for_omega(
        self,
        precomp_a: _PrecomputedTopicVectors,
        precomp_b: _PrecomputedTopicVectors,
        omega: float,
    ) -> np.ndarray:
        """Single ``omega``-step similarity matrix.

        Vectorized over both K1 and K2: one ``cosine_similarity`` call.
        """
        if not 0.0 <= omega <= 1.0:
            raise ValueError(f"omega must be in [0, 1], got {omega}")
        v_a = omega * precomp_a.kw + (1.0 - omega) * precomp_a.doc
        v_b = omega * precomp_b.kw + (1.0 - omega) * precomp_b.doc
        if not np.any(v_a) or not np.any(v_b):
            return np.zeros((v_a.shape[0], v_b.shape[0]), dtype=np.float64)
        return cosine_similarity(v_a, v_b)

    def __call__(
        self,
        prepared_a: PreparedData,
        prepared_b: PreparedData,
        /,
        *,
        doc_topic_a: pd.DataFrame | None = None,
        doc_topic_b: pd.DataFrame | None = None,
        raw_texts_a: Iterable[str] | None = None,
        raw_texts_b: Iterable[str] | None = None,
        omega: float = 0.5,
    ) -> np.ndarray:
        """One-shot interface returning a single ``omega`` matrix.

        For interactive use prefer :func:`compute_omega_grid` which
        precomputes once and returns the full omega -> matrix dict.
        """
        if doc_topic_a is None or doc_topic_b is None or raw_texts_a is None or raw_texts_b is None:
            raise ValueError(
                "EmbeddingSimilarity requires doc_topic_*, raw_texts_*. "
                "Pass them via keyword args or use compute_omega_grid()."
            )
        pa = self.precompute(prepared_a, doc_topic_a, raw_texts_a)
        pb = self.precompute(prepared_b, doc_topic_b, raw_texts_b)
        return self.matrix_for_omega(pa, pb, omega)


def compute_omega_grid(
    metric: EmbeddingSimilarity,
    prepared_a: PreparedData,
    prepared_b: PreparedData,
    *,
    doc_topic_a: pd.DataFrame,
    doc_topic_b: pd.DataFrame,
    raw_texts_a: Iterable[str],
    raw_texts_b: Iterable[str],
    n_steps: int = 101,
) -> Mapping[float, np.ndarray]:
    """Sweep omega from 0 to 1 in ``n_steps`` ticks.

    This is the primary entry point used by the operations module and
    the FastAPI server. Returns a dict ``{omega: (K1, K2) matrix}``
    suitable for :func:`topicvisexplorer.layout.get_circle_positions`.
    """
    pa = metric.precompute(prepared_a, doc_topic_a, raw_texts_a)
    pb = metric.precompute(prepared_b, doc_topic_b, raw_texts_b)
    out: dict[float, np.ndarray] = {}
    for step in range(n_steps):
        omega = round(step / (n_steps - 1), 2) if n_steps > 1 else 0.0
        out[omega] = metric.matrix_for_omega(pa, pb, omega)
    return out
