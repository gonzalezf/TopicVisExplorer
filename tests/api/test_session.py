"""Tests for cookie-based session lifecycle."""

from __future__ import annotations

from fastapi.testclient import TestClient

from topicvisexplorer.server.app import SESSION_COOKIE_NAME


def test_first_request_sets_cookie(client: TestClient) -> None:
    res = client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    assert res.status_code == 200
    assert SESSION_COOKIE_NAME in res.cookies


def test_session_persists_documents_endpoint(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.get("/SingleCorpus_documents")
    assert res.status_code == 200
    docs = res.json()
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert "text" in docs[0]


def test_documents_without_session_returns_400(client: TestClient) -> None:
    res = client.get("/SingleCorpus_documents")
    assert res.status_code == 400


def test_lru_eviction_purges_old_sessions(client: TestClient) -> None:
    """max_sessions=4 fixture; the 5th distinct session should evict the 1st."""
    cookies = []
    for _ in range(5):
        with TestClient(client.app) as fresh:
            res = fresh.get("/singlecorpus", params={"scenario": "tiny_demo"})
            cookies.append(res.cookies.get("tve_session"))
    assert len({c for c in cookies if c}) == 5
