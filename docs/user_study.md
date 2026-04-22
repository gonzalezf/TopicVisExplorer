# User study on public text (full HITL)

This guide is for **study hosts** who need a browser session with real
documents, a fitted topic model, and interactive **split / merge / word /
exclude** paths — without shipping private paper-era pickles in the public
library.

## Default demo vs. study

| Path | `Scenario` | Purpose |
|------|------------|--------|
| `tve demo` / `?scenario=20ng_tiny` | Pre-baked small **20 Newsgroups** slice (real terms) | Real keywords for the first screen; [README (datasets + licenses)](https://github.com/gonzalezf/TopicVisExplorer/blob/main/README.md#datasets-and-licenses) |
| `tve demo --corpus bbc_tiny` | Pre-baked **BBC news** slice (5 categories, real terms) | Second, news-domain demo for reviewers / study pilots |
| `tve demo --texts my.jsonl --name x --num-topics K` | Your own corpus, fit on the fly | Bring-your-own path; cache in `~/.cache/topicvisexplorer` |
| `?scenario=tiny_demo` | Synthetic `w00` / "synthetic document" | Fast CI, golden tests, exact Playwright baselines |
| `scripts/user_study/launch_20ng_study.py` | Live sklearn or HF + gensim, custom `?scenario=` | IRB: cite seed, `n_docs`, and corpus ID |

`tiny_demo` is **synthetic** by design. The paper’s **private** preprocessed
corpora and full-scale pickles are **not** in this public repo; see
[`PAPER_REPRO.md` on the repository](https://github.com/gonzalezf/TopicVisExplorer/blob/main/PAPER_REPRO.md).

## 20 Newsgroups: license and reproducibility

- **Source:** we use a subset of
  [The 20 Newsgroups data set](https://scikit-learn.org/0.20/datasets/twenty_newsgroups.html)
  via `sklearn.datasets.fetch_20newsgroups` (also documented on the
  [original host](https://kdd.ics.uci.edu/databases/20newsgroups/)).
- **In-repo fixture:** `20ng_tiny` is a **fixed** subsample: seed `42`,
  60 training documents, three categories, headers/footers/quotes removed
  — see `src/topicvisexplorer/server/fixtures/` and
  `scripts/build_20ng_tiny_fixtures.py`.
- **For IRB / reviewers:** name the public datasource, the exact script,
  random seed, number of documents, and preprocessing (e.g. removed
  headers). Do not claim the fixture is the same dump as the historical
  paper private backup.

## BBC news fixture: source and reproducibility

- **Primary source:** D. Greene and P. Cunningham's
  [BBC news corpus](http://mlg.ucd.ie/datasets/bbc.html) from the UCD
  Machine Learning Group (5 categories: `business`, `entertainment`,
  `politics`, `sport`, `tech`; ~2225 documents). Licensed for research
  use; cite Greene & Cunningham (ICML 2006).
- **Fallback:** if `mlg.ucd.ie` is unreachable, the builder uses the
  [Hugging Face `SetFit/bbc-news`](https://huggingface.co/datasets/SetFit/bbc-news)
  mirror of the same labels.
- **Build recipe:** `python scripts/build_bbc_tiny_fixtures.py` —
  downloads the zip into `~/.cache/topicvisexplorer/`, runs the full
  `text_cleaner_batch` + Gensim Phraser + LDA pipeline, writes
  `bbc_tiny.npz` / `bbc_tiny_vocab.npy` / `bbc_tiny_texts.json` under
  `src/topicvisexplorer/server/fixtures/`.

## Bring your own corpus (no code)

```bash
tve demo --texts docs.jsonl --name my_study --num-topics 7 --passes 15
```

Accepted inputs:

- **`.jsonl` / `.ndjson`** — one JSON object per line, each with a
  `"text"` field.
- **`.json`** — a list of strings, or an object with a `"texts"` array.
- **Anything else** — one document per non-empty line.

The first run fits a Gensim LDA with `text_cleaner_batch` (spaCy +
NLTK stopwords + lemmatization) and Phraser bigrams, then caches the
tensors in `~/.cache/topicvisexplorer/<name>-<hash>.npz`. Repeated
launches with the same file and parameters are instant. The resulting
scenario has a fully working `refit`, so split / merge / add-word /
remove-word all behave like the bundled demos.

## Optional: AG News on Hugging Face

The launcher supports `--source hf_ag_news` using `datasets.load_dataset("ag_news")`
after `pip install "topicvisexplorer[hf]"` (or `pip install datasets`).

A future **one-liner** `HFDatasetsLoader` is a [v1.1 roadmap item](roadmap.md);
until then, this script and your own `load_dataset` + adapter pipeline
are the supported path.

## Split in the browser

Server-side **topic split** needs `Scenario.extras["refit"]`. The public
default registers :func:`topicvisexplorer.operations.refit_helpers.refit_gensim_lda`
on `20ng_tiny` and in the user-study script. The Python API
:func:`topicvisexplorer.operations.split` supports the same `refit`
without the web server; see [edit-ops](edit-ops.md).
