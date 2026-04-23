"""Custom exceptions for TopicVisExplorer.

Every exception below follows the *"tell users what to do, not what went
wrong"* rule: the message includes the exact remedial action (which pip
extra to install, which file to inspect, which legacy branch to check
out, etc.).

This module has zero imports from third-party packages so it can be
imported safely from anywhere in the codebase, including from optional
extras' import-error fallbacks.
"""

from __future__ import annotations


class TopicVisExplorerError(Exception):
    """Base class for all errors raised inside the public API."""


class ValidationError(TopicVisExplorerError, ValueError):
    """Inputs to a public function were structurally invalid.

    Use this (not bare ``ValueError``) so library callers can catch
    TopicVisExplorer-originated input failures distinctly.
    """


class OptionalDependencyError(TopicVisExplorerError, ImportError):
    """A topic-model adapter or optional integration requires a missing package.

    The message should include a concrete ``pip install "topicvisexplorer[...]"`` line.
    """


class SBERTNotInstalledError(TopicVisExplorerError, ImportError):
    """The ``sentence-transformers`` extra is required but not installed.

    Raised by :class:`topicvisexplorer.embeddings.SBERT` on construction.
    The remedial install command is in the message.
    """

    def __init__(self) -> None:
        super().__init__(
            "sentence-transformers is required for the SBERT embedding backend. "
            "Install it via: pip install 'topicvisexplorer[full]'\n"
            "Note: SBERT is a sentence-level approximation of the paper's "
            "word-level metric; for paper-faithful results use the default "
            "Word2Vec backend (tve.embeddings.Word2Vec.fit(texts))."
        )


class HuggingFaceNotInstalledError(TopicVisExplorerError, ImportError):
    """The ``datasets`` / ``huggingface-hub`` extra is required."""

    def __init__(self) -> None:
        super().__init__(
            "Hugging Face integration requires the [hf] extra. "
            "Install via: pip install 'topicvisexplorer[hf]'"
        )


class SpacyNotInstalledError(TopicVisExplorerError, ImportError):
    """The ``spacy`` + ``en_core_web_sm`` model is required for the canonical
    text cleaner but not available."""

    def __init__(self, detail: str = "") -> None:
        msg = (
            "spaCy + en_core_web_sm is required for the canonical text "
            "cleaner. Install via: pip install 'topicvisexplorer[full]' "
            "&& python -m spacy download en_core_web_sm"
        )
        if detail:
            msg = f"{msg}\nUnderlying error: {detail}"
        super().__init__(msg)


class MalletPickleError(TopicVisExplorerError):
    """Mallet-fit topic models are not supported in v1.0+.

    Raised when an adapter detects a ``LdaMallet`` instance (or a pickle
    that contains one).
    """

    def __init__(self) -> None:
        super().__init__(
            "Mallet pickles are not supported in v1.0+ of TopicVisExplorer. "
            "Either:\n"
            "  1. Check out the legacy branch (git checkout legacy) for the "
            "paper-version code, or\n"
            "  2. Re-fit your topics with gensim LDA - see "
            "scripts/migrate_pickle.py for an automated converter."
        )


class Word2VecCorpusTooSmallError(TopicVisExplorerError):
    """The corpus passed to ``Word2Vec.fit`` is too small to learn useful
    word vectors.

    Word2Vec needs at least a few hundred documents and a vocabulary
    larger than ``min_count`` to produce embeddings that the similarity
    metric can use meaningfully. Below that, the embeddings collapse and
    the similarity matrix becomes degenerate.
    """

    def __init__(self, n_docs: int, min_required: int) -> None:
        super().__init__(
            f"Word2Vec needs >= {min_required} documents to train usefully "
            f"(got {n_docs}). Either:\n"
            "  1. Pass a pre-trained model: "
            "embeddings=tve.embeddings.Word2Vec.from_path('vectors.kv'), or\n"
            "  2. Fall back to the SBERT approximation: "
            "embeddings=tve.embeddings.SBERT() (requires the [full] extra)."
        )


class GoldenMismatchError(TopicVisExplorerError, AssertionError):
    """Test-time helper raised by ``assert_close_to_golden`` when a golden
    fixture does not match the modernized output within tolerance.

    Carries enough context (which fixture, which field, max abs diff) so
    CI logs are diagnostic without needing to download artifacts.
    """

    def __init__(self, fixture: str, field: str, max_abs_diff: float, tol: float) -> None:
        super().__init__(
            f"Golden mismatch in {fixture}: field {field!r} "
            f"differs by {max_abs_diff:.3e} (tolerance {tol:.3e}). "
            f"Either fix the regression or re-capture the golden via "
            f"scripts/capture_golden.py in a dedicated PR."
        )
        self.fixture = fixture
        self.field = field
        self.max_abs_diff = max_abs_diff
        self.tol = tol
