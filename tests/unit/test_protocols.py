"""Protocol-conformance tests.

Every shipped backend / metric / adapter must satisfy its Protocol.
``isinstance(obj, Protocol)`` works because each Protocol is decorated
with :func:`typing.runtime_checkable`.
"""

from __future__ import annotations

import numpy as np

from topicvisexplorer.embeddings.protocol import EmbeddingBackend
from topicvisexplorer.models.protocol import TopicModelAdapter
from topicvisexplorer.similarity.protocol import SimilarityMetric


class _StubEmbedding:
    """Minimal in-memory embedding used by Protocol-conformance tests."""

    vector_size = 4

    def __init__(self) -> None:
        self._vectors = {
            w: np.asarray([float(ord(w[0])), 1.0, 2.0, 3.0]) for w in ["dog", "cat", "car", "fish"]
        }

    def __contains__(self, word: str) -> bool:
        return word in self._vectors

    def __getitem__(self, word: str) -> np.ndarray:
        return self._vectors[word]


def test_word2vec_protocol() -> None:
    """Word2Vec can't be instantiated without gensim+data; assert the
    *Protocol shape* via ``hasattr`` instead."""
    from topicvisexplorer.embeddings import Word2Vec

    assert "vector_size" in Word2Vec.__annotations__
    for method in ("__contains__", "__getitem__", "fit", "from_path"):
        assert hasattr(Word2Vec, method), method


def test_stub_embedding_satisfies_protocol() -> None:
    assert isinstance(_StubEmbedding(), EmbeddingBackend)


def test_baselines_satisfy_similarity_protocol() -> None:
    from topicvisexplorer.similarity import (
        CosineSimilarity,
        HellingerSimilarity,
        JaccardSimilarity,
        JensenShannonSimilarity,
        WordEmbeddingSpaceSimilarity,
    )

    for cls, args in [
        (CosineSimilarity, ()),
        (HellingerSimilarity, ()),
        (JaccardSimilarity, ()),
        (JensenShannonSimilarity, ()),
        (WordEmbeddingSpaceSimilarity, (_StubEmbedding(),)),
    ]:
        instance = cls(*args)
        assert isinstance(instance, SimilarityMetric), cls


def test_adapters_satisfy_topic_model_adapter_protocol() -> None:
    from topicvisexplorer.models import (
        BERTopicAdapter,
        CTMAdapter,
        ETMAdapter,
        GensimLDAAdapter,
        SklearnLDAAdapter,
        SklearnNMFAdapter,
    )

    for cls in [
        GensimLDAAdapter,
        SklearnLDAAdapter,
        SklearnNMFAdapter,
        BERTopicAdapter,
        CTMAdapter,
        ETMAdapter,
    ]:
        assert isinstance(cls(), TopicModelAdapter), cls


def test_stub_adapters_raise_actionable_not_implemented() -> None:
    from topicvisexplorer.models import BERTopicAdapter, CTMAdapter, ETMAdapter

    for cls in [BERTopicAdapter, CTMAdapter, ETMAdapter]:
        try:
            cls().extract(model=None, corpus=None)
        except NotImplementedError as e:
            assert "v1.1" in str(e), f"{cls.__name__} should mention v1.1"
        else:
            raise AssertionError(f"{cls.__name__}.extract should raise NotImplementedError")
