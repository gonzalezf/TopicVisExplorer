"""Unit tests for non-LDA topic-model adapters.

The real BERTopic stack pulls in sentence-transformers, UMAP and HDBSCAN
(~600MB of wheels and a 200MB SBERT checkpoint). Running it in a unit
test would be a 60-second smoke test on every PR. Instead we drive the
adapter through a **fake BERTopic-shaped object** that exposes exactly
the public surface the adapter consumes (``c_tf_idf_``,
``vectorizer_model``, ``topics_``, ``get_topic_info``,
``approximate_distribution``).

This is the same pattern sklearn uses to test transformer adapters
without the full PyTorch stack: minimal duck-typed object + assertion
on the standardized output. It catches every adapter-internal bug
(shape mismatches, outlier handling, normalization) while keeping CI
fast and hermetic.

If/when ``bertopic`` is actually installed (e.g. on the [full]-extra
nightly job), the additional ``test_bertopic_real_smoke`` test in this
module activates and exercises the real model end-to-end.
"""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest
from sklearn.feature_extraction.text import CountVectorizer

from topicvisexplorer.errors import ValidationError
from topicvisexplorer.models import BERTopicAdapter, CTMAdapter, ETMAdapter
from topicvisexplorer.models.protocol import TopicModelData

# ---------------------------------------------------------------------------
# Fake BERTopic-shaped object. We re-build only what BERTopicAdapter touches.
# ---------------------------------------------------------------------------


class _FakeTopicInfoFrame:
    """Tiny stand-in for the pandas DataFrame BERTopic returns from get_topic_info()."""

    def __init__(self, topics: list[int]) -> None:
        self._cols: dict[str, list[int]] = {"Topic": list(topics)}

    def __getitem__(self, key: str) -> list[int]:
        return self._cols[key]


class _FakeBERTopic:
    """Duck-typed BERTopic surface used by the adapter."""

    def __init__(
        self,
        *,
        c_tf_idf: np.ndarray,
        topics: list[int],
        vectorizer: CountVectorizer,
        topics_per_doc: list[int],
        approx_distribution: np.ndarray | None = None,
    ) -> None:
        self.c_tf_idf_ = c_tf_idf
        self._topics = topics
        self.vectorizer_model = vectorizer
        self.topics_ = topics_per_doc
        self._approx = approx_distribution

    def get_topic_info(self) -> _FakeTopicInfoFrame:
        return _FakeTopicInfoFrame(self._topics)

    def approximate_distribution(
        self, texts: list[str], *, calculate_tokens: bool = False
    ) -> tuple[np.ndarray, None]:
        if self._approx is None:
            raise RuntimeError("approximate_distribution unavailable")
        return self._approx, None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_DOCS = [
    "cat dog fish",
    "cat fish",
    "car train plane",
    "car bus train",
    "dog cat fish bird",
    "plane train bus car",
]


@pytest.fixture
def fitted_vectorizer() -> CountVectorizer:
    v = CountVectorizer()
    v.fit(_DOCS)
    return v


def _make_fake_model(
    fitted_vectorizer: CountVectorizer,
    *,
    include_outlier_topic: bool,
    soft_dtd: bool,
) -> _FakeBERTopic:
    """Build a fake BERTopic with K=2 (animals, transport) ± outlier."""
    vocab = list(fitted_vectorizer.get_feature_names_out())
    V = len(vocab)
    K_real = 2  # animals topic + transport topic

    # Build a c-TF-IDF that looks like real BERTopic output: high weights
    # on a few terms per topic, zero elsewhere.
    c_tf_idf = np.zeros((K_real + (1 if include_outlier_topic else 0), V))
    animal_words = ["cat", "dog", "fish", "bird"]
    transport_words = ["car", "train", "plane", "bus"]
    rows_offset = 1 if include_outlier_topic else 0
    for word in animal_words:
        if word in vocab:
            c_tf_idf[rows_offset + 0, vocab.index(word)] = 0.5
    for word in transport_words:
        if word in vocab:
            c_tf_idf[rows_offset + 1, vocab.index(word)] = 0.5
    if include_outlier_topic:
        # Outlier row: diffuse mass across everything; the adapter must
        # drop this row by default.
        c_tf_idf[0, :] = 0.01

    topics_index = ([-1] if include_outlier_topic else []) + [0, 1]
    # Per-doc topic assignment (deliberately includes one outlier when
    # we have an outlier topic so we can assert it's renormalized).
    topics_per_doc = (
        [0, 0, 1, 1, 0, -1] if include_outlier_topic else [0, 0, 1, 1, 0, 1]
    )

    approx = None
    if soft_dtd:
        # Simulate `approximate_distribution`: shape (N, K_real),
        # excluding -1 (BERTopic strips outliers from this output).
        approx = np.array(
            [
                [0.9, 0.1],
                [0.85, 0.15],
                [0.1, 0.9],
                [0.05, 0.95],
                [0.8, 0.2],
                [0.3, 0.7],  # the "outlier" doc still gets soft mass
            ]
        )

    return _FakeBERTopic(
        c_tf_idf=c_tf_idf,
        topics=topics_index,
        vectorizer=fitted_vectorizer,
        topics_per_doc=topics_per_doc,
        approx_distribution=approx,
    )


