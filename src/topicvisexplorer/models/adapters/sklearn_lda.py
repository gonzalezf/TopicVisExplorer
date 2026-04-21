"""Adapter for :class:`sklearn.decomposition.LatentDirichletAllocation`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ...errors import ValidationError
from ..protocol import TopicModelData

if TYPE_CHECKING:
    from sklearn.feature_extraction.text import CountVectorizer


class SklearnLDAAdapter:
    """Adapter for sklearn LDA with a fitted :class:`CountVectorizer`."""

    name = "sklearn-lda"

    def extract(
        self,
        model: Any,
        corpus: Any,
        *,
        vectorizer: CountVectorizer | None = None,
    ) -> TopicModelData:
        if vectorizer is None:
            raise ValidationError(
                "SklearnLDAAdapter.extract requires a `vectorizer=` keyword "
                "argument (the fitted CountVectorizer that produced `corpus`)."
            )
        X = corpus
        components = model.components_
        topic_term_dists = components / components.sum(axis=1, keepdims=True)
        gamma = model.transform(X)
        doc_topic_dists = gamma / gamma.sum(axis=1, keepdims=True)
        doc_lengths = np.asarray(X.sum(axis=1)).ravel()
        term_frequency = np.asarray(X.sum(axis=0)).ravel()
        vocab = list(vectorizer.get_feature_names_out())
        return TopicModelData(
            topic_term_dists=np.asarray(topic_term_dists),
            doc_topic_dists=np.asarray(doc_topic_dists),
            doc_lengths=doc_lengths,
            vocab=vocab,
            term_frequency=term_frequency,
        )
