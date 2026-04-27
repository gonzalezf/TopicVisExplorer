# Runnable examples (Python)

Run these **from the repository root** after:

1. **`uv sync`** (or an editable install) — see [Install, test, BYO](../docs/installation-and-testing.md#git-clone)
2. **Vite build once** (the modern UI is not committed): `cd frontend && npm ci && npm run build && cd ..`

Data files (`sample_corpus.csv`, `byo_minimal.jsonl`, …) are resolved **next to** `examples/`, so you can run the commands from the repo root as shown.

## Scenario matrix

| You want | Run |
| -------- | --- |
| **End-to-end tutorial** (CSV → LDA → coherence → merge → HTML) | Open `examples/00_end_to_end.ipynb` in Jupyter — outputs pre-committed |
| Single-corpus, your model (Gensim LDA + `prepare`) | `uv run python examples/01_prepare_single_corpus.py` |
| Single-corpus, a CSV column (`--csv-text-column` from Python) | `uv run python examples/02_byo_csv_show.py` |
| Multicorpora, your two text sets (API → Sankey) | `uv run python examples/03_two_corpora_sankey.py` |
| Single-corpus, **bundled** scenario (no user fit) | `uv run python examples/04_bundled_single_demo.py` |
| Multicorpora, **bundled** two-corpus (Sankey) | **CLI only** (no public `tve.demo(multicorpora=…)` yet) — see [Bundled multicorpora (CLI)](#bundled-multicorpora-cli) below |
| **Hugging Face dataset** → JSONL → `tve.show()` | `uv run python examples/05_huggingface_demo.py` (requires `[hf]` extra) |
| **BERTopic / ETM / CTM** Python adapter → `tve.show()` | `uv run python examples/06_bertopic_show.py` (requires `[full]` extra) |

**Dependencies:** notebook `00_` and scripts `01_`/`02_`/`03_` use **gensim** / **scikit-learn** (core install). `05_` needs `pip install -e ".[hf]"`. `06_` needs `pip install -e ".[full]"`.

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
| `00_end_to_end.ipynb` | `uv run pytest --nbmake examples/00_end_to_end.ipynb` (re-execute to regenerate outputs: see below) |
| `01_prepare_single_corpus.py` | `uv run python examples/01_prepare_single_corpus.py --smoke` |
| `02_byo_csv_show.py` | `uv run python examples/02_byo_csv_show.py --smoke` |
| `03_two_corpora_sankey.py` | `uv run python examples/03_two_corpora_sankey.py --smoke` |
| `04_bundled_single_demo.py` | `uv run python examples/04_bundled_single_demo.py --smoke` |
| `05_huggingface_demo.py` | `uv run python examples/05_huggingface_demo.py --smoke` (requires `[hf]`) |
| `06_bertopic_show.py` | `uv run python examples/06_bertopic_show.py --smoke` (requires `[full]`) |

## Notebook: re-executing and committing outputs

The notebook `00_end_to_end.ipynb` is committed **with cell outputs** so readers
on GitHub can see the expected results without running anything. After any API
change that affects notebook output, re-execute and commit:

```bash
# From the repo root (after uv sync --all-extras):
source .venv/bin/activate
python -c "
import nbformat, nbclient, uuid
nb = nbformat.read('examples/00_end_to_end.ipynb', as_version=4)
for cell in nb.cells:
    if 'id' not in cell:
        cell['id'] = str(uuid.uuid4())[:8]
nbclient.NotebookClient(nb, timeout=120).execute()
nbformat.write(nb, 'examples/00_end_to_end.ipynb')
"
git add examples/00_end_to_end.ipynb
git commit -m "chore: re-execute notebook with updated outputs"
```
