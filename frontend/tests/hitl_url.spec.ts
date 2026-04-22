/**
 * HITL (human-in-the-loop): URL backfill for bare /singlecorpus must not
 * set hitl=false when the server embedded human_in_the_loop: true, or
 * a refresh removes Split / Merge / Reverse.
 */
import { expect, test } from "@playwright/test";

test.describe("HITL URL sync", () => {
  test("bare /singlecorpus backfills hitl to match embedded data (not false)", async ({
    page,
  }) => {
    await page.goto("/singlecorpus", { waitUntil: "networkidle" });

    const u = new URL(page.url());
    expect(u.searchParams.get("hitl"), "backfilled hitl must not be false").not.toBe("false");
    expect(u.searchParams.get("scenario")).toBeTruthy();

    const tve = await page.evaluate(() => (window as unknown as { TVE?: unknown }).TVE);
    expect(tve, "TVE bundle loaded").toBeDefined();

    const splitVisible = await page
      .locator('[id$="-split"]')
      .first()
      .isVisible()
      .catch(() => false);
    expect(
      splitVisible,
      "Split topic control should be visible when HITL is on (default single-corpus)",
    ).toBe(true);

    await page.reload({ waitUntil: "networkidle" });
    const splitAfter = await page
      .locator('[id$="-split"]')
      .first()
      .isVisible()
      .catch(() => false);
    expect(splitAfter, "After refresh, HITL controls should still be present").toBe(
      true,
    );
  });
});
