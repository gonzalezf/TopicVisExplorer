# Contributing to TopicVisExplorer

Thanks for your interest. This document covers the developer setup and the
merge gates we enforce.

## Branch model

* `main` — the only development branch. Open all PRs against `main`.
* Release tags follow semver (`v1.0.0`, `v1.1.0`, ...).

### Which GitHub repository?

* **Public library** (paper URL, issues, PRs): **`gonzalezf/TopicVisExplorer`**
  — `https://github.com/gonzalezf/TopicVisExplorer`
* **Private backup** (full history, not the contribution target):
  **`gonzalezf/Topicvisexplorer-OLD`**
  — `https://github.com/gonzalezf/Topicvisexplorer-OLD`

The directory name on your machine does not have to match; use
`git remote -v` to confirm `origin`.

## Local setup

```bash
# Install uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the development environment
uv sync --all-extras
uv run pre-commit install
```

To run **every** unit test (including BERTopic / ETM / CTM / SBERT smoke
tests, BYO with spaCy, and NLTK stopword fixture checks), install the
`[full]` extra and one-time data downloads:

```bash
uv sync --extra dev --extra full
uv run python -c "import nltk; nltk.download('stopwords')"
uv run python -m spacy download en_core_web_sm
```

The repo tracks **`uv.lock`** so CI stays reproducible and
[`astral-sh/setup-uv`](https://github.com/astral-sh/setup-uv) can cache
dependency installs. After you change dependencies in `pyproject.toml`, run
`uv lock` and commit the updated `uv.lock`.

### GitHub Actions (CI + docs)

Workflows use **pinned Python** (`.github/workflows/ci.yml` sets `CI_PYTHON` to
`3.11` for lint, visual, and the release `build` job; tests run on 3.10–3.12).
**`uv run`** is always invoked with an explicit **`--python`** so CI matches the
synced environment.

**Concurrency:** `cancel-in-progress` is **false** for CI and docs, so rapid
pushes to `main` do not cancel runs that already started (you may see several
runs in parallel until they finish).

### Documentation site (MkDocs on CI)

The **`docs`** workflow runs **`mkdocs build --strict`** on every push to
`main`. Optional: enable **Settings → Pages → Source: GitHub Actions** only if
you want a hosted site; the workflow does not deploy by default.

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