# ---------------------------------------------------------------------------
# Tests: BERTopic adapter shape + semantics on the fake model
# ---------------------------------------------------------------------------


class TestBERTopicAdapter:
    def test_adapter_satisfies_protocol(self) -> None:
        from topicvisexplorer.models.protocol import TopicModelAdapter

        assert isinstance(BERTopicAdapter(), TopicModelAdapter)
        assert BERTopicAdapter.name == "bertopic"

    def test_extract_returns_valid_topic_model_data_with_soft_dtd(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=False, soft_dtd=True
        )
        data = BERTopicAdapter().extract(model, corpus=None, texts=_DOCS)

        assert isinstance(data, TopicModelData)
        K, V = data.topic_term_dists.shape
        N = data.doc_topic_dists.shape[0]
        assert K == 2
        assert len(_DOCS) == N
        assert len(fitted_vectorizer.get_feature_names_out()) == V

        # Row-stochasticity (Sievert & Shirley contract).
        np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-10)
        np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-10)

        # Term frequency and doc lengths must be non-negative integers
        # consistent with a re-vectorization of the input docs.
        assert (data.term_frequency >= 0).all()
        assert (data.doc_lengths >= 0).all()
        assert int(data.doc_lengths.sum()) == int(data.term_frequency.sum())

        # Animal topic should put mass on at least one animal word.
        animal_idx = [data.vocab.index(w) for w in ("cat", "dog", "fish") if w in data.vocab]
        assert data.topic_term_dists[0, animal_idx].sum() > 0.5

    def test_extract_falls_back_to_one_hot_when_approx_missing(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=False, soft_dtd=False
        )
        # Strip the approximate_distribution method to force the fallback.
        model.approximate_distribution = None  # type: ignore[assignment]

        data = BERTopicAdapter().extract(model, corpus=None, texts=_DOCS)

        # One-hot doc-topic ⇒ each row has exactly one 1.0 and zeros.
        for i in range(data.doc_topic_dists.shape[0]):
            row = data.doc_topic_dists[i]
            np.testing.assert_allclose(row.sum(), 1.0, atol=1e-10)
            assert (row == 1.0).sum() == 1, f"row {i} not one-hot: {row}"

    def test_outlier_topic_dropped_by_default(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=True, soft_dtd=True
        )
        data = BERTopicAdapter().extract(model, corpus=None, texts=_DOCS)

        # We started with 3 rows (-1, 0, 1); -1 must be gone.
        assert data.topic_term_dists.shape[0] == 2

        # Outlier-doc row (index 5 -> topic -1 in the fake) must still
        # be a valid distribution -- the adapter renormalizes via the
        # approx fallback, never producing a NaN row.
        assert np.isfinite(data.doc_topic_dists).all()
        np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-10)

    def test_outlier_topic_kept_when_requested(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=True, soft_dtd=False
        )
        data = BERTopicAdapter().extract(
            model, corpus=None, texts=_DOCS, include_outliers=True
        )
        assert data.topic_term_dists.shape[0] == 3

    def test_missing_texts_raises_actionable_error(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=False, soft_dtd=True
        )
        with pytest.raises(ValidationError, match="texts="):
            BERTopicAdapter().extract(model, corpus=None)

    def test_missing_c_tf_idf_raises_actionable_error(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=False, soft_dtd=True
        )
        model.c_tf_idf_ = None
        with pytest.raises(ValidationError, match="c_tf_idf_"):
            BERTopicAdapter().extract(model, corpus=None, texts=_DOCS)

    def test_topic_count_mismatch_with_vocab_raises(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=False, soft_dtd=True
        )
        # Truncate one column to simulate vectorizer-vs-model drift.
        model.c_tf_idf_ = model.c_tf_idf_[:, :-1]
        with pytest.raises(ValidationError, match="vectorizer vocabulary"):
            BERTopicAdapter().extract(model, corpus=None, texts=_DOCS)

    def test_zero_row_topic_handled_gracefully(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        """An all-zero c-TF-IDF row must NOT produce NaN -- it gets
        replaced with a uniform distribution and a warning is logged."""
        model = _make_fake_model(
            fitted_vectorizer, include_outlier_topic=False, soft_dtd=True
        )
        model.c_tf_idf_ = model.c_tf_idf_.copy()
        model.c_tf_idf_[0, :] = 0.0

        data = BERTopicAdapter().extract(model, corpus=None, texts=_DOCS)
        np.testing.assert_allclose(data.topic_term_dists[0].sum(), 1.0, atol=1e-10)
        assert np.isfinite(data.topic_term_dists).all()


# ---------------------------------------------------------------------------
# Optional: real-BERTopic smoke test, only runs if the dep is installed.
# Marked slow so it stays out of the default CI matrix; the [full]-extra
# nightly job picks it up via -m slow.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Fake ETM-shaped objects
# ---------------------------------------------------------------------------


class _FakeETMPackageStyle:
    """Mimics the public surface of `embedded_topic_model.models.etm.ETM`.

    Used to verify the adapter against the de-facto sklearn-style PyPI
    package without pulling in PyTorch / SciPy-sparse heavy deps.
    """

    def __init__(
        self, *, vocabulary: list[str], topic_word: np.ndarray, doc_topic: np.ndarray
    ) -> None:
        self.vocabulary = vocabulary
        self._topic_word = topic_word
        self._doc_topic = doc_topic

    def get_topic_word_matrix(self) -> np.ndarray:
        return self._topic_word

    def get_document_topic_dist(self) -> np.ndarray:
        return self._doc_topic


class _FakeETMResearchStyle:
    """Mimics the original Dieng et al. PyTorch repo surface.

    Exposes ``get_beta`` (returns logits, NOT probabilities) so we can
    test the adapter's softmax-detection branch. Skips ``get_theta`` to
    force the caller to pass ``doc_topic_dists`` explicitly (the most
    common end-user pattern when working with the research repo).
    """

    def __init__(self, *, beta_logits: np.ndarray) -> None:
        self._beta = beta_logits

    def get_beta(self) -> np.ndarray:
        return self._beta


def _make_fake_etm_package(
    fitted_vectorizer: CountVectorizer, *, K: int = 2
) -> _FakeETMPackageStyle:
    vocab = list(fitted_vectorizer.get_feature_names_out())
    V = len(vocab)
    rng = np.random.default_rng(0)

    topic_word = rng.dirichlet(np.ones(V), size=K)  # already row-stochastic
    doc_topic = rng.dirichlet(np.ones(K), size=len(_DOCS))

    return _FakeETMPackageStyle(
        vocabulary=vocab, topic_word=topic_word, doc_topic=doc_topic
    )


# ---------------------------------------------------------------------------
# ETM adapter tests
# ---------------------------------------------------------------------------


class TestETMAdapter:
    def test_adapter_satisfies_protocol(self) -> None:
        from topicvisexplorer.models.protocol import TopicModelAdapter

        assert isinstance(ETMAdapter(), TopicModelAdapter)
        assert ETMAdapter.name == "etm"

    def test_extract_via_package_interface(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_etm_package(fitted_vectorizer, K=3)
        data = ETMAdapter().extract(model, corpus=None, texts=_DOCS)

        assert isinstance(data, TopicModelData)
        assert data.topic_term_dists.shape[0] == 3
        assert data.doc_topic_dists.shape[0] == len(_DOCS)
        assert data.vocab == list(fitted_vectorizer.get_feature_names_out())
        np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-10)
        np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-10)
        # term_frequency must agree with re-vectorization.
        X = fitted_vectorizer.transform(_DOCS)
        np.testing.assert_array_equal(
            data.term_frequency.astype(int),
            np.asarray(X.sum(axis=0)).ravel(),
        )

    def test_extract_via_research_interface_with_logits(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        """Research repo's `get_beta` may return raw logits; the adapter
        must detect the negative entries and softmax them."""
        vocab = list(fitted_vectorizer.get_feature_names_out())
        V = len(vocab)
        K = 2
        # Logits include negatives so the adapter's `(beta < 0).any()`
        # heuristic kicks in.
        beta_logits = np.random.default_rng(1).standard_normal((K, V))
        model = _FakeETMResearchStyle(beta_logits=beta_logits)

        # Caller supplies doc_topic_dists because this fake doesn't
        # expose `get_theta` -- common with the raw research repo.
        N = len(_DOCS)
        dtd = np.full((N, K), 1.0 / K)

        data = ETMAdapter().extract(
            model, corpus=None, texts=_DOCS, vocabulary=vocab, doc_topic_dists=dtd
        )
        np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-10)
        # Softmax output is strictly positive.
        assert (data.topic_term_dists > 0).all()

    def test_missing_texts_raises(self, fitted_vectorizer: CountVectorizer) -> None:
        model = _make_fake_etm_package(fitted_vectorizer)
        with pytest.raises(ValidationError, match="texts="):
            ETMAdapter().extract(model, corpus=None)

    def test_missing_vocabulary_raises(self, fitted_vectorizer: CountVectorizer) -> None:
        # Research-style fake without `vocabulary` attribute.
        rng = np.random.default_rng(2)
        beta = rng.dirichlet(np.ones(8), size=2)
        model = _FakeETMResearchStyle(beta_logits=beta)
        with pytest.raises(ValidationError, match="vocabulary"):
            ETMAdapter().extract(model, corpus=None, texts=_DOCS)

    def test_vocab_size_mismatch_raises(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_etm_package(fitted_vectorizer)
        # Pass a vocabulary that's the wrong size on purpose.
        wrong_vocab = list(fitted_vectorizer.get_feature_names_out())[:-2]
        with pytest.raises(ValidationError, match="vocabulary"):
            ETMAdapter().extract(
                model, corpus=None, texts=_DOCS, vocabulary=wrong_vocab
            )

    def test_unsupported_model_interface_raises(self) -> None:
        class _NoOp:
            def __init__(self) -> None:
                self.vocabulary = ["a", "b", "c"]

        with pytest.raises(ValidationError, match="get_topic_word_matrix"):
            ETMAdapter().extract(_NoOp(), corpus=None, texts=["a b", "b c"])

    def test_caller_supplied_doc_topic_overrides_model(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_etm_package(fitted_vectorizer, K=2)
        N = len(_DOCS)
        custom_dtd = np.full((N, 2), [0.25, 0.75])
        data = ETMAdapter().extract(
            model, corpus=None, texts=_DOCS, doc_topic_dists=custom_dtd
        )
        np.testing.assert_allclose(data.doc_topic_dists, custom_dtd, atol=1e-10)


# ---------------------------------------------------------------------------
# Fake CTM-shaped objects + tests
# ---------------------------------------------------------------------------


class _FakeCTMTrainData:
    """Tiny stand-in for CTM's ``train_data`` carrying ``idx2token``."""

    def __init__(self, vocab: list[str]) -> None:
        # CTM ships idx2token as a real dict[int, str]; we mirror that
        # so the adapter's `_discover_vocabulary` walks the right path.
        self.idx2token = dict(enumerate(vocab))


class _FakeCTMPackageStyle:
    """Mimics the public surface of `contextualized_topic_models.models.ctm.CTM`."""

    def __init__(
        self, *, vocabulary: list[str], topic_word: np.ndarray, with_train_data: bool = True
    ) -> None:
        self._topic_word = topic_word
        if with_train_data:
            self.train_data = _FakeCTMTrainData(vocabulary)

    def get_topic_word_matrix(self) -> np.ndarray:
        return self._topic_word


def _make_fake_ctm(
    fitted_vectorizer: CountVectorizer, *, K: int = 2, with_train_data: bool = True
) -> _FakeCTMPackageStyle:
    vocab = list(fitted_vectorizer.get_feature_names_out())
    V = len(vocab)
    rng = np.random.default_rng(3)
    topic_word = rng.dirichlet(np.ones(V), size=K)
    return _FakeCTMPackageStyle(
        vocabulary=vocab, topic_word=topic_word, with_train_data=with_train_data
    )


class TestCTMAdapter:
    def test_adapter_satisfies_protocol(self) -> None:
        from topicvisexplorer.models.protocol import TopicModelAdapter

        assert isinstance(CTMAdapter(), TopicModelAdapter)
        assert CTMAdapter.name == "ctm"

    def test_extract_with_caller_supplied_doc_topic(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_ctm(fitted_vectorizer, K=3)
        N = len(_DOCS)
        K = 3
        rng = np.random.default_rng(4)
        dtd = rng.dirichlet(np.ones(K), size=N)

        data = CTMAdapter().extract(
            model, corpus=None, texts=_DOCS, doc_topic_dists=dtd
        )

        assert isinstance(data, TopicModelData)
        assert data.topic_term_dists.shape == (K, len(data.vocab))
        assert data.doc_topic_dists.shape == (N, K)
        np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-10)
        np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-10)
        # Caller-supplied DTD should pass through (modulo renormalize).
        np.testing.assert_allclose(data.doc_topic_dists, dtd, atol=1e-10)

    def test_missing_doc_topic_raises_actionable_error(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        """CTM doc-topic posteriors require a CTMDataset; the adapter
        intentionally does not build one and must point users at
        `model.get_doc_topic_distribution(...)`."""
        model = _make_fake_ctm(fitted_vectorizer, K=2)
        with pytest.raises(ValidationError, match="get_doc_topic_distribution"):
            CTMAdapter().extract(model, corpus=None, texts=_DOCS)

    def test_missing_texts_raises(self, fitted_vectorizer: CountVectorizer) -> None:
        model = _make_fake_ctm(fitted_vectorizer)
        with pytest.raises(ValidationError, match="texts="):
            CTMAdapter().extract(model, corpus=None)

    def test_missing_vocab_and_train_data_raises(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_ctm(fitted_vectorizer, with_train_data=False)
        with pytest.raises(ValidationError, match="vocabulary"):
            CTMAdapter().extract(model, corpus=None, texts=_DOCS)

    def test_missing_topic_word_method_raises(self) -> None:
        class _NoTW:
            def __init__(self) -> None:
                self.train_data = _FakeCTMTrainData(["a", "b", "c"])

        with pytest.raises(ValidationError, match="get_topic_word_matrix"):
            CTMAdapter().extract(_NoTW(), corpus=None, texts=["a b", "b c"])

    def test_vocab_size_mismatch_raises(
        self, fitted_vectorizer: CountVectorizer
    ) -> None:
        model = _make_fake_ctm(fitted_vectorizer, K=2)
        bad_vocab = list(fitted_vectorizer.get_feature_names_out())[:-1]
        N = len(_DOCS)
        dtd = np.full((N, 2), 0.5)
        with pytest.raises(ValidationError, match="vocabulary"):
            CTMAdapter().extract(
                model,
                corpus=None,
                texts=_DOCS,
                vocabulary=bad_vocab,
                doc_topic_dists=dtd,
            )


def test_sklearn_lda_real_smoke() -> None:
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    from topicvisexplorer.models import SklearnLDAAdapter

    docs = _DOCS * 2
    vectorizer = CountVectorizer(max_df=0.5, min_df=1, max_features=500)
    X = vectorizer.fit_transform(docs)
    lda = LatentDirichletAllocation(n_components=2, random_state=0, max_iter=10)
    lda.fit(X)
    data = SklearnLDAAdapter().extract(lda, X, vectorizer=vectorizer)
    assert isinstance(data, TopicModelData)
    np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-6)
    np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-5)


def test_sklearn_nmf_real_smoke() -> None:
    from sklearn.decomposition import NMF
    from sklearn.feature_extraction.text import TfidfVectorizer

    from topicvisexplorer.models import SklearnNMFAdapter

    docs = _DOCS * 2
    vectorizer = TfidfVectorizer(max_df=0.5, min_df=1, max_features=500)
    X = vectorizer.fit_transform(docs)
    nmf = NMF(n_components=2, random_state=0, max_iter=50, init="nndsvda")
    nmf.fit(X)
    data = SklearnNMFAdapter().extract(nmf, X, vectorizer=vectorizer)
    assert isinstance(data, TopicModelData)
    np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-3)
    np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-2)


