# Contributing to TopicVisExplorer

Thanks for your interest in TopicVisExplorer. This document covers the
developer setup and the merge gates we enforce.

## Branch model

* `master` - paper-faithful v0.1 code. Read-only during the v1.0
  development cycle. Do not open PRs against `master`.
* `legacy` - permanent, protected mirror of the paper version. Read-only.
* `next` - active v1.0 development. **Open all PRs against `next`.** Will
  be promoted to `main` at the v1.0 release.

## Local setup

```bash
# Install uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the development environment
uv sync --all-extras
uv run pre-commit install
```

Smoke tests:

```bash
uv run pytest tests/unit/ -q
uv run ruff check src tests
uv run mypy src/topicvisexplorer
```

## Test layers and gates

| Layer    | Path             | Gate           | Tools                                    |
| -------- | ---------------- | -------------- | ---------------------------------------- |
| unit     | `tests/unit/`    | required       | pytest                                   |
| golden   | `tests/golden/`  | required       | pytest, fixtures from `golden_baseline/` |
| api      | `tests/api/`     | required       | pytest + httpx (Phase 2+)                |
| visual   | `tests/visual/`  | required       | Playwright screenshot diff (Phase 3a+)   |
| e2e      | `tests/e2e/`     | nightly + main | Playwright (Phase 3b+)                   |
| bench    | `tests/bench/`   | nightly + main | pytest-benchmark (Phase 3b+)             |

Coverage gate: 85% on `src/topicvisexplorer/` (visual / e2e / bench
excluded from coverage math).

## PR checklist

- [ ] Branched off `next` (not `master`).
- [ ] `uv run pytest` is green locally.
- [ ] `uv run ruff check src tests` is clean.
- [ ] `uv run mypy src/topicvisexplorer` is clean.
- [ ] If touching algorithms: golden tests still match the
      `golden_baseline/` outputs to `atol=1e-6`.
- [ ] If touching the UI: visual regression baselines updated via
      `scripts/update_visual_baselines.py` in a separate dedicated PR
      (NOT the same PR that changes the code).
- [ ] CHANGELOG entry under `## [Unreleased]`.

## Recapturing golden baselines

Algorithm changes that *intentionally* shift numerical output must
re-capture the goldens in their own PR:

```bash
# In .venv-legacy (Python 3.8) - the baseline-equivalence ref
PYTHONPATH=. .venv-legacy/bin/python scripts/capture_golden.py
git diff golden_baseline/   # review carefully before committing
```

Re-capture against the real Cambridge Analytica pickle (if you have it
locally) before claiming paper-figure parity:

```bash
PYTHONPATH=. .venv-legacy/bin/python scripts/capture_golden.py \
    --pickle models_output/single_corpus_europe_dataset_topics_new_lda_6_topics_10000_docs.pkl \
    --output-prefix golden_baseline/europe
```

## Code style

* `ruff format` (configured in `pyproject.toml`).
* Type hints required on all public APIs (`mypy --strict`).
* No `print()` in library code. Use `logging.getLogger("topicvisexplorer")`.
* No silent `try/except`. All custom exceptions live in `errors.py` and
  carry actionable messages (tell the user which `pip install` extra
  to add, which file to check, etc.).

## Commit messages

* Imperative mood, present tense ("Add adapter", not "Added adapter").
* First line <=72 characters. Body wraps at 72.
* Reference the relevant phase in the body if the change is
  phase-aligned (e.g. "Phase 1: ...").
