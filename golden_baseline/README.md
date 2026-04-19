# Golden baselines

This directory holds the **paper-equivalence reference outputs** captured from
the legacy code. Every later phase (Phase 1, 2, 3a, 3b, 4) checks its
modernized re-implementation against these files via golden tests.

## What is here

| File                              | Source                                                                | Phase 1 use                         |
| --------------------------------- | --------------------------------------------------------------------- | ----------------------------------- |
| `tiny_lda.pkl`                    | `scripts/capture_golden.py` against synthetic 20 Newsgroups subset    | Input fixture for unit + golden tests |
| `tiny_word2vec.kv`                | Word2Vec trained with paper CBOW defaults on the same subset          | Embedding fixture                   |
| `tiny_prepare_output.json`        | Legacy `_prepare.prepare(...)` output                                 | `tests/golden/test_golden_prepare.py` |
| `tiny_similarity_matrix.npy/json` | Legacy `_topic_similarity_matrix.get_matrix_by_lambda` at omega=0.5   | `tests/golden/test_golden_similarity.py` |
| `tiny_manifest.json`              | Captured-at timestamp, seed, hyperparams, sha256 of every artifact    | Drift detection                     |
| `baseline_bench.json`             | Wall-clock for the similarity hot-path on the tiny fixture            | Phase 3b 5x speedup gate            |

## Two important caveats (please read)

### 1. The tiny fixture is not the paper's data

These golden files are derived from a synthetic 4-topic, 200-document subset of
20 Newsgroups - small enough to capture in seconds inside a sandbox CI, large
enough to exercise the algorithm code paths (`_prepare`,
`_topic_similarity_matrix`, `gensim_helpers`).

They are **sufficient** for asserting that the modernized re-implementation
produces the same numbers as the legacy code on the same input, and that is
what golden tests need to do.

They are **not sufficient** for reproducing the paper's published figures.
For paper-figure reproduction the user must re-run capture against their own
copy of the Cambridge Analytica / airlines pickles (which are gitignored and
not redistributable per Twitter ToS):

```bash
PYTHONPATH=. .venv-legacy/bin/python scripts/capture_golden.py \
    --pickle models_output/single_corpus_europe_dataset_topics_new_lda_6_topics_10000_docs.pkl \
    --output-prefix golden_baseline/europe

PYTHONPATH=. .venv-legacy/bin/python scripts/capture_baseline_bench.py \
    --fixture golden_baseline/europe_lda.pkl \
    --word2vec golden_baseline/europe_word2vec.kv \
    --out golden_baseline/europe_baseline_bench.json
```

The captured `europe_*` files belong on the `legacy` branch but should NOT
be committed to `next` if they exceed a few MB; instead, hash them and
download from a Zenodo deposit at test time. See Phase 0 plan for details.

### 2. The benchmark on the tiny fixture is dominated by Python overhead

Per `baseline_bench.json` the tiny-fixture similarity recompute is ~2ms,
which is dominated by Python call overhead, not by algorithmic work. The
2ms number is **not** a meaningful Phase 3b speedup target.

The meaningful Phase 3b target is the *real-corpus* timing captured against
the Cambridge Analytica pickle (above). The legacy code's split/merge on
that corpus is documented (and remembered by the original author) as
"several seconds to tens of seconds" - that is the 5x target.

We still capture the tiny baseline so that Phase 3b's CI can detect
*infrastructural* regressions (e.g. accidentally re-introducing the
`deepcopy(lda_model)` cost) on the synthetic fixture, even when no real
corpus is available.

## Worktree convention

The plan calls for these files to be accessible from any branch via a
worktree (`git worktree add ../legacy-tree legacy`). On the `next` branch
they live at `tests/golden/` (copied during Phase 1 from this directory).
On `master` / `legacy` they live here and are committed.

## Re-capture rules

* `capture_golden.py` is deterministic at `seed=42`. Re-running it must
  produce byte-identical output (same sha256s in `tiny_manifest.json`).
  If the sha256 changes, an algorithmic dependency drifted - investigate
  before committing the new files.
* Bumping any version pinned in `legacy/requirements.lock` invalidates the
  golden files. After such a bump, re-run capture and review the diff
  before committing.
