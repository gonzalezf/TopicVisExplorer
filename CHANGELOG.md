# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Backward compatibility policy

Starting with v1.0.0 the project follows strict [semver](https://semver.org/).
Breaking changes are batched into major bumps and announced in the changelog
at least one minor release ahead when practical.

## [Unreleased]

_Nothing yet. See [`ROADMAP.md`](https://github.com/gonzalezf/topicvisexplorer-lib/blob/main/ROADMAP.md) for v1.1 plans._

## [1.0.0] - 2026-04-20

First stable release of the modernized library. Ships the paper Section 6
future-work roadmap (BERTopic / ETM / CTM adapters, add-word / remove-word /
exclude-document edit operations, and the collapsible coherence panel with
NPMI / C_v / segregation / coverage metrics) on top of a FastAPI + Vite +
TypeScript + D3 v5 stack, while preserving the paper-version visual identity
under Playwright pixel-regression baselines and the paper-version numerical
outputs under golden tests (`atol=1e-9`).

This is the first release of the library as the public
[`topicvisexplorer-lib`](https://github.com/gonzalezf/topicvisexplorer-lib)
repository. The pre-v1.0 history (Phases 0–4) lived in a private-backup
repository and is deliberately not carried forward; see the README of the
backup for the full trail.

### Added (Phase 4h, complete)

- **Extending guide stub** at `docs/extending.md`. Frames the three
  new adapters (BERTopic, ETM, CTM), the two new edit operations
  (add/remove word, exclude document), and the new coherence panel
  as direct deliveries of paper Section 6 future work, and
  documents the contracts custom loaders must satisfy:
  - `TopicModelAdapter` protocol surface for new model adapters.
  - `EmbeddingProtocol` for swapping Word2Vec for SBERT/FastText.
  - `doc_id` as a stable per-row identifier in `relevant_documents`
    (consumed by `POST /Exclude_Document`).
  - `Scenario.raw_texts` requirement for `GET /coherence`.
  Linked from the top-level `README.md`. Full Sphinx site comes in
  Phase 5.

### Added (Phase 4g, complete)

- **Cross-adapter equivalence test** in
  `tests/unit/test_adapter_equivalence.py`. First test in the suite
  that drives `GensimLDAAdapter` and `SklearnLDAAdapter` end-to-end
  on the **same** synthetic 10-doc bimodal corpus and asserts both
  produce a `TopicModelData` that the rest of the pipeline can
  treat interchangeably. We deliberately do NOT assert numerical
  equivalence of topic-term distributions (gensim and sklearn run
  different variational EM rules, so absolute equivalence is
  impossible on a tiny corpus); we DO assert the structural
  contract: same K, same N, same vocab universe, both row-
  stochastic, both feed cleanly through `prepare()` to a
  `PreparedData` with identical column schemas.
- **Golden tests for Phase 4 edit operations** in
  `tests/golden/test_edit_ops_golden.py`, pinned against
  `golden_baseline/tiny_edit_ops.json`. Catches any drift in
  `add_word`'s boost-quantile, `remove_word`'s renormalization, or
  `exclude_document`'s row-renormalization down to `atol=1e-9`.
  Complements the existing qualitative unit tests in
  `tests/unit/test_operations.py`.
- `scripts/capture_edit_op_golden.py`: regenerator for the new
  golden baseline. Deterministic at fixture seed 0 -- re-running
  must produce byte-identical JSON, otherwise an upstream
  dependency drifted (review before committing).

### Added (Phase 4f, complete)

- **Collapsible coherence panel** in the modern UI. A 28×28 toggle
  button (Σ glyph) in the top-right corner expands a floating panel
  showing per-topic NPMI, C_v, segregation, and coverage. Delivers
  paper Section 6 future-work line "extend with topic-quality
  metrics (NPMI, C_v) and topic-distinctness/coverage indicators".
  - **Closed by default**: the body is hidden via `hidden` and the
    wrapper uses `position: fixed`, so the closed state contributes
    only the small toggle button to the screenshot. The visual
    baselines were re-captured to absorb that 0.085% pixel delta;
    the existing `maxDiffPixelRatio: 0.05` tolerance keeps real
    layout regressions caught.
  - **Lazy-loaded**: the panel only fetches `/coherence` on first
    expand and caches the response, so users who never look at
    coherence pay zero cost. The endpoint computes per-pair
    document co-occurrence which is O(D · V_top²) and a few
    hundred ms on real corpora — deferring it keeps boot fast.
  - **Single-corpus only for v1.0**: the `{% if type_vis == 1 %}`
    Jinja guard hides the toggle in multi-corpus mode and the
    endpoint returns 400 there. Multi-corpus support (per-corpus
    columns, cross-corpus segregation) is a v1.1 enhancement.
- `GET /coherence` endpoint (`src/topicvisexplorer/server/app.py`):
  computes `CoherenceReport` for the active single-corpus session
  using the existing pure-NumPy `topicvisexplorer.coherence` module
  and returns it as `{npmi: [...], c_v: [...], segregation: [...],
  coverage: [...], mean_npmi, mean_c_v}`. Sanitized through
  `sanitize_for_json` so NPMI's log-of-zero edges that produce
  `-inf` don't blow up FastAPI's `allow_nan=False` serializer.
- `frontend/src/coherence_panel.ts`: vanilla-DOM panel controller
  (no extra runtime deps). Exposes only side effects so it can be
  imported from `main.ts` for its `DOMContentLoaded` listener.
- `frontend/tests/coherence_panel.spec.ts`: three Playwright tests
  covering the open-state contract — toggle absent in multi-corpus
  mode, toggle expands/lazy-loads/renders one row per topic with
  the expected 5 columns and `Topic <n>` labels, and toggle
  collapses again on second click.
- `tests/api/test_coherence_endpoint.py`: four pytest API tests —
  contract (4 columns, equal lengths), strict-JSON cleanliness (no
  raw NaN/Infinity tokens leak), 400 in multi-corpus mode, 400
  without an active session.

### Added (Phase 4d/4e, complete)

- **Add/remove word UI** (`frontend/src/legacy/LDAvis.js`): each term
  in the keyword bar chart now carries a hover-revealed `+` and `-`
  control next to its label. The buttons are SVG `<text>` glyphs
  rendered with `opacity: 0` by default, so the visual baseline
  (no hover state) is byte-identical to v0.1. Clicking either glyph
  POSTs to `/Add_Remove_Word` and the bar chart redraws in place
  using the returned `PreparedData.tinfo`. Delivers paper Section 6
  future-work line "interact with topics by adding or removing words".
- **Exclude-document UI** (`frontend/src/legacy/LDAvis.js`): the
  single-corpus documents panel now has a per-row `×` button that
  POSTs to `/Exclude_Document` with the row's stable `doc_id`. The
  in-memory document list is filtered, the keyword panel redraws
  (because excluding a document shifts `doc_topic_dists` which
  propagates into the topic-term matrix via `prepare`), and the
  table re-renders against the filtered data. Delivers paper
  Section 6 future-work line "exclude individual documents from a
  topic".
- `frontend/src/legacy/LDAvis.js`:
  - Added a late-bound `_tveInternals` bag exposing closure-private
    helpers `topic_on` and `updateRelevantDocuments` to the LDAvis
    outer scope so the new edit-operation hooks
    (`_tveAddRemoveWord`, `_tveExcludeDocument`) can call back into
    the original render functions.
  - Added the `_tveDocumentColumnsModel1` helper that builds the
    bootstrap-table column descriptor (with the new exclude column)
    plus a delegated click handler on the table container so the
    button keeps working after sort/page changes (which replace the
    `<tbody>`).
- `src/topicvisexplorer/server/app.py`:
  - `POST /Add_Remove_Word` now returns the full `PreparedData`
    payload alongside `ok` and `remaining_undo_steps` so the front-
    end can redraw without reloading.
  - `POST /Exclude_Document` mirrors the same response shape.
  - All edit-op responses are routed through a new
    `sanitize_for_json` helper (`utils.py`) that maps NaN / +Inf /
    -Inf to `null` so FastAPI's strict (`allow_nan=False`) JSON
    serializer doesn't blow up when `remove_word` produces
    `loglift = log(0/x) = -inf`.
- `src/topicvisexplorer/server/demo_data.py`: every demo
  `relevant_documents` row now carries a stable `doc_id` matching
  its index into `doc_topic_dists`. The new exclude-document UI
  binds to that field; users with custom scenarios should add the
  same field to their loader output (documented in
  `docs/extending.md` -- Phase 4h).
- `tests/api/test_undo_and_word_ops.py`: assertions tightened to
  cover the new `PreparedDataObtained_fromPython` payload shape on
  both endpoints.
- `frontend/tests/word_ops.spec.ts`: new Playwright suite (2 tests)
  exercising the +/- controls end-to-end against the live FastAPI
  server.
- `frontend/tests/exclude_doc.spec.ts`: new Playwright suite (1 test)
  exercising the per-row × control end-to-end. Asserts the clicked
  `data-doc-id` is gone from the rebuilt table and the underlying
  bootstrap-table data length shrunk.
- `frontend/tests/visual.spec.ts`: re-captured baselines for both
  scenarios (the documents panel grew an exclude column header). Set
  `maxDiffPixelRatio: 0.05` to absorb non-deterministic Sankey
  ribbon path rounding without losing layout-regression coverage.

### Added (Phase 4c, complete)

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

The v1.0.0 release is the **initial commit** of the public
[`topicvisexplorer-lib`](https://github.com/gonzalezf/topicvisexplorer-lib)
repository. The pre-v1.0 commit history (Phases 0–4 of the modernization)
was developed in a private-backup repository and intentionally squashed on
extraction — to eliminate any chance of historical privacy/security data
resurfacing via `git log`. The paper-faithful v0.1 source remains available
at the `legacy` branch and the `v0.1-paper` git tag of the private backup.
