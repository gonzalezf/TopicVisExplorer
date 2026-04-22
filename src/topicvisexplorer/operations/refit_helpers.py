"""Re-fit helpers for :func:`topicvisexplorer.operations.split` and server HITL.

The split operation needs a ``refit(sub_texts, k_new) -> TopicModelData``
callable that fits a *child* model on a document sub-corpus while keeping
the **parent vocabulary** so :func:`topicvisexplorer.operations.split` can
splice row-aligned matrices.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import numpy as np

from ..models.protocol import TopicModelData


def _tokenize_for_fit(texts: list[str], vocab_set: set[str]) -> list[list[str]]:
    """Tokenize ``texts`` keeping only tokens present in ``vocab_set``.

    Uses whitespace + lowercase splitting (fast, vocab-safe).  For the
    fixture-builder pipeline this is replaced by ``text_cleaner_batch``
    which produces a richer set of tokens; but once the vocabulary is
    fixed at LDA-train time, whitespace splitting is correct for refit
    because the vocabulary itself was built from a more thorough pipeline.
    """
    return [[w for w in t.lower().split() if w in vocab_set] for t in texts]


def refit_static(
    parent: TopicModelData, *, seed: int = 0
) -> Callable[[list[str], int], TopicModelData]:
    """Return a refit callable that splits the *parent's* topic row into k_new
    deterministic child rows without running a new LDA fit.

    Used by scenarios that don't have a real corpus (e.g. the synthetic
    ``tiny_demo``) but still need ``operations.split`` to succeed so the UI
    Split button works end-to-end.

    Algorithm (paper-faithful-enough for the demo):

    1. Take the parent topic-term row (which ``operations.split`` has already
       identified via ``topic_id``) via a closure over parent's data; but here
       we don't know which topic. Instead, this refit samples k_new vectors
       from a Dirichlet over the parent's global term frequency, then lightly
       biases each by a disjoint partition of the parent's top-N terms so the
       resulting child topics are visibly distinct.
    2. Doc-topic matrix for the sub-corpus is a softmax over bag-of-words
       overlap with each child row. This keeps row-stochasticity and gives
       non-degenerate PCoA inputs.
    """
    V = parent.topic_term_dists.shape[1]
    rng = np.random.default_rng(seed)
    global_tf = np.asarray(parent.term_frequency, dtype=np.float64)
    global_tf = global_tf / max(global_tf.sum(), 1e-12)
    vocab_list = list(parent.vocab)
    vocab_index = {t: i for i, t in enumerate(vocab_list)}
    vocab_set = set(vocab_list)

    def refit(sub_texts: list[str], k_new: int) -> TopicModelData:
        assert k_new >= 2, "refit_static requires k_new >= 2"
        # 1. k_new child topic-term rows: Dirichlet(global_tf * alpha) perturbed
        alpha = 50.0
        base = rng.dirichlet(global_tf * alpha + 1e-6, size=k_new)  # (k_new, V)
        # Partition top-M terms of the global tf into k_new disjoint buckets
        # and bump each child's mass on its bucket so they diverge.
        M = min(V, 8 * k_new)
        top_idx = np.argsort(-global_tf)[:M]
        for j in range(k_new):
            bucket = top_idx[j::k_new]
            base[j, bucket] *= 5.0
        child_topic_term = base / base.sum(axis=1, keepdims=True)

        # 2. doc-topic for the sub-corpus: simple whitespace-lowercase tokenization
        n = max(len(sub_texts), 1)
        child_doc_topic = np.full((n, k_new), 1.0 / k_new, dtype=np.float64)
        for i, t in enumerate(sub_texts or []):
            toks = [vocab_index[w] for w in _tokenize_for_fit([t], vocab_set)[0] if w in vocab_index]
            if not toks:
                continue
            # log-likelihood of this doc under each child row
            ll = np.log(child_topic_term[:, toks] + 1e-12).sum(axis=1)
            ll -= ll.max()
            p = np.exp(ll)
            child_doc_topic[i] = p / max(p.sum(), 1e-12)

        child_doc_lengths = np.asarray(
            [max(1, len(str(t).split())) for t in (sub_texts or [""])],
            dtype=np.float64,
        )

        from ..models.protocol import TopicModelData as _TMD

        class _Child:
            topic_term_dists = child_topic_term
            doc_topic_dists = child_doc_topic
            doc_lengths = child_doc_lengths
            vocab = vocab_list
            term_frequency = np.asarray(parent.term_frequency, dtype=np.float64)

        return cast(_TMD, _Child())

    return refit


def refit_gensim_lda(
    model_data: Any,
    *,
    random_state: int = 42,
    passes: int = 5,
) -> Callable[[list[str], int], TopicModelData]:
    """Return ``refit(sub_texts, k_new)`` using gensim :class:`LdaModel`.

    Parameters
    ----------
    model_data:
        The parent :class:`~topicvisexplorer.models.protocol.TopicModelData`.
        A fixed :class:`gensim.corpora.Dictionary` is built with exactly
        ``model_data.vocab`` so the child has shape ``(k_new, V)``.
    random_state, passes:
        Forwarded to ``gensim.models.LdaModel`` (``random_state=`` and
        ``passes=`` only; ``iterations=`` etc. can be added later).

    Returns
    -------
    Callable
        Usable as ``Scenario.extras[\"refit\"]`` for
        :func:`topicvisexplorer.server.app.build_app` / topic split in the
        browser.
    """
    from gensim import corpora, models, utils

    from ..models.adapters.gensim_lda import GensimLDAAdapter

    parent: TopicModelData = cast(TopicModelData, model_data)
    # One synthetic "document" listing every type once → stable ids 0..V-1
    dct: Any = corpora.Dictionary([parent.vocab])
    if len(dct) != len(parent.vocab):
        from ..errors import ValidationError

        raise ValidationError(
            "refit_gensim_lda requires unique tokens in model_data.vocab; "
            f"Dictionary length {len(dct)} != V={len(parent.vocab)}."
        )

    adapter = GensimLDAAdapter()

    def refit(sub_texts: list[str], k_new: int) -> TopicModelData:
        corpus = [dct.doc2bow(utils.simple_preprocess(t, deacc=True)) for t in sub_texts]
        lda = models.LdaModel(
            corpus=corpus,
            id2word=dct,
            num_topics=k_new,
            random_state=random_state,
            passes=passes,
            iterations=50,
        )
        return adapter.extract(lda, corpus, dictionary=dct)

    return refit


# Backwards-compatible name referenced in :mod:`split` docstring
refit_lda = refit_gensim_lda

__all__ = ["refit_gensim_lda", "refit_lda", "refit_static"]
