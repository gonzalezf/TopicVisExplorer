"""Unit tests for :mod:`topicvisexplorer.coherence`."""

from __future__ import annotations

import math

import numpy as np

from topicvisexplorer import coherence


def test_coverage_sums_to_one() -> None:
    dt = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.3, 0.3, 0.4]])
    cov = coherence.coverage_per_topic(dt)
    assert math.isclose(sum(cov), 1.0, abs_tol=1e-9)


def test_segregation_distinct_topics_high() -> None:
    out = coherence.segregation_per_topic([["a", "b", "c"], ["d", "e", "f"], ["g", "h", "i"]])
    assert all(v == 1.0 for v in out)


def test_segregation_overlap_low() -> None:
    out = coherence.segregation_per_topic([["a", "b"], ["a", "b"]])
    assert all(v == 0.0 for v in out)


def test_npmi_finite(tiny_corpus: list[list[str]]) -> None:
    top = [["dog", "puppy", "bark"], ["cat", "kitten", "purr"], ["car", "engine", "wheel"]]
    out = coherence.npmi_per_topic(top, tiny_corpus)
    assert len(out) == 3
    for v in out:
        assert math.isfinite(v) or math.isnan(v)


def test_c_v_in_range(tiny_corpus: list[list[str]]) -> None:
    top = [["dog", "puppy"], ["cat", "kitten"], ["car", "engine"]]
    out = coherence.c_v_per_topic(top, tiny_corpus)
    for v in out:
        if not math.isnan(v):
            assert -1.0 <= v <= 1.0


def test_report_to_dict(tiny_prepared, tiny_corpus, tiny_doc_topic):
    rep = coherence.report(tiny_prepared, tiny_corpus, tiny_doc_topic, n_terms=4)
    d = rep.to_dict()
    assert set(d.keys()) >= {
        "npmi",
        "c_v",
        "segregation",
        "coverage",
        "labels",
        "mean_npmi",
        "mean_c_v",
    }
    assert len(d["npmi"]) == 4
    assert len(d["labels"]) == 4
    for lab in d["labels"]:
        assert isinstance(lab, str)
