# Runnable examples (Python)

Run these **from the repository root** after:

1. **`uv sync`** (or an editable install) — see [Install, test, BYO](../docs/installation-and-testing.md#git-clone)
2. **Vite build once** (the modern UI is not committed): `cd frontend && npm ci && npm run build && cd ..`

Data files (`sample_corpus.csv`, `byo_minimal.jsonl`, …) are resolved **next to** `examples/`, so you can run the commands from the repo root as shown.

## Scenario matrix

| You want | Run |
| -------- | --- |
| Single-corpus, your model (Gensim LDA + `prepare`) | `uv run python examples/01_prepare_single_corpus.py` |
| Single-corpus, a CSV column (`--csv-text-column` from Python) | `uv run python examples/02_byo_csv_show.py` |
| Multicorpora, your two text sets (API → Sankey) | `uv run python examples/03_two_corpora_sankey.py` |
| Single-corpus, **bundled** scenario (no user fit) | `uv run python examples/04_bundled_single_demo.py` |
| Multicorpora, **bundled** two-corpus (Sankey) | **CLI only** (no public `tve.demo(multicorpora=…)` yet) — see [Bundled multicorpora (CLI)](#bundled-multicorpora-cli) below |

**Dependencies (core install):** script 01 uses **gensim**; 02 and 03 use **scikit-learn** (same as `sklearn-lda` in tests). 04 uses **bundled** fixtures only.

**Headless / SSH:** add `--no-browser` to any script. Stop the server with **Ctrl+C**.

**Fast checks without opening the server** — every script supports **`--smoke`** (build or validate only, except 04 which only checks the API is importable; `tve.demo` is not run because it would block).

**First run / caching:** example 02 fits on your file and may use cache under `~/.cache/topicvisexplorer/`. Example 03 by default sets **`TVE_EMBEDDING_DISABLE=1`** for a quick Jensen–Shannon layout; set `TVE_EMBEDDING_DISABLE=0` to train a shared Word2Vec for the Omega slider (slower first visit).

## Bundled multicorpora (CLI)

Two-corpus **bundled** Sankey, same as `tve demo --multicorpora` in the [CLI](../src/topicvisexplorer/cli.py):

```bash
# Synthetic, no extra fixture build
uv run tve demo --multicorpora --corpus tiny_multi_demo --no-browser

# Other bundled pair — may require fixture build scripts; see install doc
uv run tve demo --multicorpora --corpus bbc_vs_20ng --no-browser
```

See [Installation and testing](../docs/installation-and-testing.md) for bundled data / fixtures.

## Per-script one-liners

| Script | With smoke test only |
| ------ | -------------------- |
| `01_prepare_single_corpus.py` | `uv run python examples/01_prepare_single_corpus.py --smoke` |
| `02_byo_csv_show.py` | `uv run python examples/02_byo_csv_show.py --smoke` |
| `03_two_corpora_sankey.py` | `uv run python examples/03_two_corpora_sankey.py --smoke` |
| `04_bundled_single_demo.py` | `uv run python examples/04_bundled_single_demo.py --smoke` |
