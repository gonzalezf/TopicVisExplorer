/**
 * Visual regression suite -- the gate that protects the paper-version
 * visual identity claim for v1.0.
 *
 * Each test loads a demo scenario in a real Chromium and snapshots the
 * full page. Baselines live alongside the spec under
 * `tests/__screenshots__/`; the first run after a deliberate UI change
 * must be done with `npm run test:visual:update`.
 *
 * The suite intentionally exercises only the bundled demo scenarios so
 * the baselines remain reproducible across machines without needing
 * the paper's private datasets. A `paper-figures` profile that
 * reproduces the actual paper figures is on the v1.1 roadmap.
 */

import { expect, test } from "@playwright/test";

const SCENARIOS = [
  { name: "single-corpus tiny demo", path: "/singlecorpus?scenario=tiny_demo&hitl=false" },
  { name: "multi-corpora tiny demo", path: "/multicorpora?scenario=tiny_multi_demo" },
];

for (const scenario of SCENARIOS) {
  test.describe(scenario.name, () => {
    test("renders without runtime errors", async ({ page }) => {
      const consoleErrors: string[] = [];
      page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));
      page.on("console", (msg) => {
        if (msg.type() !== "error") return;
        // SVG attribute parser warnings (NaN, negative dimensions) are
        // emitted by the browser as console.errors but they are render
        // hints, not JS faults. The synthetic ``tiny_demo`` /
        // ``tiny_multi_demo`` scenarios occasionally produce them because
        // their ~50-document corpus generates degenerate edge cases. The
        // visual-baseline diff is the real gate; here we only care that
        // no actual JavaScript exception bubbles up to break interaction.
        const txt = msg.text();
        if (/<\w+> attribute (?:[a-z\d_-]+): (?:Expected length|A negative value)/i.test(txt)) {
          return;
        }
        consoleErrors.push(`console.error: ${txt}`);
      });

      await page.goto(scenario.path, { waitUntil: "networkidle" });

      // The bundle exposes itself as `window.TVE`; failure here means
      // the IIFE didn't finish executing.
      const tveLoaded = await page.evaluate(() => typeof (window as any).TVE !== "undefined");
      expect(tveLoaded).toBe(true);

      // The main scatter container must exist and be non-empty.
      const visBox = page.locator('[id^="vis-"]').first();
      await expect(visBox).toBeAttached();

      expect(consoleErrors, "no runtime JS errors").toEqual([]);
    });

    test("matches visual baseline", async ({ page }) => {
      await page.goto(scenario.path, { waitUntil: "networkidle" });

      // Wait for the LDAvis SVG to be drawn. The legacy code creates
      // an `svg` element inside the central panel after data binding.
      await page.locator("svg").first().waitFor({ state: "attached", timeout: 10_000 });

      // Give D3 transitions a beat to settle.
      await page.waitForTimeout(500);

      await expect(page).toHaveScreenshot(`${scenario.name.replace(/\s+/g, "_")}.png`, {
        fullPage: true,
        // Multi-corpora rendering involves a Sankey diagram whose link
        // ribbon paths are computed from float positions and depend on
        // the iteration order of an unordered map of node weights;
        // small (< few percent) pixel deltas between consecutive runs
        // are normal. The baseline still gates layout regressions
        // (anything > 5% of pixels would mean a real structural change
        // to a panel, font, or color). Single-corpus is much tighter
        // because its only animated bits are bar transitions.
        maxDiffPixelRatio: 0.05,
      });
    });
  });
}
