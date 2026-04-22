"""Parametrized split and merge tests across all bundled scenarios.

Regression coverage for the 'Status: error' UX bug (see plan section 3).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SCENARIOS = ["tiny_demo", "20ng_tiny", "bbc_tiny"]


def _scenario_builder(name: str):
    if name == "tiny_demo":
        from topicvisexplorer.server.demo_data import build_tiny_single_demo

        return build_tiny_single_demo
    if name == "20ng_tiny":
        try:
            from topicvisexplorer.server.demo_fixtures import build_20ng_tiny
        except ImportError:
            from topicvisexplorer.server.demo_20ng import build_20ng_tiny
        return build_20ng_tiny
    if name == "bbc_tiny":
        try:
            from topicvisexplorer.server.demo_fixtures import build_bbc_tiny
        except ImportError:
            pytest.skip("bbc_tiny fixture not yet built (section 5 pending)")
        fixtures = Path(__file__).resolve().parents[2] / "src/topicvisexplorer/server/fixtures"
        if not (fixtures / "bbc_tiny.npz").exists():
            pytest.skip("bbc_tiny.npz fixture is not on disk")
        from topicvisexplorer.server.demo_fixtures import build_bbc_tiny

        return build_bbc_tiny
    raise AssertionError(name)


def _bootstrap(client: TestClient, scenario: str):
    builder = _scenario_builder(scenario)
    r = client.get("/singlecorpus", params={"scenario": scenario, "hitl": "true"})
    assert r.status_code == 200, r.text
    sc = builder()
    return sc.circle_positions


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_split_returns_200_on_every_scenario(client: TestClient, scenario: str) -> None:
    old = _bootstrap(client, scenario)
    k_now = len(next(iter(old.values())))
    res = client.post(
        "/Topic_Splitting_Document_Based",
        json={
            "topic_id": 1,
            "current_number_of_topics": k_now,
            "old_circle_positions": old,
            "new_document_seeds": {"TopicA": [], "TopicB": []},
        },
    )
    assert res.status_code == 200, f"{scenario}: {res.status_code} {res.text}"
    body = res.json()
    assert "PreparedDataObtained_fromPython" in body
    assert "new_circle_positions" in body


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_merge_returns_200_on_every_scenario(client: TestClient, scenario: str) -> None:
    old = _bootstrap(client, scenario)
    res = client.post(
        "/get_new_topic_vector",
        json={
            "index_topic_name_1": 0,
            "index_topic_name_2": 1,
            "old_circle_positions": old,
            "relevantDocumentsDict_new": [],
            "lamData_new": {},
        },
    )
    assert res.status_code == 200, f"{scenario}: {res.status_code} {res.text}"
    positions = res.json()
    assert isinstance(positions, dict) and positions, positions


def test_split_error_body_is_readable(client: TestClient) -> None:
    """Regression: server must return HTTP 400 with a readable JSON message
    when split cannot run (not a useless 'Status: error' opaque blob).
    """
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    sid = client.cookies.get("tve_session")
    store = client.app.state.session_store  # type: ignore[attr-defined]
    state = store.get(sid)
    assert state is not None, "Session not found in store"
    sc = state.single_corpus.get("scenario")
    assert sc is not None
    # Strip the refit callable so the split path hits the missing-refit error.
    sc.extras.pop("refit", None)

    res = client.post(
        "/Topic_Splitting_Document_Based",
        json={
            "topic_id": 1,
            "current_number_of_topics": 5,
            "old_circle_positions": {"0.0": [[0.0, 0.0]] * 5},
            "new_document_seeds": {"TopicA": [], "TopicB": []},
        },
    )
    assert res.status_code == 400, res.text
    body = res.json()
    assert isinstance(body.get("message"), str) and len(body["message"]) > 10
    assert "refit" in body["message"].lower()
