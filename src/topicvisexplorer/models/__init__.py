"""Topic-model adapters.

Each adapter wraps a third-party topic model (gensim LDA, sklearn LDA,
sklearn NMF, BERTopic, CTM, ETM...) into the common shape consumed by
:func:`topicvisexplorer.prepare`. The shared interface is defined as a
:class:`TopicModelAdapter` Protocol so users can plug in their own
without subclassing.

Stable adapters in v1.0:

* :class:`GensimLDAAdapter` -- the paper's model, ported from
  ``gensim_helpers``.
* :class:`SklearnLDAAdapter`
* :class:`SklearnNMFAdapter`

Stub adapters (Protocol-conformant skeletons that raise
``NotImplementedError`` on extraction) shipped as scaffolding for v1.1:

* :class:`BERTopicAdapter`
* :class:`CTMAdapter`
* :class:`ETMAdapter`

The stubs let users subclass and override one method to ship their own
adapter without touching the core package.
"""

from __future__ import annotations

from .adapters.bertopic_stub import BERTopicAdapter
from .adapters.ctm_stub import CTMAdapter
from .adapters.etm_stub import ETMAdapter
from .adapters.gensim_lda import GensimLDAAdapter
from .adapters.sklearn_lda import SklearnLDAAdapter
from .adapters.sklearn_nmf import SklearnNMFAdapter
from .protocol import TopicModelAdapter, TopicModelData

__all__ = [
    "BERTopicAdapter",
    "CTMAdapter",
    "ETMAdapter",
    "GensimLDAAdapter",
    "SklearnLDAAdapter",
    "SklearnNMFAdapter",
    "TopicModelAdapter",
    "TopicModelData",
]
