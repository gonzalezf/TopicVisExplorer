#!/usr/bin/env python3
"""One-shot builder for committed ``bbc_tiny`` demo fixtures.

Downloads the UCD Machine Learning Group BBC news corpus (5 classes,
~2225 news articles) into ``~/.cache/topicvisexplorer/bbc-fulltext.zip``
(if it is not already cached), runs the full
``topicvisexplorer.preprocessing.text_cleaner_batch`` pipeline (spaCy +
NLTK stopwords + lemmatization) with Gensim Phraser bigrams, fits a small
Gensim LDA, and writes ``topicvisexplorer.server.fixtures.bbc_tiny*`` for
offline ``tve demo --corpus bbc_tiny`` (no network at runtime).

Primary source: http://mlg.ucd.ie/datasets/bbc.html
Licence: for research use only (cite D. Greene and P. Cunningham,
"Practical Solutions to the Problem of Diagonal Dominance in Kernel
Document Clustering", ICML 2006).

Fallback: if mlg.ucd.ie is unreachable, this script will attempt to use
the Hugging Face ``SetFit/bbc-news`` dataset (same five categories).

Usage (from repo root)::

    python scripts/build_bbc_tiny_fixtures.py

Prerequisites:
    uv sync --extra full --extra dev
    python -m spacy download en_core_web_sm
    python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "src" / "topicvisexplorer" / "server" / "fixtures"
STEM = "bbc_tiny"

RANDOM_SEED = 42
N_DOCS = 400
N_TOPICS = 5
N_PASSES = 15
N_ITERATIONS = 200

BBC_URL = "http://mlg.ucd.ie/files/datasets/bbc-fulltext.zip"
CACHE_DIR = Path(os.environ.get("TVE_CACHE_DIR", Path.home() / ".cache" / "topicvisexplorer"))
CACHE_ZIP = CACHE_DIR / "bbc-fulltext.zip"
BBC_CATEGORIES = ("business", "entertainment", "politics", "sport", "tech")


def _load_from_ucd() -> tuple[list[str], list[str]]:
    """Load BBC corpus from the UCD mirror; returns (texts, labels)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not CACHE_ZIP.exists():
        print(f"Downloading BBC corpus from {BBC_URL} ...", flush=True)
        with urllib.request.urlopen(BBC_URL, timeout=60) as resp:
            CACHE_ZIP.write_bytes(resp.read())
    with zipfile.ZipFile(CACHE_ZIP) as zf:
        texts: list[str] = []
        labels: list[str] = []
        for info in zf.infolist():
            parts = info.filename.split("/")
            # Expected layout: bbc/<category>/<id>.txt
            if len(parts) < 3 or not info.filename.endswith(".txt"):
                continue
            category = parts[1]
            if category not in BBC_CATEGORIES:
                continue
            with zf.open(info) as fh:
                raw = fh.read().decode("latin-1", errors="ignore")
            texts.append(raw)
            labels.append(category)
    if not texts:
        raise RuntimeError("UCD BBC zip contained no expected documents.")
    return texts, labels


def _load_from_hf() -> tuple[list[str], list[str]]:
    """Fallback loader using the Hugging Face ``SetFit/bbc-news`` dataset."""
    print("UCD source unavailable; falling back to Hugging Face SetFit/bbc-news ...", flush=True)
    from datasets import load_dataset  # type: ignore[import-not-found]

    ds = load_dataset("SetFit/bbc-news", split="train")
    texts = [str(x) for x in ds["text"]]
    label_col = "label_text" if "label_text" in ds.column_names else "label"
    labels = [str(x) for x in ds[label_col]]
    return texts, labels


