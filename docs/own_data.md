# Working with your own data

**See also:** [Custom corpus: CSV or Hugging Face → JSONL → `tve demo`](custom_corpus_tutorial.md) — a single narrative for tabular and HF conversion plus multi-corpus limits.

TopicVisExplorer is a **general-purpose** interactive tool: explore
topics, split and merge them, and export a snapshot. You do not need a
separate "user study" server or a POST endpoint — the in-browser
**Export** button saves JSON **only to your computer**.

## `tve demo`: flags and defaults

Authoritative help: `tve demo --help` (from the same version you installed).

| Flag | When it applies | Default / notes |
| ---- | --------------- | --------------- |
| `--host` | Always | `127.0.0.1` |
| `--port` | Always | `8000` |
| `--no-browser` | Always | do not open a tab |
| `--corpus` | Without `--texts` and without `--multicorpora` | `20ng_tiny` (single-corpus) |
| `--corpus` | With `--multicorpora` | `bbc_vs_20ng` (needs built fixtures) or e.g. `tiny_multi_demo` (synthetic) |
| `--multicorpora` | Open `/multicorpora` (Sankey) | incompatible with `--texts` |
| `--texts` | BYO file path | overrides `--corpus` |
| `--name` | With `--texts` | scenario name in URL, default `user_corpus` |
| `--num-topics` | With `--texts` | `5` |
| `--passes` | With `--texts` (LDA-style fits) | `10` |
| `--seed` | With `--texts` | `42` |
| `--model` | With `--texts` | `gensim-lda` (also: `sklearn-lda`, `sklearn-nmf`, `bertopic`, `etm`, `ctm` — last three need `pip install -e ".[full]"` or `uv sync --all-extras` from a clone) |
| `--embedding` | With `--texts` | `word2vec` or `sbert` (`sbert` needs `[full]`) |
| `--sbert-model` | With `--texts` and `--embedding sbert` | `all-MiniLM-L6-v2` (Sentence-Transformers id) |
| `--csv-text-column` | With `--texts` and a **`.csv`** or **`.tsv`** table file (header row) | column name for the document text; without it, `.csv`/`.tsv` are read as **raw lines** (usually wrong for exports). Ignored for `.jsonl` / `.json` / `.txt` |

**Multicorpora (no `--texts`):**

```bash
tve demo --multicorpora
tve demo --multicorpora --corpus tiny_multi_demo
```

Adapter ids and class mapping: [reference/models](reference/models.md).

## Demos and scenarios

