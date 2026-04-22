# Quickstart

This page gets you from zero to an interactive TopicVisExplorer window in
under a minute. The default browser session uses a **small 20 Newsgroups**
slice (`20ng_tiny`, real terms); the synthetic `tiny_demo` scenario is
still available for exact reproducible tests and screenshots.

## 1. Install

```bash
pip install topicvisexplorer          # core + server + demo
# or, for BERTopic / ETM / CTM / SBERT:
pip install "topicvisexplorer[full]"
```

??? note "Working from a clone"
    The repo is designed around **`uv`** and a committed **`uv.lock`**
    (see [`CONTRIBUTING.md`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/CONTRIBUTING.md) in the same tree):

    ```bash
    uv sync --all-extras
    (cd frontend && npm ci && npm run build)   # optional: modern Vite UI
    uv run tve demo
    ```

    Without `uv`, use a virtualenv: `pip install -e ".[dev,docs]"` then the
    same `tve` / `pytest` / `ruff` commands.

## 2. Launch the demo

```bash
tve demo                          # default: 20ng_tiny (20 Newsgroups slice)
tve demo --corpus bbc_tiny        # second bundled demo (BBC news, 5 categories)
tve demo --corpus tiny_demo       # synthetic fixed-vocab corpus (tests, screenshots)
```

### Bring your own corpus

```bash
# JSONL with a "text" field, plain .txt (one doc per line), or JSON array of strings:
tve demo --texts mydocs.jsonl --name my_corpus --num-topics 8 --passes 15
```

The first run fits a Gensim LDA with the full
`text_cleaner_batch` + Phraser bigram pipeline and caches the result in
`~/.cache/topicvisexplorer/<name>-<content-hash>.npz`; subsequent runs
reuse the cache (instant). The browser is opened at
`/singlecorpus?scenario=<name>&hitl=true` so split / merge / add-word /
remove-word all work out of the box.

That opens `http://127.0.0.1:8000/singlecorpus` in your
browser (default `?scenario=20ng_tiny`). You should see:

- A **topic-map scatter** on the left (2-D PCoA of topic-topic distances).
- A **bar chart** on the right of the top terms for the hovered topic.
- A **documents table** below, with a `×` button per row for the
  [exclude-document](edit-ops.md#exclude-a-document) workflow.
- A small **Σ** toggle in the top-right that opens the
  [coherence panel](coherence.md).

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

## 4. Adapters for common pipelines

If you trained a model with gensim, scikit-learn, BERTopic, ETM, or CTM,
skip `prepare()` and use the matching adapter. See the
[Tutorial](tutorial.md) for a full walkthrough and
[Extending](extending.md) for the adapter protocol.

## 5. Next

- [Tutorial](tutorial.md) — 5-minute bring-your-own-corpus walkthrough.
- [Edit operations](edit-ops.md) — interactive topic refinement.
- [User study](user_study.md) — script to fit a public corpus, register
  `refit`, and open a named scenario for a lab session.
- [API reference](reference/index.md) — all public functions.
