"""Adapter for the Embedded Topic Model (Dieng, Ruiz & Blei 2020).

Delivers paper Section 6 future work: "future versions could integrate
[...] embedded topic models such as ETM (Dieng et al. 2020)" verbatim.

Mapping ETM to the LDAvis contract
----------------------------------
ETM is a generative model where each topic is a vector in the same
embedding space as words; the per-topic word distribution is recovered
as ``softmax(alpha_k · rho)`` where ``alpha_k`` is the k-th topic
embedding and ``rho`` is the word-embedding matrix. The model already
produces row-stochastic ``topic_term_dists`` (after the softmax) and
``doc_topic_dists`` (the ``theta`` variational posterior), so unlike
the BERTopic adapter we do **not** have to rescale anything to fit the
LDAvis contract -- the matrices are already in the right shape.

Supported model interfaces
--------------------------
We duck-type two flavours of "ETM model":

1. **embedded_topic_model package** (https://github.com/lffloyd/
   embedded-topic-model, the de-facto sklearn-style PyPI implementation):
   exposes ``vocabulary``, ``get_topic_word_matrix()`` and
   ``get_document_topic_dist()``.

2. **Original Dieng et al. PyTorch implementation**
   (https://github.com/adjidieng/ETM): exposes ``rho``, ``alphas``, and
   ``get_beta()`` / ``get_theta(bows)`` that return torch tensors. The
   adapter accepts these and converts to numpy.

If your fork uses a third interface, subclass and override
:meth:`_topic_word_matrix` and :meth:`_doc_topic_matrix`.
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
    """Convert torch tensors / lists / sparse matrices to a dense ``np.ndarray``.

    ETM's reference implementation lives in PyTorch, so the natural
    return type of ``get_beta()`` is a ``torch.Tensor`` carrying a
    grad-tracking node. We detach + cpu + numpy when applicable and
    fall back to ``np.asarray`` for everything else.
    """
    if x is None:
        return np.asarray([])
    if hasattr(x, "detach") and hasattr(x, "cpu"):
        # Looks like a torch.Tensor.
        return x.detach().cpu().numpy()
    if hasattr(x, "toarray"):
        return x.toarray()
    return np.asarray(x)


class ETMAdapter:
    """Adapter for a fitted ETM model.

    Parameters to :meth:`extract`:

    * ``model``: fitted ETM. Must expose **either**:
       - ``get_topic_word_matrix()`` returning shape ``(K, V)`` (the
         ``embedded_topic_model`` package), or
       - ``get_beta()`` returning shape ``(K, V)`` (the original Dieng
         PyTorch repo, ``Tensor`` is fine).
    * ``corpus``: ignored; ETM's preprocessing is opaque to us. Pass
      whatever you like for API symmetry with the gensim adapter.

    Required kwargs:

    * ``texts``: original list of input strings. Used to compute term
      frequency and document lengths consistent with ``vocabulary``.

    Optional kwargs:

    * ``vocabulary``: the term list ETM was fitted on. If omitted, we
      look it up at ``model.vocabulary`` (the
      ``embedded_topic_model`` convention) or raise.
    * ``doc_topic_dists``: precomputed ``(N, K)`` matrix. If omitted we
      try ``model.get_document_topic_dist()``, then
      ``model.get_theta(bows)`` (with ``bows`` constructed from
      ``texts``), then fall back to ``ValidationError``.
    """

    name = "etm"

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
                "ETMAdapter.extract requires a `texts=` keyword argument "
                "(the list of input strings ETM was fitted on). The model "
                "does not store the original documents internally, so we "
                "cannot recover them automatically."
            )

        # ------------------------------------------------------------------
        # 1. Vocabulary. Prefer kwarg, fall back to ``model.vocabulary``.
        # ------------------------------------------------------------------
        if vocabulary is None:
            vocabulary = getattr(model, "vocabulary", None)
        if not vocabulary:
            raise ValidationError(
                "Could not find ETM vocabulary. Pass `vocabulary=` "
                "explicitly or use a model that exposes `model.vocabulary` "
                "(e.g. the `embedded_topic_model` PyPI package)."
            )
        vocab_list: list[str] = list(vocabulary)
        V = len(vocab_list)

        # ------------------------------------------------------------------
        # 2. Topic-term matrix. Already row-stochastic out of softmax(alpha rho^T).
        # ------------------------------------------------------------------
        topic_term = self._topic_word_matrix(model)
        topic_term = np.asarray(topic_term, dtype=np.float64)
        if topic_term.ndim != 2:
            raise ValidationError(
                f"ETM topic_word matrix must be 2-D, got shape {topic_term.shape}."
            )
        K, V_model = topic_term.shape
        if V_model != V:
            raise ValidationError(
                f"ETM topic_word matrix has {V_model} columns but vocabulary "
                f"has {V} terms. Did you pass the wrong vocabulary?"
            )

        # Defensive renormalize: the reference implementation already
        # returns rows that sum to ~1, but float roundoff and any custom
        # post-processing can leave slack. Cheap to make exact.
        row_sums = topic_term.sum(axis=1, keepdims=True)
        zero_rows = (row_sums == 0).ravel()
        if zero_rows.any():
            logger.warning(
                "ETM adapter: %d topic(s) have an all-zero word distribution; "
                "assigning uniform fallback.",
                int(zero_rows.sum()),
            )
            topic_term[zero_rows] = 1.0
            row_sums[zero_rows] = float(V)
        topic_term = topic_term / row_sums

        # ------------------------------------------------------------------
        # 3. Term frequency + doc lengths via a CountVectorizer pinned to
        #    the SAME vocabulary ETM was fitted on. Using a fixed
        #    ``vocabulary=`` argument makes the vectorizer skip its own
        #    fitting and just count occurrences over our term list.
        # ------------------------------------------------------------------
        # ``token_pattern`` matches single chars too (ETM corpora often
        # have a stop-word list that left some short tokens in vocab).
        vectorizer = CountVectorizer(vocabulary=vocab_list, token_pattern=r"(?u)\b\w+\b")
        X = vectorizer.transform(texts)
        term_frequency = np.asarray(X.sum(axis=0)).ravel().astype(np.float64)
        doc_lengths = np.asarray(X.sum(axis=1)).ravel().astype(np.int64)

        # ------------------------------------------------------------------
        # 4. Doc-topic matrix. Caller > model attr > model method > error.
        # ------------------------------------------------------------------
        N = len(texts)
        if doc_topic_dists is not None:
            dtd = _to_numpy(doc_topic_dists).astype(np.float64)
        else:
            dtd = self._doc_topic_matrix(model, X=X, N=N)
        if dtd.shape != (N, K):
            raise ValidationError(
                f"ETM doc_topic matrix has shape {dtd.shape}, expected ({N}, {K}). "
                "Pass `doc_topic_dists=` explicitly to override."
            )

        row_sums = dtd.sum(axis=1, keepdims=True)
        zero_doc_rows = (row_sums == 0).ravel()
        if zero_doc_rows.any():
            logger.warning(
                "ETM adapter: %d document(s) have all-zero topic mass; "
                "assigning uniform fallback.",
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
    # Hooks for subclasses with non-standard ETM interfaces.
    # ------------------------------------------------------------------
    def _topic_word_matrix(self, model: Any) -> np.ndarray:
        """Return the (K, V) row-stochastic topic-term matrix.

        Tries the ``embedded_topic_model`` package interface first
        (``get_topic_word_matrix``), then the original Dieng repo's
        ``get_beta`` (which already exponentiates inside the model).
        """
        if hasattr(model, "get_topic_word_dist"):
            return _to_numpy(model.get_topic_word_dist())
        if hasattr(model, "get_topic_word_matrix"):
            raw = model.get_topic_word_matrix()
            twm = _to_numpy(raw)
            if twm.ndim == 2:
                return twm
        if hasattr(model, "get_beta"):
            beta = _to_numpy(model.get_beta())
            # ``get_beta`` already returns probabilities (the softmax is
            # applied inside the forward pass). Some forks return logits;
            # detect and exponentiate. A safe heuristic is to check
            # whether any value is negative.
            if (beta < 0).any():
                # logits -> softmax
                beta = beta - beta.max(axis=1, keepdims=True)
                beta = np.exp(beta)
                beta = beta / beta.sum(axis=1, keepdims=True)
            return beta
        raise ValidationError(
            "ETM model does not expose `get_topic_word_matrix()` or "
            "`get_beta()`. Subclass ETMAdapter and override "
            "`_topic_word_matrix(model)` to return a (K, V) array."
        )

    def _doc_topic_matrix(self, model: Any, *, X: Any, N: int) -> np.ndarray:
        """Return the (N, K) row-stochastic document-topic matrix."""
        if hasattr(model, "get_document_topic_dist"):
            return _to_numpy(model.get_document_topic_dist()).astype(np.float64)
        if hasattr(model, "get_theta"):
            # Original Dieng PyTorch repo: get_theta expects a bow tensor.
            try:
                import torch  # local import; only needed on this branch
            except ImportError:
                # Pass numpy and hope; some forks accept it.
                return _to_numpy(model.get_theta(X.toarray())).astype(np.float64)
            bows = torch.from_numpy(X.toarray().astype(np.float32))
            theta, _ = model.get_theta(bows)
            return _to_numpy(theta).astype(np.float64)
        raise ValidationError(
            "ETM model does not expose `get_document_topic_dist()` or "
            "`get_theta(bows)`. Pass `doc_topic_dists=` explicitly, or "
            "subclass ETMAdapter and override `_doc_topic_matrix`."
        )
