"""Adapter for BERTopic (Grootendorst 2022).

Delivers paper Section 6 future work: "future versions could integrate
[...] contextualized topic models such as BERTopic" verbatim.

Mapping BERTopic to the LDAvis contract
---------------------------------------
BERTopic does not produce probabilities the way LDA does. It produces:

* **c-TF-IDF scores** per (topic, term): a class-conditional TF-IDF, NOT
  a row-stochastic distribution. We row-normalize to fit the LDAvis
  ``topic_term_dists`` contract. This is the same normalization used by
  BERTopic's own ``pyLDAvis`` integration recipe and by every published
  BERTopic+pyLDAvis notebook in the wild.
* **Hard topic assignments** per document via ``model.topics_``. We
  request soft assignments via ``model.approximate_distribution(docs)``
  when available (BERTopic >= 0.10), and fall back to one-hot from
  ``topics_`` when not.

Outlier topic handling
----------------------
BERTopic's HDBSCAN backend produces a special **topic ``-1``** for
documents the clustering refused to assign. We exclude it from the
visualization (it is not a real topic; including it produces a giant
diffuse "junk" cluster that dominates the 2D map). Documents originally
assigned to ``-1`` are still counted in the corpus statistics but their
``doc_topic_dists`` row is renormalized over the remaining K topics.
This matches the BERTopic+pyLDAvis recipe.

Numerical caveat (documented, not a bug)
----------------------------------------
The c-TF-IDF -> probability normalization changes the metric semantics.
A "probability" in this matrix is "share of class-TF-IDF mass that this
term carries within this topic", not "P(term | topic)" as in LDA. The
relevance metric (Sievert & Shirley Eq. 2) and our embedding similarity
(paper Eq. 9) still produce sensible orderings -- they consume the
matrix as a weight distribution -- but a strict probabilistic
interpretation does not transfer. The Extending guide makes this
explicit.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.sparse import issparse

from ...errors import ValidationError
from ...logging import get_logger
from ..protocol import TopicModelData

logger = get_logger(__name__)


class BERTopicAdapter:
    """Adapter for a fitted :class:`bertopic.BERTopic` model.

    Parameters to :meth:`extract`:

    * ``model``: fitted ``BERTopic`` instance.
    * ``corpus``: ignored (BERTopic carries its own internal vectorizer
      and document store). Pass ``None`` or anything truthy for API
      symmetry with the gensim/sklearn adapters.
    * ``texts`` (kw): the original list of input strings. Required.
      Used for the doc-topic recomputation and term-frequency tally.

    Optional kwargs:

    * ``include_outliers`` (bool, default ``False``): if ``True``, keep
      the ``-1`` topic as a regular topic. Default is to drop it.
    """

    name = "bertopic"

    def extract(
        self,
        model: Any,
        corpus: Any,
        *,
        texts: list[str] | None = None,
        include_outliers: bool = False,
    ) -> TopicModelData:
        # The adapter is fully duck-typed: anything exposing
        # ``c_tf_idf_``, ``vectorizer_model``, ``topics_`` and
        # ``get_topic_info`` works. We deliberately do NOT
        # ``import bertopic`` here -- a real user cannot construct a
        # ``BERTopic`` instance without the package being importable, so
        # the eager import would only succeed in obstructing the unit
        # tests, which exercise the adapter through a fake double.
        if texts is None:
            raise ValidationError(
                "BERTopicAdapter.extract requires a `texts=` keyword argument "
                "(the list of input strings the BERTopic model was fitted on). "
                "BERTopic does not expose the original documents through its "
                "public API, so we cannot recover them from the model alone."
            )

        # ------------------------------------------------------------------
        # 1. Pull c-TF-IDF and the topic id index out of the model.
        #    BERTopic stores a CSR sparse matrix on `c_tf_idf_` whose rows
        #    are aligned with the topic ids returned by `get_topics()`,
        #    EXCEPT that topic -1 (outliers) -- if present -- is at row 0
        #    and the rest follow in increasing order. We rebuild the
        #    mapping explicitly to avoid relying on that internal
        #    invariant across BERTopic versions.
        # ------------------------------------------------------------------
        if not hasattr(model, "c_tf_idf_") or model.c_tf_idf_ is None:
            raise ValidationError(
                "The BERTopic model has no `c_tf_idf_` matrix. Did you "
                "call `model.fit(...)` (not just construct it)?"
            )

        c_tf_idf = model.c_tf_idf_
        if issparse(c_tf_idf):
            c_tf_idf = c_tf_idf.toarray()
        c_tf_idf = np.asarray(c_tf_idf, dtype=np.float64)

        topic_info = model.get_topic_info()
        # topic_info is a pandas DataFrame with at least a "Topic" column.
        topic_ids = list(topic_info["Topic"])

        if not include_outliers and -1 in topic_ids:
            keep_mask = np.asarray([t != -1 for t in topic_ids], dtype=bool)
            c_tf_idf = c_tf_idf[keep_mask]
            kept_topic_ids = [t for t in topic_ids if t != -1]
        else:
            kept_topic_ids = topic_ids

        if c_tf_idf.shape[0] == 0:
            raise ValidationError(
                "BERTopic model has no topics after filtering outliers. "
                "Pass include_outliers=True to keep topic -1, or refit "
                "with fewer outliers (e.g. tighter HDBSCAN min_cluster_size)."
            )

        # Row-normalize c-TF-IDF to a row-stochastic matrix. Some rows can
        # be all-zero in pathological cases (a topic with no surviving
        # terms after vectorizer filtering); guard against div-by-zero
        # by leaving those rows uniform.
        row_sums = c_tf_idf.sum(axis=1, keepdims=True)
        zero_rows = (row_sums == 0).ravel()
        if zero_rows.any():
            logger.warning(
                "BERTopic adapter: %d topic(s) have all-zero c-TF-IDF after "
                "vectorizer filtering; assigning uniform topic_term_dists for them.",
                int(zero_rows.sum()),
            )
            c_tf_idf[zero_rows] = 1.0
            row_sums[zero_rows] = float(c_tf_idf.shape[1])
        topic_term_dists = c_tf_idf / row_sums

        # ------------------------------------------------------------------
        # 2. Recover the vocabulary. BERTopic owns a CountVectorizer on
        #    `vectorizer_model`; we re-vectorize the texts to also
        #    compute term frequencies and document lengths consistent
        #    with that vocabulary.
        # ------------------------------------------------------------------
        vectorizer = getattr(model, "vectorizer_model", None)
        if vectorizer is None or not hasattr(vectorizer, "get_feature_names_out"):
            raise ValidationError(
                "Could not access BERTopic's internal CountVectorizer "
                "(`model.vectorizer_model`). Are you using BERTopic >= 0.9?"
            )
        vocab = list(vectorizer.get_feature_names_out())
        if len(vocab) != topic_term_dists.shape[1]:
            raise ValidationError(
                f"BERTopic c_tf_idf has {topic_term_dists.shape[1]} columns "
                f"but the vectorizer vocabulary has {len(vocab)} terms. "
                "This usually means the model was fit with a different "
                "vectorizer than the one currently attached. Refit, or pass "
                "a custom subclass that re-aligns the two."
            )

        # Term frequency + document length over the SAME vocabulary the
        # c_tf_idf was computed against.
        X = vectorizer.transform(texts)
        term_frequency = np.asarray(X.sum(axis=0)).ravel().astype(np.float64)
        doc_lengths = np.asarray(X.sum(axis=1)).ravel().astype(np.int64)

        # ------------------------------------------------------------------
        # 3. Build doc-topic distributions. Prefer the soft distribution
        #    from `approximate_distribution` (BERTopic >= 0.10); fall back
        #    to one-hot from `topics_` for older versions or when the
        #    approximation step is too slow for the caller.
        # ------------------------------------------------------------------
        K = topic_term_dists.shape[0]
        N = len(texts)
        kept_set = set(kept_topic_ids)
        kept_index = {t: i for i, t in enumerate(kept_topic_ids)}

        doc_topic_dists: np.ndarray | None = None
        if hasattr(model, "approximate_distribution"):
            try:
                # Returns (topic_distr, topic_token_distr); we only need the first.
                approx, _ = model.approximate_distribution(texts, calculate_tokens=False)
                approx = np.asarray(approx, dtype=np.float64)
                # `approx` is shape (N, K_full) where K_full follows
                # model.get_topics() order, EXCLUDING the outlier topic
                # already (BERTopic strips -1 here). Defensive guard:
                if approx.shape == (N, K):
                    doc_topic_dists = approx
                elif approx.shape[1] == K + 1 and -1 in kept_set:
                    # Pathological: model included -1 in approx output.
                    doc_topic_dists = approx[:, :K]
                else:
                    logger.warning(
                        "BERTopic.approximate_distribution returned shape %s, "
                        "expected (%d, %d). Falling back to one-hot from .topics_.",
                        approx.shape,
                        N,
                        K,
                    )
            except Exception as e:
                logger.warning(
                    "BERTopic.approximate_distribution failed (%s); falling "
                    "back to one-hot from model.topics_.",
                    e,
                )

        if doc_topic_dists is None:
            topics_per_doc = list(getattr(model, "topics_", []))
            if len(topics_per_doc) != N:
                raise ValidationError(
                    f"len(model.topics_) = {len(topics_per_doc)} but len(texts) "
                    f"= {N}. Pass exactly the same `texts` the model was "
                    "fitted on."
                )
            doc_topic_dists = np.zeros((N, K), dtype=np.float64)
            for doc_idx, t in enumerate(topics_per_doc):
                if t in kept_index:
                    doc_topic_dists[doc_idx, kept_index[t]] = 1.0
                else:
                    # Outlier doc -> uniform over kept topics, so the doc
                    # is still counted in totals without forcing it onto
                    # one cluster.
                    doc_topic_dists[doc_idx] = 1.0 / K

        # Final renormalize: any all-zero rows (e.g. an outlier doc when
        # we excluded -1 *and* approximate_distribution returned zeros)
        # become uniform.
        row_sums = doc_topic_dists.sum(axis=1, keepdims=True)
        zero_doc_rows = (row_sums == 0).ravel()
        if zero_doc_rows.any():
            doc_topic_dists[zero_doc_rows] = 1.0 / K
            row_sums[zero_doc_rows] = 1.0
        doc_topic_dists = doc_topic_dists / row_sums

        return TopicModelData(
            topic_term_dists=topic_term_dists,
            doc_topic_dists=doc_topic_dists,
            doc_lengths=doc_lengths,
            vocab=vocab,
            term_frequency=term_frequency,
        )
