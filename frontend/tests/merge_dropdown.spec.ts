/**
 * Regression: merge partner <select> must not contain blank or
 * HTML-parsed-empty option labels (D3 name init + sanitize + .text()).
 */
import { expect, test } from "@playwright/test";

test.describe("merge modal partner list", () => {
  test("every merge option has non-empty visible label (20ng_tiny)", async ({
    page,
  }) => {
    test.setTimeout(90_000);

    await page.goto("/singlecorpus?scenario=20ng_tiny&hitl=true", {
      waitUntil: "domcontentloaded",
    });

    await page
      .locator("circle.dot")
      .first()
      .waitFor({ state: "visible", timeout: 60_000 });

    const dots = page.locator("circle.dot");
    const n = await dots.count();
    expect(n, "expected multiple topic circles").toBeGreaterThan(1);

    // Topic labels sit as SVG <text> on top of circles; force bypasses hit-testing.
    await dots.nth(1).click({ force: true });

    await page.locator('[id$="-merge"]').first().click();

    const modal = page.locator("#MergeModal_new_design");
    await modal.waitFor({ state: "visible", timeout: 15_000 });

    const options = modal.locator("#selectTopicMerge option");
    const count = await options.count();
    expect(count, "merge partner list should have at least one option").toBeGreaterThan(
      0,
    );

    for (let i = 0; i < count; i++) {
      const raw = await options.nth(i).innerText();
      const t = raw.replace(/[\u200B-\u200D\uFEFF]/g, "").replace(/\u00A0/g, " ").trim();
      expect(t.length, `option index ${i} must have visible text, got ${JSON.stringify(raw)}`).toBeGreaterThan(0);
    }
  });
});
