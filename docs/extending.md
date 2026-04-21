# Extending TopicVisExplorer

This guide covers the three extension surfaces TopicVisExplorer
deliberately exposes for v1.0:

1. **Topic models** — adding support for a new topic model beyond the
   bundled gensim LDA, sklearn LDA, sklearn NMF, BERTopic, ETM, and
   CTM adapters.
2. **Embeddings** — swapping the default Word2Vec embedding backend
   for SBERT, FastText, or a custom vector store.
3. **Custom loaders** — bringing your own corpus into the modern
   FastAPI server with the contracts the new edit operations expect.

The first three of those (BERTopic, ETM, CTM) and all four of the new
edit operations (split, merge, add/remove word, exclude document) are
**direct deliveries of paper Section 6 future work**. Each subsection
below opens with the corresponding paper paragraph so you can see how
v1.0 connects back to the published roadmap.

---

## 1. Adding a new topic model adapter

> Paper Section 6: *"future work includes adding support for newer
> neural topic models such as ETM (Dieng et al., 2020) and CTM
> (Bianchi et al., 2021), and the now-popular BERTopic
> (Grootendorst, 2022)."*

All three of these models ship in v1.0
(`topicvisexplorer.models.{BERTopicAdapter, ETMAdapter, CTMAdapter}`)
and each one is a working reference implementation of the
`TopicModelAdapter` protocol. Use one of them as a template when
adding a new adapter.

### The contract

```python
from typing import Any, Protocol
from topicvisexplorer.models.protocol import TopicModelData

class TopicModelAdapter(Protocol):
    name: str

    def extract(self, model: Any, corpus: Any, **kwargs: Any) -> TopicModelData:
        ...
```

`extract` must return a `TopicModelData` carrying:

| Field              | Shape         | Constraint                                                     |
| ------------------ | ------------- | -------------------------------------------------------------- |
| `topic_term_dists` | `(K, V)`      | Each row sums to 1.0 (row-stochastic)                          |
| `doc_topic_dists`  | `(N, K)`      | Each row sums to 1.0                                           |
| `vocab`            | `list[str]`, length `V` | One string per term column                          |
| `term_frequency`   | `(V,)`        | Non-negative; corpus-level term counts                         |
| `doc_lengths`      | `(N,)`        | Non-negative; `sum() == term_frequency.sum()` (re-vectorizable) |

That's it. If your model can produce those five arrays, the rest of
the pipeline (`prepare`, similarity, edit operations, the new
collapsible coherence panel) Just Works.

### Where to put it

```
src/topicvisexplorer/models/adapters/<your_model>.py    # the adapter
src/topicvisexplorer/models/__init__.py                  # add to __all__
tests/unit/test_adapters.py                              # add a fake-shaped test class
tests/unit/test_adapter_equivalence.py                   # opt-in cross-LDA equivalence
```

### Why the adapter pattern matters

The legacy code (paper version) hard-coded gensim LDA throughout. To
support a new model the user had to reach into `gensim_helpers.py`
and patch type checks. With the adapter protocol you write one file,
register it in `__all__`, and:

* the FastAPI server picks it up automatically through the loader
  registry;
* `tests/unit/test_adapter_equivalence.py` will (if you add your
  adapter to its corpus fixture) verify your adapter feeds cleanly
  through `prepare()` exactly the way the LDA adapters do.

---

## 2. Embedding backends

> Paper Section 6: *"the embedding-based topic similarity matrix
> currently uses Word2Vec; we plan to evaluate SBERT and FastText."*

The default embedding remains Word2Vec (paper-faithful), but the
`topicvisexplorer.similarity.embedding` module now talks to the
abstract `EmbeddingProtocol`:

```python
class EmbeddingProtocol(Protocol):
    def __getitem__(self, term: str) -> np.ndarray: ...
    def __contains__(self, term: str) -> bool: ...
```

Anything quacking like a gensim `KeyedVectors` (the Word2Vec default,
SBERT via `topicvisexplorer.embeddings.SBERTEmbedding`, your own
in-memory `dict[str, np.ndarray]`) plugs in directly. SBERT is in the
`[full]` extra so it doesn't bloat the default install; install via:

```bash
pip install "topicvisexplorer[full]"
```

then:

```python
from topicvisexplorer.embeddings import SBERTEmbedding
emb = SBERTEmbedding(model_name="all-MiniLM-L6-v2")
```

---

## 3. Custom loaders + the edit-operation contract

> Paper Section 6: *"future work includes letting users add or remove
> words from a topic, exclude individual documents from a topic, and
> show topic-quality metrics (NPMI, C_v) and topic-distinctness
> indicators alongside the visualization."*

All four of those features are in v1.0. The two **edit operations**
(add/remove word, exclude document) impose two new contracts on
custom loaders:

### 3.1 `doc_id` is a stable per-row identifier

The exclude-document UI (Phase 4e) sends `{topic_id, doc_id}` to
`POST /Exclude_Document`. The `doc_id` is the **integer index into
the loader's `relevant_documents` table**, and it must stay stable
across reorderings (paginations, sorts, splits, merges). The bundled
demo loaders in `topicvisexplorer.server.demo_data` add `"doc_id": i`
to every row of `relevant_documents`; replicate that in any custom
loader:

```python
relevant_documents = [
    {"doc_id": i, "topic_id": 1, "text": "...", "topic_perc_contrib": 0.42}
    for i, doc in enumerate(my_corpus)
]
```

If you forget this, the per-row `×` button still renders but clicking
it returns 422 from the API.

### 3.2 `raw_texts` is required for the coherence panel

The new `GET /coherence` endpoint (Phase 4f, backing the collapsible
NPMI / C_v / segregation / coverage panel) computes intrinsic
coherence from corpus co-occurrence and therefore needs
`Scenario.raw_texts: list[str]`. If your loader doesn't provide this,
the endpoint returns 404 with an actionable error and the panel
shows "Coherence unavailable for this scenario."

For multi-corpus mode the panel is hidden in the UI entirely (the
`{% if type_vis == 1 %}` Jinja guard), so multi-corpus loaders don't
need `raw_texts` for v1.0. (Multi-corpus coherence is on the v1.1
roadmap.)

### 3.3 The `add_word` / `remove_word` contract is purely on `vocab`

Word edits operate on `model_data.vocab`. As long as your loader
populated `topicvisexplorer.models.protocol.TopicModelData` correctly
(see §1 above), the buttons work end-to-end with no per-loader code.

---

## See also

* `golden_baseline/README.md` — golden-test discipline for staying
  numerically equivalent to the paper.
* `CONTRIBUTING.md` — development workflow, branch strategy
  (`master`/`legacy`/`next`), and the rule that any change to
  golden output must regenerate the baselines via the
  `scripts/capture_*` helpers.
* The reference adapters in `src/topicvisexplorer/models/adapters/`
  for working examples that satisfy the protocol.
