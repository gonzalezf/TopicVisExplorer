"""Tests for refit_static — the numpy-only refit used by tiny_demo."""
from __future__ import annotations

import numpy as np


def test_refit_static_preserves_vocab_shape() -> None:
    from topicvisexplorer.operations.refit_helpers import refit_static
    from topicvisexplorer.server.demo_data import build_tiny_single_demo

    sc = build_tiny_single_demo()
    md = sc.model_data
    V = md.topic_term_dists.shape[1]
    refit = refit_static(md)
    child = refit(
        ["synthetic document #0", "synthetic document #1", "synthetic document #2"] * 4, 2
    )
    assert child.topic_term_dists.shape == (2, V)
    assert list(child.vocab) == list(md.vocab)
    row_sums = child.topic_term_dists.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-6)


def test_refit_static_doc_topic_is_stochastic() -> None:
    from topicvisexplorer.operations.refit_helpers import refit_static
    from topicvisexplorer.server.demo_data import build_tiny_single_demo

    sc = build_tiny_single_demo()
    refit = refit_static(sc.model_data)
    texts = ["synthetic document #0"] * 5
    child = refit(texts, 3)
    assert child.doc_topic_dists.shape == (5, 3)
    assert np.allclose(child.doc_topic_dists.sum(axis=1), 1.0, atol=1e-6)


def test_tiny_demo_has_refit() -> None:
    from topicvisexplorer.server.demo_data import build_tiny_single_demo

    sc = build_tiny_single_demo()
    assert sc.extras.get("refit") is not None, "tiny_demo must have a refit callable"
    assert callable(sc.extras["refit"])
