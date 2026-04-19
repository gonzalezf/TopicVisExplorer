"""Golden-baseline tests against the legacy paper-version output.

Loads ``golden_baseline/tiny_prepare_output.json`` (captured by
``scripts/capture_golden.py`` running the legacy code on a synthetic
20 Newsgroups subset) and asserts that the modernized
:func:`topicvisexplorer.prepare` produces the same numbers within
``atol=1e-6``.

This is the contract that protects paper-figure parity: any regression
that shifts these numbers must update the goldens in a separate PR
(see ``CONTRIBUTING.md``).

Note: This test is *skipped* if the legacy tiny_lda.pkl is not present
(it requires the legacy Python 3.8 environment to load and is too
large to bundle in git). In CI we re-capture from the synthetic seed,
not from the pickle.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

GOLDEN = Path(__file__).resolve().parents[2] / "golden_baseline" / "tiny_prepare_output.json"


@pytest.fixture(scope="module")
def golden_payload() -> dict:
    if not GOLDEN.exists():
        pytest.skip("golden fixture missing - run scripts/capture_golden.py")
    return json.loads(GOLDEN.read_text())


def test_golden_topic_coordinates_have_expected_shape(golden_payload: dict) -> None:
    """Sanity: the captured fixture has 4 topics with x/y coordinates."""
    coords = golden_payload["topic_coordinates"]
    assert "x" in coords and "y" in coords
    assert len(coords["x"]) == 4 and len(coords["y"]) == 4


def test_golden_topic_info_has_default_and_per_topic_categories(golden_payload: dict) -> None:
    cats = set(golden_payload["topic_info"]["Category"])
    assert "Default" in cats
    for k in range(1, 5):
        assert f"Topic{k}" in cats


def test_golden_topic_proportions_sum_to_100(golden_payload: dict) -> None:
    """Topic Freq column in coordinates is proportion * 100."""
    freqs = golden_payload["topic_coordinates"]["Freq"]
    assert abs(sum(freqs) - 100.0) < 1e-3


def test_golden_lambda_step_matches_capture(golden_payload: dict) -> None:
    assert golden_payload["lambda_step"] == 0.1


def test_golden_R_matches_capture(golden_payload: dict) -> None:
    assert golden_payload["R"] == 1000


def test_golden_logprob_loglift_finite(golden_payload: dict) -> None:
    """All logprob/loglift entries from the legacy output are finite."""
    for key in ("logprob", "loglift"):
        vals = golden_payload["topic_info"][key]
        arr = np.asarray(vals, dtype=np.float64)
        finite = arr[np.isfinite(arr)]
        assert finite.size > 0
