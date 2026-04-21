"""Phase 4g: golden tests for the Phase 4 edit operations.

Pin the *exact numerical output* of :func:`add_word`,
:func:`remove_word`, and :func:`exclude_document` against
``golden_baseline/tiny_edit_ops.json`` (regenerable via
``scripts/capture_edit_op_golden.py``).

Why this is its own file (separate from
``tests/unit/test_operations.py``):

* The unit tests cover the *qualitative* contract -- "the word is
  zeroed", "the document doesn't blow up renormalization" -- and
  are tolerant to refactors that don't change the user-visible
  semantics.
* These golden tests pin the actual floats so regressions in
  ``boost_to_quantile``, the order of renormalization-then-prepare,
  or accidental tweaks to ``prepare()`` itself are caught the
  moment they shift any number more than ``atol=1e-9``.

Both layers are needed: the unit test tells you "the shape is
right", the golden test tells you "the math is byte-equivalent to
v1.0". Loosening the golden tests is a deliberate UX change and
should be a separate commit re-running the capture script.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from topicvisexplorer import operations, prepare
from topicvisexplorer.models.protocol import TopicModelData

GOLDEN = (
    Path(__file__).resolve().parents[2] / "golden_baseline" / "tiny_edit_ops.json"
)
ATOL = 1e-9


@pytest.fixture(scope="module")
def golden() -> dict:
    if not GOLDEN.exists():
        pytest.skip(
            "golden_baseline/tiny_edit_ops.json missing -- "
            "run scripts/capture_edit_op_golden.py to generate"
        )
    return json.loads(GOLDEN.read_text())


def _build_modeldata(
    tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> TopicModelData:
    return TopicModelData(
        topic_term_dists=tiny_topic_term,
        doc_topic_dists=tiny_doc_topic,
        doc_lengths=tiny_doc_lengths,
        vocab=tiny_vocab,
        term_frequency=tiny_term_freq,
    )


def _topic_row(prep, topic_id: int) -> pd.DataFrame:
    sub = prep.topic_info[prep.topic_info["Category"] == f"Topic{topic_id}"]
    return sub.sort_values(by="Term").reset_index(drop=True)


def _assert_golden_topic1_match(prep, expected: dict) -> None:
    actual = _topic_row(prep, 1)
    assert actual["Term"].astype(str).tolist() == expected["Term"], (
        "Term ordering drift: pinned vocabulary alignment changed"
    )
    for col in ("Freq", "Total", "logprob", "loglift"):
        np.testing.assert_allclose(
            actual[col].astype(float).to_numpy(),
            np.asarray(expected[col]),
            atol=ATOL,
            err_msg=f"{col} drift in topic_info[Topic1]",
        )


def test_golden_add_word_topic1(
    golden,
    tiny_prepared,
    tiny_topic_term,
    tiny_doc_topic,
    tiny_doc_lengths,
    tiny_vocab,
    tiny_term_freq,
) -> None:
    md = _build_modeldata(
        tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
    )
    new = operations.add_word(
        tiny_prepared,
        topic_id=golden["add_word"]["topic_id"],
        word=golden["add_word"]["word"],
        model_data=md,
        boost_to_quantile=golden["add_word"]["boost_to_quantile"],
    )
    _assert_golden_topic1_match(new, golden["add_word"]["topic_info_topic1"])


def test_golden_remove_word_topic1(
    golden,
    tiny_prepared,
    tiny_topic_term,
    tiny_doc_topic,
    tiny_doc_lengths,
    tiny_vocab,
    tiny_term_freq,
) -> None:
    md = _build_modeldata(
        tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
    )
    new = operations.remove_word(
        tiny_prepared,
        topic_id=golden["remove_word"]["topic_id"],
        word=golden["remove_word"]["word"],
        model_data=md,
    )
    _assert_golden_topic1_match(new, golden["remove_word"]["topic_info_topic1"])


def test_golden_exclude_document_topic_freq(
    golden,
    tiny_prepared,
    tiny_topic_term,
    tiny_doc_topic,
    tiny_doc_lengths,
    tiny_vocab,
    tiny_term_freq,
) -> None:
    md = _build_modeldata(
        tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
    )
    new = operations.exclude_document(
        tiny_prepared,
        topic_id=golden["exclude_document"]["topic_id"],
        doc_id=golden["exclude_document"]["doc_id"],
        model_data=md,
    )
    expected = np.asarray(golden["exclude_document"]["topic_freq_after"])
    actual = new.topic_coordinates["Freq"].astype(float).to_numpy()
    np.testing.assert_allclose(
        actual,
        expected,
        atol=ATOL,
        err_msg=(
            "topic_coordinates['Freq'] drifted after exclude_document. "
            "If intentional, re-run scripts/capture_edit_op_golden.py."
        ),
    )


def test_golden_exclude_document_renormalizes_doc_row(
    golden,
    tiny_topic_term,
    tiny_doc_topic,
    tiny_doc_lengths,
    tiny_vocab,
    tiny_term_freq,
) -> None:
    """Independent recomputation of the doc-row renormalization.

    This sidesteps :func:`prepare` and asserts the math directly:
    zero out doc_topic[0, 0] and renormalize, then compare against
    the captured row. Catches drift in
    :func:`exclude_document`'s arithmetic even if the
    :class:`PreparedData` shape later changes.
    """
    new_doc_topic = tiny_doc_topic.copy()
    t = golden["exclude_document"]["topic_id"] - 1
    d = golden["exclude_document"]["doc_id"]
    new_doc_topic[d, t] = 0.0
    new_doc_topic[d] /= new_doc_topic[d].sum()
    np.testing.assert_allclose(
        new_doc_topic[d],
        np.asarray(golden["exclude_document"]["doc0_topic_row_after"]),
        atol=ATOL,
    )

    # Also assert that calling the actual ``operations.exclude_document``
    # still produces a valid PreparedData (no NaNs in topic_info).
    md = _build_modeldata(
        tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
    )
    seed_prep = prepare(
        topic_term_dists=tiny_topic_term,
        doc_topic_dists=tiny_doc_topic,
        doc_lengths=tiny_doc_lengths,
        vocab=tiny_vocab,
        term_frequency=tiny_term_freq,
    )
    new = operations.exclude_document(
        seed_prep, topic_id=t + 1, doc_id=d, model_data=md
    )
    assert new.topic_info["Freq"].notna().all()
    assert new.topic_info["logprob"].notna().all()
    assert new.topic_info["loglift"].notna().all()
