"""Smoke tests for the modern Vite + TypeScript frontend track.

These tests are *conditional* on the Vite bundle being present in
``src/topicvisexplorer/web/dist/``. Building the bundle requires Node.js
which is not available in every CI / install environment. When the
bundle is missing the tests are skipped (not failed) so a wheel install
that uses the legacy track still passes its test suite cleanly.

Build the bundle locally with::

    cd frontend && npm install && npm run build
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from topicvisexplorer.server import ServerConfig, build_app
from topicvisexplorer.web import MODERN_DIST, has_modern_bundle

needs_bundle = pytest.mark.skipif(
    not has_modern_bundle(),
    reason=(
        "Modern Vite bundle not built. Run `cd frontend && npm install && npm run build` to enable."
    ),
)


@pytest.fixture
def modern_client() -> TestClient:
    """A TestClient where the modern frontend is forced on."""
    app = build_app(ServerConfig(register_demo=True, frontend="auto"))
    return TestClient(app)


@needs_bundle
def test_auto_mode_selects_modern_template_when_bundle_present() -> None:
    app = build_app(ServerConfig(register_demo=True, frontend="auto"))
    assert app.state.use_modern is True
    assert app.state.template_name == "index_v1.html"


def test_modern_mode_raises_when_bundle_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force the detector to lie: pretend no bundle exists, then ask for
    # modern explicitly. The factory must refuse rather than silently
    # falling back to legacy.
    monkeypatch.setattr("topicvisexplorer.server.app.has_modern_bundle", lambda: False)
    with pytest.raises(RuntimeError, match="frontend='modern' requested"):
        build_app(ServerConfig(register_demo=True, frontend="modern"))


def test_legacy_mode_always_works_even_with_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    app = build_app(ServerConfig(register_demo=True, frontend="legacy"))
    assert app.state.use_modern is False
    assert app.state.template_name == "index.html"


@needs_bundle
def test_singlecorpus_renders_modern_template(modern_client: TestClient) -> None:
    r = modern_client.get("/singlecorpus?scenario=tiny_demo")
    assert r.status_code == 200
    body = r.text
    # Modern template uses /dist/tve.* and TVE_SCENARIO; legacy template
    # would have inline `var topic_order = ...` instead. We assert on
    # both presence of modern markers and absence of legacy markers.
    assert "/dist/tve.js" in body
    assert "/dist/tve.css" in body
    assert "TVE_SCENARIO" in body
    assert 'id="BarPlotPanel_2"' not in body
    assert 'id="DocumentsPanel_2"' not in body
    # Legacy template's hotjar/google-analytics blobs must NOT bleed into
    # the modern track (they're tracking scripts we deliberately dropped).
    assert "hotjar" not in body.lower()
    assert "googletagmanager" not in body.lower()


@needs_bundle
def test_multicorpora_renders_modern_template(modern_client: TestClient) -> None:
    r = modern_client.get("/multicorpora?scenario=tiny_multi_demo")
    assert r.status_code == 200
    body = r.text
    assert "/dist/tve.js" in body
    assert "TVE_SCENARIO" in body
    # The template emits `typeVis: 2` as a JS object literal (bare key,
    # number value). Multi-corpus mode is type 2 in the legacy contract.
    assert "typeVis: 2" in body
    # Multi-corpus blocks are conditional on type_vis == 2; matrixSankey
    # / topicOrder2 keys must be present.
    assert "matrixSankey:" in body
    assert "topicOrder2:" in body
    # Three-column multicorpora row: A | Sankey | B (no top-level doc columns).
    assert 'id="BarPlotPanel"' in body
    assert 'id="CentralPanel"' in body
    assert 'id="BarPlotPanel_2"' in body
    assert "tve-multicorpus-side" in body
    assert "col-4" in body
    # Old 5-col grid had narrow BarPlot / doc columns; not used anymore.
    assert "col-2 border-right" not in body
    # DocumentsPanel_2 is created in LDAvis and appended under B; not in HTML.
    assert 'id="DocumentsPanel_2"' not in body


@needs_bundle
def test_dist_assets_served(modern_client: TestClient) -> None:
    r_js = modern_client.get("/dist/tve.js")
    assert r_js.status_code == 200
    assert "javascript" in r_js.headers["content-type"]
    # IIFE format -- the bundle exposes itself as `var TVE = ...`.
    assert r_js.content.startswith(b"var TVE=")
    assert len(r_js.content) > 100_000  # sanity: real bundle, not stub

    r_css = modern_client.get("/dist/tve.css")
    assert r_css.status_code == 200
    assert "text/css" in r_css.headers["content-type"]
    # Bootstrap reset rules must be present (Bootstrap 4.5.0 was the
    # reviewed version; pinning the assertion guards against accidental
    # major-version bumps that would break visual parity).
    assert b"bootstrap" in r_css.content.lower()


@needs_bundle
def test_dist_path_is_correct() -> None:
    """The dist directory must live where pyproject.toml expects it."""
    assert MODERN_DIST.is_dir()
    assert (MODERN_DIST / "tve.js").is_file()
    assert (MODERN_DIST / "tve.css").is_file()
