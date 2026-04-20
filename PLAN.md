# TopicVisExplorer modernization plan

> Single source of truth for the v1.0 modernization effort.
> Any agent or contributor picking up the work should read this
> file first, then `CHANGELOG.md`, then the per-phase commits.
>
> **Last touched:** end of Phase 4 (April 2026), commit `835b6d1`.
> **Current branch:** `next`. **Default branch:** `master`
> (paper-faithful v0.1).

---

## 1. Goal & guardrails

Modernize TopicVisExplorer (paper version on `master`) into a
pip-installable Python library with a FastAPI backend and a Vite +
TypeScript + D3 v5 frontend, **without breaking the visual identity
of the figures the published paper depends on**. Specifically:

1. The published paper's GitHub URL keeps working — we use the
   `next` branch and the `v0.1-paper` tag, never rewrite history on
   `master`.
2. Every visualization in the modern UI must be screenshot-equal
   to the paper version on the bundled demo scenarios. Visual
   regression is enforced by Playwright (`frontend/tests/visual.spec.ts`)
   with `maxDiffPixelRatio: 0.05`.
3. Every numerical output of `prepare`, the similarity matrix, and
   the new edit operations is pinned by golden tests under
   `tests/golden/` to `atol ≤ 1e-6` (often `1e-9`).
4. Add new functionality from paper Section 6 (future work) only
   in additive ways: new endpoints, new optional UI panels (closed
   by default), new optional dependencies behind extras.

If you have to break any of these, stop and ask the maintainer.

---

## 2. Repository layout

```
.
├── PLAN.md                         <- this file
├── CHANGELOG.md                    <- per-phase narrative; Keep-a-Changelog
├── README.md                       <- next-branch readme
├── CONTRIBUTING.md
├── pyproject.toml                  <- src layout, [full] extra
├── src/topicvisexplorer/           <- library code
│   ├── prepare.py                  <- LDAvis-style prepare()
│   ├── coherence.py                <- pure-NumPy NPMI/C_v/segregation/coverage
│   ├── operations/                 <- split, merge, add_remove_word, exclude_document
│   ├── models/                     <- TopicModelData + adapters/
│   │   └── adapters/               <- gensim_lda, sklearn_lda, sklearn_nmf, bertopic, etm, ctm
│   ├── similarity/                 <- baselines + embedding-based
│   ├── server/                     <- FastAPI app, scenarios, demo_data, schemas
│   ├── utils.py                    <- NumPyEncoder, sanitize_for_json
│   └── web/                        <- legacy templates & static assets the wheel ships
│       ├── legacy/templates/index_v1.html  <- modern Jinja template
│       └── dist/                   <- built bundle (generated; gitignored? confirm)
├── frontend/                       <- Vite + TypeScript + D3 v5 source
│   ├── src/
│   │   ├── main.ts                 <- entry; imports legacy LDAvis.js + new TS modules
│   │   ├── coherence_panel.ts      <- Phase 4f panel controller
│   │   ├── scenario_globals.ts
│   │   ├── styles/main.scss
│   │   └── legacy/                 <- vendored paper-version JS (LDAvis.js, sankey.js, ...)
│   └── tests/                      <- Playwright (visual + functional)
├── tests/
│   ├── conftest.py                 <- tiny_* fixtures
│   ├── unit/                       <- ~80 unit tests
│   ├── api/                        <- FastAPI TestClient tests
│   └── golden/                     <- pinned-numerical regression tests
├── golden_baseline/                <- captured JSON / pickles
└── scripts/                        <- capture_*.py regenerators
```

---

## 3. Branch & release strategy

| Branch        | Purpose                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------ |
| `master`      | Paper-faithful v0.1 code. Frozen. Linked from the paper. Only security backports.          |
| `legacy`      | Same as `master` plus the captured `golden_baseline/*` artifacts and the legacy lockfile.  |
| `next`        | Where v1.0 is being built. Orphan branch, no shared history with `master`. **We work here.** |
| `v0.1-paper`  | Immutable git tag pointing at the exact commit on `master` the paper was reviewed against. |

**Phase 5 promotes `next` to be the default branch** with a
`v1.0.0` tag. `master` stays read-only at the v0.1 commit so the
paper's citation URL keeps resolving.

---

## 4. Test-suite contract (must stay green before any commit)

```bash
# Python
python -m pytest -q          # 121 passed, 2 skipped (BERTopic + ETM optional)
ruff check src tests         # 0 errors

# Frontend
cd frontend
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build
node node_modules/@playwright/test/cli.js test     # 10 passed (3 visual + 7 functional)
```

Sandbox notes for the next agent:
- `npm run build` and `npx playwright test` may fail in the
  default sandbox with EACCES on `/mnt/data/caches/tmp/...`.
  Re-run the failing command with `required_permissions: ["all"]`.
- The Python suite runs cleanly inside the default sandbox.

---

## 5. Status — what is done

All eight Phase-4 items are merged on `next`. Recent commits:

