# TopicVisExplorer

[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://gonzalezf.github.io/TopicVisExplorer/)
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

## Demo

```bash
tve demo                              # opens a browser tab on 127.0.0.1:8000
```

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

## Documentation

Full docs: **<https://gonzalezf.github.io/TopicVisExplorer/>**

- [Quickstart](docs/quickstart.md)
- [Tutorial](docs/tutorial.md)
- [Edit operations](docs/edit-ops.md)
- [Coherence metrics](docs/coherence.md)
- [Extending](docs/extending.md)
- [Migration from v0.1](docs/migration.md)
- [Paper reproduction](PAPER_REPRO.md)

## Citation

If you use TopicVisExplorer in academic work, please cite the paper and the
software (see [`CITATION.cff`](./CITATION.cff)).

## License

BSD-3-Clause. See [`LICENSE`](./LICENSE).
