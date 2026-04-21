"""Exclude one document from a topic's contribution.

Listed as **future work** in the paper (Section 6). Now implemented.

Semantics
---------
We zero out ``doc_topic_dists[doc_id, topic_id]`` and renormalize the
*row* (so the document's remaining topic mass is rescaled) but **do
not** touch the topic-term matrix. This matches the user intent:
"don't count this document toward this topic anymore", visible as
the document moving in the relevant-documents panel.

The change is local; like :mod:`add_remove_word` it is a display-only
edit. Use a follow-up :func:`split` for full re-inference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..errors import ValidationError
from ..logging import get_logger

if TYPE_CHECKING:
    from ..models.protocol import TopicModelData
    from ..prepare import PreparedData

logger = get_logger(__name__)


def exclude_document(
    prepared: PreparedData,
    *,
    topic_id: int,
    doc_id: int,
    model_data: TopicModelData,
) -> PreparedData:
    """Zero ``P(topic | doc)`` for one ``(topic, doc)`` pair and renormalize."""
    N, K = model_data.doc_topic_dists.shape
    if not 1 <= topic_id <= K:
        raise ValidationError(f"topic_id must be in [1, {K}], got {topic_id}")
    if not 0 <= doc_id < N:
        raise ValidationError(f"doc_id must be in [0, {N - 1}], got {doc_id}")

    t_idx = topic_id - 1
    new_doc_topic = model_data.doc_topic_dists.copy()
    new_doc_topic[doc_id, t_idx] = 0.0
    row_sum = new_doc_topic[doc_id].sum()
    if row_sum == 0:
        raise ValidationError(
            f"Excluding doc {doc_id} from topic {topic_id} would leave the "
            "document with no topic mass at all. Refusing."
        )
    new_doc_topic[doc_id] /= row_sum

    logger.info("Excluded document %d from topic %d.", doc_id, topic_id)

    from ..prepare import prepare

    return prepare(
        topic_term_dists=model_data.topic_term_dists,
        doc_topic_dists=new_doc_topic,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
        metadata={
            **prepared.metadata,
            "operation": "exclude_document",
            "topic_id": topic_id,
            "doc_id": doc_id,
            "display_only": True,
        },
    )
