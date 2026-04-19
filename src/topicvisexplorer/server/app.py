"""FastAPI app factory.

The app is intentionally constructed by a *factory* (``build_app``) so
multiple instances can coexist in the same process - tests use this to
get an isolated app with an ephemeral session store and scenario
registry.

Endpoint inventory (all preserved from the legacy Flask app's
``TestView``, sans the user-study routes):

| Method | Path                                         | Notes                       |
|--------|----------------------------------------------|-----------------------------|
| GET    | ``/``                                        | Redirect to /singlecorpus   |
| GET    | ``/health``                                  | New: liveness               |
| GET    | ``/singlecorpus``                            | Single-corpus visualization |
| GET    | ``/multicorpora``                            | Multi-corpus visualization  |
| GET    | ``/SingleCorpus_documents``                  | List of relevant documents  |
| GET    | ``/MultiCorpora_documents_1``                | Documents for corpus A      |
| GET    | ``/MultiCorpora_documents_2``                | Documents for corpus B      |
| GET    | ``/get_topic_similarity_matrix_single_corpus`` | Matrix at one ``omega``   |
| POST   | ``/Topic_Splitting_Document_Based``          | Split a topic               |
| POST   | ``/get_new_topic_vector``                    | Merge two topics            |
| POST   | ``/undo_merge_splitting``                    | Undo last destructive op    |
| POST   | ``/Add_Remove_Word``                         | New: add/remove word        |
| POST   | ``/Exclude_Document``                        | New: exclude doc from topic |

The static blob is mounted at ``/static`` from the bundled
``topicvisexplorer.web.legacy.static`` directory so the JS that talks
to these endpoints continues to work unchanged.
"""

from __future__ import annotations

import json as _json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from .._version import __version__
from ..errors import TopicVisExplorerError, ValidationError
from ..logging import get_logger
from ..utils import NumPyEncoder
from ..web import LEGACY_STATIC, LEGACY_TEMPLATES, MODERN_DIST, has_modern_bundle
from .scenarios import Scenario, ScenarioLoader, ScenarioRegistry
from .schemas import (
    AddRemoveWordRequest,
    ExcludeDocumentRequest,
    HealthResponse,
    TopicMergeRequest,
    TopicSplitRequest,
)
from .sessions import SessionState, SessionStore

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

SESSION_COOKIE_NAME = "tve_session"

#: Default omega used by the legacy front end when none is passed.
DEFAULT_OMEGA: float = 0.0

#: Default relevance lambda for term ranking (Sievert & Shirley 2014).
DEFAULT_RELEVANCE_LAMBDA: float = 0.6

#: Default top-N used by the similarity computation.
DEFAULT_TOPN_TERMS: int = 20
DEFAULT_TOPK_DOCUMENTS: int = 20


@dataclass
class ServerConfig:
    """Runtime knobs for :func:`build_app`.

    Attributes
    ----------
    title:
        FastAPI ``title`` shown in the auto-generated docs.
    max_sessions:
        Maximum concurrent sessions kept in memory.
    session_ttl_seconds:
        How long a session may stay idle before eviction.
    cors_allow_origins:
        List of origins to add to a permissive CORS middleware. Set to
        ``[]`` (default) to skip the middleware entirely (browser local
        usage doesn't need it).
    register_demo:
        If True, register the bundled tiny demo scenarios so
        ``/singlecorpus?scenario=tiny_demo`` works out of the box.
    extra_scenarios:
        Optional ``{name: loader}`` dict to merge into the registry.
    """

    title: str = "TopicVisExplorer"
    max_sessions: int = 16
    session_ttl_seconds: float | None = 3600.0
    cors_allow_origins: list[str] = field(default_factory=list)
    register_demo: bool = True
    extra_scenarios: dict[str, ScenarioLoader] = field(default_factory=dict)
    #: Front-end track to serve. ``"auto"`` (default) prefers the modern
    #: bundled ``web/dist/`` if present, else falls back to the legacy
    #: paper-version template. ``"legacy"`` and ``"modern"`` force one or
    #: the other (raising at startup if ``"modern"`` is requested but the
    #: bundle is missing).
    frontend: str = "auto"


