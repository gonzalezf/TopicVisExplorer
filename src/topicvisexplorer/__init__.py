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

from typing import TYPE_CHECKING, Any

from . import embeddings, errors, models, similarity
from ._version import __version__
from .logging import configure_logging, get_logger
from .prepare import PreparedData, load, prepare

if TYPE_CHECKING:
    from .server.scenarios import Scenario


def show(
    prepared: PreparedData | list[PreparedData] | None = None,
    *,
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
    host, port:
        Network bind address. Defaults to ``localhost:8000``.
    open_browser:
        Open the OS default browser pointed at the new server.
    scenario_name:
        Internal name registered for the user-supplied data; surfaces in
        the URL as ``?scenario=<scenario_name>``.

    Notes
    -----
    Blocks until interrupted (Ctrl+C). For non-blocking embedding (e.g.
    Jupyter) wait for ``tve.show_inline()`` in v1.1.
    """
    from .server import ServerConfig, build_app, serve

    extras: dict[str, Any] = {}
    if prepared is not None:
        sc = _scenario_from_user_data(prepared, name=scenario_name)
        extras[scenario_name] = lambda: sc

    app = build_app(ServerConfig(extra_scenarios=extras))
    serve(app, host=host, port=port, open_browser=open_browser)


def demo(*, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    """Launch the server with only the bundled tiny demo scenarios.

    Equivalent to ``tve.show(None)`` but loads
    ``/singlecorpus?scenario=tiny_demo`` in the browser.
    """
    from .server import ServerConfig, build_app, serve

    app = build_app(ServerConfig(register_demo=True))
    serve(app, host=host, port=port, open_browser=open_browser)


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


def _scenario_from_user_data(prepared: PreparedData | list[PreparedData], *, name: str) -> Scenario:
    """Build a :class:`Scenario` from user-supplied PreparedData.

    Note: this is a *thin* registration. Split / merge endpoints will
    fail with a clear error because they require ``model_data`` +
    ``raw_texts`` + ``embedding`` that we don't have for arbitrary
    PreparedData inputs. Use the lower-level
    ``topicvisexplorer.server.scenarios.Scenario`` constructor + a custom
    loader if you need full interactive support.
    """
    from .server.scenarios import Scenario

    if isinstance(prepared, list):
        if len(prepared) != 2:
            raise ValueError("show() expects 1 or 2 PreparedData objects.")
        return Scenario(
            name=name,
            is_multi=True,
            prepared=prepared[0],
            prepared_b=prepared[1],
        )
    return Scenario(name=name, is_multi=False, prepared=prepared)


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
