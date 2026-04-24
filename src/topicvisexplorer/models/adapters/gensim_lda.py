"""Adapter for gensim ``LdaModel`` and gensim-compatible variants.

Ported from the legacy ``gensim_helpers._extract_data``. Algorithm is
unchanged - golden test fixes byte-equivalence with legacy output.

Compared to the legacy module:

* ``LdaMallet`` raises :class:`MalletPickleError` (not silently treated
  like a bare LdaModel - Mallet has subtly different topic_term shapes).
* ``HdpModel`` continues to work via the ``lda_beta``/``lda_alpha``
  attribute checks.
* No ``funcy`` dependency - we use a plain dict merge.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.sparse import issparse

from ...errors import MalletPickleError, ValidationError
from ...logging import get_logger
from ..protocol import TopicModelData

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class GensimLDAAdapter:
    """Adapter for any model exposing the gensim LDA interface."""

    name = "gensim-lda"

    def extract(
        self,
        model: Any,
        corpus: Any,
        *,
        dictionary: Any | None = None,
        doc_topic_dists: Any = None,
    ) -> TopicModelData:
        try:
            import gensim
        except ImportError as exc:
            raise ImportError(
                "gensim is required for GensimLDAAdapter. From a git clone, run "
                "`uv sync` or `pip install -e .` (see docs/installation-and-testing.md)."
            ) from exc

        if type(model).__name__ in {"LdaMallet", "MalletWrapper"}:
            raise MalletPickleError()
        if dictionary is None:
            raise ValidationError(
                "GensimLDAAdapter.extract requires a `dictionary=` keyword argument "
                "(the gensim Dictionary used to build `corpus`)."
            )

        if not gensim.matutils.ismatrix(corpus):
            corpus_csc = gensim.matutils.corpus2csc(corpus, num_terms=len(dictionary))
        else:
            corpus_csc = corpus
            corpus = gensim.matutils.Sparse2Corpus(corpus_csc)

        vocab = list(dictionary.token2id.keys())
        beta = 0.01
        fnames_argsort = np.asarray(list(dictionary.token2id.values()), dtype=np.int_)
        term_freqs = corpus_csc.sum(axis=1).A.ravel()[fnames_argsort]
        term_freqs[term_freqs == 0] = beta
        doc_lengths = corpus_csc.sum(axis=0).A.ravel()

        num_topics = len(model.lda_alpha) if hasattr(model, "lda_alpha") else model.num_topics

        if doc_topic_dists is None:
            if hasattr(model, "lda_beta"):
                gamma = model.inference(corpus)
            else:
                gamma, _ = model.inference(corpus)
            doc_topic_dists_arr = gamma / gamma.sum(axis=1)[:, None]
        else:
            if isinstance(doc_topic_dists, list):
                doc_topic_dists_arr = gensim.matutils.corpus2dense(doc_topic_dists, num_topics).T
            elif issparse(doc_topic_dists):
                doc_topic_dists_arr = np.asarray(doc_topic_dists.T.todense())
            else:
                doc_topic_dists_arr = np.asarray(doc_topic_dists)
            doc_topic_dists_arr = doc_topic_dists_arr / doc_topic_dists_arr.sum(
                axis=1, keepdims=True
            )

        topic = model.lda_beta if hasattr(model, "lda_beta") else model.state.get_lambda()
        topic = topic / topic.sum(axis=1)[:, None]
        topic_term_dists = topic[:, fnames_argsort]

        return TopicModelData(
            topic_term_dists=np.asarray(topic_term_dists),
            doc_topic_dists=np.asarray(doc_topic_dists_arr),
            doc_lengths=np.asarray(doc_lengths),
            vocab=vocab,
            term_frequency=np.asarray(term_freqs),
        )
