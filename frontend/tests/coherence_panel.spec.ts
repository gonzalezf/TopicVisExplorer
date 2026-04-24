/**
 * Phase 4f: Playwright tests for the collapsible coherence panel.
 *
 * The panel ships **closed by default** so the v0.1 visual baseline
 * survives. These tests cover the open-state behaviour:
 *
 *  1. Toggle button is present in single-corpus mode and absent in
 *     multi-corpus mode (the latter is deferred to v1.1; the
 *     {% if type_vis == 1 %} guard in index_v1.html is the contract).
 *  2. Clicking the toggle reveals the body, fetches /coherence, and
 *     renders one row per topic.
 *  3. Clicking the toggle a second time collapses the body again.
 */

import { expect, test } from "@playwright/test";

const SINGLE = "/singlecorpus?scenario=tiny_demo&hitl=false";
const MULTI = "/multicorpora?scenario=tiny_multi_demo";

test.describe("coherence panel", () => {
  test("toggle button absent in multi-corpus mode", async ({ page }) => {
    await page.goto(MULTI, { waitUntil: "networkidle" });
    await page.locator("svg").first().waitFor({ state: "attached", timeout: 10_000 });
    await expect(page.locator("#TveCoherencePanelToggle")).toHaveCount(0);
  });

  test("toggle expands the panel and renders rows", async ({ page }) => {
    await page.goto(SINGLE, { waitUntil: "networkidle" });
    await page.locator("svg").first().waitFor({ state: "attached", timeout: 10_000 });

    const toggle = page.locator("#TveCoherencePanelToggle");
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    // Body is collapsed initially -- the `hidden` attribute is on
    // ``#TveCoherencePanelBody`` straight from the Jinja template.
    const body = page.locator("#TveCoherencePanelBody");
    await expect(body).toBeHidden();

    await toggle.click();

    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(body).toBeVisible();

    // /coherence is fetched lazily; wait for the table to populate.
    const tableRows = page.locator("#TveCoherenceTable tbody tr");
    await expect.poll(async () => await tableRows.count(), { timeout: 10_000 }).toBeGreaterThan(0);

    // Five columns: Topic, NPMI, C_v, Segregation, Coverage. Anything
    // else means the column model drifted and the renderer will be
    // misaligned.
    const firstRowCells = await tableRows.first().locator("td").count();
    expect(firstRowCells).toBe(5);

    // First column uses API ``labels`` (or live TVE names when set), not only ``Topic 1``.
    const firstLabel = await tableRows.first().locator("td").first().textContent();
    const t = firstLabel?.trim() ?? "";
    expect(t.length).toBeGreaterThan(0);
    expect(t).not.toMatch(/^Topic 1$/);
  });

  test("second click collapses the panel again", async ({ page }) => {
    await page.goto(SINGLE, { waitUntil: "networkidle" });
    await page.locator("svg").first().waitFor({ state: "attached", timeout: 10_000 });

    const toggle = page.locator("#TveCoherencePanelToggle");
    const body = page.locator("#TveCoherencePanelBody");

    await toggle.click();
    await expect(body).toBeVisible();

    await toggle.click();
    await expect(body).toBeHidden();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
  });
});
