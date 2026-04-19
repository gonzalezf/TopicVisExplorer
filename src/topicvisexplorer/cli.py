"""Command-line entry point.

Currently a placeholder that prints version + a one-line "what's next"
hint. The full CLI (``tve serve``, ``tve demo``, ``tve fit``...) lands
in Phase 2 alongside the FastAPI server.
"""

from __future__ import annotations

import sys

from ._version import __version__


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv in ([], ["-h"], ["--help"]):
        print(f"TopicVisExplorer {__version__}")
        print()
        print("Usage:")
        print("  tve --version            Show version and exit.")
        print("  tve serve                (Phase 2) Launch the FastAPI server.")
        print("  tve demo                 (Phase 2) Open the bundled demo.")
        return 0
    if argv == ["--version"]:
        print(__version__)
        return 0
    print(f"Unknown command: {argv!r}. Run `tve --help`.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
