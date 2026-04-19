/**
 * Pre-import setup of the legacy globals expected by LDAvis.js / topicflow.js.
 *
 * The original paper template wrote inline ``<script>`` tags BEFORE loading
 * LDAvis.js, e.g. ``var type_vis = 1; var jsonData = {...};``. The legacy
 * code reads those globals at module top-level (not inside a function), so
 * if the legacy modules are imported before the globals exist, the bundle
 * throws ``ReferenceError: type_vis is not defined`` and the whole IIFE
 * never returns -- which means ``window.TVE`` never gets defined either.
 *
 * To preserve that contract under bundler scope, this module is imported
 * FIRST in main.ts and synchronously copies ``window.TVE_SCENARIO`` (which
 * the Jinja template renders into the page <head>) onto the corresponding
 * ``window`` properties. After this runs, the legacy modules see exactly
 * what they used to see in the script-tag world.
 *
 * If ``TVE_SCENARIO`` is missing -- e.g. when the bundle is loaded by the
 * standalone dev fixture under ``frontend/index.html`` -- we still install
 * safe defaults so the legacy code does not throw on load.
 */

const w = window as any;

const scenario = w.TVE_SCENARIO;

// If the user navigated to e.g. ``/singlecorpus`` without a ``?scenario=``
// query string, the legacy LDAvis.js code at module load time reads
// ``window.location.search`` to decide between "real visualization" and
// "tutorial mode". Backfill the query string from the server-rendered
// ``TVE_SCENARIO.name`` so the tutorial doesn't auto-fire on bare URLs.
// ``history.replaceState`` keeps the browser-bar URL coherent without
// adding a navigation entry.
if (scenario && scenario.name) {
  try {
    const params = new URLSearchParams(window.location.search);
    if (!params.has("scenario")) {
      params.set("scenario", scenario.name);
      if (!params.has("hitl")) params.set("hitl", "false");
      const newSearch = "?" + params.toString();
      window.history.replaceState({}, "", window.location.pathname + newSearch);
    }
  } catch {
    /* history API unavailable (very old browsers); legacy code falls back */
  }
}

if (scenario) {
  // Single-corpus and multi-corpus globals used by LDAvis.js / topicflow.js
  // at top-level, before any UI event ever fires.
  w[`${scenario.visidRaw}_data`] = scenario.visJson;
  w.type_vis = scenario.typeVis;
  w.topic_order = scenario.topicOrder;
  w.jsonData = scenario.visJson;

  if (scenario.typeVis === 1 && scenario.newCirclePositions) {
    w.new_circle_positions = scenario.newCirclePositions;
  }
  if (scenario.typeVis === 2) {
    w.matrix_sankey = scenario.matrixSankey;
    w.jsonData_2 = scenario.visJson2;
    w.topic_order_2 = scenario.topicOrder2;
  }
} else {
  // Standalone dev fixture: install null-ish defaults so the legacy code
  // can be parsed without ReferenceErrors. Nothing will render, but the
  // bundle still loads and the dev server can serve it.
  w.type_vis = w.type_vis ?? 0;
  w.topic_order = w.topic_order ?? [];
  w.jsonData = w.jsonData ?? null;
}

export {};