def build_app(config: ServerConfig | None = None) -> FastAPI:
    """Construct a fully wired FastAPI app.

    Parameters
    ----------
    config:
        Optional :class:`ServerConfig`. ``None`` uses defaults.

    Returns
    -------
    FastAPI
        Ready to be passed to ``uvicorn.run`` (or :func:`serve`).
    """
    config = config or ServerConfig()

    app = FastAPI(
        title=config.title,
        version=__version__,
        description=(
            "Interactive topic-modeling visualization. The HTTP contract is "
            "frozen for v1.0 to keep the React/Vite v1.1 rewrite drop-in."
        ),
    )

    if config.cors_allow_origins:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    sessions = SessionStore(
        max_sessions=config.max_sessions, ttl_seconds=config.session_ttl_seconds
    )
    registry = ScenarioRegistry()
    if config.register_demo:
        _register_bundled_demo(registry)
    for name, loader in config.extra_scenarios.items():
        registry.register(name, loader)

    app.state.sessions = sessions
    app.state.scenarios = registry
    app.state.config = config

    app.mount("/static", StaticFiles(directory=str(LEGACY_STATIC)), name="static")

    # Resolve which front-end template + bundle to serve. The decision is
    # made once at startup; the chosen template name is stored on
    # ``app.state`` so routes can pick it up cheaply per request.
    if config.frontend == "modern" and not has_modern_bundle():
        raise RuntimeError(
            f"frontend='modern' requested but no Vite bundle found at {MODERN_DIST}. "
            "Run `cd frontend && npm install && npm run build` first, or pass "
            "frontend='legacy' to force the paper-version template."
        )
    use_modern = config.frontend == "modern" or (config.frontend == "auto" and has_modern_bundle())
    if use_modern:
        # Mount the bundled JS/CSS alongside the legacy /static blob so
        # the modern template can fetch them at /dist/tve.js etc.
        app.mount("/dist", StaticFiles(directory=str(MODERN_DIST)), name="dist")
        template_name = "index_v1.html"
        logger.info("Serving modern Vite bundle from %s", MODERN_DIST)
    else:
        template_name = "index.html"
        logger.info("Serving legacy paper-version template from %s", LEGACY_TEMPLATES)
    app.state.template_name = template_name
    app.state.use_modern = use_modern

    templates = Jinja2Templates(directory=str(LEGACY_TEMPLATES))

    class _SessionMiddleware(BaseHTTPMiddleware):
        """Attach :class:`SessionState` to ``request.state.session``.

        The cookie is set on the *outgoing* response - which works for
        every response type (HTML, JSON, redirect) unlike the FastAPI
        ``response: Response`` parameter trick.
        """

        async def dispatch(self, request: Request, call_next: Any) -> Any:
            sid_in = request.cookies.get(SESSION_COOKIE_NAME)
            state = sessions.get_or_create(sid_in)
            request.state.session = state
            response = await call_next(request)
            if state.session_id != sid_in:
                response.set_cookie(
                    SESSION_COOKIE_NAME, state.session_id, httponly=True, samesite="lax"
                )
            return response

    app.add_middleware(_SessionMiddleware)

    @app.exception_handler(TopicVisExplorerError)
    async def _tve_exc(_: Request, exc: TopicVisExplorerError) -> JSONResponse:
        logger.warning("Domain error: %s", exc)
        return JSONResponse(
            status_code=400, content={"error": exc.__class__.__name__, "message": str(exc)}
        )

    def _get_session(request: Request) -> SessionState:
        return request.state.session

    SessionDep = Depends(_get_session)

    def _require_single(state: SessionState) -> Scenario:
        sc = state.single_corpus.get("scenario")
        if sc is None:
            raise HTTPException(
                400,
                "No single-corpus scenario loaded for this session. "
                "Visit /singlecorpus?scenario=<name> first.",
            )
        return sc

    def _require_multi(state: SessionState) -> Scenario:
        sc = state.multi_corpora.get("scenario")
        if sc is None:
            raise HTTPException(
                400,
                "No multi-corpora scenario loaded for this session. "
                "Visit /multicorpora?scenario=<name> first.",
            )
        return sc

    @app.get("/", include_in_schema=False)
    async def index() -> RedirectResponse:
        return RedirectResponse("/singlecorpus")

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=__version__,
            n_sessions=len(sessions),
            max_sessions=config.max_sessions,
        )

    @app.get("/scenarios")
    async def list_scenarios() -> dict[str, list[str]]:
        return {"scenarios": registry.names()}

    @app.get("/singlecorpus", response_class=HTMLResponse)
    async def single_corpus(
        request: Request,
        scenario: str = "tiny_demo",
        hitl: str = "true",
        state: SessionState = SessionDep,
    ) -> Any:
        loaded = registry.load(scenario)
        if loaded.is_multi:
            raise HTTPException(400, f"Scenario {scenario!r} is multi-corpus.")
        state.single_corpus["scenario"] = loaded
        state.single_corpus["history"] = []

        prepared_dict = loaded.require("prepared").to_dict()
        prepared_dict["human_in_the_loop"] = hitl.lower() != "false"
        topic_order = prepared_dict["topic.order"]
        return templates.TemplateResponse(
            request,
            app.state.template_name,
            _build_template_context(
                state=state,
                vis_json=_json.dumps(prepared_dict, cls=NumPyEncoder),
                vis_json_2="null",
                topic_order=topic_order,
                topic_order_2=None,
                new_circle_positions=loaded.circle_positions,
                matrix_sankey="{}",
                type_vis=1,
            ),
        )

    @app.get("/multicorpora", response_class=HTMLResponse)
    async def multi_corpora(
        request: Request,
        scenario: str = "tiny_multi_demo",
        state: SessionState = SessionDep,
    ) -> Any:
        loaded = registry.load(scenario)
        if not loaded.is_multi:
            raise HTTPException(400, f"Scenario {scenario!r} is single-corpus.")
        state.multi_corpora["scenario"] = loaded

        prep_a = loaded.require("prepared").to_dict()
        prep_b = loaded.require("prepared_b").to_dict()
        sankey = _build_sankey_dict(loaded.similarity_matrix)
        return templates.TemplateResponse(
            request,
            app.state.template_name,
            _build_template_context(
                state=state,
                vis_json=_json.dumps(prep_a, cls=NumPyEncoder),
                vis_json_2=_json.dumps(prep_b, cls=NumPyEncoder),
                topic_order=prep_a["topic.order"],
                topic_order_2=prep_b["topic.order"],
                new_circle_positions=loaded.circle_positions,
                matrix_sankey=_json.dumps(sankey),
                type_vis=2,
            ),
        )

    @app.get("/SingleCorpus_documents")
    async def single_corpus_documents(state: SessionState = SessionDep) -> JSONResponse:
        sc = _require_single(state)
        return JSONResponse(content=sc.relevant_documents)

    @app.get("/MultiCorpora_documents_1")
    async def multi_corpora_documents_1(state: SessionState = SessionDep) -> JSONResponse:
        sc = _require_multi(state)
        return JSONResponse(content=sc.relevant_documents)

    @app.get("/MultiCorpora_documents_2")
    async def multi_corpora_documents_2(state: SessionState = SessionDep) -> JSONResponse:
        sc = _require_multi(state)
        return JSONResponse(content=sc.relevant_documents_b)

    @app.get("/get_topic_similarity_matrix_single_corpus")
    async def topic_similarity_matrix(
        value: float = DEFAULT_OMEGA, state: SessionState = SessionDep
    ) -> JSONResponse:
        sc = _require_single(state)
        omega = _nearest_omega(sc.similarity_matrix.keys(), value)
        if omega is None:
            raise HTTPException(404, "No similarity matrix is loaded for this scenario.")
        return JSONResponse(content=sc.similarity_matrix[omega].tolist())

    @app.post("/Topic_Splitting_Document_Based")
    async def topic_splitting(
        body: TopicSplitRequest, state: SessionState = SessionDep
    ) -> JSONResponse:
        sc = _require_single(state)
        state.history.append({"op": "split_snapshot", "snapshot": _snapshot(sc)})
        try:
            payload = _do_split(sc, body)
        except TopicVisExplorerError:
            state.history.pop()
            raise
        return JSONResponse(content=payload)

    @app.post("/get_new_topic_vector")
    async def topic_merge(
        body: TopicMergeRequest, state: SessionState = SessionDep
    ) -> JSONResponse:
        sc = _require_single(state)
        state.history.append({"op": "merge_snapshot", "snapshot": _snapshot(sc)})
        try:
            new_circle_positions = _do_merge(sc, body)
        except TopicVisExplorerError:
            state.history.pop()
            raise
        return JSONResponse(content=new_circle_positions)

    @app.post("/undo_merge_splitting")
    async def undo(state: SessionState = SessionDep) -> JSONResponse:
        sc = _require_single(state)
        if not state.history:
            raise HTTPException(400, "Nothing to undo.")
        last = state.history.pop()
        _restore(sc, last["snapshot"])
        return JSONResponse(content={"ok": True, "remaining_undo_steps": len(state.history)})

    @app.post("/Add_Remove_Word")
    async def add_remove_word(
        body: AddRemoveWordRequest, state: SessionState = SessionDep
    ) -> JSONResponse:
        sc = _require_single(state)
        state.history.append({"op": "word_snapshot", "snapshot": _snapshot(sc)})
        try:
            from ..operations import add_word, remove_word

            prepared = sc.require("prepared")
            model_data = sc.require("model_data")
            sc.prepared = (
                add_word(prepared, topic_id=body.topic_id, word=body.word, model_data=model_data)
                if body.action == "add"
                else remove_word(
                    prepared, topic_id=body.topic_id, word=body.word, model_data=model_data
                )
            )
        except TopicVisExplorerError:
            state.history.pop()
            raise
        return JSONResponse(content={"ok": True})

    @app.post("/Exclude_Document")
    async def exclude_document_route(
        body: ExcludeDocumentRequest, state: SessionState = SessionDep
    ) -> JSONResponse:
        sc = _require_single(state)
        state.history.append({"op": "exclude_snapshot", "snapshot": _snapshot(sc)})
        try:
            from ..operations import exclude_document

            sc.prepared = exclude_document(
                sc.require("prepared"),
                topic_id=body.topic_id,
                doc_id=body.doc_id,
                model_data=sc.require("model_data"),
            )
        except TopicVisExplorerError:
            state.history.pop()
            raise
        return JSONResponse(content={"ok": True})

    return app


