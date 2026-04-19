"""Add or remove a single word from a topic's representation.

Listed as **future work** in the paper (Section 6). Now implemented.

Semantics:

* :func:`add_word` -- bump ``topic_term_dists[topic, word_idx]`` to the
  ``boost_to`` quantile of the topic's existing term mass (default the
  90th percentile, so the word appears prominently without dominating).
* :func:`remove_word` -- zero out the term in this topic and renormalize.

Both operations leave other topics unchanged - they are local edits to
one row of the topic-term matrix. After modification the doc-topic
distribution is *not* recomputed (it would require re-inference, which
is what `split` does); instead we treat the edit as a *display-only*
override and tag the metadata so the user knows the change is cosmetic.

For a full re-inference, call :func:`topicvisexplorer.operations.split`
on the affected topic with ``k_new=1`` after editing the vocabulary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ..errors import ValidationError
from ..logging import get_logger

if TYPE_CHECKING:
    from ..models.protocol import TopicModelData
    from ..prepare import PreparedData

logger = get_logger(__name__)


def _word_index(model_data: TopicModelData, word: str) -> int:
    if word not in model_data.vocab:
        raise ValidationError(
            f"Word {word!r} is not in the corpus vocabulary "
            f"({len(model_data.vocab)} terms). Pre-process the document with "
            "topicvisexplorer.preprocessing.text_cleaner first."
        )
    return model_data.vocab.index(word)


def add_word(
    prepared: PreparedData,
    *,
    topic_id: int,
    word: str,
    model_data: TopicModelData,
    boost_to_quantile: float = 0.9,
) -> PreparedData:
    """Boost ``word`` in ``topic_id``'s term distribution.

    The word's new probability is set to the ``boost_to_quantile`` of
    the topic's current non-zero term mass. The whole row is then
    renormalized so it remains a probability distribution.
    """
    K = model_data.topic_term_dists.shape[0]
    if not 1 <= topic_id <= K:
        raise ValidationError(f"topic_id must be in [1, {K}]")
    w_idx = _word_index(model_data, word)
    t_idx = topic_id - 1

    new_topic_term = model_data.topic_term_dists.copy()
    row = new_topic_term[t_idx]
    target = (
        float(np.quantile(row[row > 0], boost_to_quantile)) if np.any(row > 0) else 1.0 / len(row)
    )
    row[w_idx] = max(row[w_idx], target)
    new_topic_term[t_idx] = row / row.sum()

    logger.info("Boosted word %r in topic %d to mass %.4f.", word, topic_id, target)

    from ..prepare import prepare

    return prepare(
        topic_term_dists=new_topic_term,
        doc_topic_dists=model_data.doc_topic_dists,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
        metadata={
            **prepared.metadata,
            "operation": "add_word",
            "topic_id": topic_id,
            "word": word,
            "display_only": True,
        },
    )


def remove_word(
    prepared: PreparedData,
    *,
    topic_id: int,
    word: str,
    model_data: TopicModelData,
) -> PreparedData:
    """Zero out ``word`` in ``topic_id``'s term distribution and renormalize."""
    K = model_data.topic_term_dists.shape[0]
    if not 1 <= topic_id <= K:
        raise ValidationError(f"topic_id must be in [1, {K}]")
    w_idx = _word_index(model_data, word)
    t_idx = topic_id - 1

    new_topic_term = model_data.topic_term_dists.copy()
    new_topic_term[t_idx, w_idx] = 0.0
    row_sum = new_topic_term[t_idx].sum()
    if row_sum == 0:
        raise ValidationError(
            f"Removing {word!r} from topic {topic_id} would zero its entire "
            "term distribution (was the topic dominated by this single word?). "
            "Refusing to apply."
        )
    new_topic_term[t_idx] /= row_sum

    logger.info("Removed word %r from topic %d.", word, topic_id)

    from ..prepare import prepare

    return prepare(
        topic_term_dists=new_topic_term,
        doc_topic_dists=model_data.doc_topic_dists,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
        metadata={
            **prepared.metadata,
            "operation": "remove_word",
            "topic_id": topic_id,
            "word": word,
            "display_only": True,
        },
    )
