"""Unit tests for :mod:`topicvisexplorer.errors`.

We assert that every custom exception's message is *actionable* (i.e.
contains a ``pip install`` hint, file path, or follow-up command).
"""

from __future__ import annotations

from topicvisexplorer import errors


def test_sbert_error_message_actionable() -> None:
    err = errors.SBERTNotInstalledError()
    assert "pip install" in str(err)
    assert "topicvisexplorer[full]" in str(err)


def test_hf_error_message_actionable() -> None:
    err = errors.HuggingFaceNotInstalledError()
    assert "[hf]" in str(err)


def test_word2vec_too_small_includes_counts() -> None:
    err = errors.Word2VecCorpusTooSmallError(n_docs=10, min_required=200)
    msg = str(err)
    assert "10" in msg and "200" in msg
    assert "SBERT" in msg


def test_mallet_error_explains_alternatives() -> None:
    err = errors.MalletPickleError()
    assert "legacy" in str(err)
    assert "migrate_pickle" in str(err)


def test_validation_error_is_value_error() -> None:
    assert issubclass(errors.ValidationError, ValueError)


def test_golden_mismatch_carries_context() -> None:
    err = errors.GoldenMismatchError("foo", "bar", 1e-3, 1e-6)
    assert err.fixture == "foo"
    assert err.field == "bar"
    assert "1.000e-03" in str(err)


def test_all_errors_inherit_base() -> None:
    base = errors.TopicVisExplorerError
    for cls in [
        errors.ValidationError,
        errors.SBERTNotInstalledError,
        errors.HuggingFaceNotInstalledError,
        errors.SpacyNotInstalledError,
        errors.MalletPickleError,
        errors.Word2VecCorpusTooSmallError,
        errors.GoldenMismatchError,
    ]:
        assert issubclass(cls, base), cls
