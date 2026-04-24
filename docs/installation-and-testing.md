# Installation and testing

Python **3.10–3.12** (see `.python-version` in the repo for the pin used in CI; currently 3.11). If a command or flag here disagrees with your install, run `tve demo --help` and use that as source of truth.

## PyPI (end users)

```bash
pip install topicvisexplorer
```

Optional heavy topic models and SBERT layout embedding:

```bash
pip install "topicvisexplorer[full]"
```

`[full]` pulls in BERTopic, ETM, CTM, sentence-transformers, spaCy, NLTK (see `pyproject.toml`). You need it for `--model bertopic|etm|ctm` and for `--embedding sbert` on `tve demo --texts ...`.

Optional Hugging Face datasets (for some scripts, not the core demo):

```bash
pip install "topicvisexplorer[hf]"
```

## Git clone (contributors, coursework, repro)

Reproducible env (recommended):

```bash
git clone https://github.com/gonzalezf/TopicVisExplorer.git
cd TopicVisExplorer
uv sync --all-extras
```

The `tve` program is the package’s [console script](https://packaging.python.org/en/latest/specifications/entry-points/#use-for-scripts). It is only on your `PATH` after an install. With **`uv`**, prefer **`uv run tve …`** (uses the project venv) until you have activated that venv and/or run `pip install -e .`, after which you can type `tve` directly.

Manual venv:

```bash
pip install -e ".[dev,docs]"
```

The web UI bundle under `src/topicvisexplorer/web/dist/` is **gitignored**. After changing TypeScript/legacy JS under `frontend/`, rebuild before serving from a checkout:

```bash
cd frontend && npm ci && npm run build && cd ..
```

Without that step, the server may still run but the browser can load an outdated or missing `tve.js` (hard-refresh after every build).

## Check that it worked

```bash
uv run tve --help          # from a git clone (after uv sync; works without activating .venv)
uv run tve demo --help
uv run python -c "import topicvisexplorer; print(topicvisexplorer.__version__)"
# After pip/uv install, or venv with topicvisexplorer on PATH, you can use the same with bare: tve …
```

**`tve: command not found`** — You skipped install or the active shell is not the venv. From a clone: `uv sync` then `uv run tve --help`, or `source .venv/bin/activate` and `tve --help` after the sync. For **PyPI** users: `pip install topicvisexplorer` and ensure you are in the same environment you installed into.

## Run the app

**Shell:** In this section, examples use plain **`tve`**. From a **git clone** without that binary on your `PATH`, use **`uv run tve …`**, or activate `.venv` first. If you **installed from PyPI**, `tve` in that environment is enough.

Bundled single-corpus demo (default scenario `20ng_tiny`):

```bash
tve demo
```

No browser (useful over SSH):

```bash
tve demo --no-browser --port 8000
```

Then open `http://127.0.0.1:8000/singlecorpus?scenario=20ng_tiny` in a local browser if needed.

Server only (no preloaded scenario):

```bash
tve serve --port 8000
```

Two-corpus Sankey UI (`--texts` is not valid here):

```bash
tve demo --multicorpora
tve demo --multicorpora --corpus tiny_multi_demo
```

Bring-your-own file corpus:

```bash
tve demo --texts path/to/docs.jsonl --name my_run --num-topics 8
```

First **visit** to a scenario may take ~tens of seconds: topic fit (BYO) and/or a small Word2Vec for the topic-similarity map (cached under `~/.cache/topicvisexplorer/`). See [quickstart](quickstart.md#2-launch-the-demo) for `TVE_EMBEDDING_DISABLE=1` (skips that embedding; Omega slider on the map will not move topics).

## How to test

You will use **two** kinds of checks:

1. **Automated** — `pytest` (and the same linters/frontend build as [GitHub Actions](https://github.com/gonzalezf/TopicVisExplorer/blob/main/.github/workflows/ci.yml)). This is the proof that a change is safe; run it from a **git clone** with dev (and usually `full`) extras.
2. **Manual smoke (optional but useful)** — Start each **bundled** `tve demo` scenario once in a browser and click around (hover topics, try split/merge if you touched that code). The automated suite hits HTTP APIs; it does not replace a human pass on the UI for large frontend edits.

**Quick matrix — what lives where**

| Check | Path or command | Notes |
| ----- | --------------- | ----- |
| Unit | `tests/unit/` | Pure Python, fastest |
| Golden | `tests/golden/` | Numeric baselines under `golden_baseline/` |
| API | `tests/api/` | FastAPI + `httpx` (includes per-scenario smoke where applicable) |
| Integration | `tests/integration/` | CLI / BYO paths |
| Frontend build | `frontend/` | `npm run build` (bundle copied into the wheel) |
| Visual | `frontend/` | Playwright; separate CI job, needs `npm run build` first |

Deeper table (optional deps, recapturing goldens, PR checklist): [CONTRIBUTING.md](https://github.com/gonzalezf/TopicVisExplorer/blob/main/CONTRIBUTING.md).

### Automated: match the Python `test` job (recommended)

From the **repository root**, with dev + full stack (same as CI’s test matrix — see `ci.yml`):

```bash
uv sync --extra dev --extra full
uv run python -c "import nltk; nltk.download('stopwords')"
uv run python -m spacy download en_core_web_sm

uv run pytest tests/unit tests/golden tests/api tests/integration \
  --cov=topicvisexplorer \
  --cov-report=term-missing \
  -q
```

CI also sets `PYTHONHASHSEED=0` for reproducibility; you can add `PYTHONHASHSEED=0` in front of the `pytest` line to mirror that.

**Faster slice** when iterating (skips `golden` / `integration` and may miss scenario coverage; some tests require `[full]` and still skip if deps are missing):

```bash
uv run pytest tests/unit/ tests/api/ -q
```

**Lint (match the `lint` job):**

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src/topicvisexplorer
```

**Frontend (match the `frontend` job):**

```bash
cd frontend && npm ci && npm run lint && npx tsc --noEmit && npm run build && cd ..
```

**Playwright visual tests (match the `visual` job; slower, needs Chromium):**

```bash
cd frontend && npx playwright install --with-deps chromium && npx playwright test && cd ..
```

### Manual smoke: try each bundled scenario

Run these when you only need to “see the app work” (after UI changes, rebuild: `cd frontend && npm run build`).

| Scenario | Command |
| -------- | ------- |
| Default 20 Newsgroups tiny | `tve demo` (same as `--corpus 20ng_tiny`) |
| BBC news tiny | `tve demo --corpus bbc_tiny` |
| Synthetic single-corpus | `tve demo --corpus tiny_demo` |
| Two-corpus Sankey (real fixtures) | `tve demo --multicorpora` |
| Two-corpus Sankey (synthetic) | `tve demo --multicorpora --corpus tiny_multi_demo` |
| Server only, no preloaded data | `tve serve --port 8000` then open URLs you construct by hand |
| Over SSH (no autostart browser) | `tve demo --no-browser --port 8000` and open the printed link locally |

**Bring-your-own** is not a fixed “bundled” row; use `tve demo --texts /path/to/file.jsonl --name my_run` (and optional `--model` / `--embedding`) — see [own_data](own_data.md) for the full flag table.

## Environment variables (supported)

| Variable | Effect |
| -------- | ------ |
| `TVE_EMBEDDING_DISABLE=1` | Skip Word2Vec training for topic-layout similarity; use Jensen–Shannon–based layout. See `tve demo` CLI description. |
| `TVE_DEBUG=true` (browser) | Verbose client logs for split/merge and related UI; set on `window` in devtools, then reload. |

## Where to go next

- [Quickstart](quickstart.md) — first interactive session.
- [Working with your own data](own_data.md) — BYO files, full `tve demo` flag table, licenses.
- [Model reference](reference/models.md) — adapter ids and `pip` extras.
- [Contributing](https://github.com/gonzalezf/TopicVisExplorer/blob/main/CONTRIBUTING.md) — ruff, mypy, full pytest layers.
