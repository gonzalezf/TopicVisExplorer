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

### Added (Phase 4c, in progress)

- `CTMAdapter` (`topicvisexplorer.models.CTMAdapter`) is now a real
  adapter, not the v1.1 stub. Delivers paper Section 6 future-work
  line "future versions could integrate [...] contextualized topic
  models such as [...] CTM (Bianchi et al. 2021)" verbatim.
  - Duck-types the `contextualized-topic-models` PyPI package
    (`get_topic_word_matrix`, `train_data.idx2token`).
  - Intentionally does NOT build the `CTMDataset` needed for
    `get_doc_topic_distribution`: doing so would silently force an
    SBERT inference pass and a transformers dependency on every call.
    Instead we ask the caller to compute it once and pass it as
    `doc_topic_dists=`. The error message points users at the exact
    one-liner.
  - All matrices are renormalized defensively against float roundoff
    and zero-rows.
- `tests/unit/test_adapters.py`: 7 new CTM tests covering protocol
  conformance, caller-supplied DTD, vocabulary discovery via
  `train_data.idx2token`, missing-vocab / missing-method / size-
  mismatch error paths.
- `tests/unit/test_protocols.py`: replaced the
  `test_stub_adapters_raise_actionable_not_implemented` test with a
  `test_no_stub_adapters_remain_in_v1` regression guard. v1.0 ships
  every Section 6 model as a real adapter.
- `contextualized-topic-models>=2.5` added to the `[full]` extra (with
  matching mypy override).

### Added (Phase 4b, complete)

- `ETMAdapter` (`topicvisexplorer.models.ETMAdapter`) is now a real
  adapter, not the v1.1 stub. Delivers paper Section 6 future-work
  line "future versions could integrate [...] embedded topic models
  such as ETM (Dieng et al. 2020)" verbatim.
  - Duck-types two flavours: the de-facto `embedded_topic_model` PyPI
    package (`get_topic_word_matrix`, `get_document_topic_dist`,
    `vocabulary`) and the original Dieng PyTorch reference repo
    (`get_beta`, `get_theta`, `rho`, `alphas`).
  - Auto-detects logits vs probabilities in `get_beta` output and
    softmaxes when needed.
  - Handles torch tensors transparently via a private `_to_numpy`
    helper (no torch import unless the model returns one).
  - `vocabulary` is auto-discovered from `model.vocabulary` or accepted
    as an explicit kwarg; term-frequency and doc-length are computed
    by re-vectorizing the input texts against that exact vocabulary.
  - Subclass hooks `_topic_word_matrix(model)` and
    `_doc_topic_matrix(model, X, N)` for non-standard ETM forks.
- `tests/unit/test_adapters.py`: 7 new ETM tests + 1 `@pytest.mark.slow`
  real-model smoke that activates only when `embedded_topic_model` is
  installed.
- `embedded-topic-model>=1.2` added to the `[full]` extra (with
  matching mypy override for `embedded_topic_model.*` and `torch.*`).

### Added (Phase 4a, complete)

