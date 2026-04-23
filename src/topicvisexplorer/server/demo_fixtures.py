"""Generalized loader for real-corpus demo fixtures.

Both ``20ng_tiny`` and ``bbc_tiny`` (and any future fixture-backed
single-corpus scenario) share the same on-disk layout:

* ``src/topicvisexplorer/server/fixtures/<stem>.npz``    — numpy tensors
* ``src/topicvisexplorer/server/fixtures/<stem>_vocab.npy`` — vocabulary
* ``src/topicvisexplorer/server/fixtures/<stem>_texts.json`` — raw texts

This module reads those files and produces a full single-corpus
:class:`~topicvisexplorer.server.scenarios.Scenario` with an
Omega-varying embedding-based similarity sweep (paper Eq. 7-9), circle
positions, and a Gensim-backed ``refit`` attached under ``extras``. On
small corpora or when ``gensim`` is unavailable we fall back to a flat
Jensen-Shannon sweep so the page still renders.

The legacy :mod:`topicvisexplorer.server.demo_20ng` module is kept as a
compatibility shim that re-exports the symbols below.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from ..errors import Word2VecCorpusTooSmallError
from ..logging import get_logger
from ..models.protocol import TopicModelData
from ..operations.refit_helpers import refit_gensim_lda
from ..prepare import prepare
from ..similarity.baselines import JensenShannonSimilarity
from .scenarios import Scenario

if TYPE_CHECKING:
    from ..embeddings.protocol import EmbeddingBackend

logger = get_logger(__name__)

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

#: Default location for cached Word2Vec embeddings. Mirrors
#: :data:`topicvisexplorer.server.byo_corpus.DEFAULT_CACHE`.
TVE_CACHE_DIR = Path(
    os.environ.get("TVE_CACHE_DIR", Path.home() / ".cache" / "topicvisexplorer")
)

#: Suffix for cached Word2Vec KeyedVectors, embedding our "recipe version".
#: **Bump ``_v1`` -> ``_v2`` whenever the light tokenizer, seed, or
#: Word2Vec hyperparameters in :func:`_train_or_load_embedding` change.**
#: Stale caches silently produce wrong similarity (different vectors ->
#: different topic layouts); there is no runtime detection because the
#: KeyedVectors file does not record the training recipe.
_W2V_CACHE_SUFFIX = "_w2v_v1.kv"

#: Env var test/CI escape hatch. When set to ``"1"``,
#: :func:`_train_or_load_embedding` returns ``None`` before tokenization
#: so the builder keeps the flat JSD fallback path. Tests use this to
#: skip the ~20s Word2Vec training per fixture.
_EMBEDDING_DISABLE_ENV = "TVE_EMBEDDING_DISABLE"

# Heuristic terms used by smoke tests to detect that the real (non-wNN)
# demo is actually rendering in the page.  Extend per fixture as needed.
_KNOWN_REAL_TOKENS: dict[str, tuple[str, ...]] = {
    "20ng_tiny": ("graphics", "game", "team", "encryption", "space"),
    "bbc_tiny": ("government", "market", "film", "company", "player"),
}


def _light_tokenize_one(text: str) -> list[str]:
    """Single-string counterpart of :func:`_light_tokenize`.

    Used both at training time (via :func:`_light_tokenize`) and at
    query time (passed to
    :class:`~topicvisexplorer.similarity.embedding.EmbeddingSimilarity`
    as ``text_cleaner=``) so the two token spaces stay identical. This
    avoids nltk / spaCy dependencies for the Omega-varying path.
    """
    try:
        from gensim.utils import simple_preprocess  # type: ignore[import-untyped]

        return list(simple_preprocess(text, deacc=True, min_len=2, max_len=40))
    except Exception:  # pragma: no cover - fallback path
        import re

        return re.findall(r"[a-z]+", text.lower())


def _light_tokenize(texts: Iterable[str]) -> list[list[str]]:
    """Light regex tokenization for Word2Vec training.

    We deliberately avoid the spaCy-based ``text_cleaner_batch`` pipeline
    here: CBOW vectors do not benefit from lemmatization and spaCy would
    add 30-60s per fixture on top of the ~20s Word2Vec training cost.

    The same tokenizer is used at query time inside
    :class:`~topicvisexplorer.similarity.embedding.EmbeddingSimilarity`
    (see :func:`_build_embedding_similarity_matrix`) so training and
    query token spaces stay byte-identical.

    Prefers :func:`gensim.utils.simple_preprocess` if gensim is present;
    otherwise falls back to a plain lowercase alphabetic regex.
    """
    return [_light_tokenize_one(t) for t in texts]


def _train_or_load_embedding(
    name: str,
    raw_texts: Sequence[str],
    *,
    cache_dir: Path | None = None,
) -> EmbeddingBackend | None:
    """Train or load a cached Word2Vec embedding for ``raw_texts``.

    Returns ``None`` (caller falls back to the flat JSD path) when:

    * the ``TVE_EMBEDDING_DISABLE=1`` env var is set (CI/test escape hatch);
    * :mod:`gensim` is not importable (minimal install without embeddings);
    * the corpus is too small for a useful CBOW model
      (see :data:`~topicvisexplorer.embeddings.word2vec.MIN_DOCS_FOR_FIT`).

    Cache layout is ``<cache_dir>/<name>_w2v_v1.kv``. The ``_v1`` suffix
    is a recipe-version marker -- bump it whenever the light tokenizer,
    seed, or Word2Vec hyperparameters change. Stale caches produce
    silently wrong similarity.

    Parameters
    ----------
    name:
        Stable identifier used in the cache filename (e.g. ``"bbc_tiny"``,
        ``"20ng_tiny"``, or any user-supplied scenario name).
    raw_texts:
        Untokenized documents. We light-tokenize before fitting.
    cache_dir:
        Where to read/write the ``.kv`` file. Defaults to
        :data:`TVE_CACHE_DIR`.
    """
    if os.environ.get(_EMBEDDING_DISABLE_ENV) == "1":
        logger.info(
            "Embedding disabled via %s=1; using JSD fallback for %r.",
            _EMBEDDING_DISABLE_ENV,
            name,
        )
        return None

    cache_root = cache_dir or TVE_CACHE_DIR
    cache_file = cache_root / f"{name}{_W2V_CACHE_SUFFIX}"

    try:
        from ..embeddings.word2vec import MIN_DOCS_FOR_FIT, Word2Vec
    except ImportError as exc:
        logger.warning(
            "Omega-varying similarity unavailable for %r (gensim not installed: %s). "
            "Falling back to JSD (slider will appear flat).",
            name,
            exc,
        )
        return None

    if cache_file.exists():
        try:
            emb = Word2Vec.from_path(cache_file)
            logger.info(
                "Loaded cached topic-similarity embedding for %r from %s.",
                name,
                cache_file,
            )
            return emb
        except Exception as exc:  # pragma: no cover - corrupt cache recovery
            logger.warning(
                "Cached embedding at %s is unreadable (%s); retraining.",
                cache_file,
                exc,
            )

    n_docs = len(raw_texts)
    if n_docs < MIN_DOCS_FOR_FIT:
        logger.warning(
            "Omega-varying similarity unavailable for %r: only %d documents "
            "(need >= %d). Falling back to JSD (slider will appear flat).",
            name,
            n_docs,
            MIN_DOCS_FOR_FIT,
        )
        return None

    logger.info(
        "Training topic-similarity embedding for %r (one-time, ~20s for %d docs, "
        "will cache to %s).",
        name,
        n_docs,
        cache_file,
    )
    tokens = _light_tokenize(raw_texts)
    try:
        emb = Word2Vec.fit(tokens)
    except Word2VecCorpusTooSmallError as exc:
        logger.warning(
            "Omega-varying similarity unavailable for %r: %s. "
            "Falling back to JSD (slider will appear flat).",
            name,
            exc,
        )
        return None
    except ImportError as exc:  # pragma: no cover - gensim dropped at runtime
        logger.warning(
            "Omega-varying similarity unavailable for %r: %s. "
            "Falling back to JSD (slider will appear flat).",
            name,
            exc,
        )
        return None

    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        emb.save(cache_file)
    except OSError as exc:  # pragma: no cover - disk full / permission
        logger.warning("Could not persist embedding cache at %s: %s", cache_file, exc)

    return emb


def _load_fixture_arrays(
    stem: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
    npz = np.load(_FIXTURE_DIR / f"{stem}.npz", allow_pickle=True)
    vocab = np.load(_FIXTURE_DIR / f"{stem}_vocab.npy", allow_pickle=True).tolist()
    if not isinstance(vocab, list):
        vocab = list(vocab)  # type: ignore[unreachable]
    return (
        np.asarray(npz["topic_term_dists"], dtype=np.float64),
        np.asarray(npz["doc_topic_dists"], dtype=np.float64),
        np.asarray(npz["doc_lengths"], dtype=np.float64),
        np.asarray(npz["term_frequency"], dtype=np.float64),
        [str(x) for x in vocab],
    )


def build_scenario_from_topic_model(
    name: str,
    *,
    model_data: TopicModelData,
    raw_texts: list[str],
    prepared_metadata: dict[str, Any] | None = None,
    refit_passes: int = 5,
    refit_random_state: int = 42,
) -> Scenario:
    """Build a full single-corpus :class:`Scenario` (JS layouts + refit) from tensors."""
    md = model_data
    N = int(md.doc_topic_dists.shape[0])
    if len(raw_texts) < N:
        raise ValueError("raw_texts shorter than model_data document count.")
    raw_texts = raw_texts[:N]
    meta = prepared_metadata or {"scenario": name, "synthetic": False}
    prepared = prepare(
        topic_term_dists=md.topic_term_dists,
        doc_topic_dists=md.doc_topic_dists,
        doc_lengths=md.doc_lengths,
        vocab=md.vocab,
        term_frequency=md.term_frequency,
        metadata=meta,
    )
    K = int(md.topic_term_dists.shape[0])
    rel: list[dict[str, Any]] = []
    for i in range(N):
        row = {
            "doc_id": i,
            "text": raw_texts[i],
            **{str(k): float(md.doc_topic_dists[i, k]) for k in range(K)},
        }
        rel.append(row)

    from ..layout import circle_positions

    embedding = _train_or_load_embedding(name, raw_texts)
    similarity_matrix: dict[float, np.ndarray]

    if embedding is not None:
        try:
            import pandas as pd

            from ..similarity.embedding import EmbeddingSimilarity, compute_omega_grid

            metric = EmbeddingSimilarity(embedding=embedding, text_cleaner=_light_tokenize_one)
            doc_topic_df = pd.DataFrame(md.doc_topic_dists)
            grid = compute_omega_grid(
                metric,
                prepared,
                prepared,
                doc_topic_a=doc_topic_df,
                doc_topic_b=doc_topic_df,
                raw_texts_a=raw_texts,
                raw_texts_b=raw_texts,
                n_steps=101,
            )
            similarity_matrix = {
                float(round(k, 2)): np.asarray(v, dtype=np.float64) for k, v in grid.items()
            }
            circ_raw = circle_positions(similarity_matrix)
            circle_positions_str = {str(k): v for k, v in circ_raw.items()}
        except Exception as exc:  # pragma: no cover - robust fallback
            logger.warning(
                "Embedding-based similarity failed for %r (%s); falling back to JSD.",
                name,
                exc,
            )
            embedding = None

    if embedding is None:
        metric_jsd = JensenShannonSimilarity()
        matrix = np.asarray(metric_jsd(prepared, prepared), dtype=np.float64)
        similarity_matrix = {round(s / 100.0, 2): matrix.copy() for s in range(101)}
        sm = {i / 100.0: matrix.copy() for i in range(101)}
        circ_raw = circle_positions(sm)
        circle_positions_str = {str(k): v for k, v in circ_raw.items()}

    return Scenario(
        name=name,
        is_multi=False,
        prepared=prepared,
        model_data=md,
        relevant_documents=rel,
        similarity_matrix=similarity_matrix,
        circle_positions=circle_positions_str,
        raw_texts=raw_texts,
        embedding=embedding,
        extras={
            "refit": refit_gensim_lda(
                md, random_state=refit_random_state, passes=refit_passes
            )
        },
    )


def build_scenario_from_fixture(stem: str) -> Scenario:
    """Build a :class:`Scenario` from a committed fixture stem."""
    topic_term, doc_topic, doc_lengths, term_freq, vocab = _load_fixture_arrays(stem)
    texts_obj = json.loads((_FIXTURE_DIR / f"{stem}_texts.json").read_text(encoding="utf-8"))
    raw_texts: list[str] = list(texts_obj["texts"])
    N = int(doc_topic.shape[0])
    if len(raw_texts) < N:
        raise RuntimeError(f"Fixture texts shorter than doc_topic rows for {stem}.")
    raw_texts = raw_texts[:N]
    md = TopicModelData(
        topic_term_dists=topic_term,
        doc_topic_dists=doc_topic,
        doc_lengths=doc_lengths,
        vocab=vocab,
        term_frequency=term_freq,
    )
    return build_scenario_from_topic_model(
        stem,
        model_data=md,
        raw_texts=raw_texts,
        prepared_metadata={
            "scenario": stem,
            "synthetic": False,
            "fixture": stem,
        },
    )


def build_20ng_tiny() -> Scenario:
    """Single-corpus scenario with real 20 Newsgroups keywords."""
    return build_scenario_from_fixture("20ng_tiny")


def build_bbc_tiny() -> Scenario:
    """Single-corpus scenario with real BBC-news keywords."""
    return build_scenario_from_fixture("bbc_tiny")


def _build_prepared_and_md_from_fixture(
    stem: str,
) -> tuple[Any, TopicModelData, list[str]]:
    """Load a fixture stem and return (prepared, model_data, raw_texts).

    Thin helper shared by :func:`build_scenario_from_fixture` and
    :func:`build_bbc_vs_20ng`; we deliberately avoid reusing
    :func:`build_scenario_from_topic_model` here to skip the per-corpus
    JSD + layout path we do not need for the multi-corpus builder.
    """
    topic_term, doc_topic, doc_lengths, term_freq, vocab = _load_fixture_arrays(stem)
    texts_obj = json.loads((_FIXTURE_DIR / f"{stem}_texts.json").read_text(encoding="utf-8"))
    raw_texts = [str(x) for x in texts_obj["texts"]]
    N = int(doc_topic.shape[0])
    if len(raw_texts) < N:
        raise RuntimeError(f"Fixture texts shorter than doc_topic rows for {stem}.")
    raw_texts = raw_texts[:N]
    md = TopicModelData(
        topic_term_dists=topic_term,
        doc_topic_dists=doc_topic,
        doc_lengths=doc_lengths,
        vocab=vocab,
        term_frequency=term_freq,
    )
    prepared = prepare(
        topic_term_dists=md.topic_term_dists,
        doc_topic_dists=md.doc_topic_dists,
        doc_lengths=md.doc_lengths,
        vocab=md.vocab,
        term_frequency=md.term_frequency,
        metadata={"scenario": stem, "synthetic": False, "fixture": stem},
    )
    return prepared, md, raw_texts


def build_bbc_vs_20ng() -> Scenario:
    """Multi-corpus demo: BBC-news vs 20 Newsgroups slices.

    Trains (or loads) a single shared Word2Vec on the union of both
    corpora so cosine space is consistent across them, then runs the
    paper's cross-corpus similarity (Eq. 7-9) + aligned layout via
    :func:`topicvisexplorer.multi.cross_corpus`.

    Falls back to a flat random-ish multi-corpus scenario only if the
    required fixtures are missing or gensim is not installed; the plan
    is for this fixture to be the "real" multi-corpus baseline.
    """
    if not (fixture_exists("bbc_tiny") and fixture_exists("20ng_tiny")):
        raise FileNotFoundError(
            "bbc_vs_20ng requires both bbc_tiny and 20ng_tiny fixtures. "
            "Run scripts/build_bbc_tiny_fixtures.py and "
            "scripts/build_20ng_tiny_fixtures.py to build them."
        )

    prepared_a, md_a, raw_a = _build_prepared_and_md_from_fixture("bbc_tiny")
    prepared_b, md_b, raw_b = _build_prepared_and_md_from_fixture("20ng_tiny")

    docs_a = _relevant_rows(md_a, raw_a)
    docs_b = _relevant_rows(md_b, raw_b)

    shared = _train_or_load_embedding("bbc_vs_20ng", list(raw_a) + list(raw_b))

    similarity_matrix: dict[float, np.ndarray]
    circle_positions_str: dict[str, list[list[float]]]

    if shared is not None:
        try:
            import pandas as pd

            from ..multi import cross_corpus
            from ..similarity.embedding import EmbeddingSimilarity

            metric = EmbeddingSimilarity(embedding=shared, text_cleaner=_light_tokenize_one)
            bundle = cross_corpus(
                prepared_a,
                prepared_b,
                metric=metric,
                doc_topic_a=pd.DataFrame(md_a.doc_topic_dists),
                doc_topic_b=pd.DataFrame(md_b.doc_topic_dists),
                raw_texts_a=raw_a,
                raw_texts_b=raw_b,
                n_omega_steps=101,
            )
            similarity_matrix = {
                float(round(k, 2)): np.asarray(v, dtype=np.float64)
                for k, v in bundle.omega_to_similarity.items()
            }
            # cross_corpus returns aligned_positions_json as a JSON string
            # (via ``layout.get_circle_positions``), but Scenario.circle_positions
            # is typed as dict[str, list[list[float]]]. Decode here.
            circle_positions_str = json.loads(bundle.aligned_positions_json)
        except Exception as exc:
            logger.warning(
                "Cross-corpus embedding similarity failed for bbc_vs_20ng (%s); "
                "falling back to JSD.",
                exc,
            )
            shared = None

    if shared is None:
        metric_jsd = JensenShannonSimilarity()
        ab = np.asarray(metric_jsd(prepared_a, prepared_b), dtype=np.float64)
        aa = np.asarray(metric_jsd(prepared_a, prepared_a), dtype=np.float64)
        bb = np.asarray(metric_jsd(prepared_b, prepared_b), dtype=np.float64)
        combined = np.block([[aa, ab], [ab.T, bb]])
        similarity_matrix = {round(s / 100.0, 2): ab.copy() for s in range(101)}
        combined_grid = {round(s / 100.0, 2): combined.copy() for s in range(101)}
        from ..layout import circle_positions as _pos

        circ_raw = _pos(combined_grid)
        circle_positions_str = {str(k): v for k, v in circ_raw.items()}

    return Scenario(
        name="bbc_vs_20ng",
        is_multi=True,
        prepared=prepared_a,
        prepared_b=prepared_b,
        model_data=md_a,
        model_data_b=md_b,
        relevant_documents=docs_a,
        relevant_documents_b=docs_b,
        similarity_matrix=similarity_matrix,
        circle_positions=circle_positions_str,
        raw_texts=raw_a,
        embedding=shared,
    )


def _relevant_rows(md: TopicModelData, raw_texts: list[str]) -> list[dict[str, Any]]:
    """Build the ``relevantDocumentsDict`` rows for one corpus."""
    K = int(md.topic_term_dists.shape[0])
    N = int(md.doc_topic_dists.shape[0])
    rows: list[dict[str, Any]] = []
    for i in range(N):
        rows.append(
            {
                "doc_id": i,
                "text": raw_texts[i] if i < len(raw_texts) else "",
                **{str(k): float(md.doc_topic_dists[i, k]) for k in range(K)},
            }
        )
    return rows


def demo_page_contains_real_terms(html: str, fixture: str = "20ng_tiny") -> bool:
    """Return True if ``html`` plausibly shows a real-terms (non-wNN) demo."""
    tokens = _KNOWN_REAL_TOKENS.get(fixture, ())
    if any(tok in html for tok in tokens):
        return True
    if "w00" in html or "synthetic document" in html:
        return False
    return "tinfo" in html


def fixture_exists(stem: str) -> bool:
    """Return True if all files for a fixture stem are present on disk."""
    return all(
        (_FIXTURE_DIR / f"{stem}{suffix}").exists()
        for suffix in (".npz", "_vocab.npy", "_texts.json")
    )


__all__ = [
    "TVE_CACHE_DIR",
    "build_20ng_tiny",
    "build_bbc_tiny",
    "build_bbc_vs_20ng",
    "build_scenario_from_fixture",
    "build_scenario_from_topic_model",
    "demo_page_contains_real_terms",
    "fixture_exists",
]
