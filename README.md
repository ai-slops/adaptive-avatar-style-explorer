# Adaptive Avatar Style Explorer

A local workspace for discovering a reusable 3D character design. The default
launcher connects to the installed Codex app-server and its ChatGPT login for
image generation and optional design analysis. The [local Codex amendment](specs/codex-local-mode.md)
records this user-requested change to the [version 2 specification](specs/implementation-v2.md).

Images are evidence about immutable design versions. Camera, pose, lighting and
expression are test conditions, never taste features. Generated images enter
review; they do not automatically confirm design intent or validate 3D geometry.
The [discovery-first addendum](specs/usability-addendum.md) defines the default journey. See its [acceptance evidence](specs/usability-acceptance.md) and the broader [verification status](specs/STATUS.md) for capabilities and limits.

## Run locally

Use Python 3.11 or newer and a virtual environment, then:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
npm ci --prefix apps/web
npm run build --prefix apps/web
PYTHONPATH=apps/server .venv/bin/python -m app
```

The server binds to `127.0.0.1:8765` and prints a private launch link. Open the link
once to connect your browser. It is remembered for 30 days, including server
restarts; bookmark `http://127.0.0.1:8765/` for later visits. A new browser can use
**이 기기에서 워크스페이스 열기** to open the local default browser, or paste the
initial connection link in the onboarding form. The remembering checkbox under **설정** controls this preference; **이 브라우저 로그아웃** revokes this browser's connection.
See [browser access](specs/browser-access.md) for the session and pairing behavior.
Options include `--no-browser`, `--port`, and `--data-dir`. The default `.data/`
directory is ignored by Git.

Install Codex on the same device and sign in with ChatGPT. **설정** shows
the current connection and can open Codex's login flow if needed. Credentials stay
managed by Codex; this integration does not switch to API-key billing. This mode
is for a single-owner loopback installation.

1. Choose **다양한 방향 탐색하기**, or upload several images with **참고 이미지로 시작하기**. A name and character description are optional.
2. In private mode, **제안한 후보 생성** opens a finite request confirmation. Choose the candidates and approve any displayed reference transmission. The available Codex default model is used unless changed.
3. React directly to visible images, keep multiple directions, or compare two with **둘 다 더 탐색**, a relative choice, no preference, neither, or skip. Imported/generated images remain provisional.
4. Request **다음 후보 생성 준비**. The next proposals develop the saved directions separately and retain an alternative. **부분·다른 모습** offers ordinary-language refinement, preserved parts, contextual views and correction.
5. **이 디자인 사용** records a recoverable design choice with remaining gaps. Modeling acceptance criteria are a separate advanced activity.

In prompt-only mode the same journey uses **묶음 프롬프트 복사** or **파일 묶음 내보내기**, external generation, and **결과 이미지 여러 장 가져오기**. Exact return filenames match automatically; ambiguous files require an explicit candidate choice or remain independent inspiration. This mode never submits image-generation work.

Generation requires a new explicit finite authorization. Each selected candidate uses one Codex turn; an individual advanced analysis request uses one turn. Successful images return to their original slots. Cancellation stops remaining submissions and requests interruption of in-flight work. Already submitted work may finish or consume allowance. Failed or interrupted work is never automatically resubmitted. Retrying accepts only candidates without successful images. Reloading does not authorize any work.

**고급 작업 도구** retains manual design editing, strict evidence assessments, qualified comparisons, reasoning, prompt recipes, history branches, prototype review and modeling handoff. Discovery reactions do not become strict preference-training examples or confirm every depicted/hidden component. A design choice is separate from reference-brief preparation and actual 3D model review.

Project deletion removes application-owned data; downloaded exports and
Codex-managed caches are outside application control. Local sign-out does not
log out the device's Codex CLI.

The offline workflow supports immutable revisions, imports and user-selected crops,
manual assessments, typed canonical properties and source notes, component attachment/layer
relationships, scoped comparisons, shortlists and property locks, history
branches, text prompt exports, prototype evidence, checkpoints and ZIP handoffs.

The original community SIWC prompt-only mode remains available with
`--provider siwc`. That runtime has no native image-generation routes. Its live
provider integration is unverified; signed-token mocks cover its service behavior.
SIWC is not required for local Codex mode.

## Checks

```sh
.venv/bin/python -m pytest -q
.venv/bin/ruff check apps/server
npm run build --prefix apps/web
npm test --prefix apps/web
```

For browser tests, install Chromium with `npx playwright install chromium` in
`apps/web`. Linux may also need Playwright's browser dependencies and fonts.
Browser tests use isolated databases, drawn framing fixtures and a fake Codex worker; they incur no
provider usage. Native integration was separately tested on the installed
`codex-cli 0.162.1` with completed image generation, artifact import, and an explicitly
authorized vision-analysis turn. The installed app-server protocol is experimental and may need adaptation after
Codex upgrades.