def _build_template_context(
    *,
    state: SessionState,
    vis_json: str,
    vis_json_2: str,
    topic_order: Any,
    topic_order_2: Any,
    new_circle_positions: Any,
    matrix_sankey: str,
    type_vis: int,
) -> dict[str, Any]:
    """Build a Jinja context that satisfies both templates.

    Legacy ``index.html`` uses the values pre-encoded into JS literals
    (``var topic_order = {{topic_order}};``), so we pass strings.
    Modern ``index_v1.html`` uses ``| tojson`` filters everywhere, so it
    also accepts JSON-serialisable Python objects. To support both with a
    single context we provide:

      * ``visid`` -- legacy: pre-quoted JSON string used inside JS source
      * ``visid_str`` -- modern: bare string used as the DOM id attribute
      * ``visid_raw`` -- shared: raw session id used in JS variable names
    """
    sid = state.session_id
    return {
        # Both templates accept ``vis_json`` as a pre-rendered JSON string;
        # legacy embeds it directly, modern marks it `| safe`.
        "vis_json": vis_json,
        "vis_json_2": vis_json_2,
        # Plain JSON-serialisable values; both templates handle them.
        "topic_order": topic_order,
        "topic_order_2": topic_order_2,
        "new_circle_positions": new_circle_positions,
        "matrix_sankey": matrix_sankey,
        "type_vis": type_vis,
        # Identifiers exposed in two shapes (see docstring above).
        "visid": _json.dumps(f"vis-{sid}"),
        "visid_str": f"vis-{sid}",
        "visid_raw": f"vis-{sid}",
        # Static asset URLs used by the legacy template's <script>/<link>
        # tags. The modern template still references ldavis_css_url for
        # parity even though the bundle inlines the rest.
        "d3_url": "/static/js/d3.v5.min.js",
        "ldavis_url": "/static/js/LDAvis.js",
        "ldavis_css_url": "/static/css/LDAvis.css",
    }


