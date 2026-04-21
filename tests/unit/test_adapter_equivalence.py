"""Phase 4g: gensim-vs-sklearn LDA adapter equivalence.

Both ``GensimLDAAdapter`` and ``SklearnLDAAdapter`` are supposed to
return :class:`TopicModelData` instances that the rest of the
pipeline can treat interchangeably. The protocol contract pins the
*shape* (row-stochastic distributions, matching vocab size, etc.)
but historically there was no test that drove **both** adapters end-
to-end on the **same** corpus and asserted that contract.

This module fixes that. It is the first cross-adapter test in the
suite.

What we *don't* test:

* Numerical equivalence of the topic-term distributions. gensim and
  sklearn use different variational EM update rules, different
  initialization heuristics, and different alpha priors. On a tiny
  6-document corpus they trivially produce different topic mixtures
  even with the same seed -- testing for absolute equivalence here
  would be testing the third-party libraries, not our adapters.

What we *do* test:

* Both adapters return ``TopicModelData`` with the same vocabulary
  size, same ``K``, same ``N`` documents, and the same
  ``term_frequency.sum() == doc_lengths.sum()`` integer invariant.
* Both produce row-stochastic ``topic_term_dists`` and
  ``doc_topic_dists``.
* Feeding both through :func:`topicvisexplorer.prepare.prepare`
  yields a :class:`PreparedData` whose top-level structure
  (``topic_coordinates`` / ``topic_info`` / ``token_table``) is
  shape-equivalent so downstream code can render either output.

Skipped if gensim is not installed (it is in our default test env;
this is a defensive guard for slim users).
"""

from __future__ import annotations

import importlib.util

import numpy as np
import pytest
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from topicvisexplorer.models import GensimLDAAdapter, SklearnLDAAdapter
from topicvisexplorer.models.protocol import TopicModelData
from topicvisexplorer.prepare import prepare

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("gensim") is None,
    reason="gensim not installed; cross-adapter equivalence test requires both backends",
)


# A small, intentionally bimodal corpus: half the documents are
# clearly about "animals", half about "transport". Both LDA backends
# should converge to a 2-topic representation that respects this
# structure, even if the actual topic indices differ.
_DOCS = [
    "cat dog fish",
    "cat fish bird",
    "dog cat fish",
    "bird dog cat",
    "cat dog bird fish",
    "car train plane",
    "car bus train",
    "plane train bus car",
    "car bus train plane",
    "bus car plane",
]
_K = 2
_SEED = 1234


@pytest.fixture(scope="module")
def shared_vectorizer() -> CountVectorizer:
    v = CountVectorizer()
    v.fit(_DOCS)
    return v


@pytest.fixture(scope="module")
def sklearn_data(shared_vectorizer: CountVectorizer) -> TopicModelData:
    X = shared_vectorizer.transform(_DOCS)
    lda = LatentDirichletAllocation(
        n_components=_K, random_state=_SEED, max_iter=50, learning_method="batch"
    )
    lda.fit(X)
    return SklearnLDAAdapter().extract(lda, X, vectorizer=shared_vectorizer)


@pytest.fixture(scope="module")
def gensim_data() -> TopicModelData:
    import gensim
    from gensim.corpora import Dictionary
    from gensim.models import LdaModel

    tokenized = [d.split() for d in _DOCS]
    dictionary = Dictionary(tokenized)
    corpus = [dictionary.doc2bow(d) for d in tokenized]
    model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=_K,
        random_state=_SEED,
        passes=10,
        iterations=200,
        alpha="auto",
    )
    # gensim corpus iterators are single-pass; rebuild for the
    # adapter so it can sweep through a fresh Sparse2Corpus.
    corpus_again = [dictionary.doc2bow(d) for d in tokenized]
    return GensimLDAAdapter().extract(
        model, corpus_again, dictionary=dictionary
    )


