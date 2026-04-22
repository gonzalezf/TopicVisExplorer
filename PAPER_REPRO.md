# Reproducing the paper's figures

This document explains how to reproduce the figures in the Journal of
Visualization paper on TopicVisExplorer using the v1.0 library.

## What ships in the public repo

The public [`TopicVisExplorer`](https://github.com/gonzalezf/TopicVisExplorer)
includes:

* **Two real-terms demos** — `20ng_tiny` (20 Newsgroups subset) and
  `bbc_tiny` (UCD BBC news subset); both are committed as
  ``.npz``/JSON under `src/topicvisexplorer/server/fixtures/` and can
  be regenerated via ``scripts/build_20ng_tiny_fixtures.py`` and
  ``scripts/build_bbc_tiny_fixtures.py``. See the README for licences.
* **Bring-your-own corpus** — `tve demo --texts <file>` fits Gensim
  LDA with the same preprocessing pipeline and caches results in
  `~/.cache/topicvisexplorer/`; nothing is committed.
* **Synthetic fixtures** — `tiny_demo` and `tiny_multi_demo` stay for fast
  CI, golden baselines, and Playwright/frontend tests (``w00``-style tokens).

The paper’s **private** preprocessed corpora, full-scale dumps, and
original pickle snapshots — 20ng at the paper’s full scale, NIPS
abstracts, the author’s research-paper collection — are **not** the same
as the small public 20ng subset. Those paper-era assets were **not**
redistributed in the public library; a user study on real text can use
`20ng_tiny`, a local refit of 20ng (see
[`docs/user_study.md`](docs/user_study.md)), or your own public corpus, while
numerical equivalence with the v1.0 code paths remains covered by
`golden_baseline/` + unit tests.

## What lives in the private backup

The original paper pickles and preprocessed corpora live in the
private-backup repository that this public library was extracted from.
If you are a collaborator with access to that backup, follow the
private README for the exact filenames; the v1.0 API consumes those
pickles directly via `GensimLDAAdapter` (see below).

## End-to-end paper-rebuild recipe

Assuming you have the private-backup pickles at
`~/paper_data/{model,corpus,dictionary}.pkl`:

```python
import pickle
import topicvisexplorer as tve
from topicvisexplorer.models import GensimLDAAdapter

with open("~/paper_data/model.pkl", "rb") as f:
    model = pickle.load(f)
with open("~/paper_data/corpus.pkl", "rb") as f:
    corpus = pickle.load(f)
with open("~/paper_data/dictionary.pkl", "rb") as f:
    dictionary = pickle.load(f)

md = GensimLDAAdapter().extract(model, corpus=corpus, dictionary=dictionary)

prepared = tve.prepare(
    topic_term_dists=md.topic_term_dists,
    doc_topic_dists=md.doc_topic_dists,
    doc_lengths=md.doc_lengths,
    vocab=md.vocab,
    term_frequency=md.term_frequency,
)
tve.show(prepared)                       # Figure 2 / 3 layout
```

### Golden numerical equivalence

The paper's exact numerical outputs for `prepare()`, similarity,
split, merge, and the four edit operations are pinned in
`golden_baseline/*.json` with `atol=1e-9`. Running
`pytest tests/golden/` on the v1.0 library verifies the math is
byte-equivalent to the paper within that tolerance.

### Visual equivalence

`frontend/tests/visual.spec.ts` holds Playwright pixel baselines for
the single-corpus and multi-corpus views. A `maxDiffPixelRatio: 0.05`
tolerance absorbs the Sankey layout's inherent non-determinism; every
other panel matches byte-for-byte.

## Why the pickles are not public

The original paper pickles contain preprocessed text that may include
user-generated content the author does not have redistribution rights
for (the research-paper corpus in particular). Shipping only the
synthetic fixtures in the public repo avoids any licensing ambiguity;
the mathematical equivalence is established by the golden-test suite.

## Questions

File an issue at
[github.com/gonzalezf/TopicVisExplorer/issues](https://github.com/gonzalezf/TopicVisExplorer/issues).