def main() -> int:
    try:
        from gensim import corpora, models
        from gensim.models.phrases import Phraser, Phrases
    except ImportError as e:
        print("gensim is required to build fixtures:", e, file=sys.stderr)
        return 1

    try:
        from topicvisexplorer.preprocessing import text_cleaner_batch
    except Exception as e:
        print("preprocessing pipeline failed:", e, file=sys.stderr)
        return 1

    from topicvisexplorer.models.adapters.gensim_lda import GensimLDAAdapter

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        texts_all, labels_all = _load_from_ucd()
        source = "mlg.ucd.ie/files/datasets/bbc-fulltext.zip"
    except Exception as exc:
        print(f"UCD fetch failed ({exc}); trying Hugging Face fallback.", flush=True)
        try:
            texts_all, labels_all = _load_from_hf()
            source = "huggingface:SetFit/bbc-news"
        except Exception as exc2:
            print(f"Hugging Face fallback also failed: {exc2}", file=sys.stderr)
            return 1

    print(f"Loaded {len(texts_all)} BBC documents ({source}).", flush=True)

    rng = np.random.default_rng(RANDOM_SEED)
    n = min(N_DOCS, len(texts_all))
    choice = rng.choice(len(texts_all), size=n, replace=False)
    texts = [texts_all[i] for i in choice]
    labels = [labels_all[i] for i in choice]

    print(f"Preprocessing {n} docs with spaCy + NLTK pipeline ...", flush=True)
    tokens_clean = text_cleaner_batch(texts)

    bigram_model = Phrases(tokens_clean, min_count=5, threshold=10)
    bigram = Phraser(bigram_model)
    texts_tok = [bigram[doc] for doc in tokens_clean]
    texts_tok = [[t for t in doc if len(t) >= 3] for doc in texts_tok]

    dictionary = corpora.Dictionary(texts_tok)
    dictionary.filter_extremes(no_below=5, no_above=0.5, keep_n=5000)
    corpus = [dictionary.doc2bow(t) for t in texts_tok]

    non_empty = sum(1 for d in corpus if len(d) > 0)
    print(f"Vocab size after filtering: {len(dictionary)}  Non-empty docs: {non_empty}")
    if len(dictionary) < 10:
        raise SystemExit("Dictionary too small; adjust filters or doc count.")

    print(
        f"Training LDA: K={N_TOPICS} passes={N_PASSES} iterations={N_ITERATIONS} ...",
        flush=True,
    )
    np.random.seed(RANDOM_SEED)
    lda = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=N_TOPICS,
        random_state=RANDOM_SEED,
        passes=N_PASSES,
        iterations=N_ITERATIONS,
        alpha="auto",
        eta="auto",
    )

    print("\nTop-10 terms per topic:")
    for i in range(N_TOPICS):
        top = [w for w, _ in lda.show_topic(i, topn=10)]
        print(f"  Topic {i + 1}: {' '.join(top)}")

    try:
        from nltk.corpus import stopwords as nltk_sw

        stop = set(nltk_sw.words("english"))
    except Exception:
        stop = set()
    if stop:
        violations = []
        for i in range(N_TOPICS):
            top20 = [w for w, _ in lda.show_topic(i, topn=20)]
            bad = [w for w in top20 if w.lower() in stop]
            if bad:
                violations.append(f"  Topic {i + 1}: {bad}")
        if violations:
            print("\nERROR: stopwords found in top-20 terms!", file=sys.stderr)
            for v in violations:
                print(v, file=sys.stderr)
            return 1
        print("\nStopword check: PASSED")

    adapter = GensimLDAAdapter()
    md = adapter.extract(lda, corpus, dictionary=dictionary)
    vocab = md.vocab
    if len(vocab) != len(set(vocab)):
        raise SystemExit("Vocabulary from model must be unique (needed for refit).")

    npz_path = OUT_DIR / f"{STEM}.npz"
    np.savez_compressed(
        npz_path,
        topic_term_dists=md.topic_term_dists.astype(np.float64),
        doc_topic_dists=md.doc_topic_dists.astype(np.float64),
        doc_lengths=md.doc_lengths.astype(np.float64),
        term_frequency=md.term_frequency.astype(np.float64),
        meta=np.array(
            json.dumps(
                {
                    "seed": RANDOM_SEED,
                    "n_docs": n,
                    "n_topics": N_TOPICS,
                    "categories": list(BBC_CATEGORIES),
                    "source": source,
                    "preprocessing": "text_cleaner_batch+Phraser",
                    "lda_passes": N_PASSES,
                    "lda_iterations": N_ITERATIONS,
                }
            )
        ),
    )
    np.save(OUT_DIR / f"{STEM}_vocab.npy", np.array(md.vocab, dtype=object))

    json_path = OUT_DIR / f"{STEM}_texts.json"
    json_path.write_text(
        json.dumps(
            {
                "texts": texts,
                "labels": labels,
                "source": source,
                "categories": list(BBC_CATEGORIES),
                "n_docs": n,
                "preprocessing": "text_cleaner_batch+Phraser",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    print(f"\nWrote {npz_path} and {json_path}")
    print(f"Vocab size: {len(md.vocab)}  K={md.topic_term_dists.shape[0]}  N={n}")

    _prewarm_w2v_cache(STEM, texts)
    return 0


def _prewarm_w2v_cache(stem: str, texts: list[str]) -> None:
    """Train and persist the Word2Vec cache used at runtime.

    Warms ``<TVE_CACHE_DIR>/<stem>_w2v_v1.kv`` so the first
    ``/singlecorpus?scenario=<stem>`` page load is instant. The .kv file
    is NOT committed (repo-size hygiene); fresh clones re-train once.
    """
    try:
        from topicvisexplorer.server.demo_fixtures import _train_or_load_embedding
    except Exception as exc:
        print(f"[prewarm] skipped: could not import helper ({exc})", flush=True)
        return
    prev = os.environ.pop("TVE_EMBEDDING_DISABLE", None)
    try:
        emb = _train_or_load_embedding(stem, texts)
    finally:
        if prev is not None:
            os.environ["TVE_EMBEDDING_DISABLE"] = prev
    if emb is None:
        print(f"[prewarm] no embedding produced for {stem}", flush=True)
    else:
        print(f"[prewarm] embedding ready for {stem} (vocab={len(emb._kv):,})", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
