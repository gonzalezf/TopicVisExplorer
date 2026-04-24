"""End-to-end BYO paths a new user follows: CSV column, JSONL, JSON list (no spaCy)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("gensim")

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_journey_csv_column_sklearn(tmp_path: Path) -> None:
    from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile

    csv_path = REPO_ROOT / "examples" / "sample_corpus.csv"
    assert csv_path.is_file()
    sc = build_scenario_from_textfile(
        csv_path,
        name="journey_csv",
        num_topics=3,
        passes=2,
        seed=0,
        cache_dir=tmp_path / "c",
        model="sklearn-lda",
        csv_text_column="text",
    )
    assert sc.model_data is not None
    assert sc.model_data.topic_term_dists.shape[0] == 3
    assert sc.extras.get("refit") is not None
    assert sc.prepared is not None


def test_journey_jsonl_sklearn(tmp_path: Path) -> None:
    from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile

    p = REPO_ROOT / "examples" / "byo_minimal.jsonl"
    assert p.is_file()
    sc = build_scenario_from_textfile(
        p,
        name="journey_jsonl",
        num_topics=3,
        passes=2,
        seed=0,
        cache_dir=tmp_path / "c",
        model="sklearn-lda",
    )
    assert sc.model_data is not None
    assert sc.extras.get("refit") is not None


def test_journey_json_list_sklearn(tmp_path: Path) -> None:
    from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile

    p = REPO_ROOT / "examples" / "sample_corpus.json"
    assert p.is_file()
    sc = build_scenario_from_textfile(
        p,
        name="journey_json",
        num_topics=3,
        passes=2,
        seed=0,
        cache_dir=tmp_path / "c",
        model="sklearn-lda",
    )
    assert sc.model_data is not None
    assert sc.extras.get("refit") is not None
