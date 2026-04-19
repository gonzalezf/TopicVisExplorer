"""Adapter for :class:`sklearn.decomposition.NMF`.

NMF gives non-probabilistic topic-term and doc-topic *matrices*; we
row-normalize both into probability distributions before handing them
to :func:`topicvisexplorer.prepare`. This is the standard treatment in
the topic-modeling literature when displaying NMF results in LDAvis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ...errors import ValidationError
from ..protocol import TopicModelData

if TYPE_CHECKING:
    from sklearn.feature_extraction.text import TfidfVectorizer


class SklearnNMFAdapter:
    """Adapter for sklearn NMF with a fitted :class:`TfidfVectorizer`."""

    name = "sklearn-nmf"

    def extract(
        self,
        model: Any,
        corpus: Any,
        *,
        vectorizer: TfidfVectorizer | None = None,
    ) -> TopicModelData:
        if vectorizer is None:
            raise ValidationError(
                "SklearnNMFAdapter.extract requires a `vectorizer=` keyword "
                "argument (the fitted vectorizer that produced `corpus`)."
            )
        X = corpus
        components = model.components_
        components = np.maximum(components, 1e-12)
        topic_term_dists = components / components.sum(axis=1, keepdims=True)

        gamma = model.transform(X)
        gamma = np.maximum(gamma, 1e-12)
        row_sums = gamma.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        doc_topic_dists = gamma / row_sums

        doc_lengths = np.asarray(X.sum(axis=1)).ravel()
        term_frequency = np.asarray(X.sum(axis=0)).ravel()
        if X.dtype.kind == "f":
            doc_lengths = doc_lengths.astype(np.float64)
            term_frequency = term_frequency.astype(np.float64)
            term_frequency = np.maximum(term_frequency, 1e-12)
            doc_lengths = np.maximum(doc_lengths, 1e-12)
        vocab = list(vectorizer.get_feature_names_out())
        return TopicModelData(
            topic_term_dists=topic_term_dists,
            doc_topic_dists=doc_topic_dists,
            doc_lengths=doc_lengths,
            vocab=vocab,
            term_frequency=term_frequency,
        )
