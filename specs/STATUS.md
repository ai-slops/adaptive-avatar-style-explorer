# Implementation and verification status

Target: specification v2, all MVP milestones M0–M5. No existing application or v1
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

## Current verification

- 46 Python tests pass: domain/service transactions, reference numerical behavior,
  evidence policy, image validation, prompt compiler/export, checkpoints, and API
  authentication/CSRF/isolation/deletion; signed-token SIWC mock tests, two-account
  isolation, explicit offline binding, budgets, stale output, cancellation and recovery.
- TypeScript check and Vite production build pass.
- Two real Chromium end-to-end tests pass through project/design creation,
  image import/review, 25% structural coverage, prompt preparation, explicit gap
  acceptance, handoff ZIP download, mobile overflow, and a scoped visual comparison
  that updates only its regional preference model.
- Browser fixtures use synthetic raster bytes to test workflow. They do not prove
  visual extraction accuracy or preference quality.

Release remains unverified until Section 17 is audited, including live SIWC and
manual two-user end-to-end tests. Numerical tests do not establish visual invariance.
No production readiness or complete MVP claim is made.
