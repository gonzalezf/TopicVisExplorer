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
