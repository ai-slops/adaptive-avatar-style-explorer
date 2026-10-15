import { test, expect, type Page } from "@playwright/test";

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=",
  "base64",
);
// Drawn workflow fixtures: useful for framing/focus checks, not provider quality evidence.
async function fixtureImage(page: Page, color = "#568477") {
  const encoded = await page.evaluate((color) => {
    const canvas = document.createElement("canvas");
    canvas.width = 240;
    canvas.height = 400;
    const c = canvas.getContext("2d")!;
    c.fillStyle = "#f2f1e8";
    c.fillRect(0, 0, 240, 400);
    c.fillStyle = "#d9c3a6";
    c.beginPath();
    c.ellipse(120, 85, 38, 43, 0, 0, Math.PI * 2);
    c.fill();
    c.fillStyle = color;
    c.beginPath();
    c.ellipse(120, 60, 44, 29, 0, Math.PI, Math.PI * 2);
    c.fill();
    c.fillRect(79, 57, 11, 45);
    c.fillRect(150, 57, 11, 45);
    c.fillStyle = "#233e3a";
    c.fillRect(102, 82, 7, 8);
    c.fillRect(132, 82, 7, 8);
    c.strokeStyle = "#806854";
    c.lineWidth = 3;
    c.beginPath();
    c.arc(122, 103, 10, 0, Math.PI);
    c.stroke();
    c.fillStyle = color;
    c.beginPath();
    c.moveTo(84, 137);
    c.lineTo(156, 137);
    c.lineTo(184, 278);
    c.lineTo(56, 278);
    c.closePath();
    c.fill();
    c.fillStyle = "#f0d9a1";
    c.fillRect(116, 146, 9, 122);
    c.fillRect(71, 210, 101, 9);
    c.fillStyle = "#d9c3a6";
    c.fillRect(58, 157, 17, 95);
    c.fillRect(166, 157, 17, 95);
    c.fillStyle = "#596761";
    c.fillRect(85, 279, 26, 72);
    c.fillRect(129, 279, 26, 72);
    c.fillStyle = "#394b42";
    c.fillRect(72, 347, 40, 24);
    c.fillRect(128, 347, 40, 24);
    return canvas.toDataURL("image/png").split(",")[1];
  }, color);
  return Buffer.from(encoded, "base64");
}
const card = (page: Page) => page.locator(".discovery-board > .discovery-card");
async function state(page: Page) {
  const project = await page.locator("#project").inputValue();
  return (
    await page.request.get(
      `${new URL(page.url()).origin}/api/projects/${project}/discovery`,
    )
  ).json();
}
async function returnImages(page: Page, count?: number) {
  const s = await state(page);
  const round = s.rounds.find((r: any) => r.roundId === s.activeRoundId);
  const options = round.candidates.filter((c: any) => !c.image).slice(0, count);
  await page.getByLabel("결과 이미지 파일", { exact: true }).setInputFiles(
    await Promise.all(
      options.map(async (c: any, i: number) => ({
        name: c.returnName,
        mimeType: "image/png",
        buffer: await fixtureImage(page, i % 2 ? "#986b51" : "#568477"),
      })),
    ),
  );
  const dialog = page.getByRole("dialog", {
    name: "이미지 가져오기",
    exact: true,
  });
  await expect(dialog).toBeVisible();
  await dialog
    .getByRole("button", { name: `${options.length}장 가져오기`, exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  return round;
}
async function fresh(page: Page, native = false) {
  await page.goto(
    native
      ? "http://127.0.0.1:8767/#launch=codex-browser-test"
      : "/#launch=browser-test",
  );
  await page.getByRole("button", { name: "＋ 새 탐색", exact: true }).click();
}

test("community discovery completes feedback-informed second round and chooses without technical authoring", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const generationRequests: string[] = [];
  page.on("request", (req) => {
    if (/\/generate$/.test(req.url())) generationRequests.push(req.url());
  });
  await fresh(page);
  await page.getByRole("button", { name: "다양한 방향 탐색하기" }).click();
  await expect(card(page)).toHaveCount(2);
  await expect(
    card(page).first().getByRole("button", { name: "이런 방향 더 보기" }),
  ).toHaveCount(0);
  const pack = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "파일 묶음 내보내기", exact: true })
    .click();
  expect((await pack).suggestedFilename()).toBe("discovery-prompts.zip");
  const initial = await returnImages(page, 2);
  await expect(card(page).first().getByRole("img")).toBeVisible();
  await card(page)
    .nth(0)
    .getByRole("button", { name: "비교에 담기", exact: true })
    .click();
  await card(page)
    .nth(1)
    .getByRole("button", { name: "비교에 담기", exact: true })
    .click();
  await page.getByRole("button", { name: "담은 두 후보 비교" }).click();
  await expect(card(page)).toHaveCount(2);
  await page
    .getByRole("button", { name: "둘 다 더 탐색", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "2개 방향 저장됨" }),
  ).toBeVisible();
  const before = await state(page);
  expect(before.directions).toHaveLength(2);
  expect(before.rejected).toEqual([]);
  await page
    .getByRole("button", { name: "다음 프롬프트 준비", exact: true })
    .click();
  await expect(page.locator(".discovery-round-bar strong")).toHaveText(
    "2번째 후보 묶음",
  );
  await expect(card(page)).toHaveCount(2);
  const secondState = await state(page);
  const second = secondState.rounds[0];
  expect(
    second.candidates.slice(0, 2).map((c: any) => c.sourceCandidateId),
  ).toEqual(initial.candidates.slice(0, 2).map((c: any) => c.candidateId));
  expect(second.candidates).toHaveLength(2);
  expect(
    second.candidates[0].proposal.properties["hair.design"].value,
  ).not.toBe(initial.candidates[0].proposal.properties["hair.design"].value);
  await page.reload();
  await expect(card(page)).toHaveCount(2);
  expect((await state(page)).activeRoundId).toBe(second.roundId);
  await returnImages(page);
  await card(page).first().getByText("부분·다른 모습", { exact: true }).click();
  await card(page)
    .first()
    .getByRole("button", { name: "부분을 보존하거나 바꾸기", exact: true })
    .click();
  const refine = page.getByRole("dialog");
  await refine
    .getByRole("button", { name: "얼굴·턱 계속 보존", exact: true })
    .click();
  await expect(
    refine.getByRole("button", { name: "얼굴·턱 보존 해제", exact: true }),
  ).toBeVisible();
  await refine.getByLabel("바꿔 보고 싶은 부분").selectOption("hair");
  await refine.getByRole("button", { name: "이 범위로 대안 2개 준비" }).click();
  await expect(refine).not.toBeVisible();
  const focused = (await state(page)).rounds[0];
  expect(
    focused.candidates.every(
      (c: any) => c.preserveParts.includes("face") && c.varyPart === "hair",
    ),
  ).toBe(true);
  await returnImages(page);
  await card(page)
    .first()
    .getByRole("button", { name: "이 디자인 사용", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "내가 선택한 디자인", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("확인되지 않은 모습이 남아 있습니다.", { exact: false }),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "닫기", exact: true })
    .click();
  await page.reload();
  await expect(
    page.getByText("선택한 디자인:", { exact: false }),
  ).toBeVisible();
  const snapshot = (await state(page)).selection;
  await page
    .getByRole("button", { name: "다른 방향 탐색", exact: true })
    .click();
  expect((await state(page)).selection).toEqual(snapshot);
  expect((await state(page)).directions).toHaveLength(2);
  expect(generationRequests).toEqual([]);
  expect(errors).toEqual([]);
});

