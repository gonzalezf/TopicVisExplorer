# Quickstart

This page gets you from zero to an interactive TopicVisExplorer window in
under a minute using the bundled synthetic demo.

## 1. Install

```bash
pip install topicvisexplorer          # core + server + demo
# or, for BERTopic / ETM / CTM / SBERT:
pip install "topicvisexplorer[full]"
```

??? note "Working from a clone"
    If you are hacking on the library itself, install in editable mode and
    build the frontend bundle once:

    ```bash
    pip install -e ".[dev,docs]"
    (cd frontend && npm ci && npm run build)
    ```

## 2. Launch the demo

```bash
tve demo
```

That opens `http://127.0.0.1:8000/singlecorpus?scenario=tiny_demo` in your
browser. You should see:

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
- [API reference](reference/index.md) — all public functions.
