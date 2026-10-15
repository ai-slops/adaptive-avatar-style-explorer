import { test, expect } from "@playwright/test";

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=",
  "base64",
);

test("offline design, evidence, prompt and handoff round trip", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/#launch=browser-test");
  await page.getByLabel("Project name").fill("Astronomer");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await page.getByRole("button", { name: "Add your first design" }).click();
  await page.getByLabel("Design name").fill("Silver traveller");
  await page.getByLabel("Character structure").selectOption("humanoid");
  await page
    .getByLabel("Character idea")
    .fill("Silver hair, rounded silhouette and layered travelling clothes.");
  await page.getByRole("button", { name: "Create design direction" }).click();
  await expect(
    page.getByRole("heading", { name: "What defines this character" }),
  ).toBeVisible();
  await page
    .locator("input[type=file]")
    .setInputFiles({
      name: "reference.png",
      mimeType: "image/png",
      buffer: png,
    });
  await page.getByRole("button", { name: "Review evidence" }).click();
  await page.getByLabel("Observed view").selectOption("front");
  await page.getByLabel("Observed framing").selectOption("full_body");
  await page.getByLabel("Observed projection").selectOption("orthographic");
  await page.getByLabel("Pose", { exact: true }).fill("neutral");
  await page.getByLabel("Expression", { exact: true }).fill("neutral");
  await page.getByLabel("Lighting", { exact: true }).fill("neutral");
  await page.getByLabel("Background", { exact: true }).fill("plain");
  await page.getByRole("button", { name: "Publish assessment" }).click();
  await expect(page.getByText("25%", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "04 Prompt workspace" }).click();
  await page.getByRole("button", { name: "Prepare text prompt" }).click();
  await expect(page.locator("pre")).toContainText("NO REDESIGN");
  await expect(page.locator("pre")).toContainText("Silver hair");
  await page.getByRole("button", { name: "05 3D handoff" }).click();
  await page
    .getByLabel("Checkpoint stage")
    .selectOption("reference_handoff_ready");
  await page
    .getByLabel("Accepted gaps and tradeoffs")
    .fill("Profiles and back remain missing; handoff is a starting brief.");
  await page.getByRole("button", { name: "Confirm checkpoint" }).click();
  await expect(
    page.getByText("Checkpoint recorded.", { exact: false }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export 3D design handoff" }).click();
  expect((await download).suggestedFilename()).toBe(
    "avatar-design-handoff.zip",
  );
  await page.screenshot({
    path: "/tmp/style-explorer-desktop.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: /Explore designs/ }).click();
  await expect(
    page.getByRole("heading", { name: "Find your character." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "/tmp/style-explorer-mobile.png",
    fullPage: true,
  });
});
