"""Smoke tests for the BBC-news real-terms demo (``bbc_tiny``)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "src/topicvisexplorer/server/fixtures"

pytestmark = pytest.mark.skipif(
    not (FIXTURE_DIR / "bbc_tiny.npz").exists(),
    reason="bbc_tiny fixture not built; run scripts/build_bbc_tiny_fixtures.py",
)


def test_bbc_tiny_singlecorpus_smoke(client: TestClient) -> None:
    res = client.get("/singlecorpus", params={"scenario": "bbc_tiny", "hitl": "true"})
    assert res.status_code == 200
    body = res.text
    # Heuristic: the page should mention at least one BBC-domain term.
    assert any(tok in body for tok in ("government", "market", "film", "company", "player"))


def test_topic_split_bbc_tiny_with_refit() -> None:
    from topicvisexplorer.server import ServerConfig, build_app
    from topicvisexplorer.server.demo_fixtures import build_bbc_tiny

    app = build_app(ServerConfig(register_demo=True))
    c = TestClient(app)
    c.get("/singlecorpus", params={"scenario": "bbc_tiny", "hitl": "true"})
    sc = build_bbc_tiny()
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
    prep = res.json()["PreparedDataObtained_fromPython"]
    assert len(prep["topic.order"]) == k + 1
