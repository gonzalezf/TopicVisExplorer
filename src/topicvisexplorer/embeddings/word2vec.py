"""Word2Vec embedding backend.

This is the **paper-faithful default**. The training hyperparameters
match the paper (Section 4.1, "Word embedding model"):

==============  ===========
hyperparameter  value
==============  ===========
algorithm       CBOW (sg=0)
vector_size     300
window          5
negative        5
min_count       5
epochs          50
seed            42
==============  ===========

The class wraps gensim's :class:`gensim.models.KeyedVectors` so we can
also load *pre-trained* models (e.g. GoogleNews-300) in a single line.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np

from ..errors import Word2VecCorpusTooSmallError
from ..logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from gensim.models import KeyedVectors as _GensimKV
    from numpy.typing import NDArray

logger = get_logger(__name__)

#: Minimum number of documents required to train a useful CBOW model.
#: Below this we raise rather than silently producing degenerate vectors.
MIN_DOCS_FOR_FIT: Final[int] = 200


class Word2Vec:
    """Word2Vec embedding wrapper conforming to :class:`EmbeddingBackend`.

    Three ways to construct:

    * :meth:`fit` -- train CBOW on a tokenized corpus with paper config.
    * :meth:`from_path` -- load a pre-saved gensim ``KeyedVectors`` file.
    * :meth:`from_keyedvectors` -- adopt an existing in-memory KV.

    Examples
    --------
    >>> import topicvisexplorer as tve
    >>> emb = tve.embeddings.Word2Vec.fit(tokenized_docs)
    >>> emb["hospital"].shape
    (300,)
    """

    vector_size: int

    def __init__(self, kv: _GensimKV) -> None:
        self._kv = kv
        self.vector_size = int(kv.vector_size)

    @classmethod
    def fit(
        cls,
        tokenized_texts: Sequence[Sequence[str]],
        *,
        vector_size: int = 300,
        window: int = 5,
        negative: int = 5,
        min_count: int = 5,
        epochs: int = 50,
        seed: int = 42,
        workers: int = 1,
    ) -> Word2Vec:
        """Train a CBOW Word2Vec model with paper-faithful defaults.

        Parameters
        ----------
        tokenized_texts:
            A sequence of token lists (e.g. the output of
            :func:`topicvisexplorer.preprocessing.text_cleaner_batch`).
        workers:
            Defaults to 1 for **bit-reproducible** results - gensim
            multi-worker training is non-deterministic. Set higher only
            when you don't need exact reproducibility.

        Raises
        ------
        Word2VecCorpusTooSmallError
            If the corpus has fewer than :data:`MIN_DOCS_FOR_FIT`
            documents.
        """
        try:
            from gensim.models import Word2Vec as GensimWord2Vec
        except ImportError as exc:
            raise ImportError(
                "gensim is required for Word2Vec.fit. Install via: pip install topicvisexplorer"
            ) from exc

        n_docs = len(tokenized_texts)
        if n_docs < MIN_DOCS_FOR_FIT:
            raise Word2VecCorpusTooSmallError(n_docs, MIN_DOCS_FOR_FIT)

        logger.info(
            "Training Word2Vec (CBOW, %d-dim, %d epochs) on %d documents.",
            vector_size,
            epochs,
            n_docs,
        )
        model = GensimWord2Vec(
            sentences=list(tokenized_texts),
            vector_size=vector_size,
            window=window,
            negative=negative,
            min_count=min_count,
            epochs=epochs,
            sg=0,
            seed=seed,
            workers=workers,
        )
        return cls(model.wv)

    @classmethod
    def from_path(cls, path: str | Path, *, binary: bool | None = None) -> Word2Vec:
        """Load a serialized :class:`gensim.models.KeyedVectors` from disk.

        Auto-detects ``.bin`` vs ``.txt`` vs gensim native ``.kv`` based
        on suffix; pass ``binary=`` to override.
        """
        from gensim.models import KeyedVectors

        path = Path(path)
        if path.suffix == ".kv" or path.suffix == "":
            return cls(KeyedVectors.load(str(path)))
        is_binary = binary if binary is not None else path.suffix in {".bin", ".gz"}
        return cls(KeyedVectors.load_word2vec_format(str(path), binary=is_binary))

    @classmethod
    def from_keyedvectors(cls, kv: _GensimKV) -> Word2Vec:
        """Wrap an already-loaded :class:`gensim.models.KeyedVectors`."""
        return cls(kv)

    def save(self, path: str | Path) -> None:
        """Save the wrapped KeyedVectors so it can be reloaded later."""
        self._kv.save(str(path))

    def __contains__(self, word: str) -> bool:
        return word in self._kv

    def __getitem__(self, word: str) -> NDArray[np.float32]:
        return self._kv[word]

    def __repr__(self) -> str:
        return f"Word2Vec(vocab={len(self._kv):,}, vector_size={self.vector_size})"