| Commit    | Phase                                                         |
| --------- | ------------------------------------------------------------- |
| `835b6d1` | 4h — Extending guide stub (`docs/extending.md`)               |
| `c6d6a26` | 4g — Adapter equivalence + edit-op golden tests               |
| `52fcae5` | 4f — Collapsible coherence panel (NPMI / C_v / seg / cov)     |
| `faed295` | 4d/e — Add/remove word + exclude document UI                  |
| `102355a` | 4a/b/c — BERTopic + ETM + CTM adapters                        |
| `19f98fb` | Fix demo layout (full-viewport CSS for legacy %-heights)      |
| `e029a8f` | 3 — Vite + TypeScript bundle + visual baselines               |
| `3dc554d` | 2 — FastAPI server + cookie sessions + API tests              |
| `d55f534` | 1 — Library skeleton, typed modules, golden tests             |
| `bc646db` | 0 — Bootstrap orphan `next` branch                            |

### What each phase shipped

- **Phase 0 (`bc646db`)** — orphan `next` branch, repo conventions,
  branch policy.
- **Phase 1 (`d55f534`)** — `pyproject.toml`, src layout, ported
  `prepare`, `models/protocol.py` adapter contract, `coherence.py`,
  the four `operations/`, `similarity/baselines.py` +
  `similarity/embedding.py`, golden baselines for `prepare` and the
  similarity matrix.
- **Phase 2 (`3dc554d`)** — FastAPI app under
  `src/topicvisexplorer/server/`, cookie session store, demo
  scenarios (`tiny_demo`, `tiny_multi_demo`), `NumPyEncoder`, full
  `tests/api/` suite for every endpoint the paper UI hits.
- **Phase 3 (`e029a8f`)** — `frontend/` (Vite + TypeScript), legacy
  D3 code vendored under `frontend/src/legacy/`,
  `index_v1.html` modern template, Playwright visual baselines
  pinned at `maxDiffPixelRatio: 0.05` (Sankey is non-deterministic).
- **Phase 4a/b/c (`102355a`)** — real BERTopic, ETM, CTM adapters
  (paper Section 6 line item). All three behind the `[full]` extra
  so the default install stays slim.
- **Phase 4d/e (`faed295`)** — add/remove word UI (hover-revealed
  +/- glyphs in the bar chart) + exclude-document UI (per-row × in
  the documents table). Backend POSTs round-trip the full
  `PreparedData`. `sanitize_for_json` in `utils.py` handles
  NaN/Inf for FastAPI's strict serializer. `doc_id` is now a
  contract on `relevant_documents` rows.
- **Phase 4f (`52fcae5`)** — collapsible coherence panel (Σ button
  in top-right). Closed by default, lazy-loads `GET /coherence` on
  first expand. Single-corpus only (multi-corpus deferred to v1.1).
- **Phase 4g (`c6d6a26`)** — first cross-adapter equivalence test
  (gensim vs sklearn LDA on a shared corpus) + golden tests for
  the three Phase-4 edit operations at `atol=1e-9`. Capture
  script: `scripts/capture_edit_op_golden.py`.
- **Phase 4h (`835b6d1`)** — `docs/extending.md` framing all of
  Phase 4 as paper Section 6 deliveries with the contracts custom
  loaders must satisfy (`doc_id`, `raw_texts`, adapter protocol,
  embedding protocol).

---

## 6. Status — what is open

Only **Phase 5** remains. It has six concrete deliverables — pick
them up in this order:

### 5a. `docs/` Sphinx site (id: `phase5-docs-site`)

- Convert the existing `docs/extending.md` stub into a Sphinx site
  under `docs/site/` (or MkDocs Material — pick one and document
  it in CONTRIBUTING.md).
