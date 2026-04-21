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

```python
from topicvisexplorer import operations

new_prepared = operations.split(
    prepared,
    topic_id=1,         # 1-indexed topic number
    k_new=3,            # split into three sub-topics
    model_data=md,
    raw_texts=raw_texts,      # required for sub-topic refit
)
```

The hot path is vectorized (~10-20× the legacy Python loops) so
splitting a 500-document corpus is sub-second.

## Merge

```python
new_prepared = operations.merge(
    prepared,
    topic_a=1,
    topic_b=4,          # both 1-indexed
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