def test_both_adapters_return_topic_model_data(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    assert isinstance(sklearn_data, TopicModelData)
    assert isinstance(gensim_data, TopicModelData)


def test_both_have_same_n_topics(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    assert sklearn_data.topic_term_dists.shape[0] == _K
    assert gensim_data.topic_term_dists.shape[0] == _K


def test_both_have_same_n_docs(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    assert sklearn_data.doc_topic_dists.shape[0] == len(_DOCS)
    assert gensim_data.doc_topic_dists.shape[0] == len(_DOCS)


def test_both_have_same_vocabulary(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    """Vocab strings must match as a set.

    The two backends *order* their vocabulary differently (sklearn
    sorts; gensim uses insertion order), which is fine because each
    adapter's ``term_frequency`` and ``topic_term_dists`` are aligned
    with its own vocab. Downstream :func:`prepare` re-aligns by
    string. Here we just enforce that both adapters see the same
    universe of terms.
    """
    assert set(sklearn_data.vocab) == set(gensim_data.vocab)


def test_both_topic_term_dists_are_row_stochastic(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    np.testing.assert_allclose(
        sklearn_data.topic_term_dists.sum(axis=1), 1.0, atol=1e-6
    )
    np.testing.assert_allclose(
        gensim_data.topic_term_dists.sum(axis=1), 1.0, atol=1e-6
    )


def test_both_doc_topic_dists_are_row_stochastic(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    np.testing.assert_allclose(
        sklearn_data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-6
    )
    np.testing.assert_allclose(
        gensim_data.doc_topic_dists.sum(axis=1), 1.0, atol=1e-6
    )


def test_both_obey_term_freq_doc_length_invariant(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    """sum(term_frequency) == sum(doc_lengths) holds for both.

    This is the core "I can re-vectorize the corpus" invariant the
    LDAvis algorithm depends on. The gensim path uses a
    smoothing-bias of ``beta=0.01`` for unseen terms (legacy
    behavior preserved), which can shift its term_frequency total
    by up to ``V * 0.01`` -- the assertion absorbs that.
    """
    sk_doc, sk_tf = float(sklearn_data.doc_lengths.sum()), float(
        sklearn_data.term_frequency.sum()
    )
    gn_doc, gn_tf = float(gensim_data.doc_lengths.sum()), float(
        gensim_data.term_frequency.sum()
    )
    np.testing.assert_allclose(sk_doc, sk_tf, atol=1e-6)
    # gensim adds a tiny epsilon (beta=0.01) to zero-frequency terms.
    assert abs(gn_doc - gn_tf) <= len(gensim_data.vocab) * 0.011


def test_both_feed_through_prepare_with_same_shapes(
    sklearn_data: TopicModelData, gensim_data: TopicModelData
) -> None:
    """End-to-end: both ``TopicModelData`` -> :class:`PreparedData`."""
    sk_prep = prepare(
        topic_term_dists=sklearn_data.topic_term_dists,
        doc_topic_dists=sklearn_data.doc_topic_dists,
        doc_lengths=sklearn_data.doc_lengths,
        vocab=sklearn_data.vocab,
        term_frequency=sklearn_data.term_frequency,
    )
    gn_prep = prepare(
        topic_term_dists=gensim_data.topic_term_dists,
        doc_topic_dists=gensim_data.doc_topic_dists,
        doc_lengths=gensim_data.doc_lengths,
        vocab=gensim_data.vocab,
        term_frequency=gensim_data.term_frequency,
    )

    # Same number of topics in the layout.
    assert len(sk_prep.topic_order) == _K
    assert len(gn_prep.topic_order) == _K

    # Same vocabulary universe survived prepare's filtering.
    sk_terms = set(sk_prep.topic_info["Term"])
    gn_terms = set(gn_prep.topic_info["Term"])
    assert sk_terms == gn_terms

    # Topic info has the standard LDAvis schema in both cases.
    expected_cols = {"Term", "Category", "Freq", "Total", "logprob", "loglift"}
    assert expected_cols.issubset(sk_prep.topic_info.columns)
    assert expected_cols.issubset(gn_prep.topic_info.columns)
