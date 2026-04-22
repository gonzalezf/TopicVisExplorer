# Edit operations cookbook

The four interactive refinement actions in the UI are also a
programmatic API. Each one takes a `PreparedData` plus a
`TopicModelData` and returns a fresh `PreparedData` with the same shape,
so you can chain them in a notebook.

| Operation | UI trigger | Python | Paper ref |
|-----------|-----------|--------|-----------|
| Split | Toolbar "Split" button | `operations.split()` | §4.2 |
| Merge | Toolbar "Merge" button | `operations.merge()` | §4.2 |
| Add word | `+` next to a bar-chart term | `operations.add_word()` | §6 (future work, now shipped) |
| Remove word | `−` next to a bar-chart term | `operations.remove_word()` | §6 (future work, now shipped) |
| Exclude document | `×` in the documents table | `operations.exclude_document()` | §6 (future work, now shipped) |

All five return a new `PreparedData`; the original is not mutated.

## Split

`split` also needs a **`refit(sub_texts, k_new) -> TopicModelData`**
call that re-fits on the member documents (e.g. gensim LDA; see
`topicvisexplorer.operations.refit_helpers.refit_gensim_lda`).

```python
from topicvisexplorer import operations
from topicvisexplorer.operations import refit_gensim_lda

refit = refit_gensim_lda(md)  # parent TopicModelData; reuses `md.vocab`

new_prepared = operations.split(
    prepared,
    topic_id=1,         # 1-indexed topic number
    k_new=3,            # split into three sub-topics
    model_data=md,
    raw_texts=raw_texts,
    refit=refit,        # required
)
```

In the **web app**, the same `refit` must appear on
`Scenario.extras["refit"]`; the bundled `20ng_tiny` and `bbc_tiny`
scenarios wire a real `refit_gensim_lda`, and `tiny_demo` now also
ships a lightweight NumPy-only `refit_static` so Split and Merge work
on every bundled demo out of the box. Scenarios created via
`tve demo --texts ...` inherit the same Gensim-backed refit.

The hot path is vectorized (~10-20× the legacy Python loops) so
splitting a 500-document corpus is sub-second.

## Merge

```python
new_prepared = operations.merge(
    prepared,
    topic_id_a=1,
    topic_id_b=4,       # both 1-indexed
    model_data=md,
)
```

## Add / remove a word

```python
new_prepared = operations.add_word(
    prepared,
    topic_id=2,
    word="bioluminescent",
    model_data=md,
    boost_to_quantile=0.9,   # default: raise to the 90th-percentile freq
)

new_prepared = operations.remove_word(
    prepared,
    topic_id=2,
    word="the",
    model_data=md,
)
```

Both operations renormalize the topic-term row and recompute
`topic_info` (`Freq`, `Total`, `logprob`, `loglift`). The rest of the
visualization is untouched, so the bar chart redraws instantly with no
scatter repaint.

### Per-term `+` / `−` controls in the UI

Hovering a term in the "Most relevant terms for topic N" bar chart
reveals a small `+` (add) and `−` (remove) pair on its right edge.
These are the UI entry points for `operations.add_word` and
`operations.remove_word`; they only appear when the page is loaded
with `?hitl=true` (the default for `tve demo`). The controls edit the
currently pinned topic's top-term bar chart only — they renormalize
the topic-term row, but **do not** change the document-topic matrix or
the scatter positions, so repeated clicks are cheap and undoable from
the toolbar "Undo" button. Hover any term to try them; the SVG
`<title>` tooltip names the exact topic being edited.

## Exclude a document

```python
new_prepared = operations.exclude_document(
    prepared,
    topic_id=2,
    doc_id=47,          # stable integer from relevant_documents
    model_data=md,
)
```

`doc_id` is the integer index into the loader's `relevant_documents`
table — see the [`doc_id` contract](extending.md#31-doc_id-is-a-stable-per-row-identifier).
The row for `doc_id=47` has its `topic_id=2` mass zeroed and is
re-normalized to sum to 1 over the remaining topics.

## Golden-test discipline

Every one of these operations is pinned by a byte-level numerical
regression test in `tests/golden/test_edit_ops_golden.py` with
`atol=1e-9`. If you change any of the math, regenerate the baseline
with `scripts/capture_edit_op_golden.py` and commit both files in the
same PR.
