"""Parametrized split and merge tests across all bundled scenarios.

Regression coverage for the 'Status: error' UX bug (see plan section 3).
"""
from __future__ import annotations

import copy
import json
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


def _k_from_circle_positions(pos: dict) -> int:
    """Number of topic circles in the first omega key (legacy layout)."""
    return len(next(iter(pos.values())))


def _k_from_prepared_dict(prep: dict) -> int:
    """True topic count from a PreparedData JSON fragment (source of truth)."""
    return len(prep["topic.order"])


def _session_model_k(client: TestClient) -> int:
    """K from the in-memory single-corpus scenario (authoritative for merge/split)."""
    sid = client.cookies.get("tve_session")
    st = client.app.state.session_store.get(sid)  # type: ignore[attr-defined]
    assert st is not None, "no session"
    sc = st.single_corpus.get("scenario")
    assert sc is not None, "no scenario in session"
    return int(sc.model_data.topic_term_dists.shape[0])


# Non-trivial document seeds: must be list[dict] (same shape the UI posts).
_TRIVIAL_SEEDS: dict = {
    "TopicA": [{"doc_id": 0, "text": "seed_a"}],
    "TopicB": [{"doc_id": 1, "text": "seed_b"}],
}
_EMPTY_SEEDS: dict = {"TopicA": [], "TopicB": []}


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_split_merge_double_undo_roundtrip(
    client: TestClient, scenario: str
) -> None:
    """One split, merge topics 0+1, double-undo; run for each bundled single-corpus demo.

    Refit paths: ``tiny_demo`` uses static refit; ``20ng_tiny`` and ``bbc_tiny`` use
    Gensim LDA refit on different fixture corpora. The parametrized ``scenario`` id
    names which dataset is under test.
    """
    initial = copy.deepcopy(_bootstrap(client, scenario))
    b0 = _scenario_builder(scenario)()
    k_baseline = len(b0.prepared.topic_order)
    assert _k_from_circle_positions(initial) == k_baseline
    positions: dict = copy.deepcopy(initial)
    k_now = k_baseline
    rs = client.post(
        "/Topic_Splitting_Document_Based",
        json={
            "topic_id": 1,
            "current_number_of_topics": k_now,
            "old_circle_positions": positions,
            "new_document_seeds": _EMPTY_SEEDS,
        },
    )
    assert rs.status_code == 200, f"{scenario} split: {rs.status_code} {rs.text}"
    sp = rs.json()
    prep_split = sp["PreparedDataObtained_fromPython"]
    k_after_split = _k_from_prepared_dict(prep_split)
    assert k_after_split == k_now + 1, (scenario, k_after_split, k_now)
    assert _session_model_k(client) == k_after_split
    positions = json.loads(sp["new_circle_positions"])
    for _om, row in positions.items():
        assert len(row) == k_after_split, (scenario, _om, len(row), k_after_split)
    rm = client.post(
        "/get_new_topic_vector",
        json={
            "index_topic_name_1": 0,
            "index_topic_name_2": 1,
            "old_circle_positions": positions,
            "relevantDocumentsDict_new": [],
            "lamData_new": {},
        },
    )
    assert rm.status_code == 200, f"{scenario} merge: {rm.text}"
    positions = rm.json()
    k_merged_model = _session_model_k(client)
    assert k_merged_model == k_after_split - 1, (scenario, k_merged_model, k_after_split)
    row_lens = {len(v) for v in positions.values()}
    assert len(row_lens) == 1, f"{scenario} inconsistent omegas: {row_lens}"
    (layout_k,) = row_lens
    assert layout_k == k_merged_model, (scenario, layout_k, k_merged_model)
    assert client.post("/undo_merge_splitting").status_code == 200
    assert client.post("/undo_merge_splitting").status_code == 200
    assert _session_model_k(client) == k_baseline


