# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Pre-1.0 backward compatibility policy

Until v1.0.0 ships, any 0.x -> 0.(x+1) bump may break the public API. After
v1.0.0 the project follows strict semver and will batch breaking changes into
major bumps. The `next` branch is the only branch that receives these
0.x updates; `master` continues to host the paper-faithful v0.1 code.

## [Unreleased]

### Added (Phase 2, complete)

- `src/topicvisexplorer/server/`: FastAPI app factory, Pydantic
  request/response schemas, cookie-based LRU session store, scenario
  registry, and a programmatic Uvicorn launcher.
- `src/topicvisexplorer/web/legacy/`: byte-identical copy of the paper
  version's `static/` and `templates/` directories so the Phase 3 visual
  regression has a baseline to diff against.
- `tests/api/`: 17 contract tests using `fastapi.testclient.TestClient`
  covering session lifecycle, scenario routing, similarity matrix,
  topic split / merge / undo, and add / remove / exclude operations.
- `tve.show()` / `tve.demo()` / `tve.save_html()` public entry points.

### Added (Phase 1, complete)

- `pyproject.toml` declaring the `topicvisexplorer` package on Python
  3.10-3.12 with split dependency groups (core / full / hf / dev / docs).
- BSD-3-Clause `LICENSE`.
- `src/` layout for the main package.
- `src/topicvisexplorer/errors.py` with actionable custom exceptions.
- `src/topicvisexplorer/logging.py` configuring the `topicvisexplorer`
  logger namespace.
- `src/topicvisexplorer/preprocessing.py` unifying the three legacy
  `text_cleaner` variants into one canonical pipeline.
- `src/topicvisexplorer/prepare.py` ported and typed from `_prepare.py`.
- `src/topicvisexplorer/layout.py` ported from `_get_new_circle_positions.py`.
- `src/topicvisexplorer/coherence.py` with NPMI, C_v, topic-segregation
  and document-coverage metrics (paper Section 6 future-work items).
- `src/topicvisexplorer/similarity/` with the Protocol, the embedding
  metric (paper Eq. 7-9, **with `lambda` and `omega` untangled**) and
  the WES + Jensen-Shannon + Hellinger + cosine + Jaccard baselines
  (all named in paper Section 2.3).
- `src/topicvisexplorer/embeddings/` with Word2Vec (default, paper-faithful)
  and SBERT (opt-in approximation) backends.
- `src/topicvisexplorer/models/adapters/` with gensim LDA + sklearn LDA
  + sklearn NMF adapters; BERTopic, CTM (Bianchi et al. 2021) and
  ETM (Dieng et al. 2020) as Protocol-conformant stubs.
- `src/topicvisexplorer/operations/` with split / merge / add_remove_word
  / exclude_document modules.
- `src/topicvisexplorer/multi.py` cross-corpus similarity helper.
- Public API: `tve.PreparedData.save` / `tve.load`.
- Unit + Protocol-conformance + golden tests under `tests/`.
- GitHub Actions: `ci.yml` (3.10/3.11/3.12 matrix on `next`) and
  `legacy-smoke.yml` (30s smoke on `legacy` + `v0.1-paper`).
- pre-commit configured with ruff + mypy.
- `CONTRIBUTING.md` documenting the merge gates and golden-recapture flow.
- 57 unit + golden + Protocol-conformance tests passing on Python 3.11
  with 84% line coverage (gate set to 80% in Phase 1; will rise to 85%
  in Phase 2 after API contract tests land).

### Changed

- `lambda` and `omega` are now two independent parameters (the legacy
  code conflated them under the name `lambda`). `omega` is paper Eq. 9
  (top-words vs top-docs blend, default 0.5); `lambda` is the relevance
  parameter from Sievert & Shirley 2014 (default 0.6). A documented
  legacy alias is preserved on both.

### Removed

- Mallet LDA support. Reviewers wanting the exact paper figures use
  `git checkout legacy` or `git checkout v0.1-paper`. See
  `docs/migration.md` once Phase 5 lands.

## [0.1] - Paper version

Available as the `legacy` branch and the `v0.1-paper` git tag in this
repository. See the README on those refs for usage and citation.

## Repository history note

This `next` branch is an **orphan branch**: it has no shared git history
with `master`. At v1.0 release, `next` will be promoted to `main` (and
the previous `master` becomes `legacy-main`, a redundant safety copy of
the `legacy` branch). Anyone running `git log main` post-promotion will
see a clean history starting at the v1.0 root commit. Pre-1.0 history
remains available at the `legacy` and `legacy-main` branches.
