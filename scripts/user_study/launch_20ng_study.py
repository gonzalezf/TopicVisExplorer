#!/usr/bin/env python3
"""Reproducible 20 Newsgroups → full ``Scenario`` → local server for a user study.

Fits a small sklearn-fetched slice + gensim LDA, builds ``PreparedData``,
``model_data`` (with :attr:`doc_id` rows in ``relevant_documents``), Jensen-
Shannon + circle layouts, and registers :func:`refit_gensim_lda` for in-browser
topic split. **Does not** ship paper-private pickles; IRB text should name this
public corpus, seed, and row counts.

HuggingFace (optional)::

    pip install "topicvisexplorer[hf]"  # provides ``datasets`` / hub
    python scripts/user_study/launch_20ng_study.py --source hf_ag_news

For a one-liner :class:`datasets.Dataset` → bundled adapter pipeline, see
:file:`ROADMAP.md` (``HFDatasetsLoader``, v1.1).
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _fit_sklearn_20ng(
    *,
    seed: int,
    n_docs: int,
    n_topics: int,
    categories: list[str] | None,
) -> tuple[Any, list[str]]:
    import numpy as np
    from gensim import corpora, models, utils
    from sklearn.datasets import fetch_20newsgroups

    from topicvisexplorer.models.adapters.gensim_lda import GensimLDAAdapter

    cats: Any = categories
    if cats is None:
        cats = ["comp.graphics", "rec.sport.baseball", "sci.crypt"]
    bunch = fetch_20newsgroups(
        subset="train",
        categories=cats,
        remove=("headers", "footers", "quotes"),
        shuffle=True,
        random_state=seed,
    )
    rng = np.random.default_rng(seed)
    n = min(n_docs, len(bunch.data))
    choice = rng.choice(len(bunch.data), size=n, replace=False)
    texts = [bunch.data[i] for i in choice]
    texts_tok = [utils.simple_preprocess(t, deacc=True) for t in texts]
    dictionary = corpora.Dictionary(texts_tok)
    dictionary.filter_extremes(no_below=2, no_above=0.8, keep_n=8000)
    corpus = [dictionary.doc2bow(t) for t in texts_tok]

    lda = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=n_topics,
        random_state=seed,
        passes=8,
        alpha="auto",
    )
    return GensimLDAAdapter().extract(lda, corpus, dictionary=dictionary), texts


def _fit_hf_ag_news(*, seed: int, n_docs: int, n_topics: int) -> tuple[Any, list[str]]:
    try:
        from datasets import load_dataset
    except ImportError as e:
        print(
            "Optional dependency missing: install with "
            "``pip install 'topicvisexplorer[hf]'`` or "
            "``pip install datasets`` (then re-run).",
            file=sys.stderr,
        )
        raise SystemExit(1) from e
    # Pin dataset revision in study protocols; example uses default split
    import numpy as np
    from gensim import corpora, models, utils

    from topicvisexplorer.models.adapters.gensim_lda import GensimLDAAdapter

    ds = load_dataset("ag_news", split="train")
    rng = np.random.default_rng(seed)
    n = min(n_docs, len(ds))
    choice = rng.choice(len(ds), size=n, replace=False)
    texts = [str(ds[int(i)]["text"]) for i in choice]
    texts_tok = [utils.simple_preprocess(t, deacc=True) for t in texts]
    dictionary = corpora.Dictionary(texts_tok)
    dictionary.filter_extremes(no_below=2, no_above=0.8, keep_n=8000)
    corpus = [dictionary.doc2bow(t) for t in texts_tok]
    lda = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=n_topics,
        random_state=seed,
        passes=8,
        alpha="auto",
    )
    return GensimLDAAdapter().extract(lda, corpus, dictionary=dictionary), texts


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--source",
        choices=("sklearn_20ng", "hf_ag_news"),
        default="sklearn_20ng",
    )
    p.add_argument("--name", default="user_study_20ng", help="``?scenario=`` name")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-docs", type=int, default=60)
    p.add_argument("--n-topics", type=int, default=5)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    if args.source == "sklearn_20ng":
        md, texts = _fit_sklearn_20ng(
            seed=args.seed, n_docs=args.n_docs, n_topics=args.n_topics, categories=None
        )
    else:
        md, texts = _fit_hf_ag_news(
            seed=args.seed, n_docs=args.n_docs, n_topics=args.n_topics
        )

    from topicvisexplorer.server import ServerConfig, build_app, serve
    from topicvisexplorer.server.demo_fixtures import build_scenario_from_topic_model
    from topicvisexplorer.server.scenarios import Scenario

    study_cache: list[Scenario | None] = [None]

    def load_study() -> Scenario:
        if study_cache[0] is None:
            study_cache[0] = build_scenario_from_topic_model(
                args.name,
                model_data=md,
                raw_texts=texts,
                prepared_metadata={
                    "scenario": args.name,
                    "synthetic": False,
                    "source": args.source,
                    "seed": args.seed,
                },
            )
        return study_cache[0]

    app = build_app(
        ServerConfig(
            register_demo=True,
            extra_scenarios={args.name: load_study},
        )
    )
    import logging

    logging.getLogger("topicvisexplorer").info("Study URL: /singlecorpus?scenario=%s", args.name)
    serve(app, host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
