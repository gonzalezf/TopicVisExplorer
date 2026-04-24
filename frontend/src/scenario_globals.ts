import $ from "jquery";

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

w.TVE = w.TVE || {};

// Opt-in legacy debug logs (LDAvis merge/split progress, etc.): /singlecorpus?...&tve_debug=1
// Or set ``window.TVE_DEBUG = true`` in DevTools.
try {
  const qp = new URLSearchParams(window.location.search);
  if (w.TVE_DEBUG == null) {
    w.TVE_DEBUG = qp.get("tve_debug") === "1" || qp.get("TVE_DEBUG") === "1";
  }
} catch {
  if (w.TVE_DEBUG == null) w.TVE_DEBUG = false;
}

const scenario = w.TVE_SCENARIO;

/**
 * Map embedded prepared JSON to the ``hitl`` query string the server
 * would use. Must match ``app.py``:
 * ``prepared_dict["human_in_the_loop"] = hitl.lower() != "false"``.
 * Default to ``"true"`` (same as FastAPI's default for ``/singlecorpus``)
 * so a full page reload does not strip Split/Merge/Reverse.
 */
function _tveHitlParamFromVisJson(vis: unknown): "true" | "false" {
  if (vis == null) return "true";
  if (typeof vis === "string") {
    try {
      const p = JSON.parse(vis) as { human_in_the_loop?: boolean };
      return p.human_in_the_loop === false ? "false" : "true";
    } catch {
      return "true";
    }
  }
  if (typeof vis === "object" && vis !== null && "human_in_the_loop" in vis) {
    return (vis as { human_in_the_loop?: boolean }).human_in_the_loop === false
      ? "false"
      : "true";
  }
  return "true";
}

// If the user navigated to e.g. ``/singlecorpus`` without a ``?scenario=``
// query string, the legacy LDAvis.js code at module load time reads
// ``window.location.search`` to decide between "real visualization" and
// "tutorial mode". Backfill the query string from the server-rendered
// ``TVE_SCENARIO.name`` so the tutorial doesn't auto-fire on bare URLs.
// ``history.replaceState`` keeps the browser-bar URL coherent without
// adding a navigation entry. When we add ``hitl``, it must match the
// embedded ``human_in_the_loop`` field (or default ``true``), never
// ``false`` on its own, or a refresh would hide HITL controls.
if (scenario && scenario.name) {
  try {
    const params = new URLSearchParams(window.location.search);
    if (!params.has("scenario")) {
      params.set("scenario", scenario.name);
      if (!params.has("hitl")) {
        params.set("hitl", _tveHitlParamFromVisJson(scenario.visJson));
      }
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

// After server restart, the session cookie may not match in-memory state.
// Send the page scenario name on every XHR/fetch so POST endpoints can
// re-attach a single- or multi-corpus scenario the same way as GET /singlecorpus.
const TVE_SCENARIO_HEADER = "X-TVE-Scenario";
function _tveScenarioHeaderValue(): string | null {
  const s = w.TVE_SCENARIO;
  if (s && typeof s.name === "string" && s.name) {
    return s.name;
  }
  return null;
}
if (typeof $.ajaxSetup === "function") {
  $.ajaxSetup({
    beforeSend(jqXHR) {
      const v = _tveScenarioHeaderValue();
      if (v) {
        jqXHR.setRequestHeader(TVE_SCENARIO_HEADER, v);
      }
    },
  });
}
if (typeof w.fetch === "function") {
  const origFetch = w.fetch.bind(w);
  w.fetch = function tveFetch(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> {
    const v = _tveScenarioHeaderValue();
    if (!v) {
      return origFetch(input, init);
    }
    const next: RequestInit = { ...init, headers: new Headers(init?.headers) };
    const h = next.headers as Headers;
    if (!h.has(TVE_SCENARIO_HEADER)) {
      h.set(TVE_SCENARIO_HEADER, v);
    }
    return origFetch(input, next);
  };
}

export {};
