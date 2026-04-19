"""Tests for ``/get_topic_similarity_matrix_single_corpus``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_returns_matrix_at_default_omega(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.get("/get_topic_similarity_matrix_single_corpus", params={"value": 0.0})
    assert res.status_code == 200
    matrix = res.json()
    assert isinstance(matrix, list)
    assert len(matrix) > 0
    assert len(matrix[0]) == len(matrix), "matrix should be square"


def test_returns_matrix_at_arbitrary_omega(client: TestClient) -> None:
    client.get("/singlecorpus", params={"scenario": "tiny_demo"})
    res = client.get("/get_topic_similarity_matrix_single_corpus", params={"value": 0.42})
    assert res.status_code == 200
