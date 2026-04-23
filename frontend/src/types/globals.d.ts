/**
 * Ambient type declarations for globals consumed by the legacy paper-version
 * code (LDAvis.js, topicflow.js, sankey.js).
 *
 * These files predate ES modules and reference jQuery / d3 / lodash / etc.
 * directly on `window`. We intentionally keep them as `any` because the
 * goal of the v1.0 frontend bundle is *byte-for-byte equivalent visual
 * output*, not a full TypeScript port. Refactoring will happen in v1.x.
 */

declare global {
  interface Window {
    // Vendor globals attached by `src/vendor.ts`.
    $: any;
    jQuery: any;
    d3: any;
    _: any;
    noUiSlider: any;
    Mark: any;
    introJs: any;
    Popper: any;

    // Globals defined by the legacy LDAvis / topicflow / sankey bundles.
    LDAvis: any;
    LDAvis_load_lib: (url: string, cb: () => void) => void;

    // Server-rendered scenario state injected by Jinja in index_v1.html.
    TVE_SCENARIO?: {
      /** DOM id of the LdaVis mount node (e.g. `vis-sess-...`) */
      visid: string;
      /** Optional alias for older or forked templates */
      visidStr?: string;
      visidRaw: string;
      visJson: any;
      typeVis: number;
      topicOrder: any;
      newCirclePositions?: any;
      matrixSankey?: any;
      visJson2?: any;
      topicOrder2?: any;
      d3Url: string;
      ldavisUrl: string;
      ldavisCssUrl: string;
    };
  }
}

export {};
