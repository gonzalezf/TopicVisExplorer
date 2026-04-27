#!/usr/bin/env python3
"""
Neural topic models (BERTopic, ETM, CTM) → `tve.prepare()` → `tve.show()`.

Demonstrates the **Python-API path** for fitting a neural topic model and
passing it through the TopicVisExplorer adapter to the interactive browser UI.
Contrasts with the CLI path (``tve demo --texts … --model bertopic``).

**Prerequisites:** install the ``[full]`` extra from a git clone::

    pip install -e ".[full]"
    uv run python -m spacy download en_core_web_sm   # if using gensim-lda refit

**From the repository root**::

    uv run python examples/06_bertopic_show.py
    uv run python examples/06_bertopic_show.py --no-browser
    uv run python examples/06_bertopic_show.py --smoke

``--smoke`` fits the model and runs the adapter only; it does **not** start
the server (safe for CI when ``[full]`` deps are present).

Note
----
Only BERTopic is demonstrated interactively here. ETM and CTM are shown in
``--smoke`` mode to illustrate the adapter API. See the inline CTM note for
the extra step required when calling ``CTMAdapter``.
"""

from __future__ import annotations

import argparse
import sys

# ---------------------------------------------------------------------------
# Toy corpus — enough documents for BERTopic's HDBSCAN to find clusters.
# ---------------------------------------------------------------------------
DOCS_TECH = [
    "machine learning models learn from labeled training data",
    "deep neural networks have multiple hidden layers",
    "gradient descent optimizes the loss function during training",
    "convolutional networks excel at image classification tasks",
    "transformers use attention to model long-range dependencies",
    "natural language processing enables computers to understand text",
    "reinforcement learning agents maximize cumulative reward signals",
    "transfer learning reuses pretrained weights on new tasks",
] * 4  # repeat to give HDBSCAN enough samples

DOCS_BIO = [
    "proteins are made of amino acid chains folded into 3D structures",
    "DNA encodes genetic information in nucleotide sequences",
    "enzymes catalyze biochemical reactions inside living cells",
    "cell membranes regulate the transport of molecules in and out",
    "mitosis is the process by which cells divide and replicate",
    "ribosomes translate messenger RNA into polypeptide chains",
    "photosynthesis converts sunlight into chemical energy in plants",
    "immune cells recognize and neutralize foreign antigens",
] * 4

ALL_DOCS = DOCS_TECH + DOCS_BIO


def _check_full_extras() -> None:
    try:
        import bertopic  # noqa: F401
    except ImportError:
        print(
            "error: 'bertopic' is not installed.\n"
            "Install the [full] extra:  pip install -e \".[full]\"",
            file=sys.stderr,
        )
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# BERTopic
# ---------------------------------------------------------------------------


def _fit_bertopic() -> tuple:  # returns (model, model_data, prepared)
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer

    import topicvisexplorer as tve
    from topicvisexplorer.models import BERTopicAdapter

    print("Fitting BERTopic …")
    model = BERTopic(
        vectorizer_model=CountVectorizer(stop_words="english"),
        min_topic_size=4,
        verbose=False,
        calculate_probabilities=True,
    )
    model.fit(ALL_DOCS)

    adapter = BERTopicAdapter()
    model_data = adapter.extract(model, corpus=None, texts=ALL_DOCS)

    prepared = tve.prepare(
        topic_term_dists=model_data.topic_term_dists,
        doc_topic_dists=model_data.doc_topic_dists,
        doc_lengths=model_data.doc_lengths,
        vocab=model_data.vocab,
        term_frequency=model_data.term_frequency,
    )
    K = model_data.topic_term_dists.shape[0]
    print(f"BERTopic: {K} topics, vocab size {len(model_data.vocab)}")
    print("Top terms per topic:")
    for topic_id in prepared.topic_order:
        terms = prepared.topic_top_terms(topic_id, n=5)
        print(f"  Topic {topic_id}: {', '.join(terms)}")
    return model, model_data, prepared


