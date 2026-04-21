"""Unit tests for :mod:`topicvisexplorer.prepare`."""

from __future__ import annotations

import numpy as np
import pytest

from topicvisexplorer import PreparedData, prepare
from topicvisexplorer.errors import ValidationError


def test_prepare_returns_preparedata(tiny_prepared: PreparedData) -> None:
    assert isinstance(tiny_prepared, PreparedData)
    assert tiny_prepared.R == 24
    assert len(tiny_prepared.topic_order) == 4


def test_prepare_topic_coordinates_shape(tiny_prepared: PreparedData) -> None:
    assert tiny_prepared.topic_coordinates.shape == (4, 5)
    assert {"x", "y", "topics", "cluster", "Freq"}.issubset(tiny_prepared.topic_coordinates.columns)


def test_prepare_topic_info_has_all_topics(tiny_prepared: PreparedData) -> None:
    cats = tiny_prepared.topic_info["Category"].unique()
    assert "Default" in cats
    for k in range(1, 5):
        assert f"Topic{k}" in cats


def test_prepare_validates_shape_mismatch() -> None:
    with pytest.raises(ValidationError, match="must equal n_topics"):
        prepare(
            topic_term_dists=np.eye(3) / 3,
            doc_topic_dists=np.full((4, 5), 0.2),
            doc_lengths=np.ones(4),
            vocab=["a", "b", "c"],
            term_frequency=np.ones(3),
        )


def test_sorted_terms_returns_sorted_dataframe(tiny_prepared: PreparedData) -> None:
    df = tiny_prepared.sorted_terms(topic=1, lambda_=0.6)
    rels = df["relevance"].values
    assert np.all(rels[:-1] >= rels[1:])


def test_topic_top_terms_n(tiny_prepared: PreparedData) -> None:
    terms = tiny_prepared.topic_top_terms(topic=1, n=5)
    assert len(terms) == 5
    assert all(isinstance(t, str) for t in terms)


def test_save_and_load_round_trip(tiny_prepared: PreparedData, tmp_path) -> None:
    from topicvisexplorer import load

    out = tmp_path / "p.pkl"
    tiny_prepared.save(out)
    loaded = load(out)
    assert isinstance(loaded, PreparedData)
    assert loaded.R == tiny_prepared.R
    assert (loaded.topic_coordinates.values == tiny_prepared.topic_coordinates.values).all()


def test_to_dict_keys(tiny_prepared: PreparedData) -> None:
    d = tiny_prepared.to_dict()
    assert set(d.keys()) == {
        "mdsDat",
        "tinfo",
        "token.table",
        "R",
        "lambda.step",
        "plot.opts",
        "topic.order",
    }


def test_to_json_serializable(tiny_prepared: PreparedData) -> None:
    import json

    s = tiny_prepared.to_json()
    parsed = json.loads(s)
    assert parsed["R"] == tiny_prepared.R
