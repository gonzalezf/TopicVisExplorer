"""TopicVisExplorer - interactive topic-modeling visualization for splitting,
merging, and comparing topics across one or more corpora.

The public API mirrors pyLDAvis with extensions for multi-corpus comparison
and topic refinement::

    import topicvisexplorer as tve

    prepared = tve.prepare(model, corpus, dictionary, texts)
    tve.show(prepared)                     # opens a browser tab on localhost
    tve.show([prepared_a, prepared_b])     # multi-corpus Sankey
    tve.save_html(prepared, "out.html")    # static export
    tve.demo()                             # bundled tiny demo corpus

See :class:`topicvisexplorer.PreparedData` for the data model.
"""

from __future__ import annotations

from . import embeddings, errors, models, similarity
from ._version import __version__
from .logging import configure_logging, get_logger
from .prepare import PreparedData, load, prepare

__all__ = [
    "PreparedData",
    "__version__",
    "configure_logging",
    "embeddings",
    "errors",
    "get_logger",
    "load",
    "models",
    "prepare",
    "similarity",
]
