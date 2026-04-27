#!/usr/bin/env python3
"""
Bring-your-own corpus from a **Hugging Face** dataset → JSONL → `tve.show()`.

Loads the ``ag_news`` dataset (first 500 documents of the training split),
writes a local ``corpus.jsonl``, then opens the single-corpus browser UI with
the default Gensim LDA model.

**Prerequisites:** install the ``[hf]`` extra from a git clone::

    pip install -e ".[hf]"    # or: pip install datasets

**From the repository root**::

    uv run python examples/05_huggingface_demo.py
    uv run python examples/05_huggingface_demo.py --no-browser
    uv run python examples/05_huggingface_demo.py --smoke

``--smoke`` writes ``corpus.jsonl`` and prints the row count only; it does
**not** start the server (safe for CI and quick verification).

For a different Hugging Face dataset change ``--hf-dataset`` and
``--hf-text-column``.  The default number of documents is set by
``--num-docs`` (default 500; keep ≥ 100 for meaningful LDA topics).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_EXAMPLES = Path(__file__).resolve().parent
OUT_JSONL = REPO_EXAMPLES / "ag_news_500.jsonl"


def _check_datasets() -> None:
    try:
        import datasets  # noqa: F401
    except ImportError:
        print(
            "error: 'datasets' is not installed.\n"
            "Install it with:  pip install -e \".[hf]\"  or  pip install datasets",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _write_jsonl(hf_dataset: str, text_col: str, num_docs: int, out: Path) -> int:
    from datasets import load_dataset  # type: ignore[import-untyped]

    ds = load_dataset(hf_dataset, split=f"train[:{num_docs}]")
    written = 0
    with out.open("w", encoding="utf-8") as f:
        for row in ds:
            t = str(row[text_col]).strip()
            if t:
                f.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
                written += 1
    return written


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-browser", action="store_true", help="Do not open a tab.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--hf-dataset",
        default="ag_news",
        help="Hugging Face dataset identifier (default: ag_news).",
    )
    p.add_argument(
        "--hf-text-column",
        default="text",
        help="Column name with document text (default: text).",
    )
    p.add_argument(
        "--num-docs",
        type=int,
        default=500,
        help="Number of documents to load (default: 500; keep ≥ 100 for LDA).",
    )
    p.add_argument(
        "--out",
        default=str(OUT_JSONL),
        help=f"Output JSONL path (default: {OUT_JSONL}).",
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Write JSONL and print row count only; do not start the server.",
    )
    args = p.parse_args()

    _check_datasets()

    out_path = Path(args.out)
    print(
        f"Loading {args.num_docs} docs from '{args.hf_dataset}' "
        f"(column '{args.hf_text_column}') …"
    )
    n = _write_jsonl(args.hf_dataset, args.hf_text_column, args.num_docs, out_path)
    print(f"Wrote {n} documents → {out_path}")

    if args.smoke:
        print("Smoke OK — JSONL written; server not started (--smoke).")
        return 0

    if n < 50:
        print(
            f"warning: only {n} documents — LDA topics may be noisy. "
            "Use --num-docs to load more.",
            file=sys.stderr,
        )

    import topicvisexplorer as tve

    tve.show(
        texts_file=out_path,
        byo_model="gensim-lda",
        scenario_name="hf_ag_news",
        open_browser=not args.no_browser,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