test("multiple inspirations start independent directions and ambiguous returns remain explicit", async ({
  page,
}) => {
  await fresh(page);
  await page.getByLabel("시작할 참고 이미지", { exact: true }).setInputFiles([
    {
      name: "forest.png",
      mimeType: "image/png",
      buffer: await fixtureImage(page),
    },
    {
      name: "space.png",
      mimeType: "image/png",
      buffer: await fixtureImage(page, "#565782"),
    },
  ]);
  await page
    .getByRole("button", { name: "각 참고자료에서 탐색 시작", exact: true })
    .click();
  await expect(card(page)).toHaveCount(2);
  await expect(card(page).first().getByRole("img")).toBeVisible();
  let s = await state(page);
  expect(
    new Set(s.rounds[0].candidates.map((c: any) => c.directionId)).size,
  ).toBe(2);
  expect(s.inspirations).toHaveLength(2);
  expect(s.directions).toHaveLength(0);
  await card(page)
    .first()
    .getByRole("button", { name: "이런 방향 더 보기", exact: true })
    .click();
  await page
    .getByRole("button", { name: "다음 프롬프트 준비", exact: true })
    .click();
  await expect(page.locator(".discovery-round-bar strong")).toHaveText(
    "2번째 후보 묶음",
  );
  await expect(card(page)).toHaveCount(2);
  await page
    .getByLabel("결과 이미지 파일", { exact: true })
    .setInputFiles({ name: "unknown.png", mimeType: "image/png", buffer: png });
  const dialog = page.getByRole("dialog", {
    name: "이미지 가져오기",
    exact: true,
  });
  await expect(
    dialog.getByRole("button", { name: "1장 가져오기", exact: true }),
  ).toBeDisabled();
  await dialog.getByLabel("잘 모르겠음 · 독립 참고자료").check();
  await dialog
    .getByRole("button", { name: "1장 가져오기", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  s = await state(page);
  expect(s.inspirations).toHaveLength(3);
  expect(s.rounds[0].candidates.every((c: any) => !c.image)).toBe(true);
});

test("native discovery uses bounded rounds, preserves slots and never resubmits on reload", async ({
  page,
}) => {
  await fresh(page, true);
  const submissions: string[] = [];
  page.on("request", (req) => {
    if (req.method() === "POST" && /\/generate$/.test(req.url()))
      submissions.push(req.url());
  });
  await page.getByRole("button", { name: "다양한 방향 탐색하기" }).click();
  await page
    .getByRole("button", { name: "제안한 후보 생성", exact: true })
    .click();
  let dialog = page.getByRole("dialog", {
    name: "이번 후보 생성 확인",
    exact: true,
  });
  // A finite two-option allowance is valid for a constrained generation budget.
  await dialog
    .getByRole("button", { name: "2회 요청하고 생성 시작", exact: true })
    .click();
  await expect(card(page).nth(0).getByRole("img")).toBeVisible();
  await expect(card(page).nth(1).getByRole("img")).toBeVisible();
  await expect(
    page.getByText("요청 처리 완료 · 2/2회 처리", { exact: true }),
  ).toBeVisible();
  const ids = await card(page).evaluateAll((nodes) =>
    nodes.map((n) => n.getAttribute("data-candidate")),
  );
  await card(page)
    .first()
    .getByRole("button", { name: "이런 방향 더 보기", exact: true })
    .click();
  await expect(card(page)).toHaveCount(2);
  expect(
    await card(page).evaluateAll((nodes) =>
      nodes.map((n) => n.getAttribute("data-candidate")),
    ),
  ).toEqual(ids);
  await page
    .getByRole("button", { name: "다음 후보 생성 준비", exact: true })
    .click();
  await page
    .getByRole("button", { name: "제안한 후보 생성", exact: true })
    .click();
  dialog = page.getByRole("dialog", {
    name: "이번 후보 생성 확인",
    exact: true,
  });
  await expect(
    dialog.getByRole("button", { name: "2회 요청하고 생성 시작", exact: true }),
  ).toBeDisabled();
  await dialog.getByLabel("표시된 참조 이미지 전송에 동의합니다").check();
  await dialog
    .getByRole("button", { name: "2회 요청하고 생성 시작", exact: true })
    .click();
  await expect(card(page).first().getByRole("img")).toBeVisible();
  await expect(card(page).nth(1).getByRole("img")).toBeVisible();
  const before = submissions.length;
  await page.reload();
  await expect(card(page).first().getByRole("img")).toBeVisible();
  expect(submissions.length).toBe(before);
});

test("discovery supports enlargement focus return and both viewport fixtures", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await fresh(page);
  await page.getByLabel("시작할 참고 이미지", { exact: true }).setInputFiles({
    name: "avatar.png",
    mimeType: "image/png",
    buffer: await fixtureImage(page),
  });
  await page
    .getByRole("button", { name: "각 참고자료에서 탐색 시작", exact: true })
    .click();
  const origin = card(page)
    .first()
    .getByRole("button", { name: /크게 보기/ });
  await origin.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(origin).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: "/tmp/discovery-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    card(page)
      .first()
      .getByRole("button", { name: "이런 방향 더 보기", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await origin.click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "닫기", exact: true })
    .click();
  await expect(origin).toBeFocused();
  await page.screenshot({ path: "/tmp/discovery-mobile.png", fullPage: true });
});

test("partial native results can retry only missing work, cancel, and retain browsing offline", async ({
  page,
}) => {
  await fresh(page, true);
  const origin = "http://127.0.0.1:8767";
  const configure = (data: object) =>
    page.request.post(origin + "/fixture/codex", { headers: { origin }, data });
  await configure({ failAt: 2 });
  await page.getByRole("button", { name: "다양한 방향 탐색하기" }).click();
  await page
    .getByRole("button", { name: "제안한 후보 생성", exact: true })
    .click();
  let modal = page.getByRole("dialog", {
    name: "이번 후보 생성 확인",
    exact: true,
  });
  await modal
    .getByRole("button", { name: "2회 요청하고 생성 시작", exact: true })
    .click();
  await expect(
    page.getByText("요청 처리 완료 · 2/2회 처리", { exact: true }),
  ).toBeVisible();
  await expect(card(page).nth(0).getByRole("img")).toBeVisible();
  await expect(
    card(page)
      .nth(1)
      .getByText("이번 요청에서 이미지를 얻지 못했습니다", { exact: true }),
  ).toBeVisible();
  const before = await state(page);
  const successId = before.rounds[0].candidates[0].image.assetId;
  await page
    .getByRole("button", { name: "남은 후보 생성·재시도", exact: true })
    .click();
  modal = page.getByRole("dialog", {
    name: "이번 후보 생성 확인",
    exact: true,
  });
  await expect(
    modal
      .getByRole("group", { name: "이번에 만들 후보" })
      .getByRole("checkbox"),
  ).toHaveCount(1);
  await modal
    .getByRole("button", { name: "1회 요청하고 생성 시작", exact: true })
    .click();
  await expect(card(page).nth(1).getByRole("img")).toBeVisible();
  expect((await state(page)).rounds[0].candidates[0].image.assetId).toBe(
    successId,
  );
  expect(
    (await (await page.request.get(origin + "/fixture/codex")).json()).calls,
  ).toBe(3);
  await configure({ delay: 5 });
  await page
    .getByRole("button", { name: "다른 방향 탐색", exact: true })
    .click();
  await expect(card(page)).toHaveCount(2);
  await page
    .getByRole("button", { name: "제안한 후보 생성", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "2회 요청하고 생성 시작", exact: true })
    .click();
  await page
    .getByRole("button", { name: "남은 생성 취소", exact: true })
    .click();
  await expect(
    page.getByText("남은 생성 취소됨", { exact: false }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("남은 생성 취소됨", { exact: false }),
  ).toBeVisible();
  expect(
    (await (await page.request.get(origin + "/fixture/codex")).json()).calls,
  ).toBe(0);
  await configure({ connected: false });
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Codex 로그인 필요 · 설정", exact: true }),
  ).toBeVisible();
  await page.getByText("이전 묶음", { exact: true }).click();
  await page
    .getByRole("button", { name: "1번째 · 2/2개 이미지", exact: true })
    .click();
  await expect(card(page).first().getByRole("img")).toBeVisible();
  await card(page)
    .first()
    .getByRole("button", { name: "이런 방향 더 보기", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "1개 방향 저장됨" }),
  ).toBeVisible();
  await configure({ connected: true });
});

