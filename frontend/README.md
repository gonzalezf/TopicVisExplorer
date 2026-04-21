# TopicVisExplorer Frontend

This package builds the JavaScript / CSS bundle that the
TopicVisExplorer FastAPI server serves at `/dist/tve.js` and
`/dist/tve.css`. It replaces the dozen-or-so vendored `<script>` and
`<link>` tags from the paper version with a single, npm-managed,
TypeScript-typed bundle while preserving byte-identical visual output.

## Architecture

```
frontend/
├── package.json            npm-managed dependencies (jQuery 3.5.1,
│                           Bootstrap 4.5.0, D3 v5, nouislider, etc.
│                           — all pinned to the legacy versions).
├── vite.config.ts          IIFE-format build that emits to
│                           ../src/topicvisexplorer/web/dist/.
├── tsconfig.json           TS with allowJs so legacy *.js files can be
│                           imported alongside *.ts entries.
├── playwright.config.ts    Visual-regression suite config.
├── index.html              Standalone dev fixture (npm run dev).
├── src/
│   ├── main.ts             Entry point. Boots LDAvis from
│   │                       window.TVE_SCENARIO (server-rendered).
│   ├── vendor.ts           Imports + attaches all vendor globals to
│   │                       window so the legacy code can find them.
│   ├── styles/main.scss    Aggregated stylesheet (Bootstrap + LDAvis +
│   │                       nouislider + intro.js).
│   ├── legacy/             Verbatim paper-version JS files. Modified
│   │   ├── LDAvis.js       only by a marked "Modernization shim" block
│   │   ├── topicflow.js    that re-exposes the constructor on window;
│   │   ├── sankey.js       all visualisation logic is byte-identical.
│   │   └── highlight.js
│   └── types/globals.d.ts  Ambient declarations for window globals.
├── scripts/
│   └── serve_for_visual_tests.py   Uvicorn launcher for Playwright.
└── tests/
    └── visual.spec.ts      Screenshot-diff baselines for paper parity.
```

## Why an IIFE bundle?

The legacy code references identifiers like `topic_order`, `type_vis`,
and `new_circle_positions` 76+ times without ever declaring them — under
`<script>` tags they resolved to globals on `window`. ES module bundling
would turn those into `ReferenceError` at runtime. The IIFE format lets
unresolved identifiers fall through to `window` exactly the way they
did before, which is why visual parity is preserved without rewriting
the vendored visualisation files.

## Build

```bash
npm install               # ~7s on a warm npm cache
npm run build             # tsc --noEmit, then vite build
                          # -> ../src/topicvisexplorer/web/dist/
```

The Python wheel detects `web/dist/` at runtime and switches to the
modern `index_v1.html` template automatically. Without the bundle the
wheel still works using the legacy paper-version template, so a
Node-less environment never breaks.

## Develop

```bash
npm run dev               # http://localhost:5173 -- dev fixture only
```

For backend-integrated dev, run the FastAPI server in one terminal and
do `npm run build -- --watch` in another.

## Test

```bash
npm run lint              # ESLint over src/ (legacy/ excluded)
npm run test:visual       # Playwright screenshot diffs
npm run test:visual:update # accept new baselines
```

Visual baselines live under `tests/__screenshots__/` and are committed
to git. Failing diffs report a percentage; the tolerance is 0.5% per
project (`maxDiffPixelRatio: 0.005`) — tighter than Playwright's
default because the paper-review visual identity is a hard gate.

## Versioning

The frontend bundle's version is independent of the Python package
version *for now* (Phase 3a) but will be locked together starting at
v1.0.0 so a wheel can never ship with a stale bundle.

## Roadmap

| Version | Frontend track                                  |
| ------- | ----------------------------------------------- |
| 1.0.0   | This bundle. D3 v5 + Bootstrap 4 + jQuery.      |
| 1.1.x   | Component refactor: split LDAvis.js into typed modules. |
| 1.2.x   | D3 v7 migration (visual-regression gated).      |
| 2.0.0   | React + D3 islands. Drops jQuery + Bootstrap-table. |
