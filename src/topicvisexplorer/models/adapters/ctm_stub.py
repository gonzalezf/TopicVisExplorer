"""Stub adapter for Contextualized Topic Models (Bianchi et al. 2021).

Ships as a Protocol-conformant skeleton; subclass to use today.
"""

from __future__ import annotations

from typing import Any

from ..protocol import TopicModelData


class CTMAdapter:
    """Stub adapter for Contextualized Topic Models.

    CTM exposes ``get_topics()`` returning a ``(K, V)`` distribution and
    ``get_doc_topic_distribution(testset)`` returning ``(N, K)``, so the
    eventual adapter is a thin wrapper. We're deferring the official
    implementation to v1.1 to avoid pinning the entire ``contextualized
    -topic-models`` dependency tree (PyTorch + transformers + scipy<1.10)
    on every install.
    """

    name = "ctm"

    def extract(self, model: Any, corpus: Any, **kwargs: Any) -> TopicModelData:
        raise NotImplementedError(
            "CTM support is scheduled for v1.1. Subclass CTMAdapter and "
            "override .extract() to use it today."
        )
