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


def test_no_stub_adapters_remain_in_v1() -> None:
    """All Section 6 adapters (BERTopic, ETM, CTM) shipped in Phase 4
    a/b/c respectively. None should still raise NotImplementedError
    when called with a duck-typed model. Behaviour-level coverage lives
    in tests/unit/test_adapters.py; this is a guardrail to make sure no
    one accidentally re-introduces a stub.
    """
    from topicvisexplorer.models import BERTopicAdapter, CTMAdapter, ETMAdapter

    for cls in [BERTopicAdapter, CTMAdapter, ETMAdapter]:
        # These adapters all raise ValidationError (not
        # NotImplementedError) when invoked with `model=None` because
        # they validate inputs first. Asserting the *type* is enough.
        from topicvisexplorer.errors import ValidationError

        try:
            cls().extract(model=None, corpus=None)
        except ValidationError:
            pass  # expected: every adapter validates its inputs
        except NotImplementedError as e:  # pragma: no cover - regression guard
            raise AssertionError(
                f"{cls.__name__} regressed to a NotImplementedError stub: {e}"
            ) from e
