"""Registry of built-in topic-model adapter ids (``--model`` / BYO :attr:`byo_model`).

Maps short CLI strings to adapter classes. Optional heavy deps
(``bertopic``, ``embedded_topic_model``, ``contextualized_topic_models``) are
checked on lookup via :func:`get_adapter`.
"""

from __future__ import annotations

from importlib.util import find_spec

from ..errors import OptionalDependencyError
from .adapters.bertopic import BERTopicAdapter
from .adapters.ctm import CTMAdapter
from .adapters.etm import ETMAdapter
from .adapters.gensim_lda import GensimLDAAdapter
from .adapters.sklearn_lda import SklearnLDAAdapter
from .adapters.sklearn_nmf import SklearnNMFAdapter
from .protocol import TopicModelAdapter

ADAPTERS: dict[str, type] = {
    "gensim-lda": GensimLDAAdapter,
    "sklearn-lda": SklearnLDAAdapter,
    "sklearn-nmf": SklearnNMFAdapter,
    "bertopic": BERTopicAdapter,
    "etm": ETMAdapter,
    "ctm": CTMAdapter,
}

_REQUIRED_IMPORTS: dict[str, tuple[str, ...]] = {
    "bertopic": ("bertopic",),
    "etm": ("embedded_topic_model",),
    "ctm": ("contextualized_topic_models",),
}


def list_adapters() -> list[str]:
    """Sorted adapter ids (CLI ``--model`` values)."""
    return sorted(ADAPTERS)


def get_adapter(name: str) -> TopicModelAdapter:
    """Return a **new** adapter instance for ``name`` or raise a clear error."""
    if name not in ADAPTERS:
        raise ValueError(f"Unknown adapter {name!r}. Choose one of: {', '.join(list_adapters())}.")
    for mod in _REQUIRED_IMPORTS.get(name, ()):
        if find_spec(mod) is None:
            raise OptionalDependencyError(
                f"Adapter {name!r} requires the Python package '{mod}'. "
                f'Install with: pip install "topicvisexplorer[full]"'
            )
    return ADAPTERS[name]()


__all__ = ["ADAPTERS", "get_adapter", "list_adapters"]
