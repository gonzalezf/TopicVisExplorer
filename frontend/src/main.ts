/**
 * TopicVisExplorer browser entry point.
 *
 * Loads the vendor globals first, then the legacy visualization modules
 * (LDAvis, sankey, topicflow) which all assume those globals are on
 * `window`. Finally pulls in the merged stylesheet which
 * Vite emits as `tve.css`.
 *
 * The resulting bundle is consumed by the FastAPI server through the new
 * `index_v1.html` template, which references `/dist/tve.js` and
 * `/dist/tve.css` — replacing the dozen-or-so individual <script> tags
 * the paper version had.
 */

import "./vendor";
// IMPORTANT: must run before any legacy import. The legacy files reference
// `type_vis`, `jsonData`, etc. at module top-level; if those aren't on
// `window` yet the bundle throws and `window.TVE` never gets exported.
import "./scenario_globals";
import "./styles/main.scss";

// Legacy visualisation code, vendored verbatim from the paper version to
// guarantee visual parity. These files contain the actual D3 rendering for
// the topic scatter plot, term-relevance bar chart, sankey diagram, and the
// human-in-the-loop UI bindings.
import "./legacy/sankey.js";
import "./legacy/topicflow.js";
import "./legacy/highlight.js";
import "./legacy/LDAvis.js";

// Phase 4f: collapsible coherence panel. Self-installs on
// DOMContentLoaded; closed by default so it does not perturb the
// visual baseline. See ``./coherence_panel.ts`` for the contract
// (GET /coherence -> table).
import "./coherence_panel";

// `LDAvis` is a constructor that the legacy script registers as a global
// (in legacy land, via `window.LDAvis = ...`). Vite scopes module-level
// `var` declarations to the module, so the legacy file does not pollute the
// global scope automatically. We re-export it here for any TS consumers.
export const LDAvis = (window as any).LDAvis;

// Construct the visualisation once the DOM is ready. Globals are already
// installed by `scenario_globals.ts` (which had to run before the legacy
// imports), so this function only handles the actual instantiation.
function bootstrap(): void {
  const scenario = window.TVE_SCENARIO;
  if (!scenario) {
    return;
  }
  const LDAvisCtor = (window as any).LDAvis;
  if (typeof LDAvisCtor === "function") {
    new LDAvisCtor(`#${scenario.visid}`, scenario.visJson);
  } else {
    console.error("[TopicVisExplorer] LDAvis constructor missing from bundle");
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
