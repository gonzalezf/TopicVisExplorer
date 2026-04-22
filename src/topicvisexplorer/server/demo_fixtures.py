"""Generalized loader for real-corpus demo fixtures.

Both ``20ng_tiny`` and ``bbc_tiny`` (and any future fixture-backed
single-corpus scenario) share the same on-disk layout:

* ``src/topicvisexplorer/server/fixtures/<stem>.npz``    — numpy tensors
* ``src/topicvisexplorer/server/fixtures/<stem>_vocab.npy`` — vocabulary
* ``src/topicvisexplorer/server/fixtures/<stem>_texts.json`` — raw texts

This module reads those files and produces a full single-corpus
:class:`~topicvisexplorer.server.scenarios.Scenario` with Jensen-Shannon
similarity omega sweep, circle positions, and a Gensim-backed ``refit``
attached under ``extras``.

The legacy :mod:`topicvisexplorer.server.demo_20ng` module is kept as a
compatibility shim that re-exports the symbols below.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..models.protocol import TopicModelData
from ..operations.refit_helpers import refit_gensim_lda
from ..prepare import prepare
from ..similarity.baselines import JensenShannonSimilarity
from .scenarios import Scenario

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# Heuristic terms used by smoke tests to detect that the real (non-wNN)
# demo is actually rendering in the page.  Extend per fixture as needed.
_KNOWN_REAL_TOKENS: dict[str, tuple[str, ...]] = {
    "20ng_tiny": ("graphics", "game", "team", "encryption", "space"),
    "bbc_tiny": ("government", "market", "film", "company", "player"),
}


def _load_fixture_arrays(
    stem: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    npz = np.load(_FIXTURE_DIR / f"{stem}.npz", allow_pickle=True)
    vocab = np.load(_FIXTURE_DIR / f"{stem}_vocab.npy", allow_pickle=True).tolist()
    if not isinstance(vocab, list):
        vocab = list(vocab)  # type: ignore[unreachable]
    return (
        np.asarray(npz["topic_term_dists"], dtype=np.float64),
        np.asarray(npz["doc_topic_dists"], dtype=np.float64),
        np.asarray(npz["doc_lengths"], dtype=np.float64),
        np.asarray(npz["term_frequency"], dtype=np.float64),
        [str(x) for x in vocab],
    )


def build_scenario_from_topic_model(
    name: str,
    *,
    model_data: TopicModelData,
    raw_texts: list[str],
    prepared_metadata: dict[str, Any] | None = None,
    refit_passes: int = 5,
    refit_random_state: int = 42,
) -> Scenario:
    """Build a full single-corpus :class:`Scenario` (JS layouts + refit) from tensors."""
    md = model_data
    N = int(md.doc_topic_dists.shape[0])
    if len(raw_texts) < N:
        raise ValueError("raw_texts shorter than model_data document count.")
    raw_texts = raw_texts[:N]
    meta = prepared_metadata or {"scenario": name, "synthetic": False}
    prepared = prepare(
        topic_term_dists=md.topic_term_dists,
        doc_topic_dists=md.doc_topic_dists,
        doc_lengths=md.doc_lengths,
        vocab=md.vocab,
        term_frequency=md.term_frequency,
        metadata=meta,
    )
    K = int(md.topic_term_dists.shape[0])
    rel: list[dict[str, Any]] = []
    for i in range(N):
        row = {
            "doc_id": i,
            "text": raw_texts[i],
            **{str(k): float(md.doc_topic_dists[i, k]) for k in range(K)},
        }
        rel.append(row)

    metric_jsd = JensenShannonSimilarity()
    matrix = np.asarray(metric_jsd(prepared, prepared), dtype=np.float64)
    similarity_matrix = {round(s / 100.0, 2): matrix.copy() for s in range(101)}

    from ..layout import circle_positions

    sm = {i / 100.0: matrix.copy() for i in range(101)}
    circ_raw = circle_positions(sm)
    circle_positions_str = {str(k): v for k, v in circ_raw.items()}

    return Scenario(
        name=name,
        is_multi=False,
        prepared=prepared,
        model_data=md,
        relevant_documents=rel,
        similarity_matrix=similarity_matrix,
        circle_positions=circle_positions_str,
        raw_texts=raw_texts,
        extras={
            "refit": refit_gensim_lda(
                md, random_state=refit_random_state, passes=refit_passes
            )
        },
    )


def build_scenario_from_fixture(stem: str) -> Scenario:
    """Build a :class:`Scenario` from a committed fixture stem."""
    topic_term, doc_topic, doc_lengths, term_freq, vocab = _load_fixture_arrays(stem)
    texts_obj = json.loads((_FIXTURE_DIR / f"{stem}_texts.json").read_text(encoding="utf-8"))
    raw_texts: list[str] = list(texts_obj["texts"])
    N = int(doc_topic.shape[0])
    if len(raw_texts) < N:
        raise RuntimeError(f"Fixture texts shorter than doc_topic rows for {stem}.")
    raw_texts = raw_texts[:N]
    md = TopicModelData(
        topic_term_dists=topic_term,
        doc_topic_dists=doc_topic,
        doc_lengths=doc_lengths,
        vocab=vocab,
        term_frequency=term_freq,
    )
    return build_scenario_from_topic_model(
        stem,
        model_data=md,
        raw_texts=raw_texts,
        prepared_metadata={
            "scenario": stem,
            "synthetic": False,
            "fixture": stem,
        },
    )


def build_20ng_tiny() -> Scenario:
    """Single-corpus scenario with real 20 Newsgroups keywords."""
    return build_scenario_from_fixture("20ng_tiny")


def build_bbc_tiny() -> Scenario:
    """Single-corpus scenario with real BBC-news keywords."""
    return build_scenario_from_fixture("bbc_tiny")


def demo_page_contains_real_terms(html: str, fixture: str = "20ng_tiny") -> bool:
    """Return True if ``html`` plausibly shows a real-terms (non-wNN) demo."""
    tokens = _KNOWN_REAL_TOKENS.get(fixture, ())
    if any(tok in html for tok in tokens):
        return True
    if "w00" in html or "synthetic document" in html:
        return False
    return "tinfo" in html


def fixture_exists(stem: str) -> bool:
    """Return True if all files for a fixture stem are present on disk."""
    return all(
        (_FIXTURE_DIR / f"{stem}{suffix}").exists()
        for suffix in (".npz", "_vocab.npy", "_texts.json")
    )


__all__ = [
    "build_20ng_tiny",
    "build_bbc_tiny",
    "build_scenario_from_fixture",
    "build_scenario_from_topic_model",
    "demo_page_contains_real_terms",
    "fixture_exists",
]
