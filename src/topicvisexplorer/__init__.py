"""TopicVisExplorer - interactive topic-modeling visualization for splitting,
merging, and comparing topics across one or more corpora.

The public API mirrors pyLDAvis with extensions for multi-corpus comparison
and topic refinement::

    import topicvisexplorer as tve

    prepared = tve.prepare(model, corpus, dictionary, texts)
    tve.show(prepared)                     # opens a browser tab on localhost
    tve.show([prepared_a, prepared_b])     # multi-corpus Sankey
    tve.save_html(prepared, "out.html")    # static export
    tve.demo()                             # bundled tiny demo corpus

See :class:`topicvisexplorer.PreparedData` for the data model.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import embeddings, errors, models, similarity
from ._version import __version__
from .logging import configure_logging, get_logger
from .prepare import PreparedData, load, prepare

if TYPE_CHECKING:
    from .embeddings.protocol import EmbeddingBackend
    from .models.protocol import TopicModelData
    from .server.scenarios import Scenario


def show(
    prepared: PreparedData | list[PreparedData] | None = None,
    *,
    raw_texts: list[str] | list[list[str]] | None = None,
    model_data: TopicModelData | list[TopicModelData] | None = None,
    embedding: EmbeddingBackend | None = None,
    texts_file: str | os.PathLike[str] | None = None,
    byo_model: str = "gensim-lda",
    byo_embedding: str = "word2vec",
    sbert_model: str = "all-MiniLM-L6-v2",
    byo_num_topics: int = 5,
    byo_passes: int = 10,
    byo_seed: int = 42,
    byo_csv_text_column: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    scenario_name: str = "user_data",
) -> None:
    """Launch the local server and open the visualization in a browser.

    Parameters
    ----------
    prepared:
        A single :class:`PreparedData` (single-corpus mode) or a list of
        two (multi-corpus Sankey mode). Pass ``None`` to start an empty
        server with only the bundled demo scenarios available.
    raw_texts:
        Raw untokenized documents. Enables Omega-varying topic-similarity
        layout and unlocks the split/merge controls. For single corpus
        pass ``list[str]``; for multi-corpus pass ``[list[str], list[str]]``
        aligned with ``prepared`` and ``model_data``.
    model_data:
        The underlying :class:`TopicModelData` (or list of two for
        multi-corpus). Required alongside ``raw_texts`` so the server
        can precompute the embedding-based similarity grid.
    embedding:
        Pre-trained :class:`EmbeddingBackend`. Optional: if omitted but
        ``raw_texts`` + ``model_data`` are supplied, a Word2Vec is
        trained and cached on first run (``~/.cache/topicvisexplorer``).
        For multi-corpus, a single shared embedding is used across both
        corpora so cosine space stays consistent.
    host, port:
        Network bind address. Defaults to ``localhost:8000``.
    open_browser:
        Open the OS default browser pointed at the new server.
    scenario_name:
        Internal name registered for the user-supplied data; surfaces in
        the URL as ``?scenario=<scenario_name>``.
    texts_file:
        If set, fit a topic model on this file (same formats as ``tve demo
        --texts``) and register it — same path as the CLI. Do not pass
        ``prepared`` at the same time.
    byo_model, byo_embedding, sbert_model, byo_num_topics, byo_passes, byo_seed, byo_csv_text_column:
        BYO options when ``texts_file`` is set (mirror ``--model``,
        ``--embedding``, ``--sbert-model``, ``--num-topics``, ``--passes``,
        ``--seed``, ``--csv-text-column`` on ``tve demo --texts``).

    Notes
    -----
    Blocks until interrupted (Ctrl+C). For non-blocking embedding (e.g.
    Jupyter) wait for ``tve.show_inline()`` in v1.1.

    The first call with ``raw_texts`` trains a Word2Vec (~20s) and
    caches it. Set ``TVE_EMBEDDING_DISABLE=1`` to skip embedding and
    fall back to a flat Jensen-Shannon layout.
    """
    from .server import ServerConfig, build_app, serve

    if texts_file is not None and prepared is not None:
        raise ValueError("Pass either `prepared` or `texts_file`, not both.")

    extras: dict[str, Any] = {}
    if prepared is not None:
        sc = _scenario_from_user_data(
            prepared,
            name=scenario_name,
            raw_texts=raw_texts,
            model_data=model_data,
            embedding=embedding,
        )
        extras[scenario_name] = lambda: sc
    elif texts_file is not None:
        path = Path(os.fspath(texts_file))

        def _lazy_byo() -> Any:
            from .server.byo_corpus import build_scenario_from_textfile

            return build_scenario_from_textfile(
                path,
                name=scenario_name,
                num_topics=byo_num_topics,
                passes=byo_passes,
                seed=byo_seed,
                model=byo_model,
                embedding=byo_embedding,
                sbert_model=sbert_model,
                csv_text_column=byo_csv_text_column,
            )

        extras[scenario_name] = _lazy_byo

    app = build_app(ServerConfig(register_demo=True, extra_scenarios=extras))
    if extras:
        is_multi = (
            prepared is not None
            and isinstance(prepared, list)
            and len(prepared) == 2
        )
        if is_multi:
            browser_path = f"/multicorpora?scenario={scenario_name}&hitl=true"
        else:
            browser_path = f"/singlecorpus?scenario={scenario_name}&hitl=true"
    else:
        browser_path = "/singlecorpus"
    serve(
        app,
        host=host,
        port=port,
        open_browser=open_browser,
        browser_path=browser_path,
    )


def demo(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    corpus: str = "20ng_tiny",
) -> None:
    """Launch the server with the bundled demo scenarios.

    Opens ``/singlecorpus?scenario=<corpus>&hitl=true`` in the browser.
    Supported values for ``corpus`` are ``"20ng_tiny"`` (default - real
    20 Newsgroups subset), ``"bbc_tiny"`` (BBC news, real terms), and
    ``"tiny_demo"`` (synthetic test corpus).
    """
    from .server import ServerConfig, build_app, serve

    app = build_app(ServerConfig(register_demo=True))
    serve(
        app,
        host=host,
        port=port,
        open_browser=open_browser,
        browser_path=f"/singlecorpus?scenario={corpus}&hitl=true",
    )


def save_html(prepared: PreparedData, fileobj: str) -> None:
    """Render a self-contained, server-less HTML snapshot of ``prepared``.

    Phase 2 implementation: writes a minimal HTML page that bundles the
    PreparedData JSON inline. The full interactive split/merge UX still
    requires the server (because it issues backend calls); for a fully
    self-contained interactive export wait for v1.1's web-only build.
    """
    from pathlib import Path

    from .web import LEGACY_STATIC

    template = (LEGACY_STATIC.parent / "templates" / "index.html").read_text()
    html = template.replace("{{ vis_json }}", prepared.to_json())
    Path(fileobj).write_text(html, encoding="utf-8")


def _scenario_from_user_data(
    prepared: PreparedData | list[PreparedData],
    *,
    name: str,
    raw_texts: list[str] | list[list[str]] | None = None,
    model_data: TopicModelData | list[TopicModelData] | None = None,
    embedding: EmbeddingBackend | None = None,
) -> Scenario:
    """Build a :class:`Scenario` from user-supplied PreparedData.

    When only ``prepared`` is supplied the result is a *thin*
    registration: split / merge endpoints will fail because they need
    ``model_data`` + ``raw_texts`` + ``embedding``. Pass those to get a
    fully interactive scenario with Omega-varying layouts.
    """
    from .server.scenarios import Scenario

    if isinstance(prepared, list):
        if len(prepared) != 2:
            raise ValueError("show() expects 1 or 2 PreparedData objects.")
        if raw_texts is None or model_data is None:
            return Scenario(
                name=name,
                is_multi=True,
                prepared=prepared[0],
                prepared_b=prepared[1],
            )
        if not (isinstance(raw_texts, list) and len(raw_texts) == 2):
            raise ValueError(
                "show(): multi-corpus `prepared` requires `raw_texts` as a list of two "
                "lists (one per corpus)."
            )
        if not (isinstance(model_data, list) and len(model_data) == 2):
            raise ValueError(
                "show(): multi-corpus `prepared` requires `model_data` as a list of two."
            )
        return _build_multi_scenario_with_embedding(
            prepared_a=prepared[0],
            prepared_b=prepared[1],
            name=name,
            raw_texts_a=list(raw_texts[0]),  # type: ignore[arg-type]
            raw_texts_b=list(raw_texts[1]),  # type: ignore[arg-type]
            model_data_a=model_data[0],
            model_data_b=model_data[1],
            embedding=embedding,
        )

    if raw_texts is None or model_data is None:
        return Scenario(name=name, is_multi=False, prepared=prepared)

    if isinstance(raw_texts, list) and raw_texts and isinstance(raw_texts[0], list):
        raise ValueError(
            "show(): single-corpus `prepared` requires `raw_texts: list[str]`, "
            "not a nested list."
        )
    if isinstance(model_data, list):
        raise ValueError(
            "show(): single-corpus `prepared` requires a single `model_data`, not a list."
        )

    return _build_single_scenario_with_embedding(
        prepared=prepared,
        name=name,
        raw_texts=raw_texts,  # type: ignore[arg-type]
        model_data=model_data,
        embedding=embedding,
    )


def _build_single_scenario_with_embedding(
    *,
    prepared: PreparedData,
    name: str,
    raw_texts: list[str],
    model_data: TopicModelData,
    embedding: EmbeddingBackend | None,
) -> Scenario:
    """Build a full single-corpus Scenario with an embedding-backed layout.

    Reuses :func:`topicvisexplorer.server.demo_fixtures._train_or_load_embedding`
    so caching, logging, and the ``TVE_EMBEDDING_DISABLE`` escape hatch
    all behave identically to the bundled fixtures.
    """
    import numpy as np
    import pandas as pd

    from .layout import circle_positions
    from .server.demo_fixtures import _light_tokenize_one, _train_or_load_embedding
    from .server.scenarios import Scenario
    from .similarity.baselines import JensenShannonSimilarity

    emb = embedding if embedding is not None else _train_or_load_embedding(name, raw_texts)

    K = int(model_data.topic_term_dists.shape[0])
    N = int(model_data.doc_topic_dists.shape[0])
    raw_texts = list(raw_texts)[:N]
    rel = [
        {
            "doc_id": i,
            "text": raw_texts[i] if i < len(raw_texts) else "",
            **{str(k): float(model_data.doc_topic_dists[i, k]) for k in range(K)},
        }
        for i in range(N)
    ]

    similarity_matrix: dict[float, np.ndarray]
    if emb is not None:
        try:
            from .similarity.embedding import EmbeddingSimilarity, compute_omega_grid

            metric = EmbeddingSimilarity(embedding=emb, text_cleaner=_light_tokenize_one)
            doc_topic_df = pd.DataFrame(model_data.doc_topic_dists)
            grid = compute_omega_grid(
                metric,
                prepared,
                prepared,
                doc_topic_a=doc_topic_df,
                doc_topic_b=doc_topic_df,
                raw_texts_a=raw_texts,
                raw_texts_b=raw_texts,
                n_steps=101,
            )
            similarity_matrix = {
                float(round(k, 2)): np.asarray(v, dtype=np.float64) for k, v in grid.items()
            }
            circ_raw = circle_positions(similarity_matrix)
            circle_positions_str = {str(k): v for k, v in circ_raw.items()}
        except Exception:
            emb = None

    if emb is None:
        metric_jsd = JensenShannonSimilarity()
        matrix = np.asarray(metric_jsd(prepared, prepared), dtype=np.float64)
        similarity_matrix = {round(s / 100.0, 2): matrix.copy() for s in range(101)}
        circ_raw = circle_positions(similarity_matrix)
        circle_positions_str = {str(k): v for k, v in circ_raw.items()}

    return Scenario(
        name=name,
        is_multi=False,
        prepared=prepared,
        model_data=model_data,
        relevant_documents=rel,
        similarity_matrix=similarity_matrix,
        circle_positions=circle_positions_str,
        raw_texts=raw_texts,
        embedding=emb,
    )


def _build_multi_scenario_with_embedding(
    *,
    prepared_a: PreparedData,
    prepared_b: PreparedData,
    name: str,
    raw_texts_a: list[str],
    raw_texts_b: list[str],
    model_data_a: TopicModelData,
    model_data_b: TopicModelData,
    embedding: EmbeddingBackend | None,
) -> Scenario:
    """Build a full multi-corpus Scenario with cross-corpus similarity.

    Mirrors :func:`topicvisexplorer.server.demo_fixtures.build_bbc_vs_20ng`
    but accepts user-supplied data. A single shared Word2Vec is trained
    on the union of both raw text lists so the cosine space is
    consistent across corpora (this is what ``EmbeddingSimilarity``
    expects for cross-corpus comparison).
    """
    import json

    import numpy as np
    import pandas as pd

    from .layout import circle_positions
    from .server.demo_fixtures import _light_tokenize_one, _train_or_load_embedding
    from .server.scenarios import Scenario
    from .similarity.baselines import JensenShannonSimilarity

    emb = (
        embedding
        if embedding is not None
        else _train_or_load_embedding(name, list(raw_texts_a) + list(raw_texts_b))
    )

    def _rows(md: TopicModelData, texts: list[str]) -> list[dict[str, Any]]:
        K = int(md.topic_term_dists.shape[0])
        N = int(md.doc_topic_dists.shape[0])
        return [
            {
                "doc_id": i,
                "text": texts[i] if i < len(texts) else "",
                **{str(k): float(md.doc_topic_dists[i, k]) for k in range(K)},
            }
            for i in range(N)
        ]

    similarity_matrix: dict[float, np.ndarray]
    circle_positions_str: dict[str, list[list[float]]]

    if emb is not None:
        try:
            from .multi import cross_corpus
            from .similarity.embedding import EmbeddingSimilarity

            metric = EmbeddingSimilarity(embedding=emb, text_cleaner=_light_tokenize_one)
            bundle = cross_corpus(
                prepared_a,
                prepared_b,
                metric=metric,
                doc_topic_a=pd.DataFrame(model_data_a.doc_topic_dists),
                doc_topic_b=pd.DataFrame(model_data_b.doc_topic_dists),
                raw_texts_a=raw_texts_a,
                raw_texts_b=raw_texts_b,
                n_omega_steps=101,
            )
            similarity_matrix = {
                float(round(k, 2)): np.asarray(v, dtype=np.float64)
                for k, v in bundle.omega_to_similarity.items()
            }
            # cross_corpus returns a JSON string (layout.get_circle_positions),
            # but Scenario.circle_positions is typed as dict. Decode here.
            circle_positions_str = json.loads(bundle.aligned_positions_json)
        except Exception:
            emb = None

    if emb is None:
        metric_jsd = JensenShannonSimilarity()
        ab = np.asarray(metric_jsd(prepared_a, prepared_b), dtype=np.float64)
        aa = np.asarray(metric_jsd(prepared_a, prepared_a), dtype=np.float64)
        bb = np.asarray(metric_jsd(prepared_b, prepared_b), dtype=np.float64)
        combined = np.block([[aa, ab], [ab.T, bb]])
        similarity_matrix = {round(s / 100.0, 2): ab.copy() for s in range(101)}
        combined_grid = {round(s / 100.0, 2): combined.copy() for s in range(101)}
        circ_raw = circle_positions(combined_grid)
        circle_positions_str = {str(k): v for k, v in circ_raw.items()}

    return Scenario(
        name=name,
        is_multi=True,
        prepared=prepared_a,
        prepared_b=prepared_b,
        model_data=model_data_a,
        model_data_b=model_data_b,
        relevant_documents=_rows(model_data_a, raw_texts_a),
        relevant_documents_b=_rows(model_data_b, raw_texts_b),
        similarity_matrix=similarity_matrix,
        circle_positions=circle_positions_str,
        raw_texts=raw_texts_a,
        embedding=emb,
    )


__all__ = [
    "PreparedData",
    "__version__",
    "configure_logging",
    "demo",
    "embeddings",
    "errors",
    "get_logger",
    "load",
    "models",
    "prepare",
    "save_html",
    "show",
    "similarity",
]
