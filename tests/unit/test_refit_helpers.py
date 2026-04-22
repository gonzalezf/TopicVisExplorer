"""Contract tests for :mod:`topicvisexplorer.operations.refit_helpers`."""

from __future__ import annotations

import numpy as np
import pytest

from topicvisexplorer.models.protocol import TopicModelData
from topicvisexplorer.operations.refit_helpers import refit_gensim_lda


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_refit_gensim_lda_child_matches_parent_vocab() -> None:
    V = 12
    K = 3
    N = 20
    rng = np.random.default_rng(0)
    tt = rng.dirichlet(np.ones(V), size=K)
    dt = rng.dirichlet(np.ones(K), size=N)
    lens = np.ones(N) * 10.0
    vocab = [f"tok{i:02d}" for i in range(V)]
    tf = np.ones(V) * 3.0
    md = TopicModelData(
        topic_term_dists=tt,
        doc_topic_dists=dt,
        doc_lengths=lens,
        vocab=vocab,
        term_frequency=tf,
    )
    long = " ".join(vocab) + " " + " ".join(vocab[::-1])
    sub_texts = [long] * 12
    refit = refit_gensim_lda(md, random_state=0, passes=3)
    child = refit(sub_texts, 2)
    assert child.topic_term_dists.shape == (2, V)
    assert child.doc_topic_dists.shape[1] == 2