def _register_bundled_demo(registry: ScenarioRegistry) -> None:
    """Register the tiny demo scenarios shipped with the package.

    The loader is lazy: it only runs when the scenario is requested,
    so importing the package or building the app stays fast.
    """

    def load_tiny_demo() -> Scenario:
        from .demo_data import build_tiny_single_demo

        return build_tiny_single_demo()

    def load_tiny_multi_demo() -> Scenario:
        from .demo_data import build_tiny_multi_demo

        return build_tiny_multi_demo()

    registry.register("tiny_demo", load_tiny_demo)
    registry.register("tiny_multi_demo", load_tiny_multi_demo)


def _nearest_omega(omegas: Any, target: float) -> float | None:
    keys = list(omegas)
    if not keys:
        return None
    return min(keys, key=lambda k: abs(k - target))


def _build_sankey_dict(
    similarity_matrix: dict[float, np.ndarray],
) -> dict[float, dict[str, list[dict[str, Any]]]]:
    """Translate ``omega -> matrix`` into the Sankey JSON the front end wants."""
    out: dict[float, dict[str, list[dict[str, Any]]]] = {}
    for omega, matrix in similarity_matrix.items():
        nodes: list[dict[str, Any]] = []
        links: list[dict[str, Any]] = []
        rows, cols = matrix.shape
        for i in range(rows):
            nodes.append({"node": i, "name": f"model1-{i}"})
            for j in range(cols):
                links.append({"source": i, "target": rows + j, "value": float(matrix[i, j])})
        for j in range(cols):
            nodes.append({"node": rows + j, "name": f"model2-{j}"})
        out[omega] = {"nodes": nodes, "links": links}
    return out


