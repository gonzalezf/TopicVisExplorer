"""Unit tests for :mod:`topicvisexplorer.operations`."""

from __future__ import annotations

import numpy as np
import pytest

from topicvisexplorer import operations
from topicvisexplorer.errors import ValidationError
from topicvisexplorer.models.protocol import TopicModelData


def _model_data(
    tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> TopicModelData:
    return TopicModelData(
        topic_term_dists=tiny_topic_term,
        doc_topic_dists=tiny_doc_topic,
        doc_lengths=tiny_doc_lengths,
        vocab=tiny_vocab,
        term_frequency=tiny_term_freq,
    )


def test_remove_word_zeroes_term_in_topic(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)
    new = operations.remove_word(tiny_prepared, topic_id=1, word="dog", model_data=md)
    sub = new.topic_info.query("Category == 'Topic1' and Term == 'dog'")
    assert sub.empty or float(sub["Freq"].iloc[0]) == 0.0


def test_add_word_makes_word_visible(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)
    new = operations.add_word(tiny_prepared, topic_id=1, word="fish", model_data=md)
    top_terms = new.topic_top_terms(1, n=24)
    assert "fish" in top_terms


def test_remove_word_rejects_unknown_word(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)
    with pytest.raises(ValidationError, match="not in the corpus vocabulary"):
        operations.remove_word(tiny_prepared, topic_id=1, word="ZZZNOTAWORD", model_data=md)


def test_exclude_document_renormalizes(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)
    operations.exclude_document(tiny_prepared, topic_id=1, doc_id=0, model_data=md)


def test_merge_reduces_topic_count(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)
    new = operations.merge(tiny_prepared, topic_id_a=1, topic_id_b=2, model_data=md)
    assert len(new.topic_order) == 3


def test_merge_rejects_self_merge(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)
    with pytest.raises(ValidationError, match="merge a topic with itself"):
        operations.merge(tiny_prepared, topic_id_a=1, topic_id_b=1, model_data=md)


def test_split_with_stub_refit(
    tiny_prepared, tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq
) -> None:
    md = _model_data(tiny_topic_term, tiny_doc_topic, tiny_doc_lengths, tiny_vocab, tiny_term_freq)

    def stub_refit(sub_texts, k_new) -> TopicModelData:
        V = len(tiny_vocab)
        rng = np.random.default_rng(123)
        ttd = rng.dirichlet(np.ones(V), size=k_new)
        dtd = rng.dirichlet(np.ones(k_new), size=len(sub_texts))
        return TopicModelData(
            topic_term_dists=ttd,
            doc_topic_dists=dtd,
            doc_lengths=np.ones(len(sub_texts)),
            vocab=tiny_vocab,
            term_frequency=tiny_term_freq,
        )

    new = operations.split(
        tiny_prepared,
        topic_id=1,
        k_new=2,
        model_data=md,
        raw_texts=["x"] * tiny_doc_topic.shape[0],
        refit=stub_refit,
        min_membership_threshold=0.001,
    )
    assert len(new.topic_order) == 5
