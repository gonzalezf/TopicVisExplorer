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
tve --help
tve demo --help
python -c "import topicvisexplorer; print(topicvisexplorer.__version__)"
```

## Run the app

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

## Run tests

From the repo with dev deps installed (`uv sync --all-extras` or `pip install -e ".[dev]"`):

```bash
uv run pytest tests/unit/ -q
uv run pytest tests/api/ -q
```

These are the common gates. Some tests are skipped unless optional stack is present (e.g. spaCy, `[full]` models); that is expected. Full matrix, linters, and CI expectations: [CONTRIBUTING.md](https://github.com/gonzalezf/TopicVisExplorer/blob/main/CONTRIBUTING.md).

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
