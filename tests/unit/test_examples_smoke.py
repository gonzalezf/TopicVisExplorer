"""Run ``--smoke`` on shipped example scripts (no long-lived server)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EX = REPO / "examples"


@pytest.mark.parametrize(
    "script",
    [
        "01_prepare_single_corpus.py",
        "02_byo_csv_show.py",
        "03_two_corpora_sankey.py",
        "04_bundled_single_demo.py",
    ],
)
def test_example_script_smoke(script: str) -> None:
    path = EX / script
    assert path.is_file(), path
    r = subprocess.run(
        [sys.executable, str(path), "--smoke"],
        cwd=str(REPO),
        check=False,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
