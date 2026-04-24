# Custom corpus: CSV or Hugging Face → JSONL → `tve demo`

This guide is for **tabular CSV** or **Hugging Face `datasets`** users who want the default **bring-your-own (BYO)** path: fit a topic model and open the **single-corpus** browser UI with `tve demo --texts`.

!!! info "Prerequisites"
    [Install, test, BYO — **Git clone** (uv / venv, `tve`, Node + `npm run build` for the UI from a checkout)](installation-and-testing.md#git-clone)

## What you get (and what is out of scope)

**This library supports:**

- **Install** with **`pip install topicvisexplorer`** (or a git clone; see the prerequisites link).
- **Your own documents** on disk, after you **convert** them to a supported file shape, usually **JSONL** with one `{"text": "..."}` per line.
- The **default BYO** topic model: **Gensim LDA** (same as passing `--model gensim-lda`, which is the **CLI default** for `tve demo --texts`). This is the closest “paper-style” default stack bundled with the app (plus shared preprocessing; see [Working with your own data](own_data.md)).
- A **fully interactive** single-corpus view: **split, merge, add/remove words**, coherence, export — **as long** as you use `tve demo --texts` to open **`/singlecorpus`**. Multi-corpus **compare / Sankey** is **not** on this path; see *Multi-corpus* below.

**Not available as a one-line CLI today:**

- **`tve demo --multicorpora` and `--texts` together** — the CLI rejects that combination. Multi-corpus UIs are **bundled scenario names** (e.g. `tiny_multi_demo`) only, not two arbitrary local corpora. Comparing two custom corpora like the full paper “compare” story needs the **Python API** or future work; see [Extending](extending.md) and [Roadmap](roadmap.md).

## Track A: Tabular CSV → `corpus.jsonl`

**Problem:** a real table CSV (header + rows, text in one column) is **not** auto-parsed. If you point `tve demo --texts` at a `*.csv` file, the loader treats the file as **plain text, one line = one document** (see [own_data](own_data.md)) — with **no** header or column pick. That is wrong for a multi-column table.

**Recipe:** read the file in Python, pick a **text column** (e.g. `text` or `body`), drop nulls, write **one JSON object per line**, UTF-8.

=== "pandas"

    ```python
    import json
    from pathlib import Path

    import pandas as pd

    df = pd.read_csv("my_corpus.csv")
    col = "text"  # change to your column name
    out = Path("corpus.jsonl")
    with out.open("w", encoding="utf-8") as f:
        for t in df[col].dropna().astype(str):
            if t.strip():
                f.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
    ```

=== "stdlib only (`csv` module)"

    ```python
    import csv
    import json
    from pathlib import Path

    text_col = "text"  # must match the header
    with Path("my_corpus.csv").open(newline="", encoding="utf-8") as fin, Path(
        "corpus.jsonl"
    ).open("w", encoding="utf-8") as fout:
        r = csv.DictReader(fin)
        for row in r:
            t = (row.get(text_col) or "").strip()
            if t:
                fout.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
    ```

## Track B: Hugging Face → the same `corpus.jsonl`

There is **no** `tve demo --hf <dataset>` flag. The practical path is: **`datasets.load_dataset` in a small script** → local JSONL (or JSON list) → `tve demo --texts`.

```bash
pip install "topicvisexplorer[hf]"  # or: pip install datasets
```

```python
import json
from pathlib import Path

from datasets import load_dataset

# Example: a small public set (first run may download; needs network)
ds = load_dataset("ag_news", split="train")
text_col = "text"
out = Path("corpus.jsonl")
# Optional: .select(range(5000)) to limit size during experiments
with out.open("w", encoding="utf-8") as f:
    for row in ds:
        t = str(row[text_col]).strip()
        if t:
            f.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
```

For a larger scripted workflow used in user studies, see
[`scripts/user_study/launch_20ng_study.py`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/scripts/user_study/launch_20ng_study.py). A first-class in-library HF loader is on the [Roadmap](roadmap.md) (v1.1+).

## Run the app (shared path)

**Default (paper-style Gensim LDA, single-corpus UI):** from a **git clone** at the repo root:

```bash
uv run tve demo --texts examples/byo_minimal.jsonl --name my_run --model gensim-lda --no-browser
```

From **PyPI**, the same file is included in the wheel as **`examples/byo_minimal.jsonl`** under your environment’s `site-packages`. You can also copy it from
[GitHub (raw `byo_minimal.jsonl`)](https://github.com/gonzalezf/TopicVisExplorer/blob/main/examples/byo_minimal.jsonl).

**Your converted file:**

```bash
tve demo --texts corpus.jsonl --name my_run --model gensim-lda
```

- Omit `--no-browser` to open a tab; use `--port 8765` (or any free port) if `8000` is busy.
- **Split/merge in the browser** (after a non–gensim-lda initial fit) can behave differently: the server still wires **Gensim LDA**-style refit for some operations. Read the warning in [own_data: split/merge and refit](own_data.md#bring-your-own-corpus-cli) before relying on it with other `--model` values.

**Expected output (success criteria):**

- The process logs that Uvicorn is **listening** (e.g. `http://127.0.0.1:8000` by default) and, unless `--no-browser` is set, a line about **opening** the app in a browser.
- Hitting the single-corpus page works: open `http://127.0.0.1:8000/singlecorpus?scenario=<your --name>&hitl=true` (or follow the link the CLI printed).

**Sanity check from tests (optional):** `uv run pytest tests/unit/test_byo_corpus.py -q` should report all tests passed (exercises the same JSONL path used by the loader).

## Export, cache, and privacy

- **Export:** use the in-browser **Export** control to download a JSON snapshot of topic labels and terms **to your machine**; nothing is uploaded to a remote service. See [own_data: Export](own_data.md#export-your-curated-topics-json).
- **Cache:** the fitted model and embeddings are under **`~/.cache/topicvisexplorer/`** (name includes scenario, model, and a content hash). Delete files there to force a refit with the same inputs.

**Developer / code:** the BYO file loader is
[`load_texts`](https://github.com/gonzalezf/TopicVisExplorer/blob/main/src/topicvisexplorer/server/byo_corpus.py)
in `topicvisexplorer.server.byo_corpus` (import from your environment if you extend the app). The high-level **prepare/operations** API is in the [API reference](reference/index.md).

## Multi-corpus (compare UI) vs BYO

| Goal | Command / note |
| ---- | --------------- |
| **Your** JSONL, **single** corpus UI | `tve demo --texts corpus.jsonl --name my_run` (this page) |
| **Two bundled corpora** in the Sankey / multi UI | e.g. `tve demo --multicorpora --corpus tiny_multi_demo` **without** `--texts` |
| **Two arbitrary custom corpora** in the same compare view | **Not** supported via `tve demo` today — Python API / custom wiring; do **not** assume two `--texts` runs can be combined in the multi UI. |

## Reproducibility and case-study checklists

For **comparable** study runs, fix **inputs and flags** up front and reuse the same **`corpus.jsonl`** (or a checksum-pinned file):

- **`--num-topics`**, **`--passes`**, **`--model`**, **`--embedding`**, **`--seed`**, and **`--name`** (or URL `scenario=`) as applicable.
- **Cache:** same file bytes + same flags → same **cache key** under `~/.cache/topicvisexplorer/`. If you change **any** of those, expect a new fit or cache entry.

**Cohort with Hugging Face:** everyone runs the same **export script and split** and writes a shared filename (e.g. `corpus.jsonl`).

**Manual cohort:** distribute `corpus.jsonl` (or a generation script) and a single **invocation line** for `tve demo --texts …`.

## See also

- [Quickstart](quickstart.md) — shortest path to a running browser session with a bundled demo; links here for “my file first.”
- [Tutorial: API `prepare()`](tutorial.md) — **code-first** pipeline for tokenization and `PreparedData` (contrast: **this page** = **file + CLI first**).
- [Working with your own data](own_data.md) — full **flag table** and format rules.
- [Install, test, BYO](installation-and-testing.md#git-clone) — clone, tests, and troubleshooting.
