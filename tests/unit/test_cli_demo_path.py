"""Tests for ``tve demo`` browser_path routing (single vs multi-corpus)."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

from topicvisexplorer import cli as cli_mod


def _demo_args(
    *,
    corpus: str | None = None,
    multicorpora: bool = False,
    texts: object | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        host="127.0.0.1",
        port=8000,
        no_browser=True,
        corpus=corpus,
        multicorpora=multicorpora,
        texts=texts,
        name="user_corpus",
        num_topics=5,
        passes=10,
        seed=42,
        model="gensim-lda",
        embedding="word2vec",
        sbert_model="all-MiniLM-L6-v2",
    )


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_demo_singlecorpus_default_browser_path(
    _m_build: MagicMock, m_serve: MagicMock
) -> None:
    assert cli_mod._run_demo(_demo_args()) == 0
    kw = m_serve.call_args[1]
    assert kw["browser_path"] == "/singlecorpus?scenario=20ng_tiny&hitl=true"


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_demo_multicorpora_default_browser_path(
    _m_build: MagicMock, m_serve: MagicMock
) -> None:
    assert cli_mod._run_demo(_demo_args(multicorpora=True)) == 0
    kw = m_serve.call_args[1]
    assert kw["browser_path"] == "/multicorpora?scenario=bbc_vs_20ng&hitl=true"


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_demo_multicorpora_tiny_multi_demo(
    _m_build: MagicMock, m_serve: MagicMock
) -> None:
    assert (
        cli_mod._run_demo(
            _demo_args(corpus="tiny_multi_demo", multicorpora=True)
        )
        == 0
    )
    kw = m_serve.call_args[1]
    assert kw["browser_path"] == "/multicorpora?scenario=tiny_multi_demo&hitl=true"


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_demo_multicorpus_name_without_flag_errors(
    _m_build: MagicMock, _m_serve: MagicMock
) -> None:
    r = cli_mod._run_demo(_demo_args(corpus="bbc_vs_20ng", multicorpora=False))
    assert r == 1
    _m_serve.assert_not_called()


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_demo_texts_plus_multicorpora_errors(
    _m_build: MagicMock, _m_serve: MagicMock
) -> None:
    p = Path(__file__)
    r = cli_mod._run_demo(_demo_args(texts=p, multicorpora=True, corpus=None))
    assert r == 1
    _m_serve.assert_not_called()


@patch("topicvisexplorer.server.serve")
@patch("topicvisexplorer.server.build_app", return_value=MagicMock())
def test_main_demo_multicorpora_argv(_m_build: MagicMock, m_serve: MagicMock) -> None:
    assert (
        cli_mod.main(
            ["demo", "--no-browser", "--multicorpora", "--corpus", "tiny_multi_demo"]
        )
        == 0
    )
    kw = m_serve.call_args[1]
    assert kw["browser_path"] == "/multicorpora?scenario=tiny_multi_demo&hitl=true"
