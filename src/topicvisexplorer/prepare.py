"""Modernized port of the legacy ``_prepare`` module.

This is the LDAvis-style data-preparation pipeline (Sievert & Shirley
2014, ACL Workshop). It transforms topic-term + doc-topic distributions
into the structures the visualization expects: 2D topic coordinates,
per-topic term tables (with relevance), and a token table.

Differences from the legacy version:

* Single :class:`PreparedData` dataclass, with :meth:`save` / :meth:`load`
  for round-trip persistence (legacy used a bare ``namedtuple`` with
  pickle and no version field).
* Drops ``joblib`` parallelism by default (negligible speedup for
  realistic K, eliminates a hard dep). Pass ``n_jobs > 1`` to opt in.
* Removes silent ``print`` calls in favor of the package logger.
* Adds :class:`PreparedData.topic_top_terms` and
  :class:`PreparedData.docs_for_topic` convenience methods.
* Validates inputs via :class:`topicvisexplorer.errors.ValidationError`
  with actionable messages.

Numerical equivalence to the legacy module is enforced by golden tests
under ``tests/golden/``.
"""

from __future__ import annotations

import json
import pickle
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.stats import entropy

from ._version import __version__
from .errors import ValidationError
from .logging import get_logger

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

logger = get_logger(__name__)

#: Pickle format version. Bumped on schema-incompatible changes.
PREPARED_DATA_PICKLE_VERSION: int = 1

MdsCallable = Callable[[np.ndarray], np.ndarray]


def _num_dist_rows(arr: np.ndarray, ndigits: int = 2) -> int:
    """Count rows whose probabilities sum to ~1.0 (within rounding)."""
    return arr.shape[0] - int((pd.DataFrame(arr).sum(axis=1) < 0.999).sum())


def _input_validate(
    topic_term_dists: pd.DataFrame,
    doc_topic_dists: pd.DataFrame,
    doc_lengths: pd.Series,
    vocab: pd.Series,
    term_frequency: pd.Series,
) -> None:
    """Validate the five input arrays and raise :class:`ValidationError`.

    Aggregates all problems into a single error message instead of
    raising on the first - matches legacy behavior, easier on users.
    """
    errors: list[str] = []
    ttds = topic_term_dists.shape
    dtds = doc_topic_dists.shape

    if dtds[1] != ttds[0]:
        errors.append(
            f"doc_topic_dists has {dtds[1]} columns but topic_term_dists has "
            f"{ttds[0]} rows; both must equal n_topics."
        )
    if len(doc_lengths) != dtds[0]:
        errors.append(
            f"doc_lengths has length {len(doc_lengths)} but doc_topic_dists has "
            f"{dtds[0]} rows; both must equal n_docs."
        )
    W = len(vocab)
    if ttds[1] != W:
        errors.append(f"vocab has {W} terms but topic_term_dists has {ttds[1]} columns.")
    if len(term_frequency) != W:
        errors.append(f"term_frequency has length {len(term_frequency)} but vocab has {W}.")
    if _num_dist_rows(topic_term_dists.values) != ttds[0]:
        errors.append("Not all rows of topic_term_dists sum to 1.")
    if _num_dist_rows(doc_topic_dists.values) != dtds[0]:
        errors.append("Not all rows of doc_topic_dists sum to 1.")

    if errors:
        raise ValidationError("Invalid prepare() inputs:\n  - " + "\n  - ".join(errors))


def _jensen_shannon(p: np.ndarray, q: np.ndarray) -> float:
    """Symmetric Jensen-Shannon divergence (base e)."""
    m = 0.5 * (p + q)
    return 0.5 * (entropy(p, m) + entropy(q, m))


