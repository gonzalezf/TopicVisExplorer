"""Scenario registry: name -> loader callable -> :class:`Scenario`.

A *scenario* is the collection of artifacts the visualization needs to
render and respond to interactive operations:

* a :class:`~topicvisexplorer.PreparedData` (topic table + coordinates)
* the underlying :class:`TopicModelData` (raw distributions for split/merge)
* the per-document topic-contribution rows (``relevantDocumentsDict``)
* the topic similarity matrix dict ``omega -> ndarray``
* the layout dict ``omega -> [[x, y], ...]``
* the raw text strings (only required if the user can split topics)
* an optional embedding backend (only required for similarity recomputation)

The legacy app stored these as a per-IP dict of globals; we wrap them
in a typed dataclass so misuse fails fast with a readable error.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from ..errors import ValidationError
from ..logging import get_logger

if TYPE_CHECKING:
    from ..embeddings.protocol import EmbeddingBackend
    from ..models.protocol import TopicModelData
    from ..prepare import PreparedData

logger = get_logger(__name__)


@dataclass
class Scenario:
    """Bundle of state required to serve one visualization view.

    Either ``prepared``/``model_data`` etc. are populated (single-corpus
    mode), or the ``*_a``/``*_b`` pairs are populated (multi-corpus
    Sankey mode). ``is_multi`` distinguishes the two.
    """

    name: str
    is_multi: bool = False

    prepared: PreparedData | None = None
    model_data: TopicModelData | None = None
    relevant_documents: list[dict[str, Any]] = field(default_factory=list)
    similarity_matrix: dict[float, np.ndarray] = field(default_factory=dict)
    circle_positions: dict[float, list[list[float]]] = field(default_factory=dict)
    raw_texts: list[str] = field(default_factory=list)
    embedding: EmbeddingBackend | None = None

    prepared_b: PreparedData | None = None
    model_data_b: TopicModelData | None = None
    relevant_documents_b: list[dict[str, Any]] = field(default_factory=list)

    extras: dict[str, Any] = field(default_factory=dict)

    def require(self, attr: str) -> Any:
        """Return ``getattr(self, attr)`` or raise a clear error."""
        value = getattr(self, attr, None)
        if value is None or (hasattr(value, "__len__") and len(value) == 0):
            raise ValidationError(
                f"Scenario {self.name!r} is missing '{attr}'. "
                "The current operation cannot run on this scenario. "
                "Re-load it with the required artifacts populated."
            )
        return value


ScenarioLoader = Callable[[], Scenario]


class ScenarioRegistry:
    """Mapping of scenario name -> lazy loader callable.

    Loaders are zero-argument callables that return a fresh
    :class:`Scenario` each time they are invoked. Loading is lazy so
    booting the server is cheap even with many registered scenarios.
    """

    def __init__(self) -> None:
        self._loaders: dict[str, ScenarioLoader] = {}

    def register(self, name: str, loader: ScenarioLoader) -> None:
        if name in self._loaders:
            logger.warning("Re-registering scenario %r (was already present).", name)
        self._loaders[name] = loader

    def load(self, name: str) -> Scenario:
        if name not in self._loaders:
            raise ValidationError(
                f"Unknown scenario {name!r}. Available: {sorted(self._loaders) or '(none)'}."
            )
        return self._loaders[name]()

    def names(self) -> list[str]:
        return sorted(self._loaders)
