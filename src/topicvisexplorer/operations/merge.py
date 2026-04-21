"""Topic merge: collapse two topics into one (paper Section 4.2).

The merged topic-term distribution is the per-cell average of the two
parents *weighted by their topic mass*; the merged doc-topic column is
the per-document sum of the two parents' columns. The result is
re-normalized and handed to :func:`topicvisexplorer.prepare`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..errors import ValidationError
from ..logging import get_logger

if TYPE_CHECKING:
    from ..models.protocol import TopicModelData
    from ..prepare import PreparedData

logger = get_logger(__name__)


def merge(
    prepared: PreparedData,
    *,
    topic_id_a: int,
    topic_id_b: int,
    model_data: TopicModelData,
) -> PreparedData:
    """Merge ``topic_id_a`` and ``topic_id_b`` into a single topic.

    Parameters are 1-based to match the front end. Returns a fresh
    :class:`PreparedData` with ``K - 1`` topics; the merged topic occupies
    ``min(topic_id_a, topic_id_b)``.
    """
    if topic_id_a == topic_id_b:
        raise ValidationError("Cannot merge a topic with itself.")
    K, _V = model_data.topic_term_dists.shape
    if not 1 <= topic_id_a <= K or not 1 <= topic_id_b <= K:
        raise ValidationError(f"topic ids must be in [1, {K}]")

    a_idx, b_idx = sorted((topic_id_a - 1, topic_id_b - 1))
    logger.info("Merging topic %d into topic %d.", b_idx + 1, a_idx + 1)

    topic_freq = model_data.doc_topic_dists.sum(axis=0)
    w_a = float(topic_freq[a_idx])
    w_b = float(topic_freq[b_idx])
    w_total = w_a + w_b if (w_a + w_b) > 0 else 1.0
    merged_topic_term = (
        w_a * model_data.topic_term_dists[a_idx] + w_b * model_data.topic_term_dists[b_idx]
    ) / w_total
    merged_topic_term /= max(merged_topic_term.sum(), 1e-12)

    keep_idx = [i for i in range(K) if i != b_idx]
    new_topic_term = model_data.topic_term_dists[keep_idx].copy()
    new_topic_term[a_idx if a_idx < b_idx else a_idx - 1] = merged_topic_term

    new_doc_topic = model_data.doc_topic_dists[:, keep_idx].copy()
    new_doc_topic[:, a_idx if a_idx < b_idx else a_idx - 1] = (
        model_data.doc_topic_dists[:, a_idx] + model_data.doc_topic_dists[:, b_idx]
    )
    row_sums = new_doc_topic.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    new_doc_topic /= row_sums

    from ..prepare import prepare

    return prepare(
        topic_term_dists=new_topic_term,
        doc_topic_dists=new_doc_topic,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
        metadata={
            **prepared.metadata,
            "operation": "merge",
            "merged_topic_ids": [topic_id_a, topic_id_b],
        },
    )
