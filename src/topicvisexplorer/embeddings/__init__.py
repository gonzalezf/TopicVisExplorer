"""Pluggable word-embedding backends.

The :class:`EmbeddingBackend` Protocol defines the minimal interface
that the similarity metric (paper Eq. 7-9) needs:

* ``__contains__(word) -> bool`` to skip OOV terms cheaply.
* ``__getitem__(word) -> ndarray`` to get a fixed-dim vector.
* ``vector_size`` for sanity checks.

Two concrete backends ship with TopicVisExplorer:

* :class:`Word2Vec` - the **paper-faithful default**. CBOW, 300-dim,
  trained on the corpus with ``window=5, negative=5, min_count=5,
  epochs=50, seed=42``.
* :class:`SBERT` - opt-in alternative using ``sentence-transformers``.
  This is a *sentence-level approximation* of the paper's word-level
  metric: we encode each candidate term as a sentence, which is what
  the popular ``all-MiniLM-L6-v2`` model is trained for. Empirically
  similarities are highly correlated with Word2Vec but **not byte-
  identical**, so paper-figure reproduction must use Word2Vec.

Add your own by implementing the Protocol; no registration needed::

    class MyBackend:
        vector_size = 768
        def __contains__(self, word): ...
        def __getitem__(self, word): ...

    tve.prepare(..., embeddings=MyBackend())
"""

from __future__ import annotations

from .protocol import EmbeddingBackend
from .sbert import SBERT
from .word2vec import Word2Vec

__all__ = ["SBERT", "EmbeddingBackend", "Word2Vec"]
