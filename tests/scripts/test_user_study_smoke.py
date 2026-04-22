"""Lightweight smoke: launch_20ng_study.py and ``tve demo`` --help exit 0."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "user_study" / "launch_20ng_study.py"


@pytest.mark.skipif(not SCRIPT.is_file(), reason="study script not present")
def test_launch_20ng_study_help_exits_0() -> None:
    sys.argv = [str(SCRIPT), "--help"]
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert exc.value.code == 0


def test_tve_cli_demo_help_mentions_new_flags(capsys: pytest.CaptureFixture[str]) -> None:
    from topicvisexplorer.cli import main

    with pytest.raises(SystemExit) as exc:
        main(["demo", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--corpus" in out
    assert "--texts" in out
    assert "--num-topics" in out
    assert "bbc_tiny" in out
    assert "20ng_tiny" in out
