# Quickstart

For install options, **tests from a git clone**, `tve serve`, and a full
`tve demo` flag list, use [Install, test, BYO](installation-and-testing.md)
first; this page stays short.

This page gets you from zero to an interactive TopicVisExplorer window in
under a minute. The default browser session uses a **small 20 Newsgroups**
slice (`20ng_tiny`, real terms); the synthetic `tiny_demo` scenario is
still available for exact reproducible tests and screenshots.

## 1. Install

**If you are working from a git clone** (latest `main`, reproducible dev env — recommended for the tree on GitHub):

```bash
uv sync --all-extras
# optional: build the Vite UI bundle (not committed; needed for a modern tve.js)
(cd frontend && npm ci && npm run build && cd ..)
uv run tve demo
```

Use **`uv run tve …`** from the clone, or activate `.venv` / `pip install -e .` and run `tve` directly. If you see **`tve: command not found`**, see [Install & test: troubleshooting](installation-and-testing.md#check-that-it-worked). For details see [`CONTRIBUTING.md`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/CONTRIBUTING.md). Without `uv`, use a virtualenv: `pip install -e ".[dev,docs]"`.

**There is no published PyPI install yet;** work from a git clone. After a first release, the README and [install doc](installation-and-testing.md) will add `pip install topicvisexplorer`.

## 2. Launch the demo

```bash
tve demo                          # default: 20ng_tiny (20 Newsgroups slice)
tve demo --corpus bbc_tiny        # second bundled demo (BBC news, 5 categories)
tve demo --corpus tiny_demo       # synthetic fixed-vocab corpus (tests, screenshots)
```

### Bring your own corpus

Step-by-step from **CSV** or **Hugging Face** to JSONL and the right flags:
[Custom corpus (CSV, HF) → JSONL](custom_corpus_tutorial.md) (prerequisites: [Git clone / install only](installation-and-testing.md#git-clone)).

```bash
# JSONL with a "text" field, plain .txt (one doc per line), or JSON array of strings:
tve demo --texts mydocs.jsonl --name my_corpus --num-topics 8 --passes 15

# Table CSV/TSV (header row + text column) — set the column name:
tve demo --texts mytable.csv --csv-text-column text --name my_corpus

# Optional: different adapter or SBERT (from clone: `pip install -e ".[full]"` or `uv sync --all-extras` for bertopic/etm/ctm/sbert):
tve demo --texts mydocs.txt --model sklearn-nmf --embedding word2vec
```

The first run fits a topic model (default: Gensim LDA) with the full
`text_cleaner_batch` + Phraser bigram pipeline and caches the result in
`~/.cache/topicvisexplorer/<name>-<model>-<content-hash>.npz`; subsequent runs
reuse the cache (instant). The browser is opened at
`/singlecorpus?scenario=<name>&hitl=true` so split / merge / add-word /
remove-word all work out of the box.

!!! warning "Split/merge uses Gensim LDA refit on BYO"
    When you click split or merge in the browser after a BYO fit, the server
    re-fits with **Gensim LDA** internally, even if you used `--model bertopic`
    or `--model sklearn-nmf` for the initial fit. See
    [Working with your own data](own_data.md#bring-your-own-corpus-cli) for details.

!!! tip "One-time topic-similarity embedding"
    On the first visit to a scenario we also train a small Word2Vec
    embedding (~20s for the bundled demos) to power the Omega slider in
    the topic-map. The result is cached in
    `~/.cache/topicvisexplorer/<name>_w2v_v1.kv`; subsequent loads are
    instant. Delete the cache dir (or bump the `_v1` suffix when
    preprocessing changes) to force retraining. Set the env var
    `TVE_EMBEDDING_DISABLE=1` to skip training entirely and fall back to
    a flat Jensen-Shannon layout (Omega slider will not move bubbles).

That opens `http://127.0.0.1:8000/singlecorpus` in your
browser (default `?scenario=20ng_tiny`). You should see:

- A **topic-map scatter** on the left (2-D PCoA of topic-topic distances).
- A **bar chart** on the right of the top terms for the hovered topic.
- A **documents table** below, with a `×` button per row for the
  [exclude-document](edit-ops.md#exclude-a-document) workflow.
- A **Coherence** control (label + small Σ) in the top-right that opens the
  [coherence panel](coherence.md).
- An **Export** (download) button next to the help control: saves a JSON
  snapshot of topic labels, top terms, and layout to **your computer only**
  (no upload). See [own_data.md](own_data.md#export-your-curated-topics-json).

Hover a circle to reload the bar chart and documents table. Click it to
pin it and unlock the split / merge / add-word / remove-word controls.

## 3. Render your own model

The fastest path is `tve.prepare(...)` + `tve.show(...)`:

```python
import topicvisexplorer as tve

# Bring your own model outputs in LDAvis shape:
prepared = tve.prepare(
    topic_term_dists=topic_term,    # (K, V) row-stochastic
    doc_topic_dists=doc_topic,      # (N, K) row-stochastic
    doc_lengths=doc_lengths,        # (N,) token counts
    vocab=vocab,                    # list[str], length V
    term_frequency=term_frequency,  # (V,) corpus-level counts
)

tve.show(prepared)                  # opens a browser tab
```

For multi-corpus comparison (Sankey diagram of topic flow):

```python
tve.show([prepared_a, prepared_b])
```

### `tve.show()` parameter reference

| Parameter | Type | Default | Notes |
| --------- | ---- | ------- | ----- |
| `prepared` | `PreparedData` or `list[PreparedData]` | — | Single corpus or list of two for Sankey. Mutually exclusive with `texts_file`. |
| `texts_file` | `str` or `Path` | `None` | Fit a topic model on this file (JSONL / JSON / CSV / TXT). Mutually exclusive with `prepared`. |
| `byo_model` | `str` | `"gensim-lda"` | Model adapter id when `texts_file` is set. Options: `gensim-lda`, `sklearn-lda`, `sklearn-nmf`, `bertopic`, `etm`, `ctm`. Last three require `[full]`. |
| `byo_embedding` | `str` | `"word2vec"` | Embedding for the topic-map layout. `"sbert"` requires `[full]`. |
| `sbert_model` | `str` | `"all-MiniLM-L6-v2"` | Sentence-Transformers model id (only used when `byo_embedding="sbert"`). |
| `byo_num_topics` | `int` | `5` | Number of topics for BYO fits. |
| `byo_passes` | `int` | `10` | LDA training passes for BYO fits. |
| `byo_seed` | `int` | `42` | Random seed for BYO fits (pin for reproducibility). |
| `byo_csv_text_column` | `str` | `None` | Column name when `texts_file` is a `.csv`/`.tsv`. Required for tabular files; without it, every line is one document. |
| `raw_texts` | `list[str]` or `list[list[str]]` | `None` | Raw document strings aligned with `prepared`. Enables the embedding-based Omega layout and split/merge. |
| `model_data` | `TopicModelData` or list | `None` | Underlying adapter output, required alongside `raw_texts`. |
| `scenario_name` | `str` | `"user_data"` | Internal name registered for user data; appears in the URL as `?scenario=<name>`. |
| `open_browser` | `bool` | `True` | Open the OS default browser automatically. Pass `False` over SSH. |
| `host` | `str` | `"127.0.0.1"` | Server bind address. |
| `port` | `int` | `8000` | Server port. |

!!! warning "Split/merge refit uses Gensim LDA regardless of `--model`"
    When you use the browser split/merge controls after a BYO fit, the server
    re-fits with **Gensim LDA** internally, even if you chose `--model sklearn-nmf`
    or `--model bertopic` for the initial fit. The initial visualization is faithful
    to your model; only the *re-fit on the sub-corpus* uses Gensim LDA. See
    [Working with your own data](own_data.md#bring-your-own-corpus-cli) for details.

!!! tip "Using TopicVisExplorer inside a Jupyter notebook"
    `tve.show()` starts a **blocking** FastAPI server — the cell will never finish.
    Two workarounds until `tve.show_inline()` ships in v1.1:

    1. **Static snapshot (no server):** call `tve.save_html(prepared, "topics.html")`,
       then open the file in a browser tab, or display it inline:
       ```python
       from IPython.display import HTML
       HTML(open("topics.html").read())
       ```
    2. **Server in a terminal:** run `tve.show(prepared, open_browser=False)` from a
       separate terminal, then open the printed URL in a browser alongside your notebook.

    See [`examples/00_end_to_end.ipynb`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/examples/00_end_to_end.ipynb)
    for a fully executable notebook using the `save_html` path.

## 4. Adapters for common pipelines

If you trained a model with gensim, scikit-learn, BERTopic, ETM, or CTM,
skip `prepare()` and use the matching adapter. See the
[Tutorial](tutorial.md) for a full walkthrough and
[Extending](extending.md) for the adapter protocol.

## 5. Next

- [Tutorial](tutorial.md) — 5-minute bring-your-own-corpus walkthrough.
- [Edit operations](edit-ops.md) — interactive topic refinement.
- [Working with your own data](own_data.md) — demos, BYO corpus, export JSON,
  and the optional `launch_20ng_study.py` script for larger live fits.
- [API reference](reference/index.md) — all public functions.