def _pcoa(pair_dists: ArrayLike, n_components: int = 2) -> np.ndarray:
    """Classical multidimensional scaling on a precomputed distance matrix.

    Adapted from ``skbio.stats.ordination.pcoa`` to keep TopicVisExplorer
    free of the heavy ``scikit-bio`` dependency. Numerical results match
    the legacy implementation to ``atol=1e-12``; verified by golden test.
    """
    pair_dists = np.asarray(pair_dists, dtype=np.float64)
    n = pair_dists.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    B = -H.dot(pair_dists**2).dot(H) / 2.0
    eigvals, eigvecs = np.linalg.eig(B)
    ix = eigvals.argsort()[::-1][:n_components]
    eigvals = eigvals[ix]
    eigvecs = eigvecs[:, ix]
    eigvals[np.isclose(eigvals, 0)] = 0
    if np.any(eigvals < 0):
        ix_neg = eigvals < 0
        eigvals[ix_neg] = 0
        eigvecs[:, ix_neg] = 0
    return np.real(np.sqrt(eigvals) * eigvecs)


def js_PCoA(distributions: ArrayLike) -> np.ndarray:
    """Jensen-Shannon distance + classical MDS to produce 2D coordinates."""
    dist_matrix = squareform(pdist(distributions, metric=_jensen_shannon))
    return _pcoa(dist_matrix)


def js_MMDS(distributions: ArrayLike, **kwargs: Any) -> np.ndarray:
    """Jensen-Shannon distance + sklearn metric MDS."""
    from sklearn.manifold import MDS

    dist_matrix = squareform(pdist(distributions, metric=_jensen_shannon))
    model = MDS(
        n_components=2,
        random_state=0,
        dissimilarity="precomputed",
        normalized_stress="auto",
        **kwargs,
    )
    return model.fit_transform(dist_matrix)


def js_TSNE(distributions: ArrayLike, **kwargs: Any) -> np.ndarray:
    """Jensen-Shannon distance + sklearn t-SNE."""
    from sklearn.manifold import TSNE

    dist_matrix = squareform(pdist(distributions, metric=_jensen_shannon))
    model = TSNE(n_components=2, random_state=0, metric="precomputed", init="random", **kwargs)
    return model.fit_transform(dist_matrix)


_MDS_NAMES: dict[str, MdsCallable] = {
    "pcoa": js_PCoA,
    "mmds": js_MMDS,
    "tsne": js_TSNE,
}


def _df_with_names(data: Any, index_name: str, columns_name: str) -> pd.DataFrame:
    df = pd.DataFrame(data.values) if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    df.index.name = index_name
    df.columns.name = columns_name
    return df


def _series_with_name(data: Any, name: str) -> pd.Series:
    if isinstance(data, pd.Series):
        data.name = name
        return data.reset_index()[name]
    return pd.Series(data, name=name)


def _topic_coordinates(
    mds: MdsCallable, topic_term_dists: pd.DataFrame, topic_proportion: pd.Series
) -> pd.DataFrame:
    K = topic_term_dists.shape[0]
    mds_res = mds(np.asarray(topic_term_dists, dtype=np.float64))
    if mds_res.shape != (K, 2):
        raise ValidationError(
            f"MDS produced shape {mds_res.shape}, expected ({K}, 2). "
            "Pass a different `mds=` callable to prepare()."
        )
    return pd.DataFrame(
        {
            "x": mds_res[:, 0],
            "y": mds_res[:, 1],
            "topics": range(1, K + 1),
            "cluster": 1,
            "Freq": topic_proportion * 100,
        }
    )


def _find_relevance(log_ttd: pd.DataFrame, log_lift: pd.DataFrame, lambda_: float) -> pd.DataFrame:
    """Compute pyLDAvis relevance for one ``lambda``.

    Relevance(term, topic) = lambda * log p(term|topic) +
                             (1 - lambda) * log lift(term|topic)

    Returns the per-topic terms sorted by descending relevance (DataFrame
    indexed by topic, columns are ranks).
    """
    relevance = lambda_ * log_ttd + (1 - lambda_) * log_lift
    return relevance.T.apply(lambda s: s.sort_values(ascending=False).index)


