/**
 * Vendor entry point.
 *
 * Imports every third-party library the legacy code depends on and attaches
 * the ones that expect to live on `window` to the global scope. Order
 * matters because some libraries register jQuery plugins on import:
 *
 *   1. jQuery is needed before Bootstrap and bootstrap-table.
 *   2. Popper is needed before Bootstrap tooltips/popovers.
 *   3. d3 is needed before topicflow/sankey extend `d3.sankey`.
 *
 * After this module finishes, `window.$`, `window.d3`, `window._`,
 * `window.noUiSlider`, `window.Mark`, `window.introJs`, and `window.Popper`
 * are all available, mirroring the script-tag world the legacy code was
 * originally written against.
 */

import $ from "jquery";
import * as d3Module from "d3";
import _ from "lodash";
import noUiSlider from "nouislider";
import Mark from "mark.js";
import introJs from "intro.js";
import Popper from "popper.js";

// The ESM namespace returned by `import * as d3` is frozen by the bundler,
// so legacy plugins that mutate it (sankey.js does `d3.sankey = ...`,
// topicflow.js extends a couple of helpers) throw "object is not
// extensible". Shallow-copy into a plain mutable object that quacks like
// the original d3 v5 global. Property identities are preserved so anything
// the legacy code holds a reference to keeps working.
const d3: Record<string, any> = { ...d3Module };
// D3 v5 sets d3.event on the *module namespace* during dispatch; the copy
// above would keep a stale null. Proxy reads so legacy d3.event.stopPropagation() works.
Object.defineProperty(d3, "event", {
  configurable: true,
  get() {
    return (d3Module as any).event;
  },
});

window.$ = $;
window.jQuery = $;
window.d3 = d3;
window._ = _;
window.noUiSlider = noUiSlider;
window.Mark = Mark;
window.introJs = introJs;
window.Popper = Popper;

// Hotjar tracker stub. The original paper's user-study deployment loaded
// the Hotjar snippet in the page <head>, which exposed `window.hj` as the
// event-recorder function. The library version of TopicVisExplorer does
// not (and must not) ship analytics, but the legacy LDAvis.js calls
// `window.hj('identify', ...)` at module top-level, so we install a no-op
// to keep the bundle from throwing on load.
if (typeof (window as any).hj !== "function") {
  (window as any).hj = function noopHj(): void {
    /* analytics disabled in the open-source library */
  };
}

// jQuery plugins / Bootstrap depend on jQuery being on `window` first.
import "bootstrap";
// bootstrap-table also depends on jQuery + Bootstrap being initialised.
import "bootstrap-table";

export { $, d3, _, noUiSlider, Mark, introJs, Popper };
