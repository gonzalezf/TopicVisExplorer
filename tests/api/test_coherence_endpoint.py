"""Phase 4f: tests for ``GET /coherence``.

The endpoint backs the collapsible coherence panel in the modern UI.
We check:

* The contract: top-level keys are ``npmi``, ``c_v``, ``segregation``,
  ``coverage`` and the per-topic arrays all have the same length as
  the topic catalogue. The frontend renders one row per topic and
  would crash on a length mismatch.
* JSON cleanliness: the response must not contain raw NaN/Infinity
  tokens. FastAPI's default :class:`JSONResponse` uses
  ``allow_nan=False`` so a regression here would produce a 500 in
  prod; we additionally re-load the body via :mod:`json` to catch
  any sneaky non-compliance the framework might tolerate locally.
* The 404 path for multi-corpus mode (deferred to v1.1).
"""

from __future__ import annotations

import json
import math

from fastapi.testclient import TestClient


def test_coherence_single_corpus_contract(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.get("/coherence")
    assert res.status_code == 200, res.text

    body = res.json()
    for key in ("npmi", "c_v", "segregation", "coverage", "labels"):
        assert key in body, f"missing column {key!r}"
        assert isinstance(body[key], list), f"{key} must be a list"

    n = len(body["npmi"])
    assert n > 0, "tiny_demo should have at least one topic"
    for key in ("c_v", "segregation", "coverage", "labels"):
        assert len(body[key]) == n, (
            f"length mismatch: npmi has {n} entries but {key} has {len(body[key])}"
        )
    for lab in body["labels"]:
        assert isinstance(lab, str)


def test_coherence_response_is_strict_json(client: TestClient) -> None:
    """No raw NaN / Infinity tokens may leak into the response.

    Regression guard: ``sanitize_for_json`` is the only thing that
    keeps NPMI's log-of-zero edges from blowing up FastAPI's strict
    JSON serializer.
    """
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.get("/coherence")
    assert res.status_code == 200

    raw = res.text
    assert "NaN" not in raw, "NaN leaked into response body"
    assert "Infinity" not in raw, "Infinity leaked into response body"

    parsed = json.loads(raw)
    for key in ("npmi", "c_v", "segregation", "coverage"):
        for v in parsed[key]:
            assert v is None or (isinstance(v, (int, float)) and not math.isnan(v)), (
                f"non-finite value snuck into {key}: {v!r}"
            )


def test_coherence_404_in_multi_corpus(client: TestClient) -> None:
    """Multi-corpus is intentionally deferred to v1.1.

    The frontend does not render the panel in multi-corpus mode at
    all (``{% if type_vis == 1 %}`` guard in ``index_v1.html``), so
    a 404 is the expected contract.
    """
    client.get("/multicorpora", params={"scenario": "tiny_multi_demo"})
    res = client.get("/coherence")
    # ``_require_single`` raises HTTPException(400) when the active
    # session is multi-corpus -- the panel is hidden in that mode by
    # the ``{% if type_vis == 1 %}`` Jinja guard, so the frontend
    # never makes the call. Either 400/404/409 is an acceptable
    # "not available here" signal.
    assert res.status_code in (400, 404, 409), res.text


def test_coherence_400_without_session(client: TestClient) -> None:
    res = client.get("/coherence")
    assert res.status_code in (400, 404, 409), res.text