- Pages needed:
  - Quickstart (`pip install topicvisexplorer`, run the demo).
  - Tutorial: bring-your-own-corpus walk-through.
  - API reference (autogenerated from docstrings).
  - Extending guide (port from `docs/extending.md`).
  - Edit operations cookbook (split / merge / add-remove word /
    exclude document) with screenshots.
  - Coherence metrics primer (link the four references already in
    `coherence.py`'s module docstring).
  - Migration guide: paper version → v1.0.
- Wire CI to build the site on PRs and publish to GitHub Pages on
  every `next` push.
- **Acceptance:** site builds with zero warnings, all autodoc
  pages render, GitHub Pages serves it.

### 5b. CITATION.cff + paper-acceptance materials (id: `phase5-citation`)

- Add `CITATION.cff` at repo root. Cite the Journal of
  Visualization paper.
- Add `PAPER_REPRO.md` documenting how to reproduce the paper's
  figures from the `legacy` branch (and what's needed to
  reproduce them on `next` — likely a small `paper-figures`
  Playwright profile that runs against the real Cambridge
  Analytica / Gun Violence pickles, gated on the user supplying
  them locally).
- Add a "Cite this software" badge to README.
- **Acceptance:** zenodo.org picks up CITATION.cff on the next
  release; paper-rebuild script runs end-to-end on a machine that
  has the original pickles.

### 5c. PyPI release plumbing (id: `phase5-pypi`)

- Verify `pyproject.toml` metadata: `name`, `version`, `authors`,
  `license`, `classifiers`, URLs (homepage, docs, changelog,
  source), `[project.optional-dependencies]` for `[full]` extra.
- Add `MANIFEST.in` if needed so `src/topicvisexplorer/web/dist/*`
  ships in the wheel (the bundle MUST be included — without it
  the FastAPI server has no UI assets).
- Add a `release.yml` GitHub Actions workflow that, on a `v*` tag:
  1. Runs the full test suite.
  2. Builds the frontend bundle (`vite build`) and copies into
     `src/topicvisexplorer/web/dist/`.
  3. Builds sdist + wheel.
  4. Publishes to PyPI via OIDC trusted publisher.
- Test the wheel in a clean venv: `pip install dist/*.whl &&
  topicvisexplorer-server` and confirm the demo loads in a
  browser.
- **Acceptance:** `pip install topicvisexplorer` from PyPI works
  end-to-end on macOS, Linux, Windows (matrix in CI).

### 5d. CHANGELOG release entry + version bump (id: `phase5-version`)

- Bump `src/topicvisexplorer/_version.py` → `1.0.0`.
- Roll the `## [Unreleased]` section in `CHANGELOG.md` into
  `## [1.0.0] - YYYY-MM-DD`.
- Add a top-of-changelog note: "v1.0.0 ships the paper Section 6
  roadmap (BERTopic / ETM / CTM adapters, add/remove word,
  exclude document, coherence panel)."

### 5e. Branch promotion `next` → `main` (id: `phase5-branch-promo`)

- Coordinate with the maintainer; this is the irreversible step
  the user explicitly flagged at project start.
- On GitHub: change default branch to `next`, then rename `next`
  → `main`, then archive `master` → `legacy-paper` (or just leave
  `master` alone and rename `next` → `main` directly — see
  CONTRIBUTING.md branch policy and confirm with the maintainer
  which they want).
- Update the README, the paper's GitHub URL fallback (the
  `v0.1-paper` tag is the durable reference), and any references
  in `docs/`.
- Verify the `v0.1-paper` tag still resolves to the paper-version
  commit.
- **Acceptance:** the URL the paper cites still serves working
  paper-version code (via the tag); `pip install` from `main`
  installs v1.0.

### 5f. Open issues + roadmap for v1.1 (id: `phase5-roadmap`)

- File issues for everything explicitly deferred:
  - Multi-corpus coherence panel.
  - SBERT and FastText embedding backends as first-class options
    (Word2Vec is the paper-faithful default).
  - The `paper-figures` Playwright profile (reproduces the actual
    paper figures on a machine with the pickles).
  - Per-corpus loaders beyond the bundled demo
    (HuggingFace `datasets` integration is a popular ask).
- Add a `ROADMAP.md` linking the issues by milestone (v1.1, v1.2).

---

## 7. Open watch-items / known issues

- **Sankey non-determinism** — `frontend/tests/visual.spec.ts`
  uses `maxDiffPixelRatio: 0.05` to absorb float-rounding noise
  in D3-sankey ribbon paths. If this becomes flakier on a
  contributor's machine, do NOT raise the ratio further; first
  investigate whether `d3-sankey` has a deterministic node-order
  setting we can pin.
- **`raw_texts` for custom loaders** — the new `/coherence`
  endpoint requires `Scenario.raw_texts`. Bundled demo loaders
  set it; users porting their own corpora hit a 404. The
  extending guide (`docs/extending.md` §3.2) documents this.
- **Optional dep skips** — 2 tests skip without `bertopic` or
  `embedded_topic_model`. Both are in `[full]`; CI's nightly
  `[full]` job should run with them installed and assert no
  skips.
- **Built bundle in git** — confirm whether
  `src/topicvisexplorer/web/dist/tve.{js,css}` is gitignored or
  committed. If gitignored, Phase 5c MUST rebuild it during
  release. If committed, it must be regenerated whenever any
  `frontend/src/**` file changes.
- **Cursor's todo list** has been kept in sync with this file
  through Phase 4. Any agent continuing should re-create the
  todos from §6 above on first turn.

---

## 8. How to continue tomorrow (TL;DR for the next agent)

1. `cd /root/projects/TopicVisExplorer && git status` (should be
   clean on `next` at `835b6d1`).
2. Read this file (`PLAN.md`) and the top of `CHANGELOG.md`.
3. Run the full test suite — Python and Playwright — to confirm a
   green baseline (see §4).
4. Pick the first open Phase-5 sub-item from §6 and create todos
   for it.
5. Make the smallest possible commits, one per sub-item, with
   commit messages in the style of the recent Phase 4 commits
   (subject line names the phase, body explains the *why* and the
   test impact).
6. Update `CHANGELOG.md`'s `## [Unreleased]` section before each
   commit; the changelog is the user-facing narrative.
7. Update §5/§6 of this file when a sub-item closes.

Author identity used for commits in this branch:

```
GIT_AUTHOR_NAME="TopicVisExplorer Agent"
GIT_AUTHOR_EMAIL="agent@topicvisexplorer.local"
```

Don't push to `origin` without explicit user approval — the
maintainer wants to review before anything goes public.
