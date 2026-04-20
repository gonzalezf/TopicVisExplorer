"""Tiny in-process demo scenarios used by ``tve.demo()``.

These are intentionally tiny (5 topics, ~50 docs, ~80-word vocab) so
``tve.demo()`` boots in <2s on a laptop. They are *synthetic* (not real
news data) so the output is reproducible and deterministic.

For realistic showcases, see ``examples/`` notebooks (Phase 5).
"""

from __future__ import annotations

import numpy as np

from ..prepare import prepare
from .scenarios import Scenario


def _seed_synthetic(seed: int = 42, K: int = 5, V: int = 60, N: int = 80):
    """Generate a tiny reproducible (topic_term, doc_topic, vocab, lens, freq)."""
    rng = np.random.default_rng(seed)
    topic_term = rng.dirichlet([0.1] * V, size=K)
    doc_topic = rng.dirichlet([0.5] * K, size=N)
    vocab = [f"w{i:02d}" for i in range(V)]
    doc_lengths = rng.integers(20, 200, size=N)
    term_frequency = (doc_topic.T @ doc_lengths[:, None]).flatten()
    term_frequency = (topic_term.T @ term_frequency).astype(float)
    term_frequency = np.maximum(term_frequency, 1.0)
    return topic_term, doc_topic, vocab, doc_lengths, term_frequency


class _StaticModelData:
    """Bare :class:`TopicModelData` carrier that bypasses Protocol setup."""

    def __init__(
        self,
        topic_term_dists: np.ndarray,
        doc_topic_dists: np.ndarray,
        doc_lengths: np.ndarray,
        vocab: list[str],
        term_frequency: np.ndarray,
    ) -> None:
        self.topic_term_dists = topic_term_dists
        self.doc_topic_dists = doc_topic_dists
        self.doc_lengths = doc_lengths
        self.vocab = vocab
        self.term_frequency = term_frequency


def build_tiny_single_demo() -> Scenario:
    """5-topic synthetic single-corpus demo."""
    tt, dt, vocab, lens, freq = _seed_synthetic()
    prepared = prepare(
        topic_term_dists=tt,
        doc_topic_dists=dt,
        doc_lengths=lens,
        vocab=vocab,
        term_frequency=freq,
        metadata={"scenario": "tiny_demo", "synthetic": True},
    )

    # ``doc_id`` is a stable index into ``doc_topic_dists`` and is what
    # the ``/Exclude_Document`` endpoint expects (see
    # :class:`~topicvisexplorer.server.schemas.ExcludeDocumentRequest`).
    # Exposing it on every relevant_documents row lets the front-end
    # bind the exclude-button to a specific source document without
    # depending on table sort order or pagination.
    relevant_documents = [
        {
            "doc_id": i,
            "text": f"synthetic document #{i}",
            **{str(k): float(dt[i, k]) for k in range(dt.shape[1])},
        }
        for i in range(dt.shape[0])
    ]

    K = tt.shape[0]
    rng = np.random.default_rng(0)
    similarity = {round(step / 100.0, 2): _sym_random_matrix(K, rng) for step in range(101)}
    layout = {round(step / 100.0, 2): rng.normal(size=(K, 2)).tolist() for step in range(101)}

    return Scenario(
        name="tiny_demo",
        is_multi=False,
        prepared=prepared,
        model_data=_StaticModelData(tt, dt, lens, vocab, freq),
        relevant_documents=relevant_documents,
        similarity_matrix=similarity,
        circle_positions=layout,
        raw_texts=[f"synthetic document #{i}" for i in range(dt.shape[0])],
    )


def build_tiny_multi_demo() -> Scenario:
    """Pair of 5-topic synthetic corpora for the Sankey view."""
    tt_a, dt_a, vocab_a, lens_a, freq_a = _seed_synthetic(seed=1)
    tt_b, dt_b, vocab_b, lens_b, freq_b = _seed_synthetic(seed=2)
    prep_a = prepare(
        topic_term_dists=tt_a,
        doc_topic_dists=dt_a,
        doc_lengths=lens_a,
        vocab=vocab_a,
        term_frequency=freq_a,
        metadata={"scenario": "tiny_multi_demo", "corpus": "A"},
    )
    prep_b = prepare(
        topic_term_dists=tt_b,
        doc_topic_dists=dt_b,
        doc_lengths=lens_b,
        vocab=vocab_b,
        term_frequency=freq_b,
        metadata={"scenario": "tiny_multi_demo", "corpus": "B"},
    )
    docs_a = [
        {
            "doc_id": i,
            "text": f"corpus A doc #{i}",
            **{str(k): float(dt_a[i, k]) for k in range(dt_a.shape[1])},
        }
        for i in range(dt_a.shape[0])
    ]
    docs_b = [
        {
            "doc_id": i,
            "text": f"corpus B doc #{i}",
            **{str(k): float(dt_b[i, k]) for k in range(dt_b.shape[1])},
        }
        for i in range(dt_b.shape[0])
    ]
    K = tt_a.shape[0]
    rng = np.random.default_rng(7)
    similarity = {round(step / 100.0, 2): _sym_random_matrix(K, rng) for step in range(101)}
    layout = {round(step / 100.0, 2): rng.normal(size=(K, 2)).tolist() for step in range(101)}
    sc = Scenario(
        name="tiny_multi_demo",
        is_multi=True,
        prepared=prep_a,
        prepared_b=prep_b,
        relevant_documents=docs_a,
        relevant_documents_b=docs_b,
        similarity_matrix=similarity,
        circle_positions=layout,
    )
    return sc


def _sym_random_matrix(K: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a symmetric random similarity matrix for the demo data."""
    a = rng.uniform(0.0, 1.0, size=(K, K))
    sym = 0.5 * (a + a.T)
    np.fill_diagonal(sym, 1.0)
    return sym
