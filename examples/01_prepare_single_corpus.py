#!/usr/bin/env python3
"""
Single-corpus: tokenize, fit Gensim LDA, ``prepare()``, then open the app.

**From the repository root** (after ``uv sync`` and a one-time ``frontend`` build)::

  uv run python examples/01_prepare_single_corpus.py
  uv run python examples/01_prepare_single_corpus.py --no-browser
  uv run python examples/01_prepare_single_corpus.py --smoke

``--smoke`` writes a static HTML file and exits (no server). Requires **gensim**.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from gensim.corpora import Dictionary
from gensim.models import LdaModel

import topicvisexplorer as tve
from topicvisexplorer.models import GensimLDAAdapter


def _build_prepared() -> tve.PreparedData:
    raw = [
        "the quick brown fox jumps over the lazy dog",
        "a fox and a dog are friends",
        "the cat sat on the mat",
        "my cat loves my dog",
    ]
    tokenized = [t.lower().split() for t in raw]
    dictionary = Dictionary(tokenized)
    corpus = [dictionary.doc2bow(doc) for doc in tokenized]
    lda = LdaModel(
        corpus=corpus, id2word=dictionary, num_topics=2, random_state=0, passes=20
    )
    adapter = GensimLDAAdapter()
    model_data = adapter.extract(lda, corpus=corpus, dictionary=dictionary)
    return tve.prepare(
        topic_term_dists=model_data.topic_term_dists,
        doc_topic_dists=model_data.doc_topic_dists,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-browser", action="store_true", help="Do not open a tab.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Build PreparedData and write a static HTML file only; no server.",
    )
    args = p.parse_args()
    if args.smoke:
        out = Path(tempfile.mkstemp(suffix="-topics.html", prefix="tve-")[1])
        prepared = _build_prepared()
        tve.save_html(prepared, str(out))
        print("Smoke OK — wrote", out)
        return 0
    prepared = _build_prepared()
    tve.show(
        prepared,
        open_browser=not args.no_browser,
        port=args.port,
        scenario_name="01_api_prepare",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