# ---------------------------------------------------------------------------
# Optional: real-bertopic / real-ETM / real-CTM smoke tests, only when
# the deps are installed.
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(
    importlib.util.find_spec("bertopic") is None,
    reason="bertopic not installed (install with topicvisexplorer[full])",
)
def test_bertopic_real_smoke() -> None:
    """Fit a tiny real BERTopic and confirm the adapter produces a
    valid TopicModelData. Smoke only -- no numerical equivalence
    asserted because BERTopic's HDBSCAN clustering is non-deterministic
    even with a fixed seed (UMAP is the source of variance)."""
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer as CV

    docs = _DOCS * 4  # tiny but enough for HDBSCAN to find >=1 cluster
    model = BERTopic(
        vectorizer_model=CV(),
        min_topic_size=2,
        verbose=False,
        calculate_probabilities=False,
    )
    model.fit(docs)

    data = BERTopicAdapter().extract(model, corpus=None, texts=docs)
    assert isinstance(data, TopicModelData)
    np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-8)
    np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-8)


@pytest.mark.slow
@pytest.mark.skipif(
    importlib.util.find_spec("embedded_topic_model") is None,
    reason="embedded_topic_model not installed",
)
def test_etm_real_smoke() -> None:
    """Fit a tiny real ETM (via the `embedded_topic_model` package) and
    confirm the adapter produces valid TopicModelData. Smoke only."""
    from embedded_topic_model.models.etm import ETM

    from topicvisexplorer.server.byo_corpus import _etm_train_data_from_texts

    docs = _DOCS * 8
    train_data, vocab = _etm_train_data_from_texts(docs)
    model = ETM(
        vocabulary=vocab,
        embeddings=None,
        num_topics=2,
        batch_size=8,
        epochs=3,
    )
    model.fit(train_data)
    data = ETMAdapter().extract(
        model, corpus=None, texts=docs, vocabulary=vocab
    )
    assert isinstance(data, TopicModelData)
    np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-6)
    np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-6)


