"""Fixture quality checks for bundled real-terms scenarios.

Guards against regressions in the offline builder pipeline: every
committed ``{stem}.npz`` must carry LDA topics whose top-20 tokens
contain no NLTK English stopword, each topic must have at least 10
non-zero-probability vocabulary entries, and the vocab length must
match the ``topic_term_dists`` column count.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

try:
    from nltk.corpus import stopwords as _nltk_sw

    STOPWORDS = set(_nltk_sw.words("english"))
except Exception:  # pragma: no cover - optional at runtime
    STOPWORDS = set()

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "src/topicvisexplorer/server/fixtures"
BUNDLED_STEMS = ("20ng_tiny", "bbc_tiny")


def _available_stems() -> list[str]:
    return [s for s in BUNDLED_STEMS if (FIXTURE_DIR / f"{s}.npz").exists()]


@pytest.mark.parametrize("stem", _available_stems())
def test_fixture_has_no_stopwords_in_top20(stem: str) -> None:
    if not STOPWORDS:
        pytest.skip("NLTK stopwords corpus not available in this environment.")
    npz = np.load(FIXTURE_DIR / f"{stem}.npz", allow_pickle=True)
    vocab = np.load(FIXTURE_DIR / f"{stem}_vocab.npy", allow_pickle=True).tolist()
    tt = np.asarray(npz["topic_term_dists"], dtype=np.float64)
    assert tt.shape[1] == len(vocab)
    violations: list[str] = []
    for t in range(tt.shape[0]):
        top = np.argsort(-tt[t])[:20]
        bad = [str(vocab[i]) for i in top if str(vocab[i]).lower() in STOPWORDS]
        if bad:
            violations.append(f"topic {t}: {bad}")
    assert not violations, f"{stem} fixture has stopwords in top-20: {violations}"


@pytest.mark.parametrize("stem", _available_stems())
def test_fixture_topic_has_enough_nonzero_terms(stem: str) -> None:
    npz = np.load(FIXTURE_DIR / f"{stem}.npz", allow_pickle=True)
    tt = np.asarray(npz["topic_term_dists"], dtype=np.float64)
    for t in range(tt.shape[0]):
        nonzero = int((tt[t] > 0).sum())
        assert nonzero >= 10, f"{stem} topic {t} has only {nonzero} nonzero terms."


@pytest.mark.parametrize("stem", _available_stems())
def test_fixture_vocab_matches_term_dists(stem: str) -> None:
    npz = np.load(FIXTURE_DIR / f"{stem}.npz", allow_pickle=True)
    vocab = np.load(FIXTURE_DIR / f"{stem}_vocab.npy", allow_pickle=True).tolist()
    tt = np.asarray(npz["topic_term_dists"], dtype=np.float64)
    tf = np.asarray(npz["term_frequency"], dtype=np.float64)
    assert tt.shape[1] == len(vocab)
    assert tf.shape[0] == len(vocab)
    assert len(vocab) == len(set(vocab)), "vocabulary must be unique"


@pytest.mark.parametrize("stem", _available_stems())
def test_circle_positions_endpoints_differ(stem: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Omega endpoints (``"0.0"`` and ``"1.0"``) must produce different layouts.

    The conftest defaults to ``TVE_EMBEDDING_DISABLE=1`` to keep the test
    suite fast. This test deliberately unsets the flag so it exercises
    the real Word2Vec -> :class:`EmbeddingSimilarity` -> layout pipeline
    that powers the Omega slider. Guards against a regression to the
    old JSD-duplicated flat-layout bug.

    Skips gracefully if :mod:`gensim` is not installed (minimal install)
    -- we do not want to force the full extra for CI envs that do not
    care about Omega-varying layouts.
    """
    gensim = pytest.importorskip("gensim", reason="gensim required for Omega-varying layout test")
    del gensim  # imported only for the skip check

    monkeypatch.delenv("TVE_EMBEDDING_DISABLE", raising=False)

    from topicvisexplorer.server.demo_fixtures import build_scenario_from_fixture

    sc = build_scenario_from_fixture(stem)
    pos = sc.circle_positions
    assert "0.0" in pos and "1.0" in pos, f"{stem}: missing omega endpoints: {sorted(pos)[:5]}"
    if sc.embedding is None:
        pytest.skip(
            f"{stem}: _train_or_load_embedding returned None "
            "(corpus too small or gensim unavailable); cannot assert Omega variation."
        )
    diff = float(np.max(np.abs(np.asarray(pos["0.0"]) - np.asarray(pos["1.0"]))))
    assert diff > 1e-3, (
        f"{stem}: Omega-invariant layout (max |pos[0.0] - pos[1.0]|={diff:g}); "
        "embedding branch probably regressed to JSD duplication."
    )


def test_bbc_vs_20ng_multi_corpus_endpoints_differ(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cross-corpus Omega slider must vary the aligned bubble layout.

    Exercises the full :func:`build_bbc_vs_20ng` pipeline -- shared
    Word2Vec + :func:`cross_corpus` -- and asserts the aligned layout
    endpoints differ, the multi-corpus flag is set, and the similarity
    grid is fully populated (101 keys).

    Skips gracefully when the required fixtures or gensim are not
    available, so minimal install + fresh-clone users are not blocked.
    """
    gensim = pytest.importorskip("gensim", reason="gensim required for Omega-varying layout test")
    del gensim

    monkeypatch.delenv("TVE_EMBEDDING_DISABLE", raising=False)

    from topicvisexplorer.server.demo_fixtures import build_bbc_vs_20ng, fixture_exists

    if not (fixture_exists("bbc_tiny") and fixture_exists("20ng_tiny")):
        pytest.skip("bbc_tiny and/or 20ng_tiny fixtures not built; cannot run multi-corpus check.")

    sc = build_bbc_vs_20ng()

    assert sc.is_multi is True, "bbc_vs_20ng scenario must set is_multi=True"
    if sc.embedding is None:
        pytest.skip(
            "_train_or_load_embedding returned None for bbc_vs_20ng "
            "(gensim unavailable or corpus too small); cannot assert Omega variation."
        )

    # Similarity grid: 101 keys spanning 0.00..1.00 in 0.01 steps.
    keys = sorted(sc.similarity_matrix.keys())
    assert len(keys) == 101, f"expected 101 omega steps, got {len(keys)}"
    assert abs(keys[0] - 0.0) < 1e-9 and abs(keys[-1] - 1.0) < 1e-9

    # Endpoints must not be identical matrices (embedding-based metric is
    # omega-variant even for cross-corpus pairs).
    mat0 = np.asarray(sc.similarity_matrix[0.0], dtype=np.float64)
    mat1 = np.asarray(sc.similarity_matrix[1.0], dtype=np.float64)
    assert np.max(np.abs(mat0 - mat1)) > 1e-6, (
        "bbc_vs_20ng: endpoint similarity matrices are identical; "
        "cross_corpus likely regressed to a flat grid."
    )

    pos = sc.circle_positions
    assert "0.0" in pos and "1.0" in pos, f"missing omega endpoints: {sorted(pos)[:5]}"
    diff = float(np.max(np.abs(np.asarray(pos["0.0"]) - np.asarray(pos["1.0"]))))
    assert diff > 1e-3, (
        f"bbc_vs_20ng: Omega-invariant aligned layout "
        f"(max |pos[0.0] - pos[1.0]|={diff:g}); cross_corpus regressed."
    )