test("preservation is reversible, neither changes direction, and undo restores choices", async ({
  page,
}) => {
  await fresh(page);
  await page.getByLabel("시작할 참고 이미지", { exact: true }).setInputFiles([
    { name: "a.png", mimeType: "image/png", buffer: await fixtureImage(page) },
    {
      name: "b.png",
      mimeType: "image/png",
      buffer: await fixtureImage(page, "#715c94"),
    },
  ]);
  await page
    .getByRole("button", { name: "각 참고자료에서 탐색 시작", exact: true })
    .click();
  await expect(card(page)).toHaveCount(2);
  await expect(card(page).first().getByRole("img")).toBeVisible();
  const originals = (await state(page)).rounds[0].candidates;
  await card(page)
    .first()
    .getByRole("button", { name: "이런 방향 더 보기", exact: true })
    .click();
  await card(page)
    .nth(1)
    .getByRole("button", { name: "이런 방향 더 보기", exact: true })
    .click();
  await card(page).first().getByText("부분·다른 모습", { exact: true }).click();
  await card(page)
    .first()
    .getByRole("button", { name: "부분을 보존하거나 바꾸기", exact: true })
    .click();
  const modal = page.getByRole("dialog");
  await modal
    .getByRole("button", { name: "얼굴·턱 계속 보존", exact: true })
    .click();
  await expect(
    modal.getByRole("button", { name: "얼굴·턱 보존 해제", exact: true }),
  ).toBeVisible();
  await modal
    .getByRole("button", { name: "얼굴·턱 보존 해제", exact: true })
    .click();
  await expect(
    modal.getByRole("button", { name: "얼굴·턱 계속 보존", exact: true }),
  ).toBeVisible();
  await modal.getByRole("button", { name: "닫기", exact: true }).click();
  expect((await state(page)).directions[0].preserved).toEqual({});
  await page
    .getByRole("button", { name: "마지막 선택 되돌리기", exact: true })
    .click();
  expect((await state(page)).directions[0].preserved.face).toBeTruthy();
  await page
    .getByRole("button", { name: "마음에 드는 후보 없음", exact: true })
    .click();
  expect((await state(page)).rejected.sort()).toEqual(
    originals.map((c: any) => c.candidateId).sort(),
  );
  await page
    .getByRole("button", { name: "다음 프롬프트 준비", exact: true })
    .click();
  await expect(page.locator(".discovery-round-bar strong")).toHaveText(
    "2번째 후보 묶음",
  );
  await expect(card(page)).toHaveCount(2);
  const different = await state(page);
  expect(
    different.rounds[0].candidates.every((c: any) => !c.sourceCandidateId),
  ).toBe(true);
  await page
    .getByText("선택 기록·기존 이미지·참고자료", { exact: true })
    .click();
  await page
    .locator(".discovery-history-row")
    .first()
    .getByRole("button", { name: "되돌리기", exact: true })
    .click();
  const recovered = await state(page);
  expect(recovered.rejected).toEqual([]);
  expect(recovered.directions).toHaveLength(2);
  expect(recovered.activeRoundId).toBe(different.activeRoundId);
});

