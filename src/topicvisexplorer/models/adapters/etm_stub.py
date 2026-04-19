"""Stub adapter for Embedded Topic Models (Dieng et al. 2020)."""

from __future__ import annotations

from typing import Any

from ..protocol import TopicModelData


class ETMAdapter:
    """Stub adapter for the Embedded Topic Model.

    ETM jointly learns topic-word and word embedding spaces; the natural
    integration is to *also* expose its word embeddings as a default
    ``EmbeddingBackend`` so the similarity metric and the topic model
    share an embedding space. That cross-cutting design lands in v1.1.
    """

    name = "etm"

    def extract(self, model: Any, corpus: Any, **kwargs: Any) -> TopicModelData:
        raise NotImplementedError(
            "ETM support is scheduled for v1.1. Subclass ETMAdapter and "
            "override .extract() to use it today."
        )
