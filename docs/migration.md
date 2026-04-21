# Migration from v0.1 (paper version)

The paper-era TopicVisExplorer was a Flask app in a single repository;
v1.0 is an installable Python library with the same visual identity but
a cleaner architecture. This page is for users of the paper version who
want to port their pipeline to v1.0.

If you are starting fresh, skip this page and read the
[Quickstart](quickstart.md) instead.

## TL;DR of what changed

| Concern | Paper v0.1 | v1.0 |
|---------|-----------|------|
| Packaging | Clone + `python app.py` | `pip install topicvisexplorer` |
| Server | Flask | FastAPI + uvicorn |
| Frontend | Ad-hoc D3 v3 scripts | Vite + TypeScript + D3 v5 |
| Topic models | gensim LDA hard-coded | adapter protocol; gensim/sklearn/BERTopic/ETM/CTM bundled |
| Embeddings | Word2Vec hard-coded | `EmbeddingProtocol`; Word2Vec default, SBERT optional |
| Add/remove word | Not implemented | UI + API + golden tests |
| Exclude document | Not implemented | UI + API + golden tests |
| Coherence (NPMI, C_v, segregation, coverage) | Not implemented | Collapsible panel + `/coherence` endpoint |
| Testing | Manual | 121 pytest + 10 Playwright tests; visual baselines |
| Visual | Pixel-perfect target | **Preserved** — visual regression tests enforce it |

## What stayed the same

- The **look** of the topic map, bar chart, Sankey diagram, and
  documents table. `frontend/tests/visual.spec.ts` pins pixel-level
  baselines (with `maxDiffPixelRatio: 0.05` for inherently
  non-deterministic Sankey layouts).
- The **math**. Every output of `prepare()`, `split`, `merge`,
  similarity, and the edit operations is pinned by golden tests to the
  paper-version numerical output within `atol=1e-9`.
- The paper's URL. The paper citation now points at the new library
  URL (`github.com/gonzalezf/topicvisexplorer-lib`); the private backup
  of the original Flask tree remains at the old URL as the historical
  record.

## Mapping legacy scripts to v1.0 API

### Loading your pickled model

Paper version:

```python
# Legacy — load pickles, shuffle to DataFrame columns, feed Flask globals
model = pickle.load(open("lda.pkl", "rb"))
corpus = pickle.load(open("corpus.pkl", "rb"))
```

v1.0:

```python
import pickle
import topicvisexplorer as tve
from topicvisexplorer.models import GensimLDAAdapter

model = pickle.load(open("lda.pkl", "rb"))
corpus = pickle.load(open("corpus.pkl", "rb"))

md = GensimLDAAdapter().extract(model, corpus=corpus, dictionary=model.id2word)
prepared = tve.prepare(
    topic_term_dists=md.topic_term_dists,
    doc_topic_dists=md.doc_topic_dists,
    doc_lengths=md.doc_lengths,
    vocab=md.vocab,
    term_frequency=md.term_frequency,
)
tve.show(prepared)
```

### Launching the server

Paper version:

```bash
python app.py
```

v1.0:

```bash
tve demo                        # bundled demo
# or in Python:
python -c "import topicvisexplorer as tve; tve.show(prepared)"
```

### Split / merge endpoints

The HTTP shape is unchanged (the legacy `LDAvis.js` still makes the
same AJAX calls), so any code that talked to the old `/split` or
`/merge` endpoint continues to work against the FastAPI server without
modification.

### New endpoints (not in v0.1)

- `POST /Add_Remove_Word` — backed by `operations.add_word` /
  `remove_word`. See [Edit operations](edit-ops.md).
- `POST /Exclude_Document` — backed by `operations.exclude_document`.
- `GET /coherence` — backed by `coherence.report()`. Requires
  `Scenario.raw_texts`.

## Getting help

File an issue at
[github.com/gonzalezf/topicvisexplorer-lib/issues](https://github.com/gonzalezf/topicvisexplorer-lib/issues)
with the paper-version script you're trying to port and the error
you're hitting. Minimal reproducers are gold.
