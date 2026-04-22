"""Bring-Your-Own corpus support for ``tve demo --texts ...``.

Runs the standard ``text_cleaner_batch`` + Gensim Phraser + LDA pipeline
on a user-supplied text file, caches the resulting tensors under
``~/.cache/topicvisexplorer/<content-hash>.npz``, and returns a
:class:`Scenario` ready to register via
:attr:`ServerConfig.extra_scenarios`.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from ..models.protocol import TopicModelData
from .demo_fixtures import build_scenario_from_topic_model
from .scenarios import Scenario

DEFAULT_CACHE = Path(os.environ.get("TVE_CACHE_DIR", Path.home() / ".cache" / "topicvisexplorer"))


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
                raise ValueError(
                    f"JSONL input must contain a string 'text' field; got {obj!r}"
                )
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


def _cache_key(texts: list[str], num_topics: int, passes: int, seed: int) -> str:
    h = hashlib.sha256()
    h.update(f"K={num_topics}|P={passes}|S={seed}\n".encode())
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


def _fit_from_texts(
    texts: list[str], num_topics: int, passes: int, seed: int
) -> TopicModelData:
    from gensim import corpora, models  # type: ignore[import-untyped]
    from gensim.models.phrases import Phraser, Phrases  # type: ignore[import-untyped]

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


def build_scenario_from_textfile(
    path: Path,
    *,
    name: str,
    num_topics: int = 5,
    passes: int = 10,
    seed: int = 42,
    cache_dir: Path | None = None,
) -> Scenario:
    """Fit an LDA on user-supplied texts and return a registrable scenario.

    Fits are cached by content hash under ``cache_dir`` (default
    ``~/.cache/topicvisexplorer``); repeated runs on the same file and
    parameters are instant.
    """
    cache_root = cache_dir or DEFAULT_CACHE
    texts = load_texts(path)
    key = _cache_key(texts, num_topics, passes, seed)
    cache_file = cache_root / f"{name}-{key}.npz"

    cached = _load_cache(cache_file)
    if cached is not None:
        md, texts = cached
    else:
        md = _fit_from_texts(texts, num_topics=num_topics, passes=passes, seed=seed)
        _save_cache(cache_file, md, texts)

    meta: dict[str, Any] = {
        "scenario": name,
        "synthetic": False,
        "source_path": str(path),
        "num_topics": num_topics,
        "passes": passes,
        "seed": seed,
        "cache_file": str(cache_file),
    }
    return build_scenario_from_topic_model(
        name,
        model_data=md,
        raw_texts=texts,
        prepared_metadata=meta,
        refit_passes=max(3, passes // 2),
        refit_random_state=seed,
    )


__all__ = ["DEFAULT_CACHE", "build_scenario_from_textfile", "load_texts"]