| Path | `Scenario` | Notes |
|------|-------------|--------|
| `tve demo` / `?scenario=20ng_tiny` | **20 Newsgroups** slice (real terms) | Default; [README (datasets + licenses)](https://github.com/gonzalezf/TopicVisExplorer/blob/main/README.md#datasets-and-licenses) |
| `tve demo --corpus bbc_tiny` | **BBC news** (5 categories) | Second bundled demo |
| `tve demo --texts my.jsonl --name my_corpus` | **Your** texts, fit on the fly | Cache under `~/.cache/topicvisexplorer` (name includes `--model` / `--embedding`); add `--model`, `--embedding`, `--sbert-model` to pick a topic model or SBERT (see [reference/models](reference/models.md)) |
| `?scenario=tiny_demo` | Synthetic `w00` vocabulary | Fast tests and baselines |
| `scripts/user_study/launch_20ng_study.py` | Live **sklearn** or **Hugging Face** + gensim | Custom `?scenario=` for larger runs; cite script args in papers |

`tiny_demo` is **synthetic**. The paper-era **private** full corpora are
**not** in this repo. If you keep private reproduction context, use a
local `PAPER_REPRO.md` (that filename is gitignored and is not in the
public tree).

## 20 Newsgroups: license and reproducibility

- **Source:** subset of
  [20 Newsgroups](https://scikit-learn.org/stable/datasets/twenty_newsgroups.html)
  via `sklearn.datasets.fetch_20newsgroups` (and the
  [UCI mirror](https://kdd.ics.uci.edu/databases/20newsgroups/)).
- **In-repo fixture:** `20ng_tiny` — pinned subsample; see
  `src/topicvisexplorer/server/fixtures/` and
  `scripts/build_20ng_tiny_fixtures.py` for exact counts and preprocessing.
- **Citing in papers:** name the public datasource, script, random seed,
  document count, and preprocessing (e.g. headers removed).

## BBC news fixture: source and reproducibility

- **Primary source:** D. Greene and P. Cunningham,
  [BBC news corpus](http://mlg.ucd.ie/datasets/bbc.html) (UCD; 5
  categories; research use; cite ICML 2006).
- **Fallback:** [Hugging Face `SetFit/bbc-news`](https://huggingface.co/datasets/SetFit/bbc-news)
  if the UCD host is down.
- **Build:** `python scripts/build_bbc_tiny_fixtures.py` (cached zip under
  `~/.cache/topicvisexplorer/`; outputs in `src/topicvisexplorer/server/fixtures/`).

## Bring your own corpus (CLI)

```bash
tve demo --texts docs.jsonl --name my_corpus --num-topics 7 --passes 15
# Optional: scikit-learn NMF, BERTopic, etc. (some need pip install -e ".[full]" from a clone):
# tve demo --texts docs.txt --model sklearn-nmf --embedding word2vec
# tve demo --texts docs.txt --model bertopic --embedding sbert
```

Accepted inputs:

- **`.jsonl` / `.ndjson`** — one object per line with a `"text"` field.
- **`.json`** — list of strings, or an object with `"texts"`.
- **`.csv` / `.tsv`** (tabular export) — pass **`--csv-text-column <name>`** so the correct column is read (one document per data row; UTF-8; header required). **Example:** `tve demo --texts data.csv --csv-text-column text --name my_corpus`. Without `--csv-text-column`, these extensions are read like plain text (one line = one document), which is wrong for typical table CSVs.
- **`.txt` and other extensions** — one document per non-empty line.

The first run fits the requested topic model (default: **gensim-lda** with
`text_cleaner_batch` + Phraser for that path; **sklearn-lda** / **sklearn-nmf**
use scikit-learn vectorizers on raw lines). Results are cached in
`~/.cache/topicvisexplorer/<name>-<model>-<content-hash>.npz` (the hash
includes `model`, `embedding`, and `sbert_model` when relevant).

!!! warning "Browser split/merge use Gensim LDA refit on BYO"
    The web scenario still registers a **Gensim LDA**-backed `refit` for
    server-side split/merge (same pattern as bundled demos). Your *initial* fit
    may have used a different `--model`. If you rely on a non-gensim adapter,
    check behavior before trusting interactive merge/split; see
    [edit-ops](edit-ops.md).

## Optional: AG News (Hugging Face)

`scripts/user_study/launch_20ng_study.py` supports `--source hf_ag_news`
with `pip install -e ".[hf]"` from a clone (or `pip install datasets`). A
dedicated one-liner loader is a [v1.1 roadmap](roadmap.md) item.

## Export your curated topics (JSON)

In the **single- or multi-corpus** UI, use the **download**-style
**Export** control next to the help button. It writes a `tve_topics_<scenario>.json` file
**in your browser** (Blob download). Nothing is sent to the server. The
file includes, for the **current** session state (after any splits, merges, renames):

- Scenario name, timestamp, and relevance / omega controls where applicable.
- Per-topic **labels** and **top terms** (from the current bar-chart data).
- **Circle positions** for the 2-D map.

For a full **Python** `PreparedData` round-trip (pickle), use
:meth:`topicvisexplorer.PreparedData.save` and :func:`topicvisexplorer.load` from
a notebook; see the [API reference](reference/index.md).

## Split in the browser

Server-side **topic split** needs `Scenario.extras["refit"]`. The bundled
`20ng_tiny` and `bbc_tiny` scenarios register
:func:`topicvisexplorer.operations.refit_helpers.refit_gensim_lda`, and
`tiny_demo` includes a small NumPy `refit_static` so every demo can split/merge. The same
:func:`topicvisexplorer.operations.split` works without the web server; see
[Edit operations](edit-ops.md).
