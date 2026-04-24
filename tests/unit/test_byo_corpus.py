"""Smoke tests for ``server.byo_corpus.build_scenario_from_textfile``.

These exercise the 'bring your own corpus' path used by
``tve demo --texts ...`` without any network.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

pytest.importorskip("gensim")


def _sample_texts() -> list[str]:
    return [
        "machine learning models train from data and improve with experience",
        "deep neural networks learn representations for images and text",
        "topic models discover latent themes in document collections",
        "baseball teams play games in summer with home runs and pitchers",
        "soccer fans cheer goals by players on the football field",
        "the stock market rose today on strong company earnings reports",
        "investors trade shares and bonds in global financial markets",
        "governments debate policy on taxation and healthcare spending",
        "elections bring voters to polling stations across the country",
        "cooking recipes combine vegetables herbs spices and fresh ingredients",
    ] * 4  # 40 docs so dictionary survives filter_extremes(no_below=2)


def test_build_scenario_from_textfile_txt(tmp_path: Path) -> None:
    pytest.importorskip("spacy")
    from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile

    txt = tmp_path / "docs.txt"
    txt.write_text("\n".join(_sample_texts()), encoding="utf-8")
    cache = tmp_path / "cache"
    sc = build_scenario_from_textfile(
        txt,
        name="user_test",
        num_topics=3,
        passes=3,
        seed=0,
        cache_dir=cache,
    )
    assert sc.name == "user_test"
    assert sc.model_data is not None
    assert sc.extras.get("refit") is not None
    assert sc.prepared is not None
    K = sc.model_data.topic_term_dists.shape[0]
    assert K == 3


def test_build_scenario_cache_hits_second_time(tmp_path: Path) -> None:
    pytest.importorskip("spacy")
    from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile

    txt = tmp_path / "docs.txt"
    txt.write_text("\n".join(_sample_texts()), encoding="utf-8")
    cache = tmp_path / "cache"
    build_scenario_from_textfile(
        txt, name="u", num_topics=3, passes=3, seed=0, cache_dir=cache
    )
    cache_files = list(cache.glob("*.npz"))
    assert cache_files, "expected a .npz cache file under cache_dir"

    # Second call should not re-fit; reloading from cache is by far the
    # fastest path, so just verify that a scenario comes out identical.
    sc2 = build_scenario_from_textfile(
        txt, name="u", num_topics=3, passes=3, seed=0, cache_dir=cache
    )
    assert sc2.model_data.topic_term_dists.shape[0] == 3


def test_load_texts_accepts_jsonl(tmp_path: Path) -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    jl = tmp_path / "docs.jsonl"
    jl.write_text(
        textwrap.dedent(
            """\
            {"text": "first document one"}
            {"text": "second document two"}
            """
        ),
        encoding="utf-8",
    )
    docs = load_texts(jl)
    assert docs == ["first document one", "second document two"]


def test_load_texts_byo_minimal_example_file() -> None:
    """Committed ``examples/byo_minimal.jsonl`` must match the custom-corpus tutorial path."""
    from topicvisexplorer.server.byo_corpus import load_texts

    root = Path(__file__).resolve().parents[2]
    path = root / "examples" / "byo_minimal.jsonl"
    assert path.is_file(), f"missing {path} — keep in sync with docs/custom_corpus_tutorial.md"
    docs = load_texts(path)
    assert len(docs) == 40
    assert all(isinstance(s, str) and s for s in docs)


@pytest.mark.parametrize("model", ["sklearn-nmf", "sklearn-lda"])
def test_build_scenario_sklearn_models(tmp_path: Path, model: str) -> None:
    """BYO sklearn paths do not require spaCy (no ``text_cleaner_batch``)."""
    from topicvisexplorer.server.byo_corpus import build_scenario_from_textfile

    txt = tmp_path / "docs.txt"
    txt.write_text("\n".join(_sample_texts()), encoding="utf-8")
    cache = tmp_path / "cache"
    sc = build_scenario_from_textfile(
        txt,
        name="sk",
        num_topics=3,
        passes=2,
        seed=7,
        cache_dir=cache,
        model=model,
    )
    assert sc.model_data is not None
    assert sc.model_data.topic_term_dists.shape[0] == 3


def test_load_texts_csv_with_column() -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    path = Path(__file__).resolve().parents[2] / "examples" / "sample_corpus.csv"
    assert path.is_file()
    docs = load_texts(path, csv_text_column="text")
    assert len(docs) == 25
    assert all(s.strip() for s in docs)


def test_load_texts_csv_without_column_is_linewise() -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    path = Path(__file__).resolve().parents[2] / "examples" / "sample_corpus.csv"
    docs = load_texts(path)
    # Line-oriented mode: header line + 25 data lines => 26 "documents" (wrong for a table)
    assert len(docs) == 26
    assert docs[0] == "id,text"


def test_load_texts_csv_missing_column_raises() -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    path = Path(__file__).resolve().parents[2] / "examples" / "sample_corpus.csv"
    with pytest.raises(ValueError, match=r"not in .* header"):
        load_texts(path, csv_text_column="nonexistent_column")


def test_load_texts_tsv_with_column(tmp_path: Path) -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    tsv = tmp_path / "a.tsv"
    tsv.write_text("label\tcontent\n1\tone doc here\n2\tsecond doc here\n", encoding="utf-8")
    assert load_texts(tsv, csv_text_column="content") == ["one doc here", "second doc here"]


def test_load_texts_json_list() -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    path = Path(__file__).resolve().parents[2] / "examples" / "sample_corpus.json"
    assert path.is_file()
    docs = load_texts(path)
    assert len(docs) == 25
    assert "machine learning" in docs[0].lower()


def test_load_texts_json_texts_key(tmp_path: Path) -> None:
    from topicvisexplorer.server.byo_corpus import load_texts

    p = tmp_path / "x.json"
    p.write_text('{"texts": ["aa", "bb", "cc"]}', encoding="utf-8")
    assert load_texts(p) == ["aa", "bb", "cc"]