def test_split_merge_undo_chain_20ng_tiny(client: TestClient) -> None:
    """Run split then merge, double-undo to baseline, three times; chain layout JSON.

    Uses both empty and minimal dict seeds in alternating rounds. We assert on
    session model K and ``topic.order``; circle JSON row counts are checked for
    internal consistency (same length across keys) and against the model when
    they match.
    """
    scenario = "20ng_tiny"
    initial = copy.deepcopy(_bootstrap(client, scenario))
    b0 = _scenario_builder(scenario)()
    k_baseline = len(b0.prepared.topic_order)
    assert _k_from_circle_positions(initial) == k_baseline
    positions: dict = copy.deepcopy(initial)
    for r in range(3):
        k_now = k_baseline
        seeds: dict = _EMPTY_SEEDS if (r % 2 == 0) else _TRIVIAL_SEEDS
        rs = client.post(
            "/Topic_Splitting_Document_Based",
            json={
                "topic_id": 1,
                "current_number_of_topics": k_now,
                "old_circle_positions": positions,
                "new_document_seeds": seeds,
            },
        )
        assert rs.status_code == 200, f"round {r} split: {rs.status_code} {rs.text}"
        sp = rs.json()
        assert "PreparedDataObtained_fromPython" in sp
        assert "new_circle_positions" in sp
        prep_split = sp["PreparedDataObtained_fromPython"]
        k_after_split = _k_from_prepared_dict(prep_split)
        assert k_after_split == k_now + 1, (k_after_split, k_now)
        assert _session_model_k(client) == k_after_split
        positions = json.loads(sp["new_circle_positions"])
        for _om, row in positions.items():
            assert len(row) == k_after_split, (len(row), k_after_split, _om)
        rm = client.post(
            "/get_new_topic_vector",
            json={
                "index_topic_name_1": 0,
                "index_topic_name_2": 1,
                "old_circle_positions": positions,
                "relevantDocumentsDict_new": [],
                "lamData_new": {},
            },
        )
        assert rm.status_code == 200, f"round {r} merge: {rm.status_code} {rm.text}"
        positions = rm.json()
        assert isinstance(positions, dict) and positions
        k_merged_model = _session_model_k(client)
        assert k_merged_model == k_after_split - 1, (k_merged_model, k_after_split)
        row_lens = {len(v) for v in positions.values()}
        assert len(row_lens) == 1, f"inconsistent layout omegas: {row_lens}"
        (layout_k,) = row_lens
        assert layout_k == k_merged_model, (layout_k, k_merged_model)
        u1 = client.post("/undo_merge_splitting")
        assert u1.status_code == 200, f"round {r} undo1: {u1.text}"
        u2 = client.post("/undo_merge_splitting")
        assert u2.status_code == 200, f"round {r} undo2: {u2.text}"
        assert _session_model_k(client) == k_baseline
        positions = copy.deepcopy(initial)


def test_split_undo_repeat_tiny_demo(client: TestClient) -> None:
    """Split topic 1, undo, repeat — no merge (exercises only split+undo + history)."""
    scenario = "tiny_demo"
    initial = copy.deepcopy(_bootstrap(client, scenario))
    b0 = _scenario_builder(scenario)()
    k0 = len(b0.prepared.topic_order)
    positions: dict = copy.deepcopy(initial)
    for r in range(2):
        rs = client.post(
            "/Topic_Splitting_Document_Based",
            json={
                "topic_id": 1,
                "current_number_of_topics": k0,
                "old_circle_positions": positions,
                "new_document_seeds": _EMPTY_SEEDS,
            },
        )
        assert rs.status_code == 200, f"round {r} split: {rs.text}"
        k1 = _k_from_prepared_dict(rs.json()["PreparedDataObtained_fromPython"])
        assert k1 == k0 + 1
        u = client.post("/undo_merge_splitting")
        assert u.status_code == 200, u.text
        assert _session_model_k(client) == k0
        positions = copy.deepcopy(initial)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_split_merge_different_index_pairs(
    client: TestClient, scenario: str
) -> None:
    """After a split, merge (2,3) when K>=4 (stable middle pair), then double-undo.

    Complements ``test_split_merge_double_undo_roundtrip`` (merge 0+1) with merge 2+3.
    """
    _bootstrap(client, scenario)
    b0 = _scenario_builder(scenario)()
    k0 = len(b0.prepared.topic_order)
    if k0 < 4:
        pytest.skip("need K>=4 to merge a middle pair (2,3) after split")
    old = b0.circle_positions
    r1 = client.post(
        "/Topic_Splitting_Document_Based",
        json={
            "topic_id": 1,
            "current_number_of_topics": k0,
            "old_circle_positions": old,
            "new_document_seeds": _EMPTY_SEEDS,
        },
    )
    assert r1.status_code == 200, r1.text
    lay = json.loads(r1.json()["new_circle_positions"])
    r2 = client.post(
        "/get_new_topic_vector",
        json={
            "index_topic_name_1": 2,
            "index_topic_name_2": 3,
            "old_circle_positions": lay,
            "relevantDocumentsDict_new": [],
            "lamData_new": {},
        },
    )
    assert r2.status_code == 200, r2.text
    assert _session_model_k(client) == k0
    u1, u2 = client.post("/undo_merge_splitting"), client.post("/undo_merge_splitting")
    assert u1.status_code == 200 and u2.status_code == 200
    assert _session_model_k(client) == k0


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
