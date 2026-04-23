"""Bring-Your-Own corpus support for ``tve demo --texts ...``.

Fits a topic model on a user-supplied text file, caches the resulting
tensors under ``~/.cache/topicvisexplorer/<name>-<model>-<hash>.npz``,
and returns a :class:`Scenario` ready to register via
:attr:`ServerConfig.extra_scenarios`.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from ..embeddings.protocol import EmbeddingBackend
from ..errors import OptionalDependencyError
from ..models.protocol import TopicModelData
from ..models.registry import get_adapter, list_adapters
from .demo_fixtures import build_scenario_from_topic_model
from .scenarios import Scenario

DEFAULT_CACHE = Path(os.environ.get("TVE_CACHE_DIR", Path.home() / ".cache" / "topicvisexplorer"))

_EMBEDDING_CHOICES = ("word2vec", "sbert")


def _resolve_topic_embedding(embedding: str, sbert_model: str) -> EmbeddingBackend | None:
    """Return ``None`` to train Word2Vec in :func:`build_scenario_from_topic_model`."""
    if embedding not in _EMBEDDING_CHOICES:
        raise ValueError(
            f"Unknown embedding {embedding!r}. Choose one of: {', '.join(_EMBEDDING_CHOICES)}."
        )
    if embedding == "word2vec":
        return None
    from ..embeddings.sbert import SBERT

    return SBERT(model_name=sbert_model)


def load_texts(path: Path) -> list[str]:
    """Load one document per line, or JSONL with a ``"text"`` field.

    ``.jsonl`` / ``.json`` files are parsed line-by-line; other files are
    treated as plain text (one doc per non-empty line).
    """
    raw = path.read_text(encoding="utf-8")
    texts: list[str] = []
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            t = obj.get("text") if isinstance(obj, dict) else None
            if not isinstance(t, str):
                raise ValueError(f"JSONL input must contain a string 'text' field; got {obj!r}")
            texts.append(t)
    elif path.suffix.lower() == ".json":
        obj = json.loads(raw)
        if isinstance(obj, dict) and isinstance(obj.get("texts"), list):
            texts = [str(x) for x in obj["texts"]]
        elif isinstance(obj, list):
            texts = [str(x) for x in obj]
        else:
            raise ValueError(
                "JSON input must be a list of strings or an object with a 'texts' array."
            )
    else:
        for line in raw.splitlines():
            s = line.strip()
            if s:
                texts.append(s)
    if not texts:
        raise ValueError(f"No documents found in {path}.")
    return texts


def _cache_key(
    texts: list[str],
    num_topics: int,
    passes: int,
    seed: int,
    model: str,
    embedding: str,
    sbert_model: str,
) -> str:
    h = hashlib.sha256()
    h.update(
        f"K={num_topics}|P={passes}|S={seed}|M={model}|E={embedding}|SB={sbert_model}\n".encode()
    )
    for t in texts:
        h.update(t.encode("utf-8", errors="ignore"))
        h.update(b"\n")
    return h.hexdigest()[:16]


def _save_cache(cache_file: Path, md: TopicModelData, texts: list[str]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_file,
        topic_term_dists=md.topic_term_dists.astype(np.float64),
        doc_topic_dists=md.doc_topic_dists.astype(np.float64),
        doc_lengths=md.doc_lengths.astype(np.float64),
        term_frequency=md.term_frequency.astype(np.float64),
        vocab=np.array(md.vocab, dtype=object),
        texts=np.array(texts, dtype=object),
    )


def _load_cache(cache_file: Path) -> tuple[TopicModelData, list[str]] | None:
    if not cache_file.exists():
        return None
    try:
        npz = np.load(cache_file, allow_pickle=True)
        md = TopicModelData(
            topic_term_dists=np.asarray(npz["topic_term_dists"], dtype=np.float64),
            doc_topic_dists=np.asarray(npz["doc_topic_dists"], dtype=np.float64),
            doc_lengths=np.asarray(npz["doc_lengths"], dtype=np.float64),
            vocab=[str(x) for x in npz["vocab"].tolist()],
            term_frequency=np.asarray(npz["term_frequency"], dtype=np.float64),
        )
        texts = [str(x) for x in npz["texts"].tolist()]
        return md, texts
    except Exception:
        return None


def _fit_gensim_lda(texts: list[str], num_topics: int, passes: int, seed: int) -> TopicModelData:
    from gensim import corpora, models
    from gensim.models.phrases import Phraser, Phrases

    from ..models.adapters.gensim_lda import GensimLDAAdapter
    from ..preprocessing import text_cleaner_batch

    tokens = text_cleaner_batch(texts)
    bigram = Phraser(Phrases(tokens, min_count=5, threshold=10))
    toks = [[t for t in bigram[doc] if len(t) >= 3] for doc in tokens]
    dictionary = corpora.Dictionary(toks)
    dictionary.filter_extremes(no_below=2, no_above=0.5, keep_n=5000)
    corpus = [dictionary.doc2bow(t) for t in toks]
    if len(dictionary) < 10:
        raise ValueError("Vocabulary too small after filtering; provide more documents.")
    np.random.seed(seed)
    lda = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=seed,
        passes=passes,
        iterations=200,
        alpha="auto",
        eta="auto",
    )
    adapter = GensimLDAAdapter()
    return adapter.extract(lda, corpus, dictionary=dictionary)


def _fit_sklearn_lda(texts: list[str], num_topics: int, passes: int, seed: int) -> TopicModelData:
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    from ..models.adapters.sklearn_lda import SklearnLDAAdapter

    vectorizer = CountVectorizer(max_df=0.5, min_df=2, max_features=5000)
    X = vectorizer.fit_transform(texts)
    if X.shape[1] < 5:
        raise ValueError("Vocabulary too small after vectorization; provide more documents.")
    lda = LatentDirichletAllocation(
        n_components=num_topics,
        random_state=seed,
        max_iter=max(2, passes),
    )
    lda.fit(X)
    return SklearnLDAAdapter().extract(lda, X, vectorizer=vectorizer)


def _fit_sklearn_nmf(texts: list[str], num_topics: int, passes: int, seed: int) -> TopicModelData:
    from sklearn.decomposition import NMF
    from sklearn.feature_extraction.text import TfidfVectorizer

    from ..models.adapters.sklearn_nmf import SklearnNMFAdapter

    vectorizer = TfidfVectorizer(max_df=0.5, min_df=2, max_features=5000)
    X = vectorizer.fit_transform(texts)
    if X.shape[1] < 5:
        raise ValueError("Vocabulary too small after vectorization; provide more documents.")
    nmf = NMF(
        n_components=num_topics,
        random_state=seed,
        max_iter=max(20, passes * 20),
        init="nndsvda",
    )
    nmf.fit(X)
    return SklearnNMFAdapter().extract(nmf, X, vectorizer=vectorizer)


def _fit_bertopic(texts: list[str], num_topics: int) -> TopicModelData:
    from bertopic import BERTopic  # type: ignore[import-untyped]

    from ..models.adapters.bertopic import BERTopicAdapter

    n_topics: int | str = "auto" if num_topics < 1 else num_topics
    model = BERTopic(
        nr_topics=n_topics,
        calculate_probabilities=False,
        verbose=False,
    )
    model.fit(texts)
    return BERTopicAdapter().extract(model, corpus=None, texts=texts)


def _etm_train_data_from_texts(texts: list[str]) -> tuple[dict[str, Any], list[str]]:
    """Build the ``{"tokens", "counts"}`` dict expected by ``ETM.fit`` (PyPI API)."""
    from sklearn.feature_extraction.text import CountVectorizer

    vectorizer = CountVectorizer(max_df=0.5, min_df=1, max_features=2000)
    X = vectorizer.fit_transform(texts)
    if X.shape[1] < 2:
        raise ValueError("Corpus too small for ETM after vectorization.")
    vocab = list(vectorizer.get_feature_names_out())
    tok_list: list[np.ndarray] = []
    cnt_list: list[np.ndarray] = []
    for i in range(X.shape[0]):
        row = X.getrow(i)
        tok_list.append(np.asarray(row.indices, dtype=np.int64))
        cnt_list.append(np.asarray(row.data, dtype=np.float64))
    train_data = {
        "tokens": np.asarray(tok_list, dtype=object),
        "counts": np.asarray(cnt_list, dtype=object),
    }
    return train_data, vocab


def _fit_etm(texts: list[str], num_topics: int, passes: int, seed: int) -> TopicModelData:
    from embedded_topic_model.models.etm import ETM  # type: ignore[import-untyped]

    from ..models.adapters.etm import ETMAdapter

    np.random.seed(seed)
    train_data, vocab = _etm_train_data_from_texts(texts)
    n_epochs = max(3, min(passes, 20))
    model = ETM(
        vocabulary=vocab,
        embeddings=None,
        num_topics=num_topics,
        batch_size=min(32, max(2, len(texts))),
        epochs=n_epochs,
    )
    model.fit(train_data)
    return ETMAdapter().extract(
        model, corpus=None, texts=texts, vocabulary=vocab
    )


def _fit_ctm(
    texts: list[str], num_topics: int, passes: int, seed: int, sbert_name: str
) -> TopicModelData:
    from contextualized_topic_models.models.ctm import CombinedTM  # type: ignore[import-untyped]
    from contextualized_topic_models.utils.data_preparation import (  # type: ignore[import-untyped]
        TopicModelDataPreparation,
    )

    from ..models.adapters.ctm import CTMAdapter

    np.random.seed(seed)
    prep = TopicModelDataPreparation(sbert_name)
    training = prep.fit(text_for_contextual=texts, text_for_bow=texts)
    xc = training.X_contextual
    n_epochs = max(1, min(passes, 20))
    ctm = CombinedTM(
        bow_size=len(prep.vocab),
        contextual_size=int(xc.shape[1]),
        n_components=num_topics,
        num_epochs=n_epochs,
        batch_size=min(64, max(2, len(texts))),
    )
    ctm.fit(training)
    dtd = ctm.get_doc_topic_distribution(training, n_samples=min(10, max(2, passes)))
    return CTMAdapter().extract(
        ctm, corpus=None, texts=texts, doc_topic_dists=np.asarray(dtd, dtype=np.float64)
    )


def _fit_from_texts(
    texts: list[str],
    num_topics: int,
    passes: int,
    seed: int,
    *,
    model: str = "gensim-lda",
    sbert_model: str = "all-MiniLM-L6-v2",
) -> TopicModelData:
    """Dispatch to the requested adapter; :func:`get_adapter` validates optional deps."""
    if model not in list_adapters():
        raise ValueError(f"Unknown model {model!r}. Choose one of: {', '.join(list_adapters())}.")
    if model in ("bertopic", "etm", "ctm"):
        get_adapter(model)

    if model == "gensim-lda":
        return _fit_gensim_lda(texts, num_topics, passes, seed)
    if model == "sklearn-lda":
        return _fit_sklearn_lda(texts, num_topics, passes, seed)
    if model == "sklearn-nmf":
        return _fit_sklearn_nmf(texts, num_topics, passes, seed)
    if model == "bertopic":
        return _fit_bertopic(texts, num_topics)
    if model == "etm":
        return _fit_etm(texts, num_topics, passes, seed)
    if model == "ctm":
        return _fit_ctm(texts, num_topics, passes, seed, sbert_name=sbert_model)
    raise ValueError(f"Unhandled model: {model!r}")


def build_scenario_from_textfile(
    path: Path,
    *,
    name: str,
    num_topics: int = 5,
    passes: int = 10,
    seed: int = 42,
    model: str = "gensim-lda",
    embedding: str = "word2vec",
    sbert_model: str = "all-MiniLM-L6-v2",
    cache_dir: Path | None = None,
) -> Scenario:
    """Fit a topic model on user-supplied texts and return a registrable scenario.

    Fits are cached by content hash under ``cache_dir`` (default
    ``~/.cache/topicvisexplorer``); repeated runs on the same file and
    parameters are instant.
    """
    if embedding not in _EMBEDDING_CHOICES:
        raise ValueError(
            f"Unknown embedding {embedding!r}. Choose one of: {', '.join(_EMBEDDING_CHOICES)}."
        )
    if embedding == "sbert":
        from importlib.util import find_spec

        if find_spec("sentence_transformers") is None:
            raise OptionalDependencyError(
                "Embedding 'sbert' requires sentence-transformers. "
                'Install with: pip install "topicvisexplorer[full]"'
            )

    cache_root = cache_dir or DEFAULT_CACHE
    texts = load_texts(path)
    key = _cache_key(texts, num_topics, passes, seed, model, embedding, sbert_model)
    safe_model = model.replace(os.sep, "_").replace("/", "_")
    cache_file = cache_root / f"{name}-{safe_model}-{key}.npz"

    cached = _load_cache(cache_file)
    if cached is not None:
        md, texts = cached
    else:
        md = _fit_from_texts(
            texts,
            num_topics=num_topics,
            passes=passes,
            seed=seed,
            model=model,
            sbert_model=sbert_model,
        )
        _save_cache(cache_file, md, texts)

    topic_emb = _resolve_topic_embedding(embedding, sbert_model)

    meta: dict[str, Any] = {
        "scenario": name,
        "synthetic": False,
        "source_path": str(path),
        "num_topics": num_topics,
        "passes": passes,
        "seed": seed,
        "model": model,
        "embedding": embedding,
        "sbert_model": sbert_model,
        "cache_file": str(cache_file),
    }
    return build_scenario_from_topic_model(
        name,
        model_data=md,
        raw_texts=texts,
        prepared_metadata=meta,
        refit_passes=max(3, passes // 2),
        refit_random_state=seed,
        embedding=topic_emb,
    )


__all__ = ["DEFAULT_CACHE", "build_scenario_from_textfile", "load_texts"]