@pytest.mark.slow
@pytest.mark.skipif(
    importlib.util.find_spec("contextualized_topic_models") is None,
    reason="contextualized_topic_models not installed (use topicvisexplorer[full])",
)
def test_ctm_real_smoke() -> None:
    from contextualized_topic_models.models.ctm import CombinedTM
    from contextualized_topic_models.utils.data_preparation import TopicModelDataPreparation

    from topicvisexplorer.models import CTMAdapter

    docs = list(_DOCS) * 4
    prep = TopicModelDataPreparation("all-MiniLM-L6-v2")
    training = prep.fit(text_for_contextual=docs, text_for_bow=docs)
    ctm = CombinedTM(
        bow_size=len(prep.vocab),
        contextual_size=int(training.X_contextual.shape[1]),
        n_components=2,
        num_epochs=3,
        batch_size=8,
    )
    ctm.fit(training)
    dtd = ctm.get_doc_topic_distribution(training, n_samples=5)
    data = CTMAdapter().extract(
        ctm,
        corpus=None,
        texts=docs,
        doc_topic_dists=np.asarray(dtd, dtype=np.float64),
        vocabulary=list(prep.vocab),
    )
    assert isinstance(data, TopicModelData)
    np.testing.assert_allclose(data.topic_term_dists.sum(axis=1), 1.0, atol=1e-2)
    np.testing.assert_allclose(data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-2)
