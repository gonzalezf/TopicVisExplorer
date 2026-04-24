"""``tve.show()`` should open ``/multicorpora`` when two ``PreparedData`` are passed."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("sklearn")

from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

import topicvisexplorer as tve
from topicvisexplorer.models import SklearnLDAAdapter

_DOCS_A = [
    "cat dog fish",
    "cat fish",
    "car train plane",
]
_DOCS_B = [
    "car bus train",
    "dog cat fish bird",
    "plane train bus car",
]


def _two_prepared_and_model_data() -> tuple:
    v = CountVectorizer(max_df=1.0, min_df=1)
    all_docs = list(_DOCS_A) + list(_DOCS_B)
    v.fit(all_docs)
    xa = v.transform(_DOCS_A)
    xb = v.transform(_DOCS_B)
    lda_a = LatentDirichletAllocation(
        n_components=2, random_state=0, max_iter=20, learning_method="batch"
    )
    lda_b = LatentDirichletAllocation(
        n_components=2, random_state=1, max_iter=20, learning_method="batch"
    )
    lda_a.fit(xa)
    lda_b.fit(xb)
    ad = SklearnLDAAdapter()
    mda = ad.extract(lda_a, xa, vectorizer=v)
    mdb = ad.extract(lda_b, xb, vectorizer=v)
    pa = tve.prepare(
        topic_term_dists=mda.topic_term_dists,
        doc_topic_dists=mda.doc_topic_dists,
        doc_lengths=mda.doc_lengths,
        vocab=mda.vocab,
        term_frequency=mda.term_frequency,
    )
    pb = tve.prepare(
        topic_term_dists=mdb.topic_term_dists,
        doc_topic_dists=mdb.doc_topic_dists,
        doc_lengths=mdb.doc_lengths,
        vocab=mdb.vocab,
        term_frequency=mdb.term_frequency,
    )
    return pa, pb, mda, mdb


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_show_two_prepared_uses_multicorpora_path(
    m_build: MagicMock, m_serve: MagicMock
) -> None:
    pa, pb, mda, mdb = _two_prepared_and_model_data()
    tve.show(
        [pa, pb],
        raw_texts=[list(_DOCS_A), list(_DOCS_B)],
        model_data=[mda, mdb],
        scenario_name="u_multi",
        open_browser=False,
    )
    m_build.assert_called()
    path = m_serve.call_args[1]["browser_path"]
    assert path == "/multicorpora?scenario=u_multi&hitl=true"


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_show_one_prepared_uses_singlecorpus_path(
    m_build: MagicMock, m_serve: MagicMock
) -> None:
    pa, _, mda, _ = _two_prepared_and_model_data()
    tve.show(
        pa,
        raw_texts=list(_DOCS_A),
        model_data=mda,
        scenario_name="u_one",
        open_browser=False,
    )
    m_build.assert_called()
    path = m_serve.call_args[1]["browser_path"]
    assert path == "/singlecorpus?scenario=u_one&hitl=true"
