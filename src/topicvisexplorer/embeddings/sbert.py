"""Sentence-BERT embedding backend (opt-in).

This is a **sentence-level approximation** of the paper's word-level
metric. We encode each query word as a single-token "sentence" using
:mod:`sentence_transformers`. Empirically this gives similarities
that are highly correlated with Word2Vec on every benchmark we ran,
but the absolute values *do* differ - so paper-figure reproduction
should always use the default :class:`Word2Vec` backend.

Why sentence-level for a word-level metric?
-------------------------------------------
Most modern embedding models are trained on sentence pairs (e.g.
NLI / STS). Their token-level representations are not optimized for
similarity comparisons, but their pooled sentence vectors are. By
encoding a single word as a sentence we get the best available proxy
for "what does this word mean in this model's space".

The class implements an LRU cache over single-word encodings because
the similarity metric (Eq. 7-9) calls the encoder *many* times for the
same words across topics.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from ..errors import SBERTNotInstalledError
from ..logging import get_logger

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)


class SBERT:
    """Sentence-BERT embedding wrapper conforming to :class:`EmbeddingBackend`.

    Parameters
    ----------
    model_name:
        Any model identifier accepted by :class:`SentenceTransformer`.
        ``all-MiniLM-L6-v2`` is the default (small, fast, high-quality).
    device:
        ``"cpu"``, ``"cuda"``, or ``None`` to auto-detect.
    cache_size:
        Maximum number of word-vector cache entries. Set to ``None`` for
        unbounded (uses ``functools.lru_cache(maxsize=None)``).
    """

    vector_size: int

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        *,
        device: str | None = None,
        cache_size: int | None = 100_000,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise SBERTNotInstalledError() from exc

        logger.info("Loading SBERT model %r on %s.", model_name, device or "auto")
        self._model: SentenceTransformer = SentenceTransformer(model_name, device=device)
        self.vector_size = int(self._model.get_sentence_embedding_dimension())
        self._encode = lru_cache(maxsize=cache_size)(self._encode_uncached)

    def _encode_uncached(self, word: str) -> tuple[float, ...]:
        vec = self._model.encode(word, show_progress_bar=False, normalize_embeddings=False)
        return tuple(float(x) for x in vec)

    def __contains__(self, word: str) -> bool:
        return bool(word) and isinstance(word, str)

    def __getitem__(self, word: str) -> NDArray[np.float32]:
        return np.asarray(self._encode(word), dtype=np.float32)

    def __repr__(self) -> str:
        return f"SBERT(model={self._model._first_module()!r}, vector_size={self.vector_size})"
