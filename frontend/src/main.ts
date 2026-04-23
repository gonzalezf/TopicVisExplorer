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

function tveShowBootstrapError(message: string): void {
  const p = document.createElement("div");
  p.setAttribute("role", "alert");
  p.style.cssText =
    "margin:1rem;padding:1rem;background:#ffebee;border:1px solid #b71c1c;font:14px system-ui,Segoe UI,sans-serif;max-width:48rem;z-index:99999;position:relative;";
  p.textContent = message;
  document.body.prepend(p);
}

function tveD3IdSelector(plainId: string): string {
  if (typeof CSS !== "undefined" && typeof (CSS as any).escape === "function") {
    return "#" + (CSS as any).escape(plainId);
  }
  return "#" + plainId.replace(/([ !"#$%&'()*+,./:;<=>?@[\\\]^`{|}~])/g, "\\$&");
}

// Construct the visualisation once the DOM is ready. Globals are already
// installed by `scenario_globals.ts` (which had to run before the legacy
// imports), so this function only handles the actual instantiation.
function bootstrap(): void {
  const scenario = window.TVE_SCENARIO;
  if (!scenario) {
    return;
  }
  const raw = scenario.visid ?? (scenario as { visidStr?: string }).visidStr;
  const plainId = String(raw ?? "")
    .trim()
    .replace(/^#+/, "");
  if (!plainId) {
    const msg =
      "TopicVisExplorer: TVE_SCENARIO.visid is missing. The page must be served from the FastAPI app with index_v1.html so the vis root <div> and script agree.";
    console.error(msg);
    tveShowBootstrapError(msg);
    return;
  }
  const visRoot = document.getElementById(plainId);
  if (!visRoot) {
    const msg = `TopicVisExplorer: no element with id ${JSON.stringify(plainId)}. Check that the HTML has <div id=\"${plainId}\"> and hard-refresh (Ctrl+Shift+R) so the template and TVE_SCENARIO match.`;
    console.error(msg);
    tveShowBootstrapError(msg);
    return;
  }
  if (scenario.typeVis === 2) {
    const need = ["BarPlotPanel", "CentralPanel", "BarPlotPanel_2"] as const;
    for (const id of need) {
      if (!document.getElementById(id)) {
        const msg = `TopicVisExplorer: multicorpora page is missing #${id}. Rebuild the bundle (cd frontend && npm run build), run the server from this repo, and use a hard refresh.`;
        console.error(msg);
        tveShowBootstrapError(msg);
        return;
      }
    }
  } else if (scenario.typeVis === 1) {
    const need = ["BarPlotPanel", "CentralPanel", "DocumentsPanel"] as const;
    for (const id of need) {
      if (!document.getElementById(id)) {
        const msg = `TopicVisExplorer: page is missing #${id}. Rebuild, hard-refresh, and ensure the modern template is used.`;
        console.error(msg);
        tveShowBootstrapError(msg);
        return;
      }
    }
  }
  const LDAvisCtor = (window as any).LDAvis;
  if (typeof LDAvisCtor !== "function") {
    console.error("[TopicVisExplorer] LDAvis constructor missing from bundle");
    return;
  }
  try {
    new LDAvisCtor(tveD3IdSelector(plainId), scenario.visJson);
  } catch (err) {
    const text =
      err instanceof Error
        ? err.message
        : "TopicVisExplorer: visualization failed to start (see console).";
    console.error("[TopicVisExplorer] LDAvis failed:", err);
    tveShowBootstrapError(
      `TopicVisExplorer could not start: ${text} If the console mentions appendChild, the usual cause is a missing #CentralPanel or other layout #id, or a stale cached page.`,
    );
  }
}

function bootstrapSafe(): void {
  try {
    bootstrap();
  } catch (err) {
    const text =
      err instanceof Error
        ? err.message
        : "TopicVisExplorer: bootstrap failed (see console).";
    console.error("[TopicVisExplorer] bootstrap failed:", err);
    tveShowBootstrapError(
      `TopicVisExplorer could not start: ${text} If the console mentions appendChild, the usual cause is a missing #CentralPanel or other layout #id, or a stale cached page.`,
    );
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrapSafe);
} else {
  bootstrapSafe();
}
