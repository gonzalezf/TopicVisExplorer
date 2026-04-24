#!/usr/bin/env python3
"""
Single-corpus from a table file — same as ``tve demo --texts …`` from Python.

Uses ``sample_corpus.csv`` next to this script (25 rows, ``id`` + ``text``).
**scikit-learn** LDA stack (no spaCy). **From the repository root**::

  uv run python examples/02_byo_csv_show.py
  uv run python examples/02_byo_csv_show.py --no-browser
  uv run python examples/02_byo_csv_show.py --smoke
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import topicvisexplorer as tve

REPO_EXAMPLES = Path(__file__).resolve().parent
CSV = REPO_EXAMPLES / "sample_corpus.csv"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Check CSV load only (25 documents); do not start the server.",
    )
    args = p.parse_args()
    if not CSV.is_file():
        print(f"error: missing data file: {CSV}", file=sys.stderr)
        return 1
    if args.smoke:
        from topicvisexplorer.server.byo_corpus import load_texts

        texts = load_texts(CSV, csv_text_column="text")
        if len(texts) != 25:
            print("smoke: expected 25 rows, got", len(texts), file=sys.stderr)
            return 1
        print("Smoke OK —", len(texts), "documents from column 'text'")
        return 0
    tve.show(
        texts_file=CSV,
        byo_csv_text_column="text",
        byo_model="sklearn-lda",
        byo_num_topics=3,
        byo_passes=2,
        byo_seed=0,
        scenario_name="02_byo_csv",
        open_browser=not args.no_browser,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
