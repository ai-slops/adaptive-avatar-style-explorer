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
  await page.locator("input[type=file]").setInputFiles({
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

test("matched visual comparison records only the shown scoped evidence", async ({
  page,
}) => {
  await page.goto("/#launch=browser-test");
  await page.getByRole("button", { name: "New project", exact: false }).click();
  await page.getByLabel("Project name").fill("Matched comparison");
  await page.getByRole("button", { name: "Create workspace" }).click();
  const session = await (await page.request.get("/api/session")).json();
  const headers = {
    origin: "http://127.0.0.1:8766",
    "x-csrf-token": session.csrfToken,
  };
  const projects = await (await page.request.get("/api/projects")).json();
  const project = projects.find(
    (p: { title: string }) => p.title === "Matched comparison",
  ).project_id;
  const base = `/api/projects/${project}`;
  const ids: string[] = [];
  for (const [title, amount, color] of [
    ["Soft hair", 0.2, "#a0b0a0"],
    ["Full hair", 0.8, "#b08060"],
  ] as const) {
    const version = await (
      await page.request.post(base + "/designs", {
        headers,
        data: {
          title,
          spec: {
            morphology: "humanoid",
            properties: { "hair.color": { value: color, state: "proposed" } },
          },
        },
      })
    ).json();
    ids.push(version.version_id);
    const bytes = await page.evaluate((color) => {
      const canvas = document.createElement("canvas");
      canvas.width = 16;
      canvas.height = 24;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = color;
      ctx.fillRect(0, 0, 16, 24);
      return canvas.toDataURL().split(",")[1];
    }, color);
    const asset = await (
      await page.request.post(base + "/assets", {
        headers,
        data: Buffer.from(bytes, "base64"),
      })
    ).json();
    const depiction = await (
      await page.request.post(base + "/depictions", {
        headers,
        data: { assetId: asset.assetId },
      })
    ).json();
    const link = await (
      await page.request.post(base + "/depiction-links", {
        headers,
        data: {
          depictionId: depiction.depictionId,
          versionId: version.version_id,
        },
      })
    ).json();
    const state = (await (await page.request.get("/api/projects")).json()).find(
      (p: { project_id: string }) => p.project_id === project,
    );
    const reviewed = await page.request.post(base + "/evidence-reviews", {
      headers,
      data: {
        linkId: link.linkId,
        status: "compatible",
        reviewedRegions: ["hair"],
        observations: [
          {
            region: "hair",
            attributes: {
              "hair.volume": {
                value: amount,
                confidence: 0.9,
                visibility: "visible",
              },
            },
            observedPresentation: {
              view: "front",
              projection: "orthographic",
              framing: "full_body",
              poseId: "neutral",
              expressionId: "neutral",
            },
          },
        ],
        expectedEventSequence: state.event_sequence,
      },
    });
    expect(reviewed.ok()).toBe(true);
  }
  await page.reload();
  await page.getByRole("button", { name: /02 Compare/ }).click();
  await page
    .getByRole("combobox", { name: "Design A", exact: true })
    .selectOption(ids[0]);
  await page
    .getByRole("combobox", { name: "Design B", exact: true })
    .selectOption(ids[1]);
  await page.getByRole("button", { name: "Seal this comparison" }).click();
  await expect(
    page.getByText(
      "This matched, scoped comparison can inform visual preference learning.",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Choose A", exact: true }).click();
  await expect(
    page.getByText("Decision saved with the exact evidence shown."),
  ).toBeVisible();
  const preferences = await (
    await page.request.get(base + "/preferences")
  ).json();
  expect(preferences.models.hair.effectiveWeight).toBe(1);
  expect(Object.keys(preferences.models)).toEqual(["hair"]);
  await page.getByRole("button", { name: /01 Explore designs/ }).click();
  await page.screenshot({
    path: "/tmp/style-explorer-board.png",
    fullPage: true,
  });
});
