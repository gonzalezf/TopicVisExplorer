"""Smoke tests for the real-terms ``20ng_tiny`` scenario + split with refit."""

from __future__ import annotations

from fastapi.testclient import TestClient

from topicvisexplorer.server import ServerConfig, build_app
from topicvisexplorer.server.demo_fixtures import build_20ng_tiny, demo_page_contains_real_terms


def test_20ng_singlecorpus_smoke(client: TestClient) -> None:
    res = client.get("/singlecorpus", params={"scenario": "20ng_tiny", "hitl": "true"})
    assert res.status_code == 200
    body = res.text
    assert demo_page_contains_real_terms(body)


def test_topic_split_20ng_with_refit() -> None:
    app = build_app(ServerConfig(register_demo=True))
    c = TestClient(app)
    c.get("/singlecorpus", params={"scenario": "20ng_tiny", "hitl": "true"})
    sc = build_20ng_tiny()
    assert sc.extras.get("refit") is not None
    old = sc.circle_positions
    k = int(sc.model_data.topic_term_dists.shape[0])
    res = c.post(
        "/Topic_Splitting_Document_Based",
        json={
            "topic_id": 1,
            "current_number_of_topics": k,
            "old_circle_positions": old,
            "new_document_seeds": {"TopicA": [], "TopicB": []},
        },
    )
    assert res.status_code == 200, res.text
    out = res.json()
    assert "PreparedDataObtained_fromPython" in out
    prep = out["PreparedDataObtained_fromPython"]
    assert "topic.order" in prep
    assert len(prep["topic.order"]) == k + 1


def test_topic_split_then_merge_20ng(client: TestClient) -> None:
    import json

    client.get("/singlecorpus", params={"scenario": "20ng_tiny", "hitl": "true"})
    sc = build_20ng_tiny()
    old = sc.circle_positions
    k = int(sc.model_data.topic_term_dists.shape[0])
    r1 = client.post(
        "/Topic_Splitting_Document_Based",
        json={
            "topic_id": 1,
            "current_number_of_topics": k,
            "old_circle_positions": old,
            "new_document_seeds": {"TopicA": [], "TopicB": []},
        },
    )
    assert r1.status_code == 200, r1.text
    new_pos = json.loads(r1.json()["new_circle_positions"])
    r2 = client.post(
        "/get_new_topic_vector",
        json={
            "index_topic_name_1": 0,
            "index_topic_name_2": 1,
            "old_circle_positions": new_pos,
            "relevantDocumentsDict_new": [],
            "lamData_new": {},
        },
    )
    assert r2.status_code == 200, r2.text
