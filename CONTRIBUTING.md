# Contributing to TopicVisExplorer

Thanks for your interest. This document covers the developer setup and the
merge gates we enforce.

## Branch model

* `main` — the only development branch. Open all PRs against `main`.
* Release tags follow semver (`v1.0.0`, `v1.1.0`, ...).

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
| api      | `tests/api/`     | required       | pytest + httpx                           |
| visual   | `frontend/tests/`| required       | Playwright screenshot diff               |
| bench    | `tests/bench/`   | nightly + main | pytest-benchmark                         |

Coverage gate: 80% on `src/topicvisexplorer/` (visual / bench excluded
from coverage math — see `[tool.coverage]` in `pyproject.toml`).

## PR checklist

- [ ] Branched off `main`.
- [ ] `uv run pytest` is green locally.
- [ ] `uv run ruff check src tests` is clean.
- [ ] `uv run mypy src/topicvisexplorer` is clean.
- [ ] If touching algorithms: golden tests still match the
      `golden_baseline/` outputs to `atol=1e-9`.
- [ ] If touching the UI: visual regression baselines updated via the
      Playwright snapshot workflow in a separate dedicated PR (NOT the
      same PR that changes the code).
- [ ] CHANGELOG entry under `## [Unreleased]`.

## Recapturing golden baselines

Algorithm changes that *intentionally* shift numerical output must
re-capture the goldens in their own PR:

```bash
uv run python scripts/capture_edit_op_golden.py
git diff golden_baseline/   # review carefully before committing
```

## Code style

* `ruff format` (configured in `pyproject.toml`).
* Type hints required on all public APIs (`mypy --strict`).
* No `print()` in library code. Use `logging.getLogger("topicvisexplorer")`.
* No silent `try/except`. All custom exceptions live in `errors.py` and
  carry actionable messages (tell the user which `pip install` extra to
  add, which file to check, etc.).

## Commit messages

* Imperative mood, present tense ("Add adapter", not "Added adapter").
* First line ≤72 characters. Body wraps at 72.
