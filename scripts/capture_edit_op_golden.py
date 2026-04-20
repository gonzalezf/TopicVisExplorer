"""Capture golden baselines for the Phase 4 edit operations.

Phase 4d (add/remove word) and Phase 4e (exclude document) ship as
small, surgical edits to ``topic_term_dists`` / ``doc_topic_dists``.
The unit tests in ``tests/unit/test_operations.py`` cover the
*qualitative* contract (the word disappears from the topic, the
document is renormalized away). The golden tests in
``tests/golden/test_edit_ops_golden.py`` pin the *exact numerical
output* against a committed JSON baseline, so any future regression
that silently re-tweaks the boost-quantile or the renormalization
math gets caught immediately.

Run this once after intentionally changing the algorithm:

    python scripts/capture_edit_op_golden.py

The output goes to ``golden_baseline/tiny_edit_ops.json``. The
fixture is the deterministic ``tiny_*`` set defined in
``tests/conftest.py`` (12 docs, 4 topics, 24-term vocab, fixed
seed 0), so re-running the script must produce byte-identical JSON.
If it doesn't, an upstream dependency drifted -- investigate
before committing the new file.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from topicvisexplorer import operations, prepare
from topicvisexplorer.models.protocol import TopicModelData

OUT = Path(__file__).resolve().parents[1] / "golden_baseline" / "tiny_edit_ops.json"


def _tiny_fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], np.ndarray]:
    """Mirror of the ``tiny_*`` fixtures in tests/conftest.py.

    Replicated here so this script doesn't depend on pytest fixture
    machinery -- it can be run as a plain CLI.
    """
    np.random.seed(0)
    K, V = 4, 24
    base = np.full((K, V), 0.001)
    for k, slice_ in enumerate([(0, 6), (6, 12), (12, 18), (18, 24)]):
        base[k, slice_[0] : slice_[1]] += 1.0 + 0.1 * np.random.rand(6)
    topic_term = base / base.sum(axis=1, keepdims=True)

    rng = np.random.default_rng(0)
    N = 12
    dt = np.full((N, K), 0.05)
    for d in range(N):
        dt[d, d % K] += 1.0
        bleed = rng.choice(K)
        dt[d, bleed] += 0.3
    doc_topic = dt / dt.sum(axis=1, keepdims=True)

    vocab = [
        "dog", "puppy", "leash", "bark", "park", "walk",
        "cat", "kitten", "purr", "scratch", "litter", "nap",
        "fish", "tank", "ocean", "swim", "deep", "fin",
        "car", "engine", "wheel", "tire", "road", "highway",
    ]
    corpus = [
        ["dog", "cat", "puppy", "kitten", "pet", "animal"],
        ["dog", "bark", "leash", "park", "walk", "pet"],
        ["cat", "purr", "litter", "nap", "scratch", "pet"],
        ["fish", "tank", "water", "swim", "fin", "scale"],
        ["fish", "ocean", "boat", "swim", "fin", "deep"],
        ["puppy", "kitten", "pet", "fluffy", "animal", "cute"],
        ["car", "engine", "wheel", "brake", "road", "tire"],
        ["car", "fuel", "speed", "drive", "highway", "engine"],
        ["car", "tire", "wheel", "highway", "road", "fast"],
        ["dog", "puppy", "leash", "bark", "walk", "park"],
        ["cat", "kitten", "purr", "scratch", "litter", "nap"],
        ["fish", "tank", "water", "swim", "deep", "ocean"],
    ]
    counts = pd.Series([w for d in corpus for w in d]).value_counts()
    term_freq = np.asarray([counts.get(w, 1) for w in vocab], dtype=np.float64)
    doc_lengths = np.asarray([len(d) for d in corpus], dtype=np.float64)
    return topic_term, doc_topic, doc_lengths, vocab, term_freq


def main() -> None:
    topic_term, doc_topic, doc_lengths, vocab, term_freq = _tiny_fixture()
    prepared = prepare(
        topic_term_dists=topic_term,
        doc_topic_dists=doc_topic,
        doc_lengths=doc_lengths,
        vocab=vocab,
        term_frequency=term_freq,
    )
    md = TopicModelData(
        topic_term_dists=topic_term,
        doc_topic_dists=doc_topic,
        doc_lengths=doc_lengths,
        vocab=vocab,
        term_frequency=term_freq,
    )

    def _topic_row(prep, topic_id: int) -> dict[str, list]:
        """Extract a ``Topic{N}``-category slice from ``topic_info``.

        The operations don't return the modified raw arrays; what
        survives in :class:`PreparedData` is the LDAvis-style
        ``topic_info`` table. Capturing the per-topic Term/Freq/Total/
        logprob/loglift slice gives us full coverage of the
        operation's downstream effect, which is what the front-end
        actually consumes.
        """
        sub = prep.topic_info[prep.topic_info["Category"] == f"Topic{topic_id}"]
        sub_sorted = sub.sort_values(by="Term").reset_index(drop=True)
        return {
            "Term": sub_sorted["Term"].astype(str).tolist(),
            "Freq": sub_sorted["Freq"].astype(float).tolist(),
            "Total": sub_sorted["Total"].astype(float).tolist(),
            "logprob": sub_sorted["logprob"].astype(float).tolist(),
            "loglift": sub_sorted["loglift"].astype(float).tolist(),
        }

    def _doc_row(prep, doc_id: int) -> list[float]:
        """Read doc-topic mass for ``doc_id`` out of ``topic_coordinates``.

        ``PreparedData`` doesn't directly store doc_topic_dists, but
        ``topic_coordinates['Freq']`` is derived from the column-sum
        of ``(doc_topic.T * doc_lengths).T`` -- so any change to a
        single doc's topic row will perturb the *aggregate* topic
        frequencies. We capture the topic frequency vector after the
        exclusion as the observable signal, plus the doc's own
        retained topic mass via ``token_table`` is not applicable.
        For the deeper signal we recompute the modified
        ``doc_topic_dists`` ourselves.
        """
        # Reproduce the operation's internal math on a copy so we
        # have something to pin in JSON. ``exclude_document`` zeroes
        # one cell and renormalizes its row; verifying that against
        # a captured row catches accidental algorithm drift.
        return prep.topic_coordinates["Freq"].astype(float).tolist()

    add = operations.add_word(prepared, topic_id=1, word="fish", model_data=md)
    rem = operations.remove_word(prepared, topic_id=1, word="dog", model_data=md)
    excl = operations.exclude_document(prepared, topic_id=1, doc_id=0, model_data=md)

    # Capture a row of the modified raw doc_topic for exclude_document
    # by recomputing exactly what the op does (pure, no LDA call).
    new_doc_topic = doc_topic.copy()
    new_doc_topic[0, 0] = 0.0
    new_doc_topic[0] /= new_doc_topic[0].sum()

    payload = {
        "fixture_seed": 0,
        "K": 4,
        "V": 24,
        "N": 12,
        "vocab": vocab,
        "add_word": {
            "topic_id": 1,
            "word": "fish",
            "boost_to_quantile": 0.9,
            "topic_info_topic1": _topic_row(add, 1),
        },
        "remove_word": {
            "topic_id": 1,
            "word": "dog",
            "topic_info_topic1": _topic_row(rem, 1),
        },
        "exclude_document": {
            "topic_id": 1,
            "doc_id": 0,
            "topic_freq_after": excl.topic_coordinates["Freq"].astype(float).tolist(),
            "doc0_topic_row_after": new_doc_topic[0].astype(float).tolist(),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {OUT.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
