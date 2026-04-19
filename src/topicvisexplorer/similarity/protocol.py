"""Common Protocol for any topic-similarity metric.

A metric takes two :class:`PreparedData` objects (one per corpus, or
two views of the same corpus for split/merge operations) plus optional
hyperparameters and returns a ``(K1, K2)`` matrix of similarities in
``[0, 1]`` (1 = identical, 0 = completely dissimilar).

Implementations should be **stateless** so a single instance can be
reused across many calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import numpy as np

    from ..prepare import PreparedData


@runtime_checkable
class SimilarityMetric(Protocol):
    """Compute a topic-vs-topic similarity matrix between two corpora."""

    name: str

    def __call__(
        self,
        prepared_a: PreparedData,
        prepared_b: PreparedData,
        /,
    ) -> np.ndarray:
        """Return a ``(K_a, K_b)`` similarity matrix."""
        ...
