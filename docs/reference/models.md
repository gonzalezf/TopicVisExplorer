# `topicvisexplorer.models`

Topic-model adapters. See [Extending](../extending.md) for the adapter
protocol.

**Registry (CLI / BYO):** short names map to the classes below. Use
`--model <id>` with `tve demo --texts ...` or `byo_model=` with
`tve.show(..., texts_file=...)`.

| CLI / API id     | Class                 | Extra / notes        |
| ---------------- | --------------------- | -------------------- |
| `gensim-lda`     | `GensimLDAAdapter`    | core (default)       |
| `sklearn-lda`    | `SklearnLDAAdapter`   | core                 |
| `sklearn-nmf`    | `SklearnNMFAdapter`   | core                 |
| `bertopic`       | `BERTopicAdapter`     | `[full]`             |
| `etm`            | `ETMAdapter`          | `[full]`             |
| `ctm`            | `CTMAdapter`          | `[full]`             |

Embeddings for the layout similarity (BYO only): `--embedding word2vec`
(default, trains Gensim Word2Vec) or `--embedding sbert` (requires
`[full]`, uses `sentence-transformers`).

## Protocol

::: topicvisexplorer.models.protocol.TopicModelData

::: topicvisexplorer.models.protocol.TopicModelAdapter

## Bundled adapters

::: topicvisexplorer.models.GensimLDAAdapter

::: topicvisexplorer.models.SklearnLDAAdapter

::: topicvisexplorer.models.SklearnNMFAdapter

::: topicvisexplorer.models.BERTopicAdapter

::: topicvisexplorer.models.ETMAdapter

::: topicvisexplorer.models.CTMAdapter