test("a drifting alternate view can be corrected or retained as an independent candidate", async ({
  page,
}) => {
  await fresh(page);
  await page.getByLabel("시작할 참고 이미지", { exact: true }).setInputFiles({
    name: "avatar.png",
    mimeType: "image/png",
    buffer: await fixtureImage(page),
  });
  await page
    .getByRole("button", { name: "각 참고자료에서 탐색 시작", exact: true })
    .click();
  await expect(card(page)).toHaveCount(1);
  await expect(card(page).first().getByRole("img")).toBeVisible();
  const original = (await state(page)).rounds[0].candidates[0];
  await card(page).first().getByText("부분·다른 모습", { exact: true }).click();
  await card(page)
    .first()
    .getByRole("button", { name: "같은 디자인 옆모습 확인", exact: true })
    .click();
  await expect(
    card(page)
      .first()
      .getByText("같은 디자인 · 다른 모습 확인", { exact: true }),
  ).toBeVisible();
  await returnImages(page);
  let s = await state(page);
  expect(s.rounds[0].candidates[0].versionId).toBe(original.versionId);
  await card(page).first().getByText("부분·다른 모습", { exact: true }).click();
  await card(page)
    .first()
    .getByRole("button", {
      name: "이미지가 틀리거나 판단하기 어려움",
      exact: true,
    })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", {
      name: "이미지가 틀린 것 같아요 · 문제로 표시만 하기",
      exact: true,
    })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await card(page)
    .first()
    .getByRole("button", {
      name: "이미지가 틀리거나 판단하기 어려움",
      exact: true,
    })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", {
      name: "의도와 다르지만 좋아요 · 독립 후보로 보관",
      exact: true,
    })
    .click();
  await expect(card(page).first().getByRole("img")).toBeVisible();
  s = await state(page);
  expect(s.rounds[0].candidates[0].versionId).not.toBe(original.versionId);
  expect(s.rounds[0].candidates[0].directionId).not.toBe(original.directionId);
  expect(s.rejected).toEqual([]);
});

