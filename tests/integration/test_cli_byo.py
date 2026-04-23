"""HTTP smoke for BYO scenarios (same registration path as ``tve demo --texts``)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from topicvisexplorer.server import ServerConfig, build_app
from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile


def _docs_file(tmp: Path) -> Path:
    lines = [
        "machine learning models train from data",
        "neural networks learn from large datasets",
        "topic models find themes in text",
        "sports teams play games in stadiums",
        "markets move on news and earnings",
        "cooking recipes use herbs spices and vegetables",
        "elections bring voters to polling places nationwide",
        "ocean waves crash on sandy beaches at sunset",
    ] * 12
    p = tmp / "c.txt"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


@pytest.mark.parametrize(
    ("model", "embedding"),
    [
        ("gensim-lda", "word2vec"),
        ("sklearn-lda", "word2vec"),
        ("sklearn-nmf", "word2vec"),
    ],
)
def test_byo_singlecorpus_200(tmp_path: Path, model: str, embedding: str) -> None:
    if model == "gensim-lda":
        pytest.importorskip("spacy")
    txt = _docs_file(tmp_path)
    sc = build_scenario_from_textfile(
        txt,
        name="byo",
        num_topics=3,
        passes=2,
        seed=1,
        cache_dir=tmp_path / "cache",
        model=model,
        embedding=embedding,
    )
    app = build_app(ServerConfig(register_demo=False, extra_scenarios={"byo": lambda: sc}))
    client = TestClient(app)
    r = client.get("/singlecorpus", params={"scenario": "byo"})
    assert r.status_code == 200


@pytest.mark.skipif(
    importlib.util.find_spec("sentence_transformers") is None,
    reason="sentence_transformers not installed",
)
def test_byo_sbert_embedding(tmp_path: Path) -> None:
    pytest.importorskip("spacy")
    txt = _docs_file(tmp_path)
    sc = build_scenario_from_textfile(
        txt,
        name="byo_s",
        num_topics=3,
        passes=2,
        seed=1,
        cache_dir=tmp_path / "cache",
        model="gensim-lda",
        embedding="sbert",
    )
    app = build_app(ServerConfig(register_demo=False, extra_scenarios={"byo_s": lambda: sc}))
    r = TestClient(app).get("/singlecorpus", params={"scenario": "byo_s"})
    assert r.status_code == 200


@pytest.mark.skipif(
    importlib.util.find_spec("bertopic") is None,
    reason="bertopic not installed",
)
@pytest.mark.slow
def test_byo_bertopic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # conftest sets TVE_EMBEDDING_DISABLE=1; Procrustes needs non-degenerate layouts.
    monkeypatch.delenv("TVE_EMBEDDING_DISABLE", raising=False)
    txt = _docs_file(tmp_path)
    sc = build_scenario_from_textfile(
        txt,
        name="byo_b",
        num_topics=6,
        passes=1,
        seed=1,
        cache_dir=tmp_path / "cache",
        model="bertopic",
    )
    app = build_app(ServerConfig(register_demo=False, extra_scenarios={"byo_b": lambda: sc}))
    r = TestClient(app).get("/singlecorpus", params={"scenario": "byo_b"})
    assert r.status_code == 200