- `BERTopicAdapter` (`topicvisexplorer.models.BERTopicAdapter`) is now a
  real adapter, not the v1.1 stub it was in 0.1.0.dev0. Delivers the
  paper Section 6 future-work line "future versions could integrate
  contextualized topic models such as BERTopic" verbatim.
  - Maps BERTopic's c-TF-IDF matrix to the LDAvis row-stochastic
    `topic_term_dists` contract via row-normalization (the same recipe
    BERTopic's own pyLDAvis integration uses).
  - Drops the HDBSCAN outlier topic `-1` by default; pass
    `include_outliers=True` to keep it.
  - Prefers `model.approximate_distribution(texts)` for soft
    doc-topic distributions (BERTopic >= 0.10) and falls back to
    one-hot from `model.topics_` on older versions.
  - Fully duck-typed: anything exposing `c_tf_idf_`,
    `vectorizer_model`, `topics_` and `get_topic_info` works, so the
    unit tests run without pulling in UMAP/HDBSCAN/sentence-transformers.
- `tests/unit/test_adapters.py`: 12 unit tests covering protocol
  conformance, soft-vs-hard doc-topic, outlier handling (drop and
  keep), zero-row defenses, vocab/c-TF-IDF mismatch detection, and
  missing-arg error messages. Plus one `@pytest.mark.slow` real-model
  smoke that activates only when `bertopic` is actually installed.
- `bertopic>=0.16` added to the `[full]` extra (and the matching mypy
  override).

### Changed (Phase 4a)

- `tests/unit/test_protocols.py`: removed `BERTopicAdapter` from the
  "stubs raise NotImplementedError mentioning v1.1" assertion now that
  it's a real adapter; CTM and ETM remain stubs there.
- `topicvisexplorer.models.__init__` docstring updated to list
  BERTopicAdapter in the stable-adapters section.

### Added (Phase 3, complete)

- `frontend/` Vite + TypeScript project (Node 22, npm-managed). Pinned
  to the legacy versions of jQuery 3.5.1, Bootstrap 4.5.0, D3 v5.16.0,
  nouislider 14.6.2, popper.js 1.16.1, lodash 4.17.21, mark.js 8.11.1,
  intro.js 4.3.0 and bootstrap-table 1.18.3 -- the exact versions the
  paper figures were produced with.
- IIFE-format Vite build that emits a single deterministic `tve.js` +
  `tve.css` to `src/topicvisexplorer/web/dist/`. Unresolved identifiers
  in the legacy code (76 references to `topic_order`, `type_vis`, etc.)
  fall through to `window` exactly the way they did under script tags,
  so visual parity is preserved without rewriting the vendored
  visualisation files.
- `frontend/src/scenario_globals.ts`: pre-import shim that copies
  `window.TVE_SCENARIO` (rendered by the Jinja template) onto the
  exact globals (`type_vis`, `jsonData`, `matrix_sankey`, ...) the
  legacy modules read at top-level. Required because the bundler
  hoists imports above the inline `<script>` block, so the legacy
  globals must exist before the IIFE evaluates.
- `src/topicvisexplorer/web/legacy/templates/index_v1.html`: modern
  Jinja template that loads the bundled `tve.js` instead of the
  dozen-or-so vendored `<script>` tags. Carries the same DOM ids and
  modal markup as the legacy `index.html` so LDAvis.js's
  `getElementById(...)` calls still resolve. Server-rendered scenario
  state is delivered through `window.TVE_SCENARIO`. Tracking-script
  blobs (Hotjar, Google Analytics) deliberately removed.
- `topicvisexplorer.web.has_modern_bundle()` and a `frontend="auto"`
  switch on `ServerConfig` that auto-detects the bundle at startup and
  picks the modern template iff the bundle was built. `frontend="legacy"`
  forces the paper-version template (verified by tests); `frontend="modern"`
  raises if the bundle is missing.
- `frontend/playwright.config.ts` + `tests/visual.spec.ts`:
  visual-regression suite (Chromium 1280x800, deterministic clock /
  RNG / animations disabled, 0.5% pixel-diff tolerance). Baselines
  for `tiny_demo` and `tiny_multi_demo` committed under
  `tests/visual.spec.ts-snapshots/`.
- `frontend/scripts/serve_for_visual_tests.py` Uvicorn launcher used by
  the Playwright `webServer` block.
- `tests/api/test_modern_frontend.py`: 7 conditional smoke tests that
  exercise the modern track end-to-end (skipped automatically when the
  bundle is absent so Node-less installs still pass).
- CI: `frontend` job (lint + type-check + build, uploads bundle artifact)
  and `visual` job (runs Playwright). `build` job now cross-builds the
  frontend before packaging the wheel and asserts both `tve.js`,
  `tve.css`, `index.html`, and `index_v1.html` are present in the wheel.

### Changed (Phase 3)

- `pyproject.toml`: `[tool.hatch.build.targets.wheel].artifacts` now
  also globs `src/topicvisexplorer/web/dist/**/*` so a freshly built
  wheel ships the modern bundle.
- `frontend/src/legacy/highlight.js`: removed deprecated `with(...)`
  block (rejected by Rollup/esbuild). Replaced with a 3-line
  semantically-identical alternative; visual behaviour unchanged.
- `frontend/src/legacy/LDAvis.js`: removed the Hotjar `hj('identify', ...)`
  call (the paper deployment used Hotjar to record user-study
  sessions; the open-source library ships no analytics). Also
  null-guarded `getElementById(topicReverse).disabled` near line ~4470
  to match the existing defensive pattern just above it -- the
  unguarded form was unreachable in the paper deployment but
  hard-fails when human-in-the-loop is disabled.
- `frontend/src/legacy/sankey.js`: declared `jsonDataArray` as an
  explicit closure local instead of an implicit window global; strict
  bundler scope rejects the implicit-global trick.
- `frontend/src/legacy/topicflow.js`: fixed a one-character
  comma-vs-semicolon typo in the `link()` helper that made `y1` an
  implicit window global (same strict-mode reason as above).
- `src/topicvisexplorer/server/app.py`: when type 2 (multi-corpus),
  pass `matrix_sankey` to the modern template via `| safe` (string
  already pre-encoded) instead of `| tojson` (would double-encode it
  and crash the sankey renderer).
- `.gitignore`: previously ignored ALL of `src/topicvisexplorer/web/`
  (including the legacy assets that need to be committed). Now only
  ignores the `web/dist/` build output.

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
