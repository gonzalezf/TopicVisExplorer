# TopicVisExplorer

[![Docs](https://img.shields.io/badge/docs-markdown%20in%20repo-blue)](https://github.com/gonzalezf/TopicVisExplorer/tree/main/docs)
[![Cite this software](https://img.shields.io/badge/cite-CITATION.cff-informational)](./CITATION.cff)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-green.svg)](./LICENSE)

**Interactive topic-modeling visualization — split, merge, compare, and curate
topics across corpora.**

TopicVisExplorer is a Python library and web app that renders LDAvis-style
topic explorations with human-in-the-loop (HITL) refinement. It reproduces the
visual identity of the tool from the accompanying Journal of Visualization
paper while modernizing the implementation as an installable library backed by
FastAPI + Vite + TypeScript + D3 v5.

## Install

```bash
pip install topicvisexplorer          # core + server + demo
pip install "topicvisexplorer[full]"  # + BERTopic / ETM / CTM / SBERT
```

**Developing from a git clone** (reproducible venv, tests, and scripts): use
**`uv sync`** as in [`CONTRIBUTING.md`](CONTRIBUTING.md) (`uv.lock` + Python
from `.python-version`), or `pip install -e ".[dev]"` in a virtualenv.

**Minimal clone → run → test:**

```bash
uv sync
uv run tve demo
uv run pytest tests/unit/ -q
# If you change UI files under frontend/:
cd frontend && npm ci && npm run build && cd ..
```

The built bundle at `src/topicvisexplorer/web/dist/` is not committed; run the
`npm` step after UI edits or you may get a stale or missing `tve.js` in the browser.

## Defaults at a glance

| What | Default |
| ---- | ------- |
| Bundled demo (no `--texts`) | `tve demo` → scenario `20ng_tiny` |
| BYO (`--texts`) | `--model gensim-lda`, `--embedding word2vec`, `--name user_corpus` |
| HTTP bind | `127.0.0.1:8000` (override with `--host` / `--port`) |
| On-disk cache | `~/.cache/topicvisexplorer/` (fit + layout embedding; path includes content hash) |

## Demo

```bash
tve demo                              # real-terms 20ng_tiny (default)
tve demo --corpus bbc_tiny            # second bundled demo (BBC news, 5 categories)
tve demo --corpus tiny_demo           # synthetic w00 fixture (tests / screenshots)
tve demo --texts my.jsonl --name x    # bring-your-own corpus (default: gensim-lda; use --model / --embedding)
```

### Choose a topic model or embedding

TopicVisExplorer ships with **six** topic-model adapters and **two** embedding
backends for the BYO CLI path (`tve demo --texts ...`):

```bash
tve demo --texts my.txt --model sklearn-nmf --num-topics 5
tve demo --texts my.txt --model bertopic --embedding sbert
```

| `--model` | Default | Notes |
| --------- | ------- | ----- |
| `gensim-lda` | yes | Gensim LDA + spaCy cleaning (same as before) |
| `sklearn-lda`, `sklearn-nmf` | | scikit-learn (no extra beyond core) |
| `bertopic`, `etm`, `ctm` | | require `pip install "topicvisexplorer[full]"` |

| `--embedding` | Default | Notes |
| ------------- | ------- | ----- |
| `word2vec` | yes | Trains a small Word2Vec for the topic map (cached) |
| `sbert` | | Sentence-Transformers (requires `[full]`) |

## Datasets and licenses

* **`20ng_tiny` (default)** — A small, **pinned** subset of the [20
  Newsgroups](https://scikit-learn.org/stable/datasets/twenty_newsgroups.html)
  corpus (UCI / sklearn distribution; standard for research and
  benchmarking).  Bundled as committed `npz` + JSON under
  `src/topicvisexplorer/server/fixtures/`; regenerate with
  `python scripts/build_20ng_tiny_fixtures.py` from a dev checkout.
* **`bbc_tiny`** — 400-document subsample of the
  [UCD BBC news corpus](http://mlg.ucd.ie/datasets/bbc.html) (5
  categories: `business`, `entertainment`, `politics`, `sport`, `tech`),
  licensed for research use; cite Greene & Cunningham (ICML 2006). If
  `mlg.ucd.ie` is unreachable the builder falls back to the
  [`SetFit/bbc-news`](https://huggingface.co/datasets/SetFit/bbc-news)
  Hugging Face mirror. Build recipe:
  `python scripts/build_bbc_tiny_fixtures.py`.
* **`tiny_demo` / `tiny_multi_demo`** — **Synthetic** data only; kept
  for fast tests and exact visual baselines.
* **`tve demo --texts ...`** — run the same pipeline on your own
  documents; nothing is committed, fits are cached under
  `~/.cache/topicvisexplorer/` (cache key includes `--model` and
  `--embedding`).
* The **paper's private** full corpora and original pickles are **not**
  in this repository; see [`docs/own_data.md`](docs/own_data.md) for public
  alternatives. A local `PAPER_REPRO.md` is gitignored if you keep private
  reproduction notes beside the tree.

## Library API

```python
import topicvisexplorer as tve
prepared = tve.prepare(
    topic_term_dists=topic_term,
    doc_topic_dists=doc_topic,
    doc_lengths=doc_lengths,
    vocab=vocab,
    term_frequency=term_frequency,
)
tve.show(prepared)                    # single-corpus
tve.show([prepared_a, prepared_b])    # multi-corpus Sankey
```

## What's in the box

- Adapters for **gensim LDA, sklearn LDA + NMF, BERTopic, ETM, CTM**.
- Interactive **split / merge / add-word / remove-word / exclude-document**
  operations; all golden-tested.
- **NPMI, C_v, segregation, coverage** per-topic metrics in a collapsible UI
  panel.
- Paper-faithful visuals (Playwright visual-regression baselines).
- **Two real-terms built-in demos** — `20ng_tiny` (20 Newsgroups slice,
  default) and `bbc_tiny` (BBC news) — plus a **bring-your-own-corpus**
  CLI path (`tve demo --texts ...`). All bundled scenarios (including
  the synthetic `tiny_demo`) wire a `refit` callable, so server-side
  topic **split** and **merge** work out of the box.

## Documentation

**Documentation** lives in the [`docs/`](https://github.com/gonzalezf/TopicVisExplorer/tree/main/docs) folder
(Markdown; browsable on GitHub). To build a static HTML site locally:
`pip install -e ".[docs]"` then `mkdocs serve` (or `mkdocs build --strict`). A
separate public GitHub Pages URL is **not** enabled in this repository by
default; CI only **builds** the site to verify it.

- [Install, test, BYO, CLI flags](docs/installation-and-testing.md) — from PyPI
  or a clone, run tests, environment variables, multicorpora. **Start here to
  share the repo with others.**
- [Quickstart](docs/quickstart.md) — first interactive session.
- [Tutorial](docs/tutorial.md) — from raw tokens to `tve.show`.
- [Working with your own data](docs/own_data.md) — `tve demo` flag table, licenses, export.
- [Model / adapter reference](docs/reference/models.md) — change `--model` / extras.
- [Edit operations](docs/edit-ops.md)
- [Coherence metrics](docs/coherence.md)
- [Extending](docs/extending.md)
- [Migration from v0.1](docs/migration.md)
- [Contributing / CI](CONTRIBUTING.md)

## Citation

If you use TopicVisExplorer in academic work, please cite the paper and the
software (see [`CITATION.cff`](./CITATION.cff)).

## License

BSD-3-Clause. See [`LICENSE`](./LICENSE).
