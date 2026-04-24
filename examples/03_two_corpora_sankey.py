#!/usr/bin/env python3
"""
Multicorpora: fit two small LDA models, then open the two-corpus (Sankey) view.

**scikit-learn** on two synthetic text lists. Default: ``TVE_EMBEDDING_DISABLE=1``
so the first run skips Word2Vec (set to ``0`` to train an embedding and use the
Omega layout). **From the repository root**::

  uv run python examples/03_two_corpora_sankey.py
  uv run python examples/03_two_corpora_sankey.py --no-browser
  TVE_EMBEDDING_DISABLE=0 uv run python examples/03_two_corpora_sankey.py
  uv run python examples/03_two_corpora_sankey.py --smoke
"""

from __future__ import annotations

import argparse
import os
import sys

import topicvisexplorer as tve
from topicvisexplorer.models import SklearnLDAAdapter
from topicvisexplorer.models.protocol import TopicModelData
from topicvisexplorer.prepare import PreparedData

# Toy “sports” vs “cooking” corpora (repeated for enough rows for LDA)
DOCS_A = [
    "the team won the game at the stadium with the coach",
    "league final score and players on the field",
    "basketball tournament running fast break defense",
] * 5

DOCS_B = [
    "bake the bread in the oven with butter and salt",
    "recipe for soup vegetables simmer on the stove",
    "cooking dinner with herbs and tomato sauce in the kitchen",
] * 5


def _fit() -> tuple[PreparedData, PreparedData, TopicModelData, TopicModelData]:
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    v = CountVectorizer(max_df=0.95, min_df=1, max_features=200)
    v.fit(list(DOCS_A) + list(DOCS_B))
    xa = v.transform(DOCS_A)
    xb = v.transform(DOCS_B)
    if xa.shape[0] < 2 or xb.shape[0] < 2:
        print("error: not enough documents for LDA", file=sys.stderr)
        raise SystemExit(1)
    k = 2
    lda_a = LatentDirichletAllocation(
        n_components=k, random_state=0, max_iter=20, learning_method="batch"
    )
    lda_b = LatentDirichletAllocation(
        n_components=k, random_state=1, max_iter=20, learning_method="batch"
    )
    lda_a.fit(xa)
    lda_b.fit(xb)
    ad = SklearnLDAAdapter()
    mda = ad.extract(lda_a, xa, vectorizer=v)
    mdb = ad.extract(lda_b, xb, vectorizer=v)
    pa = tve.prepare(
        topic_term_dists=mda.topic_term_dists,
        doc_topic_dists=mda.doc_topic_dists,
        doc_lengths=mda.doc_lengths,
        vocab=mda.vocab,
        term_frequency=mda.term_frequency,
    )
    pb = tve.prepare(
        topic_term_dists=mdb.topic_term_dists,
        doc_topic_dists=mdb.doc_topic_dists,
        doc_lengths=mdb.doc_lengths,
        vocab=mdb.vocab,
        term_frequency=mdb.term_frequency,
    )
    return pa, pb, mda, mdb


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--smoke", action="store_true", help="Fit both models; do not start the server."
    )
    args = p.parse_args()
    os.environ.setdefault("TVE_EMBEDDING_DISABLE", "1")
    if args.smoke:
        pa, pb, mda, mdb = _fit()
        assert mda.topic_term_dists.shape[0] == mdb.topic_term_dists.shape[0] == 2
        print("Smoke OK — two PreparedData, K =", mda.topic_term_dists.shape[0])
        return 0
    pa, pb, mda, mdb = _fit()
    tve.show(
        [pa, pb],
        raw_texts=[list(DOCS_A), list(DOCS_B)],
        model_data=[mda, mdb],
        scenario_name="03_two_corpora",
        open_browser=not args.no_browser,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
