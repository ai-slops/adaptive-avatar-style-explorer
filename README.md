# Adaptive Avatar Style Explorer

A local workspace for discovering a reusable 3D character design. The default
launcher connects to the installed Codex app-server and its ChatGPT login for
image generation and optional design analysis. The [local Codex amendment](specs/codex-local-mode.md)
records this user-requested change to the [version 2 specification](specs/implementation-v2.md).

Images are evidence about immutable design versions. Camera, pose, lighting and
expression are test conditions, never taste features. Generated images enter
review; they do not automatically confirm design intent or validate 3D geometry.
See [verification status](specs/STATUS.md) for capabilities and remaining limits.

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
initial connection link in the onboarding form. The Account & privacy checkbox
controls remembering; **Sign out locally** revokes this browser's connection.
See [browser access](specs/browser-access.md) for the session and pairing behavior.
Options include `--no-browser`, `--port`, and `--data-dir`. The default `.data/`
directory is ignored by Git.

Install Codex on the same device and sign in with ChatGPT. Account & privacy shows
the current connection and can open Codex's login flow if needed. Credentials stay
managed by Codex; this integration does not switch to API-key billing. This mode
is for a single-owner loopback installation.

1. Create a project and character design, or select an existing design card.
2. Open **Prompt workspace**, choose a requested view, and **Prepare text prompt**.
3. Select a Codex model and, if references are listed, approve their transmission.
4. Press **Codex로 이미지 1장 생성**. Progress, cancellation and results appear below.
5. Open **생성 이미지 검토** to assess adherence and observed conditions.

Each generation/analysis action authorizes one Codex turn under the signed-in
account. Failed or interrupted work is never automatically resubmitted. A stale
result remains attached to its original immutable target and requires review.
Project deletion removes application-owned data; downloaded exports and
Codex-managed caches are outside application control. Local sign-out does not
log out the device's Codex CLI.

The offline workflow supports immutable revisions, imports and user-selected crops,
manual assessments, scoped comparisons, shortlists and property locks, history
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
Browser tests use isolated databases and a fake Codex worker; they incur no
provider usage. Native integration was separately tested on the installed
`codex-cli 0.162.1` with completed image generation, artifact import, and an explicitly
authorized vision-analysis turn. The installed app-server protocol is experimental and may need adaptation after
Codex upgrades.
