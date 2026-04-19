"""Unit tests for :mod:`topicvisexplorer.similarity`."""

from __future__ import annotations

import numpy as np
import pytest

from topicvisexplorer.similarity import (
    CosineSimilarity,
    EmbeddingSimilarity,
    HellingerSimilarity,
    JaccardSimilarity,
    JensenShannonSimilarity,
    WordEmbeddingSpaceSimilarity,
)
from topicvisexplorer.similarity.embedding import compute_omega_grid


class _StubEmbedding:
    vector_size = 4

    def __init__(self, vocab: list[str]) -> None:
        rng = np.random.default_rng(0)
        self._vectors = {w: rng.standard_normal(self.vector_size) for w in vocab}

    def __contains__(self, w: str) -> bool:
        return w in self._vectors

    def __getitem__(self, w: str) -> np.ndarray:
        return self._vectors[w]


def test_cosine_similarity_diagonal_high(tiny_prepared) -> None:
    metric = CosineSimilarity()
    M = metric(tiny_prepared, tiny_prepared)
    diag = np.diag(M)
    off = M - np.diag(diag)
    assert np.all(diag > off.max(axis=1) - 1e-9)


def test_jensen_shannon_self_similarity_one(tiny_prepared) -> None:
    M = JensenShannonSimilarity()(tiny_prepared, tiny_prepared)
    assert np.allclose(np.diag(M), 1.0, atol=1e-6)


def test_hellinger_in_unit_range(tiny_prepared) -> None:
    M = HellingerSimilarity()(tiny_prepared, tiny_prepared)
    assert M.min() >= -1e-9 and M.max() <= 1.0 + 1e-9


def test_jaccard_self_one(tiny_prepared) -> None:
    M = JaccardSimilarity(n_terms=5)(tiny_prepared, tiny_prepared)
    assert np.allclose(np.diag(M), 1.0)


def test_wes_with_stub_embedding(tiny_prepared, tiny_vocab) -> None:
    M = WordEmbeddingSpaceSimilarity(_StubEmbedding(tiny_vocab))(tiny_prepared, tiny_prepared)
    assert M.shape == (4, 4)
    assert np.allclose(np.diag(M), 1.0, atol=1e-6)


def test_embedding_similarity_omega_grid_shape(
    tiny_prepared, tiny_corpus, tiny_doc_topic, tiny_vocab
) -> None:
    import pandas as pd

    metric = EmbeddingSimilarity(
        _StubEmbedding(tiny_vocab),
        n_terms=5,
        n_top_docs=3,
        text_cleaner=lambda s: s.split() if isinstance(s, str) else s,
    )
    grid = compute_omega_grid(
        metric,
        tiny_prepared,
        tiny_prepared,
        doc_topic_a=pd.DataFrame(tiny_doc_topic),
        doc_topic_b=pd.DataFrame(tiny_doc_topic),
        raw_texts_a=[" ".join(d) for d in tiny_corpus],
        raw_texts_b=[" ".join(d) for d in tiny_corpus],
        n_steps=11,
    )
    assert len(grid) == 11
    assert all(v.shape == (4, 4) for v in grid.values())


def test_embedding_similarity_omega_extremes_pure_kw_vs_doc(
    tiny_prepared, tiny_corpus, tiny_doc_topic, tiny_vocab
):
    import pandas as pd

    metric = EmbeddingSimilarity(
        _StubEmbedding(tiny_vocab),
        n_terms=5,
        n_top_docs=3,
        text_cleaner=lambda s: s.split() if isinstance(s, str) else s,
    )
    pa = metric.precompute(
        tiny_prepared, pd.DataFrame(tiny_doc_topic), [" ".join(d) for d in tiny_corpus]
    )
    M0 = metric.matrix_for_omega(pa, pa, omega=0.0)
    M1 = metric.matrix_for_omega(pa, pa, omega=1.0)
    assert not np.allclose(M0, M1)


def test_embedding_similarity_rejects_bad_omega() -> None:
    metric = EmbeddingSimilarity(_StubEmbedding(["x"]), n_terms=1, n_top_docs=1)
    with pytest.raises(ValueError, match="omega must be in"):
        metric.matrix_for_omega(
            precomp_a=type("P", (), {"kw": np.zeros((1, 4)), "doc": np.zeros((1, 4))})(),
            precomp_b=type("P", (), {"kw": np.zeros((1, 4)), "doc": np.zeros((1, 4))})(),
            omega=1.5,
        )
