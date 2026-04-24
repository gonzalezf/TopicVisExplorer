"""Command-line entry point for TopicVisExplorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._version import __version__
from .models.registry import list_adapters

_BUILTIN_CORPORA = ("20ng_tiny", "bbc_tiny", "tiny_demo")
_BUILTIN_MULTICORPORA = ("bbc_vs_20ng", "tiny_multi_demo")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="tve",
        description="TopicVisExplorer - interactive topic-modeling visualization",
    )
    parser.add_argument(
        "--version", action="store_true", help="Print version and exit"
    )
    sub = parser.add_subparsers(
        dest="command",
        help="Subcommands",
        required=False,
    )

    p_demo = sub.add_parser(
        "demo",
        help=(
            "Start the server and open a bundled or user-supplied real-terms demo "
            "in a browser"
        ),
        description=(
            "First run of a single-corpus scenario trains and caches a small Word2Vec "
            "embedding (~20s for the bundled demos, cached under "
            "~/.cache/topicvisexplorer/). Subsequent runs are instant. "
            "Set TVE_EMBEDDING_DISABLE=1 to skip the embedding and fall "
            "back to a flat Jensen-Shannon layout (Omega slider will not "
            "move bubbles). Use --multicorpora to open the two-corpus Sankey "
            "view (see --corpus: bbc_vs_20ng or tiny_multi_demo)."
        ),
    )
    p_demo.add_argument(
        "--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)"
    )
    p_demo.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_demo.add_argument(
        "--no-browser", action="store_true", help="Do not open a browser tab"
    )
    p_demo.add_argument(
        "--corpus",
        default=None,
        metavar="NAME",
        help=(
            "Bundled scenario: single-corpus=20ng_tiny, bbc_tiny, or tiny_demo; "
            "with --multicorpora: bbc_vs_20ng (needs bbc_tiny+20ng_tiny fixture "
            "build scripts) or tiny_multi_demo (synthetic, no build). "
            "Defaults: 20ng_tiny, or bbc_vs_20ng with --multicorpora."
        ),
    )
    p_demo.add_argument(
        "--multicorpora",
        action="store_true",
        help=(
            "Open /multicorpora (two-corpus Sankey) instead of /singlecorpus. "
            "Set --corpus to bbc_vs_20ng or tiny_multi_demo (default: bbc_vs_20ng). "
            "Incompatible with --texts."
        ),
    )
    p_demo.add_argument(
        "--texts",
        type=Path,
        default=None,
        help=(
            "Path to a text file to run as a one-off 'bring your own' corpus. "
            "Accepts plain .txt (one doc per line), .jsonl (with a 'text' field), "
            ".json (a list of strings or object with 'texts'), or .csv/.tsv with "
            "--csv-text-column. Overrides --corpus."
        ),
    )
    p_demo.add_argument(
        "--csv-text-column",
        metavar="COLUMN",
        default=None,
        help=(
            "Column name to read from a .csv or .tsv passed to --texts (header row "
            "required). Ignored for .jsonl, .json, and plain-text files. Without this "
            "flag, .csv is read as raw lines (wrong for table exports)."
        ),
    )
    p_demo.add_argument(
        "--name",
        default="user_corpus",
        help="Scenario name for --texts (default: user_corpus).",
    )
    p_demo.add_argument(
        "--num-topics", type=int, default=5, help="Number of topics for --texts fit."
    )
    p_demo.add_argument(
        "--passes", type=int, default=10, help="LDA training passes for --texts fit."
    )
    p_demo.add_argument(
        "--seed", type=int, default=42, help="RNG seed for --texts fit."
    )
    _adapter_choices = list_adapters()
    p_demo.add_argument(
        "--model",
        choices=_adapter_choices,
        default="gensim-lda",
        help=(
            "Topic-model adapter for --texts (default: gensim-lda). "
            "bertopic/etm/ctm need pip install 'topicvisexplorer[full]'."
        ),
    )
    p_demo.add_argument(
        "--embedding",
        choices=["word2vec", "sbert"],
        default="word2vec",
        help="Embedding backend for layout similarity with --texts (default: word2vec).",
    )
    p_demo.add_argument(
        "--sbert-model",
        default="all-MiniLM-L6-v2",
        metavar="NAME",
        help="Sentence-Transformers model id when --embedding sbert (default: all-MiniLM-L6-v2).",
    )

    p_serve = sub.add_parser(
        "serve",
        help=(
            "Start the FastAPI server only (no browser; visit e.g. /singlecorpus "
            "or /multicorpora?scenario=... )"
        ),
    )
    p_serve.add_argument(
        "--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)"
    )
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "demo":
        return _run_demo(args)
    if args.command == "serve":
        import topicvisexplorer as tve

        tve.show(
            None,
            host=args.host,
            port=args.port,
            open_browser=False,
        )
        return 0
    return 2


def _run_demo(args: argparse.Namespace) -> int:
    """Dispatch ``tve demo`` including --corpus and --texts handling."""
    from .server import ServerConfig, build_app, serve

    if args.texts is not None and args.multicorpora:
        print(
            "error: --multicorpora cannot be used with --texts (BYO is single-corpus).",
            file=sys.stderr,
        )
        return 1

    if args.texts is None:
        if getattr(args, "model", "gensim-lda") != "gensim-lda":
            print("error: --model is only valid with --texts.", file=sys.stderr)
            return 1
        if getattr(args, "embedding", "word2vec") != "word2vec":
            print("error: --embedding is only valid with --texts.", file=sys.stderr)
            return 1
        if getattr(args, "sbert_model", "all-MiniLM-L6-v2") != "all-MiniLM-L6-v2":
            print("error: --sbert-model is only valid with --texts.", file=sys.stderr)
            return 1

    extras: dict = {}
    scenario_name: str

    if args.texts is not None:
        if not args.texts.exists():
            print(f"error: --texts file does not exist: {args.texts}", file=sys.stderr)
            return 1
        from .server.byo_corpus import build_scenario_from_textfile

        cached: dict = {}

        def _lazy():
            if "sc" not in cached:
                cached["sc"] = build_scenario_from_textfile(
                    args.texts,
                    name=args.name,
                    num_topics=args.num_topics,
                    passes=args.passes,
                    seed=args.seed,
                    model=args.model,
                    embedding=args.embedding,
                    sbert_model=args.sbert_model,
                    csv_text_column=getattr(args, "csv_text_column", None),
                )
            return cached["sc"]

        extras[args.name] = _lazy
        scenario_name = args.name
        print(
            f"Fitting topic model {args.model!r} on {args.texts} "
            f"(K={args.num_topics}, passes={args.passes}, embedding={args.embedding!r}) "
            f"with caching under ~/.cache/topicvisexplorer ..."
        )
    else:
        corpus = args.corpus
        if corpus is None:
            corpus = "bbc_vs_20ng" if args.multicorpora else "20ng_tiny"
        if args.multicorpora:
            if corpus not in _BUILTIN_MULTICORPORA:
                print(
                    "error: with --multicorpora, --corpus must be one of: "
                    f"{', '.join(_BUILTIN_MULTICORPORA)} (got {corpus!r})",
                    file=sys.stderr,
                )
                return 1
        else:
            if corpus in _BUILTIN_MULTICORPORA:
                print(
                    f"error: {corpus!r} is a multi-corpus scenario; "
                    "re-run with --multicorpora",
                    file=sys.stderr,
                )
                return 1
            if corpus not in _BUILTIN_CORPORA:
                print(
                    "error: --corpus must be one of: "
                    f"{', '.join(_BUILTIN_CORPORA)} (got {corpus!r})",
                    file=sys.stderr,
                )
                return 1
        scenario_name = corpus

    cfg = ServerConfig(register_demo=True, extra_scenarios=extras)
    app = build_app(cfg)
    if args.multicorpora:
        browser_path = f"/multicorpora?scenario={scenario_name}&hitl=true"
    else:
        browser_path = f"/singlecorpus?scenario={scenario_name}&hitl=true"
    serve(
        app,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        browser_path=browser_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
