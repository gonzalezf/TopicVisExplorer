"""User-driven topic refinement operations.

These are the four interactive actions the visualization exposes:

* :func:`split` -- split a topic into ``k_new`` sub-topics (paper Section
  4.2). The hot path; vectorized version is ~10-20x the legacy speed.
* :func:`merge` -- merge two topics into one (paper Section 4.2).
* :func:`add_remove_word` -- add or remove a single word from a topic's
  representation (paper Section 6, future work; now implemented).
* :func:`exclude_document` -- remove a document from one topic's
  contribution (paper Section 6, future work; now implemented).

All four return a freshly computed :class:`PreparedData` so the front
end can swap in the new visualization atomically.
"""

from __future__ import annotations

from .add_remove_word import add_word, remove_word
from .exclude_document import exclude_document
from .merge import merge
from .refit_helpers import refit_gensim_lda, refit_lda, refit_static
from .split import split

__all__ = [
    "add_word",
    "exclude_document",
    "merge",
    "refit_gensim_lda",
    "refit_lda",
    "refit_static",
    "remove_word",
    "split",
]
