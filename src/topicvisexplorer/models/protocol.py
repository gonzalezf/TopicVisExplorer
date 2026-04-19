"""Protocol shared by every topic-model adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    import numpy as np


@dataclass
class TopicModelData:
    """Standardized output of any :class:`TopicModelAdapter.extract`.

    Mirrors the five inputs of :func:`topicvisexplorer.prepare`.
    """

    topic_term_dists: np.ndarray  # (K, V) row-stochastic
    doc_topic_dists: np.ndarray  # (N, K) row-stochastic
    doc_lengths: np.ndarray  # (N,) integer
    vocab: list[str]  # length V
    term_frequency: np.ndarray  # (V,) integer

    def __post_init__(self) -> None:
        K, V = self.topic_term_dists.shape
        N, K2 = self.doc_topic_dists.shape
        if K != K2:
            raise ValueError(
                f"K mismatch: topic_term_dists has {K} rows but doc_topic_dists has {K2} columns."
            )
        if len(self.vocab) != V:
            raise ValueError(f"vocab length {len(self.vocab)} != V={V}")
        if len(self.term_frequency) != V:
            raise ValueError(f"term_frequency length {len(self.term_frequency)} != V={V}")
        if len(self.doc_lengths) != N:
            raise ValueError(f"doc_lengths length {len(self.doc_lengths)} != N={N}")


@runtime_checkable
class TopicModelAdapter(Protocol):
    """Convert any topic model into a :class:`TopicModelData`."""

    name: str

    def extract(self, model: Any, corpus: Any, **kwargs: Any) -> TopicModelData:
        """Pull the five tensors out of ``model`` + ``corpus``."""
        ...
