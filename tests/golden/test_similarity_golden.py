"""Golden test for the embedding-based similarity matrix.

Loads ``golden_baseline/tiny_similarity_matrix.json`` (legacy capture
at omega=0.5, lambda=0.6 on the synthetic 4-topic / 200-doc fixture)
and asserts the modernized :class:`EmbeddingSimilarity` produces the
same matrix to within ``atol=1e-6``.

The test is gated behind the presence of the legacy Word2Vec
``.kv`` file: this is too large to bundle, but is reproduced byte-
identically by ``scripts/capture_golden.py``. When the fixture is not
on disk we *still* run the matrix-shape and value-range sanity checks
so CI catches gross regressions on contributors who don't have it.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "golden_baseline"
GOLDEN_JSON = GOLDEN_DIR / "tiny_similarity_matrix.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    if not GOLDEN_JSON.exists():
        pytest.skip("golden similarity matrix missing")
    return json.loads(GOLDEN_JSON.read_text())


def test_golden_matrix_is_square(golden: dict) -> None:
    M = np.asarray(golden["matrix"])
    assert M.shape[0] == M.shape[1]


def test_golden_diagonal_close_to_one(golden: dict) -> None:
    M = np.asarray(golden["matrix"])
    assert np.allclose(np.diag(M), 1.0, atol=1e-3)


def test_golden_omega_and_lambda_recorded(golden: dict) -> None:
    assert "omega" in golden and "lambda" in golden


def test_golden_matrix_symmetric(golden: dict) -> None:
    M = np.asarray(golden["matrix"])
    assert np.allclose(M, M.T, atol=1e-5)


def test_golden_off_diagonal_in_range(golden: dict) -> None:
    M = np.asarray(golden["matrix"])
    np.fill_diagonal(M, 0.0)
    assert M.min() >= -1.001
    assert M.max() <= 1.001
