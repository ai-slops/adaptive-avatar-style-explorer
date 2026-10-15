import { test, expect, type Page } from "@playwright/test";

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=",
  "base64",
);

async function advanced(page: Page) {
  const tools = page.locator(".advanced-tools");
  if (!(await tools.getAttribute("open"))) {
    if (!(await tools.evaluate((e) => (e as HTMLDetailsElement).open)))
      await tools.locator("summary").first().click();
  }
}
async function managedProject(page: Page, title: string) {
  await page.getByRole("button", { name: "＋ 새 탐색", exact: true }).click();
  await page
    .getByText("이름이나 떠오르는 생각이 있나요? 선택 사항", { exact: true })
    .click();
  await page.getByLabel("탐색 이름", { exact: true }).fill(title);
  await page
    .getByText("직접 설계하거나 기존 도구 사용", { exact: true })
    .click();
  await page
    .getByRole("button", { name: "고급 작업 도구 열기", exact: true })
    .click();
  await advanced(page);
}

test("offline design, evidence, prompt and handoff round trip", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/#launch=browser-test");
  await managedProject(page, "Astronomer");
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
  await managedProject(page, "Matched comparison");
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
  await advanced(page);
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

test("native Codex connection, generation and unreviewed evidence round trip", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://127.0.0.1:8767/#launch=codex-browser-test");
  await expect(
    page.getByText("개인 Codex 생성", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "설정", exact: true }).click();
  await expect(page.getByText("연결됨", { exact: false })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Continue with ChatGPT" }),
  ).toHaveCount(0);
  await advanced(page);
  await page.getByRole("button", { name: "01 Explore designs" }).click();
  await managedProject(page, "Codex generation");
  await page.getByRole("button", { name: "Add your first design" }).click();
  await page.getByLabel("Design name").fill("Moon traveller");
  await page.getByLabel("Character structure").selectOption("humanoid");
  await page
    .getByLabel("Character idea")
    .fill("Friendly silver-haired traveller with blue clothes.");
  await page.getByRole("button", { name: "Create design direction" }).click();
  await page.getByRole("button", { name: "04 Prompt workspace" }).click();
  await page.getByLabel("Requested view").selectOption("front");
  await page.getByRole("button", { name: "Prepare text prompt" }).click();
  await expect(page.getByLabel("Codex 모델")).toHaveValue("test-model");
  await page.getByRole("button", { name: "Codex로 이미지 1장 생성" }).click();
  await expect(
    page.getByAltText("Codex 생성 이미지 · 검토 대기"),
  ).toBeVisible();
  await expect(
    page.getByText("생성 완료 · 검토 대기", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "/tmp/style-explorer-codex-browser.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "생성 이미지 검토" }).click();
  await expect(
    page.getByRole("button", { name: "Review evidence →", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("article").getByText("unreviewed", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await advanced(page);
  await expect(
    page.getByText("개인 Codex 생성", { exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("first browser connection remembers the plain URL and supports explicit sign-out", async ({
  page,
  context,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "이 브라우저를 연결해 주세요." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "이 기기에서 워크스페이스 열기" }),
  ).toBeVisible();
  await page
    .getByText("창이 열리지 않거나 다른 브라우저를 사용하시나요?")
    .click();
  await page
    .getByLabel("최초 연결 링크", { exact: true })
    .fill("http://127.0.0.1:8766/#launch=browser-test");
  await page
    .getByRole("button", { name: "이 브라우저 연결하고 기억하기" })
    .click();
  await expect(
    page.getByRole("button", { name: "설정", exact: true }),
  ).toBeVisible();
  expect(new URL(page.url()).hash).toBe("");
  const cookie = (await context.cookies()).find(
    (c) => c.name === "avatar_session",
  )!;
  expect(cookie.httpOnly).toBe(true);
  expect(cookie.sameSite).toBe("Strict");
  expect(cookie.expires - Date.now() / 1000).toBeGreaterThan(29 * 86400);
  const otherTab = await context.newPage();
  await otherTab.goto("/");
  await expect(
    otherTab.getByRole("button", { name: "설정", exact: true }),
  ).toBeVisible();
  await otherTab.close();
  await page.getByRole("button", { name: "설정", exact: true }).click();
  await expect(
    page.getByLabel("이 브라우저를 30일 동안 기억하기"),
  ).toBeChecked();
  await page.getByRole("button", { name: "이 브라우저 로그아웃" }).click();
  await expect(
    page.getByRole("heading", { name: "이 브라우저를 연결해 주세요." }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "이 브라우저를 연결해 주세요." }),
  ).toBeVisible();
  // A launch link can change only the fragment of the already-open page.
  await page.goto("/#launch=browser-test");
  await expect(
    page.getByRole("button", { name: "설정", exact: true }),
  ).toBeVisible();
  expect(new URL(page.url()).hash).toBe("");
});

test("canonical editor adopts relationships and sources without losing typed values or history", async ({
  page,
}) => {
  page.setDefaultTimeout(5000);
  await page.goto("/#launch=browser-test");
  await expect(
    page.getByRole("button", { name: "설정", exact: true }),
  ).toBeVisible();
  const session = await (await page.request.get("/api/session")).json();
  const headers = {
    origin: "http://127.0.0.1:8766",
    "x-csrf-token": session.csrfToken,
  };
  const project = await (
    await page.request.post("/api/projects", {
      headers,
      data: { title: "Canonical construction" },
    })
  ).json();
  const base = `/api/projects/${project.project_id}`;
  const original = await (
    await page.request.post(base + "/designs", {
      headers,
      data: {
        title: "Layered traveller",
        spec: {
          morphology: "humanoid",
          properties: {
            "design.description": {
              value: "A travelling astronomer",
              state: "proposed",
              notes: "Keep the original decision provenance",
            },
            "body.head_ratio": { value: 0.18, state: "proposed" },
            "face.blink_capability": { value: true, state: "proposed" },
            "outfit.layers": { value: ["tunic", "cape"], state: "proposed" },
          },
        },
      },
    })
  ).json();
  const asset = await (
    await page.request.post(base + "/assets", { headers, data: png })
  ).json();
  const depiction = await (
    await page.request.post(base + "/depictions", {
      headers,
      data: { assetId: asset.assetId },
    })
  ).json();
  const source = await (
    await page.request.post(base + "/depiction-links", {
      headers,
      data: {
        depictionId: depiction.depictionId,
        versionId: original.version_id,
      },
    })
  ).json();
  const events = await (await page.request.get(base + "/events")).json();
  const decision = events.find(
    (event: { sequence: number }) =>
      event.sequence === original.created_sequence,
  ).event_id;
  await page.reload();
  await advanced(page);
  await page
    .getByRole("combobox", { name: "프로젝트", exact: true })
    .selectOption(project.project_id);
  await page.getByRole("button", { name: "03 Design & evidence" }).click();
  await page
    .getByRole("combobox", { name: "Design version" })
    .selectOption(original.version_id);
  await page.getByRole("button", { name: "Revise design" }).click();
  const editor = page.getByRole("dialog");
  await editor
    .getByRole("textbox", { name: "Character idea", exact: true })
    .fill("A travelling astronomer with chosen layered clothing");
  await editor.getByLabel("body.head_ratio value", { exact: true }).fill("0.2");
  await editor
    .getByLabel("face.blink_capability value", { exact: true })
    .selectOption("false");
  const layers = editor.getByRole("group", {
    name: "outfit · layers",
    exact: true,
  });
  const layerValue = layers.getByLabel("outfit.layers value", { exact: true });
  await layerValue.press("ControlOrMeta+End");
  await layerValue.press("Enter");
  await layerValue.pressSequentially("lining");
  await layers.getByText("Notes & sources", { exact: true }).click();
  await layers
    .getByLabel("outfit.layers notes", { exact: true })
    .fill("Separate cloth layers; source is inspiration, not geometry proof.");
  await layers
    .getByRole("group", { name: "outfit.layers source images", exact: true })
    .getByRole("checkbox")
    .check();
  await layers
    .getByRole("group", {
      name: "outfit.layers supporting decisions",
      exact: true,
    })
    .getByRole("checkbox", {
      name: `#${original.created_sequence} · adopt variant`,
      exact: true,
    })
    .check();
  await editor
    .getByRole("button", { name: "Add component relationship" })
    .click();
  await editor
    .getByLabel("Relationship 1 component", { exact: true })
    .fill("cape");
  await editor
    .getByLabel("Relationship 1 relation", { exact: true })
    .selectOption("layered_over");
  await editor
    .getByLabel("Relationship 1 target", { exact: true })
    .fill("tunic");
  await editor
    .getByLabel("Relationship 1 state", { exact: true })
    .selectOption("user_confirmed");
  const unresolved = editor.getByLabel("Unresolved design decisions", {
    exact: false,
  });
  await unresolved.fill("Rear clasp construction");
  await unresolved.press("End");
  await unresolved.press("Enter");
  await unresolved.pressSequentially("Hair attachment thickness");
  await editor
    .getByLabel("Why this design changes")
    .fill("Choose layered construction while keeping hidden attachments open");
  await editor.getByRole("button", { name: "Publish new revision" }).click();
  await expect(editor).toHaveCount(0);
  const designs = await (await page.request.get(base + "/designs")).json();
  const revised = designs[0].versions[0];
  expect(designs[0].versions[1].spec).toEqual(original.spec);
  expect(revised.spec.properties["body.head_ratio"].value).toBe(0.2);
  expect(revised.spec.properties["face.blink_capability"].value).toBe(false);
  expect(revised.spec.properties["outfit.layers"].value).toEqual([
    "tunic",
    "cape",
    "lining",
  ]);
  expect(
    revised.spec.properties["outfit.layers"].sourceDepictionLinkIds,
  ).toEqual([source.linkId]);
  expect(revised.spec.properties["outfit.layers"].sourceEventIds).toEqual([
    decision,
  ]);
  expect(revised.spec.properties["design.description"].notes).toBe(
    original.spec.properties["design.description"].notes,
  );
  expect(revised.spec.componentRelations).toEqual([
    {
      component: "cape",
      relation: "layered_over",
      target: "tunic",
      state: "user_confirmed",
    },
  ]);
  expect(revised.spec.unresolvedDecisions).toEqual([
    "Rear clasp construction",
    "Hair attachment thickness",
  ]);
});
