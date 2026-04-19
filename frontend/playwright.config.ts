/**
 * Playwright configuration for TopicVisExplorer visual regression tests.
 *
 * The suite spins up a real FastAPI server (via the bundled Uvicorn
 * launcher) and a headless Chromium that loads each demo scenario.
 * Screenshots are diffed against committed baselines under
 * `tests/__screenshots__/`. A baseline drift greater than the
 * `maxDiffPixelRatio` threshold fails the build, which is the actual
 * gate that protects the paper-version visual identity claim.
 *
 * Update baselines after intentional UI changes with::
 *
 *     npm run test:visual:update
 */

import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.TVE_E2E_BASE_URL ?? "http://127.0.0.1:8765";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false, // Single backend process; avoid session contention.
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    viewport: { width: 1440, height: 900 },
    // Disable animations + smooth transitions so screenshots are stable.
    launchOptions: {
      args: ["--force-prefers-reduced-motion"],
    },
  },
  expect: {
    toHaveScreenshot: {
      // 0.5% pixel drift tolerance: tighter than typical Playwright
      // defaults (1%) because visual parity with the reviewed paper
      // figures is a hard requirement for v1.0.
      maxDiffPixelRatio: 0.005,
      animations: "disabled",
    },
  },
  projects: [
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // Boot a dedicated TVE server for the visual tests. The Python
    // launcher script lives under frontend/scripts/ so this config
    // doesn't depend on a globally installed `tve` CLI.
    command: "python3 frontend/scripts/serve_for_visual_tests.py",
    cwd: "..",
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: {
      TVE_E2E_PORT: BASE_URL.split(":").pop() ?? "8765",
    },
  },
});
