"""Tests for :mod:`topicvisexplorer.models.registry`."""

from __future__ import annotations

import importlib.util

import pytest

from topicvisexplorer.errors import OptionalDependencyError
from topicvisexplorer.models.adapters.gensim_lda import GensimLDAAdapter
from topicvisexplorer.models.registry import get_adapter, list_adapters

_real_find_spec = importlib.util.find_spec


def test_get_adapter_gensim_returns_instance() -> None:
    a = get_adapter("gensim-lda")
    assert isinstance(a, GensimLDAAdapter)


def test_get_adapter_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown adapter"):
        get_adapter("not-a-real-adapter")
    with pytest.raises(ValueError, match="gensim-lda"):
        get_adapter("not-a-real-adapter")


def test_list_adapters_sorted() -> None:
    names = list_adapters()
    assert names == sorted(names)
    assert "gensim-lda" in names
    assert "bertopic" in names


def test_get_adapter_missing_optional_uses_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def _no_bertopic(name: str, package: str | None = None):  # type: ignore[no-untyped-def]
        if name == "bertopic":
            return None
        return _real_find_spec(name, package)

    import topicvisexplorer.models.registry as reg

    monkeypatch.setattr(reg, "find_spec", _no_bertopic)
    with pytest.raises(OptionalDependencyError, match="bertopic") as ei:
        get_adapter("bertopic")
    assert "topicvisexplorer[full]" in str(ei.value)
