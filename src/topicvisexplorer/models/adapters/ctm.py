"""Adapter for Contextualized Topic Models (Bianchi, Terragni & Hovy 2021).

Delivers paper Section 6 future work: "future versions could integrate
[...] contextualized topic models such as [...] CTM (Bianchi et al.
2021)" verbatim.

Mapping CTM to the LDAvis contract
----------------------------------
CTM (CombinedTM, ZeroShotTM) is a neural variational topic model that
augments ProdLDA's bag-of-words decoder with SBERT contextual
embeddings. Its decoder produces a row-stochastic ``(K, V)``
``topic_word_matrix`` already in the LDAvis shape; the encoder produces
a row-stochastic ``(N, K)`` ``doc_topic_distribution`` after sampling.
We just have to expose them.

Supported model interfaces
--------------------------
The de-facto Python implementation is the ``contextualized-topic-models``
PyPI package (https://github.com/MilaNLProc/contextualized-topic-models).
It exposes:

* ``model.get_topic_word_matrix()`` -> ``(K, V)`` numpy array
  (row-stochastic).
* ``model.get_doc_topic_distribution(dataset, n_samples=...)`` ->
  ``(N, K)`` numpy array. Requires CTM's own ``CTMDataset`` carrying
  the SBERT contextual embeddings, so the caller must pass the
  result via ``doc_topic_dists=`` (see Note below).
* ``model.train_data.idx2token`` -> ``dict[int, str]`` vocabulary.

Note on doc-topic computation
-----------------------------
Unlike ETM, CTM's doc-topic posterior requires a CTM-specific
``CTMDataset`` carrying both bag-of-words and SBERT contextual
embeddings. We do **not** try to construct that here -- it would
require the caller to pass an SBERT model and accept a hidden
inference cost. Instead we ask the caller to compute it once and pass
it via ``doc_topic_dists=``:

>>> doc_topic = ctm.get_doc_topic_distribution(testing_dataset, n_samples=20)
>>> data = CTMAdapter().extract(ctm, corpus=None, texts=raw_texts,
...                             doc_topic_dists=doc_topic)

This keeps the adapter free of an SBERT runtime dependency and lets
CTM users control the number of MC samples / batch size.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from ...errors import ValidationError
from ...logging import get_logger
from ..protocol import TopicModelData

logger = get_logger(__name__)


def _to_numpy(x: Any) -> np.ndarray:
    """Convert torch tensors / lists / sparse matrices to dense numpy.

    Mirrors the helper in :mod:`etm`; duplicated rather than shared so
    each adapter file is self-contained for users who copy it as a
    template for their own model.
    """
    if x is None:
        return np.asarray([])
    if hasattr(x, "detach") and hasattr(x, "cpu"):
        return x.detach().cpu().numpy()
    if hasattr(x, "toarray"):
        return x.toarray()
    return np.asarray(x)


class CTMAdapter:
    """Adapter for a fitted CTM model (CombinedTM or ZeroShotTM).

    Parameters to :meth:`extract`:

    * ``model``: fitted CTM. Must expose ``get_topic_word_matrix()``.
    * ``corpus``: ignored. Pass ``None``.

    Required kwargs:

    * ``texts``: original list of input strings (used for term
      frequency and document length tallies).

    Optional kwargs:

    * ``vocabulary``: list of vocabulary terms in the order the
      ``topic_word_matrix`` columns are aligned with. If omitted, we
      look up ``model.train_data.idx2token`` (the CTM convention) or
      raise.
    * ``doc_topic_dists``: precomputed ``(N, K)`` matrix. **Strongly
      recommended** for CTM (see module docstring for why we don't
      compute it here).
    """

    name = "ctm"

    def extract(
        self,
        model: Any,
        corpus: Any,
        *,
        texts: list[str] | None = None,
        vocabulary: list[str] | None = None,
        doc_topic_dists: Any = None,
    ) -> TopicModelData:
        if texts is None:
            raise ValidationError(
                "CTMAdapter.extract requires a `texts=` keyword argument "
                "(the list of input strings CTM was fitted on). The model "
                "does not store the original texts internally."
            )

        # ------------------------------------------------------------------
        # 1. Vocabulary. Try kwarg, then `model.train_data.idx2token`.
        # ------------------------------------------------------------------
        if vocabulary is None:
            vocabulary = self._discover_vocabulary(model)
        if not vocabulary:
            raise ValidationError(
                "Could not find CTM vocabulary. Pass `vocabulary=` "
                "explicitly or use a model whose `model.train_data.idx2token` "
                "is populated (the contextualized-topic-models PyPI package "
                "convention)."
            )
        vocab_list: list[str] = list(vocabulary)
        V = len(vocab_list)

        # ------------------------------------------------------------------
        # 2. Topic-term matrix.
        # ------------------------------------------------------------------
        if not hasattr(model, "get_topic_word_matrix"):
            raise ValidationError(
                "CTM model does not expose `get_topic_word_matrix()`. "
                "Are you using contextualized-topic-models >= 2.4? "
                "If you have a custom fork, subclass CTMAdapter and override "
                "`_topic_word_matrix(model)`."
            )
        topic_term = self._topic_word_matrix(model)
        topic_term = np.asarray(topic_term, dtype=np.float64)
        if topic_term.ndim != 2:
            raise ValidationError(
                f"CTM topic_word matrix must be 2-D, got shape {topic_term.shape}."
            )
        K, V_model = topic_term.shape
        if V_model != V:
            raise ValidationError(
                f"CTM topic_word matrix has {V_model} columns but vocabulary "
                f"has {V} terms. Check that you passed the same vocabulary "
                "the CTM model was fitted on."
            )

        # CTM's decoder output is already row-stochastic, but renormalize
        # cheaply against float roundoff and degenerate zero-rows.
        row_sums = topic_term.sum(axis=1, keepdims=True)
        zero_rows = (row_sums == 0).ravel()
        if zero_rows.any():
            logger.warning(
                "CTM adapter: %d topic(s) had all-zero word distribution; "
                "uniform fallback applied.",
                int(zero_rows.sum()),
            )
            topic_term[zero_rows] = 1.0
            row_sums[zero_rows] = float(V)
        topic_term = topic_term / row_sums

        # ------------------------------------------------------------------
        # 3. Term frequency + doc lengths via a CountVectorizer pinned to
        #    the SAME vocabulary CTM was fitted on.
        # ------------------------------------------------------------------
        vectorizer = CountVectorizer(vocabulary=vocab_list, token_pattern=r"(?u)\b\w+\b")
        X = vectorizer.transform(texts)
        term_frequency = np.asarray(X.sum(axis=0)).ravel().astype(np.float64)
        doc_lengths = np.asarray(X.sum(axis=1)).ravel().astype(np.int64)

        # ------------------------------------------------------------------
        # 4. Doc-topic matrix. We strongly prefer the caller to pass it
        #    in (see module docstring). Fall through to the model only if
        #    `get_doc_topic_distribution` exists and a CTMDataset is
        #    discoverable on the model -- a rare convenience.
        # ------------------------------------------------------------------
        N = len(texts)
        if doc_topic_dists is not None:
            dtd = _to_numpy(doc_topic_dists).astype(np.float64)
        else:
            dtd = self._doc_topic_matrix(model, N=N, K=K)
        if dtd.shape != (N, K):
            raise ValidationError(
                f"CTM doc_topic matrix has shape {dtd.shape}, expected ({N}, {K}). "
                "Pass `doc_topic_dists=` explicitly with the output of "
                "`model.get_doc_topic_distribution(your_dataset)`."
            )

        row_sums = dtd.sum(axis=1, keepdims=True)
        zero_doc_rows = (row_sums == 0).ravel()
        if zero_doc_rows.any():
            logger.warning(
                "CTM adapter: %d document(s) had all-zero topic mass; "
                "uniform fallback applied.",
                int(zero_doc_rows.sum()),
            )
            dtd[zero_doc_rows] = 1.0 / K
            row_sums[zero_doc_rows] = 1.0
        dtd = dtd / row_sums

        return TopicModelData(
            topic_term_dists=topic_term,
            doc_topic_dists=dtd,
            doc_lengths=doc_lengths,
            vocab=vocab_list,
            term_frequency=term_frequency,
        )

    # ------------------------------------------------------------------
    # Hooks for subclasses with non-standard CTM interfaces.
    # ------------------------------------------------------------------
    def _topic_word_matrix(self, model: Any) -> np.ndarray:
        return _to_numpy(model.get_topic_word_matrix())

    def _doc_topic_matrix(self, model: Any, *, N: int, K: int) -> np.ndarray:
        """Last-resort doc-topic recovery.

        We don't construct a ``CTMDataset`` here (it would require an
        SBERT model and a contextual-embedding pass). The expectation is
        that the caller passes ``doc_topic_dists=`` directly.
        """
        raise ValidationError(
            "CTM doc-topic matrix not provided. CTM requires a "
            "CTMDataset (with SBERT contextual embeddings) to compute "
            "doc-topic posteriors, which the adapter intentionally does "
            "not build for you. Compute it once with "
            "`doc_topic = ctm.get_doc_topic_distribution(your_dataset, n_samples=20)` "
            "and pass it as `doc_topic_dists=doc_topic`."
        )

    def _discover_vocabulary(self, model: Any) -> list[str] | None:
        """Walk the standard CTM attribute paths to find the vocab list."""
        train_data = getattr(model, "train_data", None)
        idx2token = getattr(train_data, "idx2token", None) if train_data else None
        if idx2token:
            # idx2token is a dict[int, str]; preserve index order.
            return [idx2token[i] for i in sorted(idx2token.keys())]
        # Some forks store it directly on the model.
        if hasattr(model, "vocabulary"):
            return list(model.vocabulary)
        return None
