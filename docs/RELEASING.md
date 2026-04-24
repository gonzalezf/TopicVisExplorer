# Releasing: checks before a version tag

Use this as a **readiness** list before (or right after) publishing **`topicvisexplorer`** to PyPI. The library can be used from a **git clone** without tagging; this page is the **“no surprises”** matrix for a release cut.

## Automated gates (match CI and docs)

From the repo root, with `uv sync --all-extras` (or your choice of venv) and
optional `cd frontend && npm ci && npm run build`:

```bash
# Full CI-parity test run (see installation-and-testing.md#how-to-test for variants)
uv run pytest tests/unit/ tests/golden/ tests/api/ tests/integration/ -q
uv run ruff check src tests
```

Docs (must pass with no broken internal links):

```bash
uv run --extra docs mkdocs build --strict
```

## PyPI / end-user smoke (before or after a tag)

In a **fresh** virtual environment (isolated from your dev clone):

```bash
pip install topicvisexplorer
# Optional heavy adapters:
# pip install "topicvisexplorer[full]"
tve --help
tve demo --help
```

**BYO** using the file shipped in the wheel:

```bash
# Path: site-packages/examples/byo_minimal.jsonl inside the venv, or
# use examples/byo_minimal.jsonl at the root of a git clone.
tve demo --texts /path/to/byo_minimal.jsonl --name pypi_smoke --no-browser
# Table CSV (column flag required for header+rows exports):
tve demo --texts /path/to/sample_corpus.csv --csv-text-column text --name csv_smoke --model sklearn-lda --no-browser
```

**Multi-corpus UI** (bundled scenario, no `--texts`):

```bash
tve demo --multicorpora --corpus tiny_multi_demo --no-browser
# Then open http://127.0.0.1:8000/multicorpora
```

**Contributor clone** (same `examples` path as docs):

```bash
uv run tve demo --texts examples/byo_minimal.jsonl --name dev_smoke --no-browser
```

## Documented “promises”

User-facing statement of what is supported: [README: What the library is meant to do](https://github.com/gonzalezf/TopicVisExplorer/blob/main/README.md#what-the-library-is-meant-to-do-and-what-is-out-of-scope) and
[Custom corpus tutorial](custom_corpus_tutorial.md#what-you-get-and-what-is-out-of-scope).

## Optional extras

- `pip install "topicvisexplorer[full]"` and one BYO run with e.g. `--model sklearn-nmf` if release notes highlight optional adapters.
- [installation-and-testing.md](installation-and-testing.md#how-to-test) — full manual scenario table, Playwright, and NLTK/spaCy download steps for maintainers.
