"""Tests for the multi-corpus document endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_multicorpora_pages_render(client: TestClient) -> None:
    res = client.get("/multicorpora", params={"scenario": "tiny_multi_demo"})
    assert res.status_code == 200
    assert "html" in res.headers["content-type"]


def test_multicorpora_documents_endpoints(client: TestClient) -> None:
    client.get("/multicorpora", params={"scenario": "tiny_multi_demo"})
    res1 = client.get("/MultiCorpora_documents_1")
    res2 = client.get("/MultiCorpora_documents_2")
    assert res1.status_code == 200
    assert res2.status_code == 200
    docs_1 = res1.json()
    docs_2 = res2.json()
    assert isinstance(docs_1, list) and len(docs_1) > 0
    assert isinstance(docs_2, list) and len(docs_2) > 0
    assert docs_1[0]["text"].startswith("corpus A")
    assert docs_2[0]["text"].startswith("corpus B")


def test_singlecorpus_request_for_multi_scenario_rejected(client: TestClient) -> None:
    res = client.get("/singlecorpus", params={"scenario": "tiny_multi_demo"})
    assert res.status_code == 400
