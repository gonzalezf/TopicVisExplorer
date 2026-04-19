"""Canonical text preprocessing pipeline.

The legacy codebase had **three** subtly different ``text_cleaner``
implementations - one inside ``_topic_similarity_matrix.py``, one inside
``calculate_topic_similarity.py``, and one inside
``official_notebooks/...``. They differed in punctuation, lemmatization
order, and whether ``unidecode`` was applied. We reconcile them here
into a single deterministic pipeline that is *exactly* the union of
``_topic_similarity_matrix.text_cleaner`` (the version used at runtime
by the live visualization). Golden-test fixtures verify this is byte-
identical for the synthetic corpus.

Pipeline (in order):

1. Drop digits (replace with space, *not* delete - paper-faithful).
2. Drop punctuation (replace with space).
3. Drop the literal ``#`` character (keep hashtag word).
4. Lowercase.
5. Strip diacritics via :mod:`unidecode`.
6. Tokenize with :class:`nltk.tokenize.TweetTokenizer`.
7. Drop English stopwords (NLTK list).
8. Lemmatize with spaCy ``en_core_web_sm`` keeping NOUN/ADJ/VERB/ADV.

spaCy is loaded lazily and cached process-wide so importing this module
does *not* eagerly load 50 MB of language data.
"""

from __future__ import annotations

import string
from collections.abc import Iterable
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from .errors import SpacyNotInstalledError
from .logging import get_logger

if TYPE_CHECKING:
    from spacy.language import Language

logger = get_logger(__name__)

_EXTRA_PUNCT = "¡¿<>'`\""
_PUNCTUATION = string.punctuation + _EXTRA_PUNCT
_DIGITS_TABLE = str.maketrans(string.digits, " " * len(string.digits))
_PUNCT_TABLE = str.maketrans(_PUNCTUATION, " " * len(_PUNCTUATION))
_HASHTAG_TABLE = str.maketrans("#", " ")
_ALLOWED_POS: frozenset[str] = frozenset({"NOUN", "ADJ", "VERB", "ADV"})


@lru_cache(maxsize=1)
def _get_spacy_nlp() -> Language:
    """Load and cache the spaCy English pipeline.

    Disables ``parser`` and ``ner`` (paper config) - we only need the
    tagger + lemmatizer.
    """
    try:
        import spacy
    except ImportError as exc:
        raise SpacyNotInstalledError(str(exc)) from exc
    try:
        return spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except OSError as exc:
        raise SpacyNotInstalledError(
            "en_core_web_sm not downloaded. Run: python -m spacy download en_core_web_sm"
        ) from exc


@lru_cache(maxsize=1)
def _get_stopwords() -> frozenset[str]:
    """Load NLTK English stopwords, downloading the corpus if missing."""
    try:
        from nltk.corpus import stopwords
    except ImportError as exc:
        raise ImportError("nltk is required. Install via: pip install topicvisexplorer") from exc
    try:
        return frozenset(stopwords.words("english"))
    except LookupError:
        logger.info("Downloading NLTK 'stopwords' corpus (~30 KB).")
        import nltk

        nltk.download("stopwords", quiet=True)
        return frozenset(stopwords.words("english"))


@lru_cache(maxsize=1)
def _get_tokenizer() -> Any:
    """Load and cache the NLTK :class:`TweetTokenizer` instance."""
    from nltk.tokenize import TweetTokenizer

    return TweetTokenizer()


def text_cleaner(text: str) -> list[str]:
    """Clean and tokenize one document, returning a list of lemmas.

    This is the public entry point used by both
    :mod:`topicvisexplorer.similarity.embedding` and the test fixtures.
    For batch use, prefer :func:`text_cleaner_batch`, which amortizes
    spaCy pipeline overhead.

    Parameters
    ----------
    text:
        Raw document text. Empty / whitespace-only input returns ``[]``.

    Returns
    -------
    list[str]
        Cleaned, lemmatized tokens.
    """
    if not text or not text.strip():
        return []

    text = text.translate(_DIGITS_TABLE)
    text = text.translate(_PUNCT_TABLE)
    text = text.translate(_HASHTAG_TABLE)
    text = text.lower()

    try:
        from unidecode import unidecode

        text = unidecode(text)
    except ImportError:
        logger.debug("unidecode not installed; skipping diacritic stripping.")

    tokens = _get_tokenizer().tokenize(text)
    stop = _get_stopwords()
    filtered = [t for t in tokens if t and t not in stop]
    if not filtered:
        return []

    nlp = _get_spacy_nlp()
    doc = nlp(" ".join(filtered))
    return [tok.lemma_ for tok in doc if tok.pos_ in _ALLOWED_POS]


def text_cleaner_batch(
    texts: Iterable[str], *, n_process: int = 1, batch_size: int = 64
) -> list[list[str]]:
    """Clean a batch of documents using spaCy's :meth:`Language.pipe`.

    For corpora >= a few hundred documents this is significantly faster
    than calling :func:`text_cleaner` in a loop because spaCy can amortize
    model warmup across documents.

    Parameters
    ----------
    texts:
        Raw documents.
    n_process:
        Number of parallel processes for the spaCy pipeline. Default 1
        (single-process) which is reproducible and works in notebooks.
        Set to ``-1`` to use all cores; this trades reproducibility for
        speed because spaCy multiprocessing reorders documents.
    batch_size:
        spaCy ``pipe`` batch size.

    Returns
    -------
    list[list[str]]
        One token list per input document, in input order.
    """
    materialized = [t or "" for t in texts]
    if not materialized:
        return []

    pre = []
    stop = _get_stopwords()
    tokenize = _get_tokenizer().tokenize
    try:
        from unidecode import unidecode
    except ImportError:
        unidecode = None  # type: ignore[assignment]

    for raw in materialized:
        if not raw.strip():
            pre.append("")
            continue
        text = raw.translate(_DIGITS_TABLE)
        text = text.translate(_PUNCT_TABLE)
        text = text.translate(_HASHTAG_TABLE)
        text = text.lower()
        if unidecode is not None:
            text = unidecode(text)
        tokens = [t for t in tokenize(text) if t and t not in stop]
        pre.append(" ".join(tokens))

    nlp = _get_spacy_nlp()
    out: list[list[str]] = []
    for doc in nlp.pipe(pre, batch_size=batch_size, n_process=n_process):
        out.append([tok.lemma_ for tok in doc if tok.pos_ in _ALLOWED_POS])
    return out