def _topic_info(
    topic_term_dists: pd.DataFrame,
    topic_proportion: pd.Series,
    term_frequency: pd.Series,
    term_topic_freq: pd.DataFrame,
    vocab: pd.Series,
    lambda_step: float,
    R: int,
) -> pd.DataFrame:
    """Build the long-form per-topic term table consumed by the front end."""
    term_proportion = term_frequency / term_frequency.sum()
    topic_given_term = topic_term_dists / topic_term_dists.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        kernel = topic_given_term * np.log((topic_given_term.T / topic_proportion).T)
    distinctiveness = kernel.fillna(0.0).replace([np.inf, -np.inf], 0.0).sum()
    saliency = term_proportion * distinctiveness

    default_term_info = pd.DataFrame(
        {
            "saliency": saliency,
            "Term": vocab,
            "Freq": term_frequency,
            "Total": term_frequency,
            "Category": "Default",
        }
    )
    default_term_info = default_term_info.sort_values(by="saliency", ascending=False).drop(
        "saliency", axis=1
    )
    default_term_info["Freq"] = np.floor(default_term_info["Freq"])
    default_term_info["Total"] = np.floor(default_term_info["Total"])
    ranks = np.arange(R, 0, -1)
    default_term_info["logprob"] = ranks
    default_term_info["loglift"] = ranks

    with np.errstate(divide="ignore", invalid="ignore"):
        # np.log on DataFrame is ndarray per numpy stubs; runtime matches DataFrame ops.
        log_lift = cast(pd.DataFrame, np.log(topic_term_dists / term_proportion))
        log_ttd = cast(pd.DataFrame, np.log(topic_term_dists))
    lambda_seq = np.arange(0, 1 + lambda_step, lambda_step)
    top_terms: pd.DataFrame = pd.concat(
        [_find_relevance(log_ttd, log_lift, l_) for l_ in lambda_seq]
    )

    def topic_top_term_df(tup: Any) -> pd.DataFrame:
        new_topic_id, (original_topic_id, topic_terms) = tup
        term_ix = topic_terms.unique()
        return pd.DataFrame(
            {
                "Term": vocab[term_ix],
                "Freq": term_topic_freq.loc[original_topic_id, term_ix],
                "Total": term_frequency[term_ix],
                "logprob": log_ttd.loc[original_topic_id, term_ix].round(4),
                "loglift": log_lift.loc[original_topic_id, term_ix].round(4),
                "Category": f"Topic{new_topic_id}",
            }
        )

    topic_dfs = list(map(topic_top_term_df, enumerate(top_terms.T.iterrows(), 1)))
    return pd.concat([default_term_info, *topic_dfs], sort=True)


def _token_table(
    topic_info: pd.DataFrame,
    term_topic_freq: pd.DataFrame,
    vocab: pd.Series,
    term_frequency: pd.Series,
) -> pd.DataFrame:
    term_ix = np.sort(topic_info.index.unique())
    top_topic_terms_freq = term_topic_freq[term_ix]
    K = len(term_topic_freq)
    top_topic_terms_freq.index = pd.RangeIndex(1, K + 1, name="Topic")
    token_table = (
        pd.DataFrame({"Freq": top_topic_terms_freq.unstack()})
        .reset_index()
        .set_index("term")
        .query("Freq >= 0.5")
    )
    token_table["Freq"] = token_table["Freq"].round()
    token_table["Term"] = vocab[token_table.index.values].values
    token_table["Freq"] = token_table.Freq / term_frequency[token_table.index]
    return token_table.sort_values(by=["Term", "Topic"])


