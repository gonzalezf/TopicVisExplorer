"""Protocol shared by every embedding backend.

Kept in its own module so concrete backends can import it without
pulling each other in (and so user-defined backends in third-party
packages can ``from topicvisexplorer.embeddings import EmbeddingBackend``
without paying any sentence-transformers / spaCy import cost).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from numpy.typing import NDArray


@runtime_checkable
class EmbeddingBackend(Protocol):
    """Minimal interface the similarity metric needs from an embedding."""

    vector_size: int

    def __contains__(self, word: str) -> bool:
        """Return True if the backend has a vector for ``word``."""
        ...

    def __getitem__(self, word: str) -> NDArray:
        """Return the embedding vector for ``word``.

        Raises ``KeyError`` for OOV terms; callers must guard with
        ``__contains__`` first (the similarity loops do this).
        """
        ...
