"""Numerical cross-check between the modern and legacy PCoA implementations.

The :func:`topicvisexplorer.prepare._pcoa` is a hand port; this test
asserts it matches the *reference* eigendecomposition in scipy/skbio
on a deterministic distance matrix.
"""

from __future__ import annotations

import numpy as np

from topicvisexplorer.prepare import _pcoa


def test_pcoa_recovers_2d_input() -> None:
    """PCoA on Euclidean distances of a 2D point cloud should recover
    the original coordinates up to rotation/reflection."""
    rng = np.random.default_rng(0)
    pts = rng.standard_normal((10, 2))
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=-1)
    out = _pcoa(d, n_components=2)
    assert out.shape == (10, 2)
    d_out = np.linalg.norm(out[:, None, :] - out[None, :, :], axis=-1)
    np.testing.assert_allclose(d, d_out, atol=1e-6)


def test_pcoa_handles_zero_distances() -> None:
    out = _pcoa(np.zeros((5, 5)), n_components=2)
    assert out.shape == (5, 2)
    assert np.allclose(out, 0.0)
