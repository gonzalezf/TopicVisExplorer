"""Topic-quality metrics displayed in the new collapsible coherence panel.

The visualization always showed similarity between topics but never any
per-topic *quality* signal. The paper (Section 6, "Future Work") calls
out four metrics that should be added to the UI; this module implements
all four:

* **NPMI** -- Normalized Pointwise Mutual Information of top-N keywords.
  Standard intrinsic coherence (Lau et al. 2014). Range ``[-1, 1]``,
  higher is better.
* **C_v** -- Roder, Both & Hinneburg (2015) sliding-window coherence
  using indirect cosine similarity. Range ``[0, 1]``, higher is better.
* **Topic segregation** -- 1 minus the mean pairwise top-keyword Jaccard
  overlap with all *other* topics (paper Section 6). Range ``[0, 1]``,
  higher = topic is more lexically distinct.
* **Document coverage** -- fraction of documents for which this topic is
  the argmax assignment (paper Section 6). Range ``[0, 1]``.

All four are returned as a single :class:`CoherenceReport`.

Implementations are pure NumPy / pandas with no extra deps. NPMI and
C_v are *intrinsic* (computed from the corpus itself), so they need
the original tokenized texts to count co-occurrences.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from .logging import get_logger

if TYPE_CHECKING:
    from .prepare import PreparedData

logger = get_logger(__name__)


def _short_label_from_top_terms(terms: Sequence[str], *, n_words: int = 3) -> str:
    """One-line label from top terms (coherence table); independent of client renames."""
    t = [x for x in terms if x]
    if not t:
        return ""
    return " ".join(t[:n_words])


@dataclass
class CoherenceReport:
    """Per-topic and corpus-level quality scores."""

    npmi: list[float] = field(default_factory=list)
    c_v: list[float] = field(default_factory=list)
    segregation: list[float] = field(default_factory=list)
    coverage: list[float] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)

    @property
    def mean_npmi(self) -> float:
        return float(np.mean(self.npmi)) if self.npmi else float("nan")

    @property
    def mean_c_v(self) -> float:
        return float(np.mean(self.c_v)) if self.c_v else float("nan")

    def to_dict(self) -> dict[str, list[float] | list[str] | float]:
        return {
            "npmi": self.npmi,
            "c_v": self.c_v,
            "segregation": self.segregation,
            "coverage": self.coverage,
            "labels": self.labels,
            "mean_npmi": self.mean_npmi,
            "mean_c_v": self.mean_c_v,
        }


def _doc_token_sets(tokenized_texts: Sequence[Sequence[str]]) -> list[set[str]]:
    return [set(d) for d in tokenized_texts]


def _doc_freq(token_sets: Sequence[set[str]], terms: Iterable[str]) -> dict[str, int]:
    """Document-frequency for ``terms``."""
    terms_set = set(terms)
    counts: dict[str, int] = defaultdict(int)
    for ts in token_sets:
        for t in ts & terms_set:
            counts[t] += 1
    return counts


def _co_doc_freq(
    token_sets: Sequence[set[str]], terms: Iterable[str]
) -> dict[tuple[str, str], int]:
    """Co-document-frequency for unordered pairs of ``terms``."""
    terms_list = list(set(terms))
    co: dict[tuple[str, str], int] = defaultdict(int)
    for ts in token_sets:
        present = sorted(set(ts) & set(terms_list))
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                co[(present[i], present[j])] += 1
    return co


def npmi_per_topic(
    top_terms_per_topic: Sequence[Sequence[str]],
    tokenized_texts: Sequence[Sequence[str]],
    *,
    epsilon: float = 1e-12,
) -> list[float]:
    """NPMI coherence per topic over its top keywords."""
    token_sets = _doc_token_sets(tokenized_texts)
    n = max(len(token_sets), 1)
    all_terms = {t for terms in top_terms_per_topic for t in terms}
    df = _doc_freq(token_sets, all_terms)
    co = _co_doc_freq(token_sets, all_terms)

    scores: list[float] = []
    for terms in top_terms_per_topic:
        terms = list(terms)
        if len(terms) < 2:
            scores.append(float("nan"))
            continue
        s = 0.0
        c = 0
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                a, b = sorted((terms[i], terms[j]))
                p_a = df.get(a, 0) / n
                p_b = df.get(b, 0) / n
                p_ab = co.get((a, b), 0) / n
                if p_a == 0 or p_b == 0 or p_ab == 0:
                    continue
                pmi = math.log((p_ab + epsilon) / (p_a * p_b))
                norm = -math.log(p_ab + epsilon)
                if norm == 0:
                    continue
                s += pmi / norm
                c += 1
        scores.append(s / c if c else float("nan"))
    return scores


def c_v_per_topic(
    top_terms_per_topic: Sequence[Sequence[str]],
    tokenized_texts: Sequence[Sequence[str]],
) -> list[float]:
    """C_v coherence per topic (sliding-window NPMI + indirect cosine).

    Faithful but lightweight implementation of Roder et al. 2015. We use
    *document-window* segmentation (each document is one window) to keep
    the dependency surface tiny - this matches the gensim ``c_v`` choice
    when ``window_size=None``.
    """
    token_sets = _doc_token_sets(tokenized_texts)
    n = max(len(token_sets), 1)
    all_terms = {t for terms in top_terms_per_topic for t in terms}
    df = _doc_freq(token_sets, all_terms)
    co = _co_doc_freq(token_sets, all_terms)

    def npmi(a: str, b: str) -> float:
        a_, b_ = sorted((a, b))
        if a_ == b_:
            return 1.0
        p_a = df.get(a_, 0) / n
        p_b = df.get(b_, 0) / n
        p_ab = co.get((a_, b_), 0) / n
        if p_a == 0 or p_b == 0 or p_ab == 0:
            return 0.0
        return math.log(p_ab / (p_a * p_b)) / -math.log(p_ab)

    scores: list[float] = []
    for terms in top_terms_per_topic:
        terms = list(terms)
        if len(terms) < 2:
            scores.append(float("nan"))
            continue
        npmi_vecs: list[np.ndarray] = []
        for w in terms:
            npmi_vecs.append(np.asarray([npmi(w, x) for x in terms]))
        topic_centroid = np.mean(npmi_vecs, axis=0)
        sims = []
        for v in npmi_vecs:
            denom = np.linalg.norm(v) * np.linalg.norm(topic_centroid)
            sims.append(float(v @ topic_centroid / denom) if denom else 0.0)
        scores.append(float(np.mean(sims)))
    return scores


def segregation_per_topic(top_terms_per_topic: Sequence[Sequence[str]]) -> list[float]:
    """1 - mean(Jaccard with every other topic) per topic."""
    sets = [set(t) for t in top_terms_per_topic]
    K = len(sets)
    if K < 2:
        return [1.0] * K
    out: list[float] = []
    for i in range(K):
        overlaps = []
        for j in range(K):
            if i == j:
                continue
            u = sets[i] | sets[j]
            overlaps.append(len(sets[i] & sets[j]) / len(u) if u else 0.0)
        out.append(1.0 - float(np.mean(overlaps)))
    return out


def coverage_per_topic(doc_topic_dists: np.ndarray) -> list[float]:
    """Fraction of documents argmax-assigned to each topic."""
    n_docs, K = doc_topic_dists.shape
    if n_docs == 0:
        return [0.0] * K
    argmax = np.argmax(doc_topic_dists, axis=1)
    counts = np.bincount(argmax, minlength=K)
    return (counts / n_docs).tolist()


def report(
    prepared: PreparedData,
    tokenized_texts: Sequence[Sequence[str]],
    doc_topic_dists: np.ndarray,
    *,
    n_terms: int = 10,
    lambda_: float = 0.6,
) -> CoherenceReport:
    """Compute all four metrics and return a :class:`CoherenceReport`."""
    K = len(prepared.topic_order)
    top_terms = [prepared.topic_top_terms(k + 1, n=n_terms, lambda_=lambda_) for k in range(K)]
    labels = [_short_label_from_top_terms(terms) for terms in top_terms]
    return CoherenceReport(
        npmi=npmi_per_topic(top_terms, tokenized_texts),
        c_v=c_v_per_topic(top_terms, tokenized_texts),
        segregation=segregation_per_topic(top_terms),
        coverage=coverage_per_topic(np.asarray(doc_topic_dists)),
        labels=labels,
    )
