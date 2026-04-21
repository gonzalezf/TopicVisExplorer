# Golden baselines

This directory holds **paper-equivalence reference outputs** captured from the
paper-version code. Every module in the modernized library checks its output
against these files via golden tests in `tests/golden/`.

## What is here

| File                              | Covered by                               |
| --------------------------------- | ---------------------------------------- |
| `tiny_prepare_output.json`        | `tests/golden/test_prepare_golden.py`    |
| `tiny_similarity_matrix.json`     | `tests/golden/test_similarity_golden.py` |
| `tiny_edit_ops.json`              | `tests/golden/test_edit_ops_golden.py`   |
| `tiny_manifest.json`              | Drift detection (seed, hyperparams, hashes) |
| `baseline_bench.json`             | Similarity hot-path wall-clock reference |

All baselines are derived from a **synthetic tiny fixture** (see
`tests/conftest.py`) — small enough to capture deterministically in CI, large
enough to exercise every algorithm code path.

## Two important caveats

### 1. The tiny fixture is not the paper's data

These golden files assert that the modernized implementation produces the same
numbers as the paper-version code on the **same synthetic input**. They do
**not** reproduce the paper's published figures — those depend on private
corpora that are not shipped with the library (see
[`PAPER_REPRO.md`](../PAPER_REPRO.md)).

### 2. The synthetic benchmark is dominated by Python overhead

Per `baseline_bench.json` the tiny-fixture similarity recompute is ~2 ms,
dominated by Python call overhead, not algorithmic work. It is a
**regression guard** (catching, e.g., accidental `deepcopy`s), not an
absolute performance target.

## Re-capture rules

Algorithm changes that intentionally shift numerical output must re-capture
these files in a dedicated PR:

```bash
uv run python scripts/capture_edit_op_golden.py
git diff golden_baseline/            # review carefully before committing
```

Re-capture scripts are deterministic at `seed=42`. A change in output hash
that you did not expect means an upstream dependency drifted — investigate
before committing the new files.
