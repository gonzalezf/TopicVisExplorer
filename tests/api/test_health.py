"""Smoke and contract tests for the health and listing endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert isinstance(body["n_sessions"], int)
    assert body["max_sessions"] == 4
    assert "version" in body


def test_scenarios_list_includes_demo(client: TestClient) -> None:
    res = client.get("/scenarios")
    assert res.status_code == 200
    names = res.json()["scenarios"]
    assert "20ng_tiny" in names
    assert "tiny_demo" in names
    assert "tiny_multi_demo" in names


def test_index_redirects_to_singlecorpus(client: TestClient) -> None:
    res = client.get("/", follow_redirects=False)
    assert res.status_code in (302, 307)
    # The redirect now embeds the demo scenario in the query string so the
    # legacy LDAvis.js code (which gates its tutorial on whether it sees a
    # ``scenario`` query param) does not auto-launch the tutorial when a
    # user opens a bare URL.
    location = res.headers["location"]
    assert location.startswith("/singlecorpus")
    assert "scenario=20ng_tiny" in location


def test_unknown_scenario_returns_400(client: TestClient) -> None:
    res = client.get("/singlecorpus", params={"scenario": "does_not_exist"})
    assert res.status_code == 400
    assert "Unknown scenario" in res.json()["message"]
