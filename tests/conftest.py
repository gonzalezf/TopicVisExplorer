"""Shared pytest fixtures.

* :func:`tiny_prepared` -- a small synthetic :class:`PreparedData` with
  4 topics, used by every unit test that needs a realistic but fast
  fixture.
* :func:`tiny_corpus` -- the matching tokenized corpus (for coherence /
  similarity tests).
* :func:`tiny_doc_topic_dists` -- the doc-topic matrix.

Also sets ``TVE_EMBEDDING_DISABLE=1`` at import time (unless the host
environment already set it) so the parametrized fixture-backed API
tests fall through to the flat-JSD path instead of paying a ~20s
Word2Vec training cost per scenario. The
``test_fixture_quality::test_circle_positions_endpoints_differ`` test
explicitly unsets this to exercise the real embedding path.
"""

from __future__ import annotations

import os

# Default ON for the whole test session; individual tests that want the
# real Omega-varying path override via monkeypatch. Must be set before
# :mod:`topicvisexplorer` (or any module that reads the env) is imported.
os.environ.setdefault("TVE_EMBEDDING_DISABLE", "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from topicvisexplorer import prepare  # noqa: E402


@pytest.fixture(scope="session")
def tiny_corpus() -> list[list[str]]:
    return [
        ["dog", "cat", "puppy", "kitten", "pet", "animal"],
        ["dog", "bark", "leash", "park", "walk", "pet"],
        ["cat", "purr", "litter", "nap", "scratch", "pet"],
        ["fish", "tank", "water", "swim", "fin", "scale"],
        ["fish", "ocean", "boat", "swim", "fin", "deep"],
        ["puppy", "kitten", "pet", "fluffy", "animal", "cute"],
        ["car", "engine", "wheel", "brake", "road", "tire"],
        ["car", "fuel", "speed", "drive", "highway", "engine"],
        ["car", "tire", "wheel", "highway", "road", "fast"],
        ["dog", "puppy", "leash", "bark", "walk", "park"],
        ["cat", "kitten", "purr", "scratch", "litter", "nap"],
        ["fish", "tank", "water", "swim", "deep", "ocean"],
    ]


@pytest.fixture(scope="session")
def tiny_topic_term() -> np.ndarray:
    """4 topics x 24 terms, deliberately well-separated."""
    np.random.seed(0)
    K, V = 4, 24
    base = np.full((K, V), 0.001)
    for k, slice_ in enumerate([(0, 6), (6, 12), (12, 18), (18, 24)]):
        base[k, slice_[0] : slice_[1]] += 1.0 + 0.1 * np.random.rand(6)
    return base / base.sum(axis=1, keepdims=True)


@pytest.fixture(scope="session")
def tiny_doc_topic(tiny_topic_term: np.ndarray) -> np.ndarray:
    """12 docs assigned 3 per topic with some bleed."""
    K = tiny_topic_term.shape[0]
    N = 12
    rng = np.random.default_rng(0)
    dt = np.full((N, K), 0.05)
    for d in range(N):
        dt[d, d % K] += 1.0
        bleed = rng.choice(K)
        dt[d, bleed] += 0.3
    return dt / dt.sum(axis=1, keepdims=True)


@pytest.fixture(scope="session")
def tiny_vocab() -> list[str]:
    return [
        "dog",
        "puppy",
        "leash",
        "bark",
        "park",
        "walk",
        "cat",
        "kitten",
        "purr",
        "scratch",
        "litter",
        "nap",
        "fish",
        "tank",
        "ocean",
        "swim",
        "deep",
        "fin",
        "car",
        "engine",
        "wheel",
        "tire",
        "road",
        "highway",
    ]


@pytest.fixture(scope="session")
def tiny_term_freq(tiny_corpus: list[list[str]], tiny_vocab: list[str]) -> np.ndarray:
    counts = pd.Series([w for d in tiny_corpus for w in d]).value_counts()
    return np.asarray([counts.get(w, 1) for w in tiny_vocab], dtype=np.float64)


@pytest.fixture(scope="session")
def tiny_doc_lengths(tiny_corpus: list[list[str]]) -> np.ndarray:
    return np.asarray([len(d) for d in tiny_corpus], dtype=np.float64)


@pytest.fixture(scope="session")
def tiny_prepared(
    tiny_topic_term: np.ndarray,
    tiny_doc_topic: np.ndarray,
    tiny_doc_lengths: np.ndarray,
    tiny_vocab: list[str],
    tiny_term_freq: np.ndarray,
):
    return prepare(
        topic_term_dists=tiny_topic_term,
        doc_topic_dists=tiny_doc_topic,
        doc_lengths=tiny_doc_lengths,
        vocab=tiny_vocab,
        term_frequency=tiny_term_freq,
    )