test("an image must load before it can receive a visual preference", async ({
  page,
}) => {
  await fresh(page);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/projects/*/assets/*", async (route) => {
    await gate;
    await route.continue();
  });
  try {
    await page.getByLabel("시작할 참고 이미지", { exact: true }).setInputFiles({
      name: "delayed.png",
      mimeType: "image/png",
      buffer: await fixtureImage(page),
    });
    await page
      .getByRole("button", { name: "각 참고자료에서 탐색 시작", exact: true })
      .click();
    await expect(card(page)).toHaveCount(1);
    const interest = card(page)
      .first()
      .getByRole("button", { name: "이런 방향 더 보기", exact: true });
    await expect(interest).toBeDisabled();
    await expect(
      card(page)
        .first()
        .getByRole("button", { name: "이 디자인 사용", exact: true }),
    ).toBeDisabled();
    release();
    await expect(interest).toBeEnabled();
    await interest.click();
    await expect(
      page.getByRole("heading", { name: "1개 방향 저장됨" }),
    ).toBeVisible();
  } finally {
    release();
    await page.unrouteAll({ behavior: "wait" });
  }
});

test("legacy rounds keep every candidate but display and export only the selected pair", async ({
  page,
}) => {
  await fresh(page);
  await page.getByRole("button", { name: "다양한 방향 탐색하기" }).click();
  await expect(card(page)).toHaveCount(2);
  const pid = await page.locator("#project").inputValue();
  const session = await (await page.request.get("/api/session")).json();
  const response = await page.request.post("/api/fixture/legacy-round", {
    headers: {
      origin: "http://127.0.0.1:8766",
      "x-csrf-token": session.csrfToken,
    },
    data: { projectId: pid },
  });
  expect(response.ok()).toBe(true);
  await page.reload();
  await expect(card(page)).toHaveCount(2);
  const legacy = (await state(page)).rounds[0];
  expect(legacy.candidates).toHaveLength(4);
  await page
    .getByRole("button", { name: "기록의 다음 2개", exact: true })
    .click();
  const shown = await card(page).evaluateAll((nodes) =>
    nodes.map((n) => n.getAttribute("data-candidate")),
  );
  expect(shown).toEqual(
    legacy.candidates.slice(2).map((c: any) => c.candidateId),
  );
  await page.reload();
  await expect(card(page)).toHaveCount(2);
  expect(
    await card(page).evaluateAll((nodes) =>
      nodes.map((n) => n.getAttribute("data-candidate")),
    ),
  ).toEqual(shown);
  const request = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().endsWith("/export"),
  );
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "파일 묶음 내보내기", exact: true })
    .click();
  expect((await request).postDataJSON().candidateIds).toEqual(shown);
  await download;
  expect((await state(page)).rounds[0].candidates).toHaveLength(4);
  await page
    .getByRole("button", { name: "다른 방향 탐색", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "기록의 다음 2개", exact: true }),
  ).toHaveCount(0);
  expect((await state(page)).rounds[0].candidates).toHaveLength(2);
});
