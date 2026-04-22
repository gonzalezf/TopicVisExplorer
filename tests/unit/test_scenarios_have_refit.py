"""Ensure every registered single-corpus scenario ships a refit callable."""
from __future__ import annotations


def test_every_single_corpus_scenario_has_refit() -> None:
    from topicvisexplorer.server import ServerConfig, build_app

    app = build_app(ServerConfig(register_demo=True))
    registry = app.state.registry
    for name in registry.names():
        sc = registry.load(name)
        if sc.is_multi:
            continue
        assert sc.extras.get("refit") is not None, (
            f"Scenario {name!r} is missing extras['refit']. "
            "Every single-corpus scenario must attach a refit callable so "
            "the Split button works in the browser."
        )
        assert callable(sc.extras["refit"]), f"{name!r} extras['refit'] is not callable"