def _snapshot(sc: Scenario) -> dict[str, Any]:
    """Capture the mutable parts of a scenario for undo support."""
    return {
        "prepared": deepcopy(sc.prepared),
        "model_data": deepcopy(sc.model_data),
        "relevant_documents": deepcopy(sc.relevant_documents),
        "similarity_matrix": {k: v.copy() for k, v in sc.similarity_matrix.items()},
        "circle_positions": deepcopy(sc.circle_positions),
    }


def _restore(sc: Scenario, snapshot: dict[str, Any]) -> None:
    sc.prepared = snapshot["prepared"]
    sc.model_data = snapshot["model_data"]
    sc.relevant_documents = snapshot["relevant_documents"]
    sc.similarity_matrix = snapshot["similarity_matrix"]
    sc.circle_positions = snapshot["circle_positions"]


def _do_split(sc: Scenario, body: TopicSplitRequest) -> dict[str, Any]:
    """Run the modernized split and assemble the legacy-shaped JSON.

    The legacy front end expects three keys::

        relevantDocumentsDict_fromPython  (JSON-encoded list of dicts)
        PreparedDataObtained_fromPython   (the new PreparedData.to_dict())
        new_circle_positions              (JSON-encoded omega -> layout)
    """
    from ..layout import circle_positions_from_old_matrix
    from ..operations import split

    prepared = sc.require("prepared")
    model_data = sc.require("model_data")
    raw_texts = sc.require("raw_texts")
    refit = sc.extras.get("refit")
    if refit is None:
        raise ValidationError(
            "Scenario does not provide a 'refit' callable in extras; "
            "topic splitting cannot run. See docs/extending.md."
        )

    new_prepared = split(
        prepared,
        topic_id=body.topic_id,
        k_new=2,
        model_data=model_data,
        raw_texts=raw_texts,
        refit=refit,
    )
    sc.prepared = new_prepared

    new_matrix = _recompute_similarity(sc, new_prepared)
    sc.similarity_matrix = new_matrix
    new_layout = circle_positions_from_old_matrix(body.old_circle_positions, new_matrix)
    sc.circle_positions = new_layout

    return {
        "relevantDocumentsDict_fromPython": _json.dumps(sc.relevant_documents, cls=NumPyEncoder),
        "PreparedDataObtained_fromPython": _json.loads(new_prepared.to_json()),
        "new_circle_positions": _json.dumps(
            {str(k): v for k, v in new_layout.items()}, cls=NumPyEncoder
        ),
    }


def _do_merge(sc: Scenario, body: TopicMergeRequest) -> dict[str, list[list[float]]]:
    from ..layout import circle_positions_from_old_matrix
    from ..operations import merge

    prepared = sc.require("prepared")
    model_data = sc.require("model_data")
    new_prepared = merge(
        prepared,
        topic_id_a=body.index_topic_name_1 + 1,
        topic_id_b=body.index_topic_name_2 + 1,
        model_data=model_data,
    )
    sc.prepared = new_prepared
    if body.relevantDocumentsDict_new:
        sc.relevant_documents = body.relevantDocumentsDict_new

    new_matrix = _recompute_similarity(sc, new_prepared)
    sc.similarity_matrix = new_matrix
    new_layout = circle_positions_from_old_matrix(body.old_circle_positions, new_matrix)
    sc.circle_positions = new_layout
    return {str(k): v for k, v in new_layout.items()}


def _recompute_similarity(sc: Scenario, prepared: Any) -> dict[float, np.ndarray]:
    """Recompute the topic similarity matrix after a structural edit.

    The full embedding-based metric needs ``doc_topic_dists`` +
    ``raw_texts`` precomputation; if those aren't on the scenario we
    fall back to a vocabulary-based Jensen-Shannon baseline so the
    visualization can still update layouts. The fallback is acceptable
    for tests; production scenarios should populate ``embedding`` and
    ``raw_texts``.
    """
    if sc.embedding is not None and sc.raw_texts and sc.model_data is not None:
        from ..similarity.embedding import EmbeddingSimilarity, compute_omega_grid

        metric = EmbeddingSimilarity(embedding=sc.embedding)
        doc_topic = pd.DataFrame(sc.model_data.doc_topic_dists)
        return dict(
            compute_omega_grid(
                metric,
                prepared,
                prepared,
                doc_topic_a=doc_topic,
                doc_topic_b=doc_topic,
                raw_texts_a=sc.raw_texts,
                raw_texts_b=sc.raw_texts,
                n_steps=101,
            )
        )

    from ..similarity.baselines import JensenShannonSimilarity

    metric_jsd = JensenShannonSimilarity()
    matrix = metric_jsd(prepared, prepared)
    return {round(step / 100.0, 2): matrix for step in range(101)}
