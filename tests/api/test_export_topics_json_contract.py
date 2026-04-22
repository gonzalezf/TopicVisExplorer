"""Contract tests for the browser-only `tve_topics_<scenario>.json` export.

The payload is built in `frontend/src/legacy/LDAvis.js` (and the legacy static
copy) inside the ``#export_topics_button`` click handler. These tests document
**what the UI saves** so tooling and future refactors can rely on a stable
shape.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
LDAVIS_SOURCES = (
    REPO / "frontend" / "src" / "legacy" / "LDAvis.js",
    REPO
    / "src"
    / "topicvisexplorer"
    / "web"
    / "legacy"
    / "static"
    / "js"
    / "LDAvis.js",
)


def _export_topics_json_errors(data: Any) -> list[str]:
    """Return human-readable errors if *data* is not a valid export payload."""
    if not isinstance(data, dict):
        return ["root must be a JSON object"]
    err: list[str] = []
    required = [
        "_tve_version",
        "type_vis",
        "scenario",
        "exported_at",
        "lambda",
        "omega_topic_similarity",
        "current_topic_id",
        "topics",
        "circle_positions",
    ]
    for k in required:
        if k not in data:
            err.append(f"missing key {k!r}")

    allowed = set(required) | {"relevantDocumentsDict"}
    extra = set(data) - allowed
    if extra:
        err.append(f"unknown top-level keys: {sorted(extra)!r}")

    if data.get("_tve_version") != "1.0":
        err.append("expected _tve_version '1.0'")

    tv = data.get("type_vis")
    if tv not in (1, 2):
        err.append("type_vis must be 1 (circle) or 2 (sankey)")

    if "scenario" in data and not isinstance(data.get("scenario"), str):
        err.append("scenario must be a string")

    for key in ("lambda", "omega_topic_similarity"):
        v = data.get(key)
        if v is not None and not isinstance(v, (int, float)):
            # JSON numbers decode as int/float; reject bool (subclass of int) explicitly
            if isinstance(v, bool):
                err.append(f"{key} must be a number or null, not bool")
            else:
                err.append(f"{key} must be a number or null")

    cti = data.get("current_topic_id")
    if cti is not None and (not isinstance(cti, int) or isinstance(cti, bool)):
        err.append("current_topic_id must be an int or null")

    ts = data.get("exported_at")
    if not isinstance(ts, str):
        err.append("exported_at must be an ISO-8601 string")
    else:
        try:
            _parse_iso_utcish(ts)
        except ValueError as e:
            err.append(f"exported_at: {e}")

    circ = data.get("circle_positions")
    if circ is not None and not isinstance(circ, (dict, list)):
        err.append("circle_positions must be null, array, or object")

    rdd = data.get("relevantDocumentsDict", "__absent__")
    if rdd not in (None, "__absent__") and not isinstance(rdd, dict):
        err.append("relevantDocumentsDict must be a JSON object or null if present")

    topics = data.get("topics")
    if not isinstance(topics, list):
        err.append("topics must be a list")
        return err

    if tv == 1:
        for i, t in enumerate(topics):
            if not isinstance(t, dict):
                err.append(f"topics[{i}] must be an object")
                continue
            wk = set(t) - {"id", "label", "top_terms"}
            if wk:
                err.append(f"topics[{i}] has unexpected keys: {sorted(wk)!r}")
            if "id" not in t or not isinstance(t.get("id"), int) or isinstance(
                t.get("id"), bool
            ):
                err.append(f"topics[{i}].id must be an int")
            if "label" not in t or not isinstance(t.get("label"), str):
                err.append(f"topics[{i}].label must be a string")
            tt = t.get("top_terms", [])
            if not isinstance(tt, list):
                err.append(f"topics[{i}].top_terms must be a list of strings")
            elif len(tt) > 20:
                err.append(f"topics[{i}].top_terms has more than 20 terms (UI caps at 20)")
            else:
                for j, term in enumerate(tt):
                    if not isinstance(term, str):
                        err.append(
                            f"topics[{i}].top_terms[{j}] must be a string (term label)"
                        )
    elif tv == 2:
        for i, t in enumerate(topics):
            if not isinstance(t, dict):
                err.append(f"topics[{i}] must be an object")
                continue
            wk = set(t) - {"key", "label"}
            if wk:
                err.append(f"topics[{i}] has unexpected keys: {sorted(wk)!r}")
            if "key" not in t or not isinstance(t.get("key"), str):
                err.append(f"topics[{i}].key must be a string")
            if "label" not in t or not isinstance(t.get("label"), str):
                err.append(f"topics[{i}].label must be a string")
    return err


def _parse_iso_utcish(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        return d.replace(tzinfo=timezone.utc)
    return d


def _sample_circle_export() -> dict[str, Any]:
    return {
        "_tve_version": "1.0",
        "type_vis": 1,
        "scenario": "20ng_tiny",
        "exported_at": "2026-01-15T12:00:00.000Z",
        "lambda": 0.6,
        "omega_topic_similarity": 0.0,
        "current_topic_id": 0,
        "topics": [
            {
                "id": 0,
                "label": "Topic0",
                "top_terms": ["word1", "word2"],
            }
        ],
        "circle_positions": None,
    }


def _sample_sankey_export() -> dict[str, Any]:
    return {
        "_tve_version": "1.0",
        "type_vis": 2,
        "scenario": "default",
        "exported_at": "2026-01-15T12:00:00.000Z",
        "lambda": None,
        "omega_topic_similarity": None,
        "current_topic_id": None,
        "topics": [{"key": "T1", "label": "left topic"}],
        "circle_positions": None,
    }


def test_sample_circle_payload_valid() -> None:
    d = _sample_circle_export()
    assert _export_topics_json_errors(d) == []


def test_sample_sankey_payload_valid() -> None:
    d = _sample_sankey_export()
    assert _export_topics_json_errors(d) == []


def test_hitl_may_add_relevant_documents_dict() -> None:
    d = _sample_circle_export()
    d["relevantDocumentsDict"] = {
        "doc-0": {"title": "x", "text": "y"},
    }
    assert _export_topics_json_errors(d) == []


def test_rejects_bad_version() -> None:
    d = _sample_circle_export()
    d["_tve_version"] = "0.9"
    assert any("_tve_version" in m for m in _export_topics_json_errors(d))


def test_rejects_unknown_top_level_key() -> None:
    d = _sample_circle_export()
    d["user_study_actions"] = []
    err = _export_topics_json_errors(d)
    assert any("user_study_actions" in m or "unknown" in m for m in err)


def test_circle_topics_top_terms_cap() -> None:
    d = _sample_circle_export()
    d["topics"][0]["top_terms"] = [f"w{i}" for i in range(21)]
    err = _export_topics_json_errors(d)
    assert any("20" in m for m in err)


def test_ldavis_both_copies_export_block_matches() -> None:
    """Keep Vite and legacy static LDAvis in sync for the download payload."""
    start = "var exportObj = {"
    end = "if (type_vis == 1 && is_human_in_the_loop == true) {"
    blocks: list[str] = []
    for path in LDAVIS_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert "exportObj.relevantDocumentsDict" in text or "relevantDocumentsDict" in text
        assert '_tve_version: "1.0"' in text
        i = text.index(start)
        j = text.index(end, i)
        block = re.sub(r"\s+", " ", text[i:j].strip())
        blocks.append(block)
    assert blocks[0] == blocks[1], "LDAvis.js export object differs between frontend and static"


@pytest.mark.parametrize("path", LDAVIS_SOURCES, ids=["vite_ldavis", "static_ldavis"])
def test_ldavis_mentions_tve_filename_pattern(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert 'a.download = "tve_topics_" + _scen.replace' in text, (
        f"{path} missing tve_topics_<scenario>.json download pattern"
    )
    assert "#export_topics_button" in text