# ---------------------------------------------------------------------------
# ETM smoke illustration
# ---------------------------------------------------------------------------


def _smoke_etm() -> None:
    """Show the ETM adapter API (smoke only — training is slow without GPU)."""
    try:
        from embedded_topic_model.models.etm import ETM  # type: ignore[import-untyped]
    except ImportError:
        print("  ETM: skipped (embedded_topic_model not installed)")
        return

    from topicvisexplorer.models import ETMAdapter
    from topicvisexplorer.server.byo_corpus import _etm_train_data_from_texts

    print("  Fitting ETM (CPU, 3 epochs) …")
    train_data, vocab = _etm_train_data_from_texts(ALL_DOCS)
    etm = ETM(vocabulary=vocab, embeddings=None, num_topics=2, batch_size=16, epochs=3)
    etm.fit(train_data)
    md = ETMAdapter().extract(etm, corpus=None, texts=ALL_DOCS, vocabulary=vocab)
    print(f"  ETM: {md.topic_term_dists.shape[0]} topics, OK")


# ---------------------------------------------------------------------------
# CTM smoke illustration — NOTE the required extra step
# ---------------------------------------------------------------------------


def _smoke_ctm() -> None:
    """Show the CTM adapter API (smoke only).

    CTM GOTCHA
    ----------
    ``CTMAdapter.extract()`` does **not** call the model's inference internally.
    You must run ``ctm.get_doc_topic_distribution(training_data, n_samples=5)``
    yourself and pass the result as ``doc_topic_dists=``.  Omitting this
    argument raises a :class:`~topicvisexplorer.errors.ValidationError` with
    an actionable message pointing you here.
    """
    try:
        from contextualized_topic_models.models.ctm import CombinedTM  # type: ignore[import-untyped]
        from contextualized_topic_models.utils.data_preparation import (  # type: ignore[import-untyped]
            TopicModelDataPreparation,
        )
    except ImportError:
        print("  CTM: skipped (contextualized_topic_models not installed)")
        return

    import numpy as np

    from topicvisexplorer.models import CTMAdapter

    print("  Fitting CTM (CPU, 3 epochs) …")
    prep = TopicModelDataPreparation("all-MiniLM-L6-v2")
    training = prep.fit(text_for_contextual=ALL_DOCS, text_for_bow=ALL_DOCS)
    ctm = CombinedTM(
        bow_size=len(prep.vocab),
        contextual_size=int(training.X_contextual.shape[1]),
        n_components=2,
        num_epochs=3,
        batch_size=16,
    )
    ctm.fit(training)

    # REQUIRED: obtain doc-topic posteriors and pass them explicitly.
    dtd = np.asarray(
        ctm.get_doc_topic_distribution(training, n_samples=5), dtype=np.float64
    )
    md = CTMAdapter().extract(
        ctm,
        corpus=None,
        texts=ALL_DOCS,
        doc_topic_dists=dtd,
        vocabulary=list(prep.vocab),
    )
    print(f"  CTM: {md.topic_term_dists.shape[0]} topics, OK")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-browser", action="store_true", help="Do not open a tab.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Fit + extract only; do not start the server.",
    )
    p.add_argument(
        "--also-etm-ctm",
        action="store_true",
        help="Also smoke-test ETM and CTM adapters (slow on CPU; skipped by default).",
    )
    args = p.parse_args()

    _check_full_extras()

    _model, model_data, prepared = _fit_bertopic()

    if args.also_etm_ctm:
        print("\nETM adapter smoke:")
        _smoke_etm()
        print("\nCTM adapter smoke:")
        _smoke_ctm()

    if args.smoke:
        print("\nSmoke OK — BERTopic fit+extract complete; server not started (--smoke).")
        return 0

    import topicvisexplorer as tve

    tve.show(
        prepared,
        raw_texts=ALL_DOCS,
        model_data=model_data,
        scenario_name="06_bertopic",
        open_browser=not args.no_browser,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
