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
* :class:`BERTopicAdapter` -- contextualized topic model (Grootendorst
  2022); requires ``pip install 'topicvisexplorer[full]'``. Delivers
  paper Section 6 future work.
* :class:`ETMAdapter` -- embedded topic model (Dieng, Ruiz & Blei 2020);
  duck-typed against the ``embedded_topic_model`` PyPI package and the
  original Dieng PyTorch reference implementation. Delivers paper
  Section 6 future work.
* :class:`CTMAdapter` -- contextualized topic model (Bianchi, Terragni &
  Hovy 2021); duck-typed against the ``contextualized-topic-models``
  PyPI package. Delivers paper Section 6 future work.

No stub adapters remain in v1.0; every model named in the paper's
Section 6 future-work list ships as a real, tested implementation.
"""

from __future__ import annotations

from .adapters.bertopic import BERTopicAdapter
from .adapters.ctm import CTMAdapter
from .adapters.etm import ETMAdapter
from .adapters.gensim_lda import GensimLDAAdapter
from .adapters.sklearn_lda import SklearnLDAAdapter
from .adapters.sklearn_nmf import SklearnNMFAdapter
from .protocol import TopicModelAdapter, TopicModelData
from .registry import ADAPTERS, get_adapter, list_adapters

__all__ = [
    "ADAPTERS",
    "BERTopicAdapter",
    "CTMAdapter",
    "ETMAdapter",
    "GensimLDAAdapter",
    "SklearnLDAAdapter",
    "SklearnNMFAdapter",
    "TopicModelAdapter",
    "TopicModelData",
    "get_adapter",
    "list_adapters",
]
