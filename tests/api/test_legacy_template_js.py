from __future__ import annotations

import re

from fastapi.testclient import TestClient

from topicvisexplorer.server import ServerConfig, build_app


def test_legacy_template_avoids_invalid_js_identifiers() -> None:
    """Legacy HTML must not emit `var vis-... = ...` declarations.

    Session ids contain hyphens, so using them directly as JS identifiers
    causes a parse error and blank UI. Keep the payload on `window[...]`
    access instead.
    """
    app = build_app(ServerConfig(register_demo=True, frontend="legacy"))
    client = TestClient(app)

    response = client.get("/multicorpora?scenario=tiny_multi_demo")
    assert response.status_code == 200

    body = response.text
    assert re.search(r"\bvar\s+vis-[A-Za-z0-9_-]*_data\s*=", body) is None
    assert "window[visDataKey]" in body


def test_legacy_multicorpora_script_payload_not_html_escaped() -> None:
    """Jinja autoescape must not turn embedded JSON into &#34; entities (breaks JS)."""
    app = build_app(ServerConfig(register_demo=True, frontend="legacy"))
    client = TestClient(app)
    body = client.get("/multicorpora?scenario=tiny_multi_demo").text
    assert "&#34;" not in body
    assert "&quot;" not in body[:80000]
    assert "window[visDataKey] =" in body


def test_legacy_singlecorpus_script_payload_not_html_escaped() -> None:
    """Jinja autoescape must not turn embedded JSON into &#34; entities (breaks JS)."""
    app = build_app(ServerConfig(register_demo=True, frontend="legacy"))
    client = TestClient(app)
    r = client.get("/singlecorpus?scenario=tiny_demo")
    assert r.status_code == 200
    body = r.text
    assert "&#34;" not in body
    assert "window[visDataKey] =" in body
    assert re.search(r"\bvar\s+vis-[A-Za-z0-9_-]*_data\s*=", body) is None
