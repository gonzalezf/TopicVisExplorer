# Roadmap

This file tracks work that has been **consciously deferred** past v1.0.0. It is
complementary to the [CHANGELOG](https://github.com/gonzalezf/TopicVisExplorer/blob/main/CHANGELOG.md)
(what shipped) and to GitHub Issues (open bug reports). Items land on the
roadmap when they are in scope for the project but require real effort to do
well and weren't in the v1.0 critical path.

## v1.1 (planned)

### PyPI release pipeline

**Why deferred:** v1.0.0 was extracted into a fresh public repository and the
author wants a burn-in period ("won't do PyPI release until we test it a
lot") before publishing installable wheels. v1.0.0 is installable from the
git URL; PyPI wheels come next.

Scope:

- `release.yml` GitHub Actions workflow that builds + signs wheels and sdist
  on a `v*` tag, publishes to TestPyPI first, and on manual approval
  publishes to PyPI.
- `MANIFEST.in` audit for correctly shipping the Vite bundle and the demo
  fixtures.
- A dry-run release to TestPyPI from `v1.0.1` or `v1.1.0-rc1`, then a real
  publish.
- Trusted-publishing configuration on PyPI (no long-lived API tokens).

### Multi-corpus coherence panel

Today the `Σ` panel is single-corpus only (`type_vis == 1` Jinja guard); the
Sankey view hides it. A v1.1 version should show per-corpus coherence and
highlight topics that diverge sharply in NPMI/C_v between corpora.

Scope:

- Compute `CoherenceReport` for each `PreparedData` in the multi-corpus
  session.
- Show a two-column NPMI / C_v table with per-topic deltas.
- Drive the `GET /coherence` endpoint to accept `?corpus=a|b` in
  multi-corpus mode.

### SBERT and FastText as first-class embedding backends

Today `SBERTEmbedding` lives in the `[full]` extra and FastText requires
users to hand-construct a `KeyedVectors`. v1.1 should:

- Ship `FastTextEmbedding` under `topicvisexplorer.embeddings` with lazy
  model download + a `cache_dir` knob.
- Promote SBERT to a first-class loader registered by name so the CLI
  can do `tve demo --embedding sbert:all-MiniLM-L6-v2`.
- Benchmark SBERT vs. Word2Vec topic-similarity quality on the three
  paper corpora and document the findings in a new
  `docs/embeddings-comparison.md`.

### HuggingFace `datasets` loader

A `topicvisexplorer.loaders.HFDatasetsLoader` that consumes `datasets.Dataset`
directly — tokenize on the fly, fit a bundled adapter, and serve a scenario.
Would eliminate the most common "I have texts, now what?" friction.

### Paper-figures Playwright profile

A dedicated `tests/visual/paper_figures/` profile that renders the three
paper corpora end-to-end and pins them against screenshots of the
published paper. Useful for reviewers; gated by the presence of the
private-backup pickles so it can't run on the public CI but can be
spot-checked locally.

## Nice-to-have / unscheduled

- **`tve.show_inline()`** — embed the visualization in a Jupyter notebook
  without spawning a separate server (pyLDAvis-style `show_in_notebook`).
- **PDF / SVG static export** of the current view (useful for paper figures).
- **Bring-your-own-tokenizer** hook so users can plug in a spaCy or
  HuggingFace tokenizer without pre-tokenizing at the loader level.
- **Topic relabeling UI** — let users rename a topic from the default
  `Topic N` to a human-readable label, persisted in the session.

## Want to work on something?

Pick an item, open an issue first to discuss scope/approach, then send a PR.
Check [`docs/extending.md`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/docs/extending.md)
for the adapter / embedding contracts before implementing a new model or
backend.
