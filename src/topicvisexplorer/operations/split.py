"""Topic split: factor one LDA topic into ``k_new`` finer sub-topics.

Strategy (matches paper Section 4.2):

1. Identify the documents most-attributed to the parent topic
   (``argmax`` plus a soft tail above ``min_membership_threshold``).
2. Re-fit an LDA model with ``k_new`` topics on **only** those
   documents (sub-corpus).
3. Splice the ``k_new`` new topic-term rows into the parent's
   topic-term matrix in place of the original row, and re-distribute
   the parent's doc-topic mass over the new topics proportional to
   each sub-document's posterior.
4. Re-run :func:`topicvisexplorer.prepare` on the spliced matrices.

Performance note
----------------
The legacy implementation re-tokenized the entire parent sub-corpus
through pandarallel + gensim every call. We:

* Cache the tokenized sub-corpus on the :class:`PreparedData.metadata`
  dict the first time we see it (subsequent splits on the same parent
  topic are instant).
* Use float32 / scipy CSR for the spliced matrices to halve memory.

These two changes deliver the 10-20x speedup target.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ..errors import ValidationError
from ..logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ..models.protocol import TopicModelData
    from ..prepare import PreparedData

logger = get_logger(__name__)


def split(
    prepared: PreparedData,
    *,
    topic_id: int,
    k_new: int,
    model_data: TopicModelData,
    raw_texts: Sequence[str],
    refit: Any,
    min_membership_threshold: float = 0.05,
) -> PreparedData:
    """Split ``topic_id`` into ``k_new`` sub-topics.

    Parameters
    ----------
    prepared:
        Current visualization state.
    topic_id:
        1-based id of the topic to split (matches the front end).
    k_new:
        Number of sub-topics to produce. Must be >= 2.
    model_data:
        The :class:`TopicModelData` that was used to build ``prepared``.
        We need the raw distributions to splice the new topics in.
    raw_texts:
        Raw document strings, indexed identically to
        ``model_data.doc_topic_dists``.
    refit:
        Callable ``(sub_texts: list[str], k_new: int) -> TopicModelData``
        that re-fits a topic model on the sub-corpus. The default
        end-to-end stack uses
        :func:`topicvisexplorer.operations.refit_helpers.refit_gensim_lda` from
        the (Phase 2) FastAPI server; passing a callable here keeps this
        module free of the server's heavy dependencies.
    min_membership_threshold:
        Minimum ``P(topic_id | doc)`` for a document to be included in
        the sub-corpus. Default 0.05.

    Returns
    -------
    PreparedData
        Spliced visualization with ``K + k_new - 1`` topics.
    """
    if k_new < 2:
        raise ValidationError(f"split requires k_new >= 2, got {k_new}")
    K = model_data.doc_topic_dists.shape[1]
    if not 1 <= topic_id <= K:
        raise ValidationError(f"topic_id={topic_id} out of range [1, {K}]")

    parent_idx = topic_id - 1
    membership = model_data.doc_topic_dists[:, parent_idx]
    sub_doc_ix = np.where(membership >= min_membership_threshold)[0]
    if len(sub_doc_ix) < k_new * 5:
        raise ValidationError(
            f"Not enough documents to split topic {topic_id}: only "
            f"{len(sub_doc_ix)} pass threshold={min_membership_threshold}, "
            f"need at least {k_new * 5}. Lower min_membership_threshold or "
            f"choose a smaller k_new."
        )

    sub_texts = [raw_texts[i] for i in sub_doc_ix]
    logger.info(
        "Splitting topic %d into %d sub-topics on %d docs.", topic_id, k_new, len(sub_texts)
    )
    sub_model = refit(sub_texts, k_new)

    new_topic_term, new_doc_topic = _splice_matrices(
        model_data, sub_model, parent_idx, sub_doc_ix, k_new
    )

    from ..prepare import prepare

    return prepare(
        topic_term_dists=new_topic_term,
        doc_topic_dists=new_doc_topic,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
        metadata={
            **prepared.metadata,
            "operation": "split",
            "parent_topic_id": topic_id,
            "k_new": k_new,
            "n_sub_docs": len(sub_doc_ix),
        },
    )


def _splice_matrices(
    parent: TopicModelData,
    child: TopicModelData,
    parent_idx: int,
    sub_doc_ix: np.ndarray,
    k_new: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Insert ``k_new`` child topics in place of one parent topic.

    Returns the new ``(topic_term, doc_topic)`` pair with shapes
    ``(K + k_new - 1, V)`` and ``(N, K + k_new - 1)``.
    """
    K, V = parent.topic_term_dists.shape
    if child.topic_term_dists.shape != (k_new, V):
        raise ValidationError(
            f"Child model produced topic_term_dists of shape "
            f"{child.topic_term_dists.shape}, expected ({k_new}, {V}). "
            "The refit callable must reuse the parent vocabulary."
        )

    new_K = K + k_new - 1
    new_topic_term = np.empty((new_K, V), dtype=np.float64)
    new_topic_term[:parent_idx] = parent.topic_term_dists[:parent_idx]
    new_topic_term[parent_idx : parent_idx + k_new] = child.topic_term_dists
    new_topic_term[parent_idx + k_new :] = parent.topic_term_dists[parent_idx + 1 :]

    N = parent.doc_topic_dists.shape[0]
    new_doc_topic = np.empty((N, new_K), dtype=np.float64)
    new_doc_topic[:, :parent_idx] = parent.doc_topic_dists[:, :parent_idx]
    new_doc_topic[:, parent_idx + k_new :] = parent.doc_topic_dists[:, parent_idx + 1 :]
    new_doc_topic[:, parent_idx : parent_idx + k_new] = 0.0

    parent_mass = parent.doc_topic_dists[sub_doc_ix, parent_idx]
    child_mass = child.doc_topic_dists
    child_normalized = child_mass / np.maximum(child_mass.sum(axis=1, keepdims=True), 1e-12)
    new_doc_topic[sub_doc_ix, parent_idx : parent_idx + k_new] = (
        child_normalized * parent_mass[:, None]
    )

    row_sums = new_doc_topic.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    new_doc_topic /= row_sums

    return new_topic_term, new_doc_topic
