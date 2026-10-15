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
  Custom evaluation profiles, finding resolution and further visual fixture tests
  remain to be implemented.
- M3: pending — SIWC registration, identity validation, streaming, budgets and jobs.
  Official registration, account, inference and preview docs were retrieved for
  revalidation on 2026-10-15; no live account test has been performed.
- M4: offline compiler implemented — self-contained text prompts, reference roles,
  canonical hashes, no-redesign policy, export and manually mapped result import.
  Provider planner and richer state-study recipe controls remain.
- M5: baseline handoff implemented — ZIP specification, reference permissions,
  coverage, findings, effective event provenance, acceptance checks and checkpoints.
  Reported build API exists; full prototype UI, migration tooling, and preference
  evaluation remain.

## Current verification

- 29 Python tests pass: domain/service transactions, reference numerical behavior,
  evidence policy, image validation, prompt compiler/export, checkpoints, and API
  authentication/CSRF/isolation/deletion.
- TypeScript check and Vite production build pass.
- One real Chromium end-to-end test passes through project/design creation,
  image import/review, 25% structural coverage, prompt preparation, explicit gap
  acceptance, handoff ZIP download, and mobile overflow check.
- Browser fixtures use synthetic raster bytes to test workflow. They do not prove
  visual extraction accuracy or preference quality.

Release remains unverified until Section 17 is audited, including live SIWC and
manual two-user end-to-end tests. Numerical tests do not establish visual invariance.
No production readiness or complete MVP claim is made.
