# Implementation and verification status

Target: specification v2, all MVP milestones M0–M5, amended by
[the requested local Codex mode](codex-local-mode.md). No existing application or v1
installation was present at initialization. This is a fresh-install implementation.

- M0: baseline implemented — canonical SQLite schema, strict write contracts,
  design-only numerical baseline, ownership-bound services, loopback session policy.
- M1: offline workflow implemented — designs/revisions, safe raster imports,
  append-only assessments, frozen comparison bundles, events, undo/reset/fork,
  React exploration, comparisons and evidence inspection.
- M2: baseline implemented — conservative observed-condition qualification,
  scoped masked learning, family caps, correction invalidation, structural coverage.
  Versioned morphology/state profiles, explicit finding dispositions, inherited
  property locks, shared-basis regional ranking, informative pairs, and duplicate
  source checks are implemented. Real image-confounding fixtures and live visual
  analysis accuracy remain unverified.
- M3: implemented against a signed-token mock — PKCE/OIDC registration, account
  switching and explicit offline binding, protected credentials, refresh/revocation,
  model catalog, terminal SSE parsing, image consent, budgets and durable jobs.
  Restart/cancel/account-switch do not resubmit or transfer work. Official
  registration, account, inference and preview docs were revalidated on 2026-10-15.
  Live SIWC callback, model admission and text/vision smoke tests remain unverified.
- M4: offline compiler implemented — self-contained text prompts, reference roles,
  canonical hashes, no-redesign policy, export and manually mapped result import.
  Provider reasoning returns strictly validated, unconfirmed observations, findings
  and next actions. User review is required before adopting features. Richer
  state-study recipe controls are implemented. Provider-authored prompt proposals
  remain separate from the deterministic canonical compiler.
- M5: baseline handoff implemented — ZIP specification, reference permissions,
  coverage, findings, effective event provenance, acceptance checks and checkpoints.
  External model builds/capture mapping and scoped prototype checkpoints have UI
  and API support. Pre-feedback predictions and an honest observational evaluation
  report are exported. Legacy migration tooling and empirical preference evaluation
  remain unverified.

The [open acceptance audit](ACCEPTANCE.md) records remaining functional and
verification gaps. In particular, hypothesis management, the complete next-action
workflow, explicit observations in reasoning context, the full manual scenario,
legacy migration and empirical preference evaluation are not proven complete.

Canonical editing now supports typed values, provenance, notes, attachment/layer
relationships and multi-line unresolved decisions. Historical canonical decision
sources export under their own original version and never inflate current coverage.
Branch variants retain their user-authored rationale and can explicitly unlock
inherited properties without altering parent-branch locks.

## Current verification

- 59 Python tests pass: domain/service transactions, reference numerical behavior,
  evidence policy, image validation, prompt compiler/export, checkpoints, and API
  authentication/CSRF/isolation/deletion; signed-token SIWC mock tests, two-account
  isolation, explicit offline binding, budgets, stale output, cancellation and recovery.
- TypeScript check and Vite production build pass.
- Five real Chromium end-to-end tests pass through project/design creation,
  image import/review, 25% structural coverage, prompt preparation, explicit gap
  acceptance, handoff ZIP download, mobile overflow, and a scoped visual comparison
  that updates only its regional preference model. The third checks native-mode
  connection, generation, unreviewed import and reload using an isolated fake worker.
  The fourth covers initial browser pairing, remembered plain-URL access, the
  remembering setting, explicit sign-out and revoked access. The fifth verifies
  typed canonical values, component relationships, notes, source image/decision IDs,
  multi-line decisions, deliberate adoption and preservation of the old version.
- Browser fixtures use synthetic raster bytes to test workflow. They do not prove
  visual extraction accuracy or preference quality.

Remembered browser sessions survive application restart with a fixed 30-day
expiry, revocation, runtime mode isolation, and zero restored provider budgets.
[Browser access evidence](browser-access.md) describes the new first-visit flow.

## Local Codex acceptance (2026-10-15)

- The launcher defaults to native local Codex; SIWC prompt-only mode is selectable.
  Native routes are registered only by the server-selected mode and require the
  bootstrap-authenticated installation owner. Request role flags cannot enable them.
- Installed codex-cli 0.162.1 app-server initialized successfully, read the existing
  ChatGPT account and model catalog, and completed a native image-generation turn.
  A separate live request through the running application's enqueue/poll/import
  pipeline also succeeded using the installed default `gpt-6.1-sol`.
- The application imported exactly one terminal native artifact, preserved its
  immutable target/hash and prompt revision, recorded thread/turn/tool provenance,
  and created an unreviewed depiction with no automatic observations or coverage.
  The sample project is local data and is not committed.
- Credentials remain managed by Codex. Child workers disable shell, apps, plugins,
  MCP configuration, browsing and delegation. They reject interactive tool requests.
  API-key fallback is rejected. Only native structured image artifacts are imported.
- Tests cover idempotency, ownership, terminal failures, cancellation, stale output,
  bounded artifact paths, login type, mode isolation and strict analysis suggestions.
  Crop coordinates/source families and inherited branch locks are also tested.
- After explicit user approval to transmit the generated sample, a live Codex
  vision-analysis job completed successfully and passed strict application validation.
  The native transport closes all objects and sends sparse attributes as typed rows
  with fixed numeric bounds/categorical values before restoring the domain map.
  Initial response-schema failures were fixed and retained as failed jobs; each
  verification attempt was explicitly issued, with no automatic retry. The successful
  result remains unconfirmed suggestions and adds no observations or design changes.

The local Codex generation acceptance gate is satisfied. A live SIWC callback is
no longer a gate for this user-requested mode. SIWC distribution/two-user live
verification, legacy migration, empirical preference quality and visual extraction
accuracy remain outside the verified local experience. Numerical tests do not
establish visual invariance. No production readiness or complete original MVP
release claim is made.
