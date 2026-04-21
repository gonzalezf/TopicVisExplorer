# Tutorial: from a raw corpus to an interactive topic map

This walkthrough uses the bundled `tiny_demo` fixture so it runs
end-to-end without any downloads. The same pattern applies to a real
corpus — just swap in your tokenized texts and model.

## 1. Prepare a tokenized corpus

`tve.prepare()` takes five NumPy arrays — no preprocessing opinions
baked in. If you already have a tokenizer pipeline, keep it. For a
minimal illustration:

```python
import numpy as np

raw_texts = [
    "the quick brown fox jumps over the lazy dog",
    "a fox and a dog are friends",
    "the cat sat on the mat",
    "my cat loves my dog",
]

tokenized = [t.lower().split() for t in raw_texts]
vocab = sorted({w for doc in tokenized for w in doc})
v2i = {w: i for i, w in enumerate(vocab)}

doc_lengths = np.array([len(doc) for doc in tokenized])
term_frequency = np.zeros(len(vocab), dtype=float)
for doc in tokenized:
    for w in doc:
        term_frequency[v2i[w]] += 1
```

## 2. Fit a topic model

Any model that produces a topic-term distribution and doc-topic
distribution works. Here's gensim LDA through the bundled adapter:

```python
from gensim.corpora import Dictionary
from gensim.models import LdaModel
from topicvisexplorer.models import GensimLDAAdapter

dictionary = Dictionary(tokenized)
corpus = [dictionary.doc2bow(doc) for doc in tokenized]

lda = LdaModel(corpus=corpus, id2word=dictionary, num_topics=2,
               random_state=0, passes=20)

adapter = GensimLDAAdapter()
model_data = adapter.extract(lda, corpus=corpus, dictionary=dictionary)
```

`model_data` is a `TopicModelData` — the universal shape TopicVisExplorer
consumes. See [Extending](extending.md) for the exact contract and how
to write your own adapter.

## 3. Call `prepare()`

```python
import topicvisexplorer as tve

prepared = tve.prepare(
    topic_term_dists=model_data.topic_term_dists,
    doc_topic_dists=model_data.doc_topic_dists,
    doc_lengths=model_data.doc_lengths,
    vocab=model_data.vocab,
    term_frequency=model_data.term_frequency,
)
```

`prepared` is a `PreparedData` dataclass — the same shape pyLDAvis uses,
plus a few extra columns used by the edit operations. See
[`reference/prepare.md`](reference/prepare.md).

## 4. Launch the visualization

```python
tve.show(prepared)
```

This spawns a FastAPI server on `127.0.0.1:8000` and opens a browser
tab. The page stays interactive until you `Ctrl+C` the process. If you
want a static HTML snapshot instead:

```python
tve.save_html(prepared, "topics.html")
```

## 5. Compare two corpora side-by-side

For the Sankey "topic flow" comparison (paper Section 5):

```python
prepared_2024 = tve.prepare(...)   # fit on 2024 docs
prepared_2025 = tve.prepare(...)   # fit on 2025 docs
tve.show([prepared_2024, prepared_2025])
```

The Sankey diagram links topics between the two corpora by topic-term
cosine similarity, with hover-to-highlight and click-to-freeze.

## 6. Refine topics interactively

Every control in the UI has a matching typed function on
`topicvisexplorer.operations`. See the
[edit-operations cookbook](edit-ops.md) for examples of:

- **split** a topic into sub-topics
- **merge** two topics
- **add / remove a word** from a topic's representation
- **exclude a document** from a topic's contribution

All four return a fresh `PreparedData` so you can drive them from a
notebook without touching the UI.

## Next

- [Edit operations](edit-ops.md)
- [Coherence metrics](coherence.md)
- [Extending](extending.md) — wire in a new model or embedding backend.
