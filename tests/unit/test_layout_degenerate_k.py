"""Tests for layout Procrustes correspondence helpers and degenerate-K guards."""
from __future__ import annotations

import numpy as np
import pytest

from topicvisexplorer.layout import (
    circle_positions_from_old_matrix,
    merge_correspondence,
    split_correspondence,
)


def _omega_keys() -> list[str]:
    return [str(i / 100.0) for i in range(101)]


def test_k_equals_one_does_not_raise() -> None:
    old = {k: [[0.1, 0.2]] for k in _omega_keys()}
    sim = {i / 100.0: np.array([[1.0]]) for i in range(101)}
    out = circle_positions_from_old_matrix(old, sim)
    assert set(out.keys()) == set(old.keys())
    assert all(len(v) == 1 for v in out.values())


def test_k_shrinks_by_one_with_merge_map_preserves_rotation() -> None:
    rng = np.random.default_rng(0)
    K_old, K_new = 5, 4
    old = {k: rng.standard_normal((K_old, 2)).tolist() for k in _omega_keys()}
    sims = {}
    for raw in range(101):
        m = rng.uniform(0.0, 0.5, size=(K_new, K_new))
        m = (m + m.T) / 2
        np.fill_diagonal(m, 1.0)
        sims[raw / 100.0] = m
    corr = merge_correspondence(K_old, a_idx=1, b_idx=3)
    out = circle_positions_from_old_matrix(old, sims, correspondence=corr)
    assert all(len(v) == K_new for v in out.values())


def test_split_correspondence_shape() -> None:
    # split topic 2 of 5 into 3 children: K_old=5, parent_idx=2, k_new=3 -> K_new=7
    corr = split_correspondence(5, parent_idx=2, k_new=3)
    # Before: (0,0), (1,1). Parent idx=2 dropped. After: (3, 5), (4, 6).
    assert corr == [(0, 0), (1, 1), (3, 5), (4, 6)]


def test_merge_correspondence_shape() -> None:
    # merge topics (1, 3) of K_old=5: a=1, b=3 -> K_new=4.
    # Before: (0,0). Keep a: (1,1). Middle (j=2, unchanged): (2,2).
    # After b (j=4 -> shift left): (4,3). Row 3 (b_idx) dropped.
    corr = merge_correspondence(5, a_idx=1, b_idx=3)
    assert corr == [(0, 0), (1, 1), (2, 2), (4, 3)]


def test_correspondence_swapped_merge_normalises() -> None:
    # Caller passes b_idx < a_idx; helper must swap internally.
    corr = merge_correspondence(5, a_idx=3, b_idx=1)
    assert corr == merge_correspondence(5, a_idx=1, b_idx=3)


def test_merge_at_end_of_topic_list() -> None:
    # Merging the last two topics is the easy case (no "after" shift).
    corr = merge_correspondence(5, a_idx=3, b_idx=4)
    assert corr == [(0, 0), (1, 1), (2, 2), (3, 3)]


def test_split_last_topic_appends_children() -> None:
    # Splitting the final topic should not shift any old index.
    corr = split_correspondence(5, parent_idx=4, k_new=3)
    # Parent=4 dropped; before=[(0,0),(1,1),(2,2),(3,3)]; after loop is empty.
    assert corr == [(0, 0), (1, 1), (2, 2), (3, 3)]


def test_split_first_topic() -> None:
    # Splitting topic 0 of 4 into 2 children.
    corr = split_correspondence(4, parent_idx=0, k_new=2)
    # Before is empty. After: j=1->(1+2-1=2), j=2->(2+2-1=3), j=3->(3+2-1=4).
    assert corr == [(1, 2), (2, 3), (3, 4)]


def test_correspondence_none_fallback_warns(caplog: pytest.LogCaptureFixture) -> None:
    """None correspondence triggers a logger warning (legacy fallback)."""
    import logging

    rng = np.random.default_rng(1)
    K = 3
    old = {k: rng.standard_normal((K, 2)).tolist() for k in _omega_keys()}
    sims = {}
    for raw in range(101):
        m = np.eye(K)
        sims[raw / 100.0] = m
    with caplog.at_level(logging.WARNING, logger="topicvisexplorer.layout"):
        out = circle_positions_from_old_matrix(old, sims, correspondence=None)
    assert any("no correspondence map" in r.message for r in caplog.records)
    assert all(len(v) == K for v in out.values())
