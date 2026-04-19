/**
 * Vite build configuration for the TopicVisExplorer frontend.
 *
 * Why a custom config?
 *
 *   1. The Python wheel (src/topicvisexplorer/web/dist/) needs deterministic
 *      filenames so the Jinja template can reference `tve.js` / `tve.css`
 *      directly without a manifest lookup. We therefore disable hashing and
 *      use a library-style build for the JS entry while emitting CSS to a
 *      predictable name.
 *
 *   2. The legacy code (LDAvis, topicflow, sankey, user_study_code) was
 *      written before module systems and assumes globals on `window`
 *      (jQuery, d3, _, noUiSlider, Mark, introJs, LDAvis, ...). The vendor
 *      entry attaches them to `window` so the legacy modules continue to
 *      work without modification, preserving visual + behavioural parity.
 *
 *   3. The dev server (`npm run dev`) serves the standalone fixture in
 *      `index.html` so a frontend developer can iterate on styles + JS
 *      without spinning up the FastAPI backend.
 */

import { defineConfig } from "vite";
import { resolve } from "node:path";

const PYTHON_WEB_DIST = resolve(__dirname, "../src/topicvisexplorer/web/dist");

export default defineConfig(({ mode }) => ({
  // Where the Python wheel expects the bundled assets to live.
  // We use library-mode IIFE so:
  //   * Unresolved identifiers in legacy code (e.g. `topic_order` referenced
  //     76 times in LDAvis.js but never declared there) fall through to
  //     `window` exactly the way they did under <script> tags.
  //   * The whole bundle becomes a single self-contained <script> tag, so
  //     the new index_v1.html template stays simple and cacheable.
  build: {
    outDir: PYTHON_WEB_DIST,
    emptyOutDir: true,
    sourcemap: mode === "development",
    cssCodeSplit: false,
    lib: {
      entry: resolve(__dirname, "src/main.ts"),
      name: "TVE",
      formats: ["iife"],
      fileName: () => "tve.js",
    },
    rollupOptions: {
      output: {
        // Single deterministic stylesheet name; everything else preserves
        // its extension under an `assets/` subfolder for fonts/images.
        assetFileNames: (info) => {
          if (info.name && info.name.endsWith(".css")) {
            return "tve.css";
          }
          return "assets/[name][extname]";
        },
        // Inline dynamic imports so we always emit a single tve.js.
        inlineDynamicImports: true,
      },
    },
    target: "es2018",
    minify: mode === "production" ? "esbuild" : false,
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
      "@legacy": resolve(__dirname, "src/legacy"),
    },
  },
  server: {
    port: 5173,
    open: false,
    fs: {
      // Allow serving files from the Python web/legacy directory so the dev
      // fixture can pull legacy assets (fonts, images) directly when needed.
      allow: [resolve(__dirname, ".."), resolve(__dirname, "../src")],
    },
  },
}));
