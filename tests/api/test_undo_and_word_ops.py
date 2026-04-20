"""Tests for the add/remove word, exclude document, and undo endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_undo_with_no_history_400(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.post("/undo_merge_splitting")
    assert res.status_code == 400


def test_add_word_then_undo(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    add_res = client.post(
        "/Add_Remove_Word",
        json={"topic_id": 1, "word": "w01", "action": "add"},
    )
    assert add_res.status_code == 200
    add_body = add_res.json()
    assert add_body["ok"] is True
    assert add_body["remaining_undo_steps"] == 1
    # Phase 4d wired the response to include the updated PreparedData
    # so the client can redraw the affected topic in place. Verify the
    # legacy keys are present.
    assert "PreparedDataObtained_fromPython" in add_body
    prep = add_body["PreparedDataObtained_fromPython"]
    assert "tinfo" in prep
    assert "mdsDat" in prep
    assert "topic.order" in prep

    undo_res = client.post("/undo_merge_splitting")
    assert undo_res.status_code == 200
    body = undo_res.json()
    assert body["ok"] is True
    assert body["remaining_undo_steps"] == 0


def test_remove_unknown_word_returns_400(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.post(
        "/Add_Remove_Word",
        json={"topic_id": 1, "word": "not_in_vocab_zzz", "action": "remove"},
    )
    assert res.status_code == 400


def test_exclude_document_then_undo(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.post("/Exclude_Document", json={"topic_id": 1, "doc_id": 0})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "PreparedDataObtained_fromPython" in body
    undo = client.post("/undo_merge_splitting")
    assert undo.status_code == 200