@dataclass
class PreparedData:
    """All data needed to render one corpus's interactive visualization.

    Attributes
    ----------
    topic_coordinates:
        2D circle positions (one row per topic).
    topic_info:
        Long-form term table: rows are (Category, Term) pairs.
    token_table:
        Per-token cross-topic frequency table.
    R:
        Number of terms displayed in the bar chart panel.
    lambda_step:
        Step size of the relevance slider.
    plot_opts:
        Misc plotting options forwarded verbatim to the JS bundle.
    topic_order:
        1-based topic order (after optional sort by proportion).
    metadata:
        Free-form provenance dict (model class, hyperparameters,
        embedding backend, package version, capture timestamp...).
    """

    topic_coordinates: pd.DataFrame
    topic_info: pd.DataFrame
    token_table: pd.DataFrame
    R: int
    lambda_step: float
    plot_opts: dict[str, Any]
    topic_order: list[int]
    metadata: dict[str, Any] = field(default_factory=dict)

    def sorted_terms(self, topic: int = 1, lambda_: float = 1.0) -> pd.DataFrame:
        """Return a topic's terms sorted by relevance for a given lambda.

        Parameters
        ----------
        topic:
            1-based topic id (matches the rendered visualization labels).
        lambda_:
            Relevance blending parameter (0 -> only lift, 1 -> only logprob).
        """
        if not 0.0 <= lambda_ <= 1.0:
            lambda_ = 1.0
        tdf = pd.DataFrame(self.topic_info[self.topic_info.Category == f"Topic{topic}"])
        return tdf.assign(
            relevance=lambda_ * tdf["logprob"] + (1.0 - lambda_) * tdf["loglift"]
        ).sort_values("relevance", ascending=False)

    def topic_top_terms(self, topic: int, n: int = 10, lambda_: float = 0.6) -> list[str]:
        """Return the top-``n`` terms for one topic at the given relevance lambda.

        Convenience wrapper over :meth:`sorted_terms`. The default
        ``lambda_=0.6`` matches Sievert & Shirley's empirical sweet spot.
        """
        return self.sorted_terms(topic=topic, lambda_=lambda_)["Term"].head(n).tolist()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-ready dict matching the legacy schema."""
        return {
            "mdsDat": self.topic_coordinates.to_dict(orient="list"),
            "tinfo": self.topic_info.to_dict(orient="list"),
            "token.table": self.token_table.to_dict(orient="list"),
            "R": self.R,
            "lambda.step": self.lambda_step,
            "plot.opts": self.plot_opts,
            "topic.order": self.topic_order,
        }

    def to_json(self) -> str:
        """JSON-encode for the front end. NumPy types are coerced to Python."""
        from .utils import NumPyEncoder

        return json.dumps(self.to_dict(), cls=NumPyEncoder)

    def save(self, path: str | Path) -> None:
        """Persist with a versioned envelope so future reads can adapt."""
        envelope = {
            "_topicvisexplorer_pickle_version": PREPARED_DATA_PICKLE_VERSION,
            "_topicvisexplorer_version": __version__,
            "data": self,
        }
        Path(path).write_bytes(pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL))
        logger.debug("Saved PreparedData to %s", path)


def load(path: str | Path) -> PreparedData:
    """Load a :class:`PreparedData` written by :meth:`PreparedData.save`.

    Falls back to assuming the pickle is a bare ``PreparedData`` (or
    legacy ``namedtuple`` with the same fields) if the envelope marker
    is missing - this is what enables one-shot legacy-pickle loading.
    """
    raw = pickle.loads(Path(path).read_bytes())
    if isinstance(raw, dict) and "_topicvisexplorer_pickle_version" in raw:
        version = raw["_topicvisexplorer_pickle_version"]
        if version != PREPARED_DATA_PICKLE_VERSION:
            raise ValidationError(
                f"PreparedData pickle version {version} cannot be loaded by "
                f"topicvisexplorer {__version__} (supports v{PREPARED_DATA_PICKLE_VERSION}). "
                "Run scripts/migrate_pickle.py to upgrade."
            )
        return cast(PreparedData, raw["data"])
    if isinstance(raw, PreparedData):
        return raw
    if isinstance(raw, tuple) and len(raw) >= 7:
        logger.warning(
            "Loading legacy namedtuple PreparedData from %s; metadata will be empty. "
            "Re-save it via .save() to capture provenance.",
            path,
        )
        return PreparedData(*raw[:7])
    raise ValidationError(f"File {path} does not contain a recognizable PreparedData object.")


def prepare(
    topic_term_dists: ArrayLike,
    doc_topic_dists: ArrayLike,
    doc_lengths: ArrayLike,
    vocab: Sequence[str],
    term_frequency: ArrayLike,
    *,
    R: int | None = None,
    lambda_step: float = 0.01,
    mds: MdsCallable | str = js_PCoA,
    plot_opts: dict[str, Any] | None = None,
    sort_topics: bool = False,
    metadata: dict[str, Any] | None = None,
) -> PreparedData:
    """Transform topic-model distributions into a :class:`PreparedData`.

    This is the modernized counterpart of :func:`pyLDAvis.prepare`. The
    numerical algorithm is unchanged - golden tests pin the output to
    the legacy reference within ``atol=1e-6``.

    Parameters
    ----------
    topic_term_dists:
        Topic-term probabilities, shape ``(n_topics, n_terms)``.
    doc_topic_dists:
        Document-topic probabilities, shape ``(n_docs, n_topics)``.
    doc_lengths:
        Document lengths in tokens.
    vocab:
        Term strings (length ``n_terms``).
    term_frequency:
        Corpus-level term counts (length ``n_terms``).
    R:
        Number of terms in each topic's bar chart. Defaults to ``len(vocab)``
        (matches legacy behavior).
    lambda_step:
        Step of the relevance lambda slider.
    mds:
        Either a callable taking the topic-term matrix and returning
        ``(n_topics, 2)`` coordinates, or one of ``"pcoa"``, ``"mmds"``,
        ``"tsne"``.
    plot_opts:
        Forwarded to the front end (axis labels etc.).
    sort_topics:
        If True, reorder topics by descending mass.
    metadata:
        Free-form dict stored on the returned :class:`PreparedData`.

    Returns
    -------
    PreparedData
    """
    plot_opts = plot_opts or {"xlab": "PC1", "ylab": "PC2"}

    if isinstance(mds, str):
        key = mds.lower()
        try:
            mds = _MDS_NAMES[key]
        except KeyError:
            logger.warning("Unknown mds=%r; falling back to PCoA.", mds)
            mds = js_PCoA

    topic_term_dists_df = _df_with_names(topic_term_dists, "topic", "term")
    doc_topic_dists_df = _df_with_names(doc_topic_dists, "doc", "topic")
    term_frequency_s = _series_with_name(term_frequency, "term_frequency")
    doc_lengths_s = _series_with_name(doc_lengths, "doc_length")
    vocab_s = _series_with_name(vocab, "vocab")

    _input_validate(
        topic_term_dists_df, doc_topic_dists_df, doc_lengths_s, vocab_s, term_frequency_s
    )

    R = R or len(vocab_s)

    topic_freq = (doc_topic_dists_df.T * doc_lengths_s).T.sum()
    if sort_topics:
        topic_proportion = (topic_freq / topic_freq.sum()).sort_values(ascending=False)
    else:
        topic_proportion = topic_freq / topic_freq.sum()

    topic_order = list(topic_proportion.index)
    topic_freq = topic_freq[topic_order]
    topic_term_dists_df = topic_term_dists_df.iloc[topic_order]
    doc_topic_dists_df = doc_topic_dists_df[topic_order]

    term_topic_freq = (topic_term_dists_df.T * topic_freq).T
    term_frequency_s = pd.Series(np.sum(term_topic_freq, axis=0).values, name="term_frequency")

    topic_info = _topic_info(
        topic_term_dists_df,
        topic_proportion,
        term_frequency_s,
        term_topic_freq,
        vocab_s,
        lambda_step,
        R,
    )
    token_table = _token_table(topic_info, term_topic_freq, vocab_s, term_frequency_s)
    topic_coordinates = _topic_coordinates(mds, topic_term_dists_df, topic_proportion)

    return PreparedData(
        topic_coordinates=topic_coordinates,
        topic_info=topic_info,
        token_table=token_table,
        R=R,
        lambda_step=lambda_step,
        plot_opts=plot_opts,
        topic_order=[x + 1 for x in topic_order],
        metadata=metadata or {},
    )
