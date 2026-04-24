#!/usr/bin/env python3
"""
Bundled **single-corpus** demo: no file of yours — uses a prebuilt scenario.

**From the repository root**::

  uv run python examples/04_bundled_single_demo.py
  uv run python examples/04_bundled_single_demo.py --no-browser
  uv run python examples/04_bundled_single_demo.py --corpus bbc_tiny
  uv run python examples/04_bundled_single_demo.py --smoke
"""

from __future__ import annotations

import argparse

import topicvisexplorer as tve

_CORPUS_CHOICES = ("20ng_tiny", "bbc_tiny", "tiny_demo")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument(
        "--corpus",
        default="tiny_demo",
        choices=_CORPUS_CHOICES,
        help="Bundled single-corpus scenario (default: tiny_demo).",
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Verify API only; do not start the server (tve.demo would block).",
    )
    args = p.parse_args()
    if args.smoke:
        if not callable(tve.demo):
            return 1
        print("Smoke OK — tve.demo is available; corpus choices:", _CORPUS_CHOICES)
        return 0
    tve.demo(
        corpus=args.corpus,
        open_browser=not args.no_browser,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
