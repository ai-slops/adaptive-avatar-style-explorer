# Original v2 acceptance audit — open

Source: `specs/implementation-v2.md` was byte-for-byte compared with the user's
`.local/adaptive-avatar-style-explorer-implementation-spec.v2.en.md` on 2026-10-15.
Version 2 supersedes the older document. The approved [Codex amendment](codex-local-mode.md)
changes execution and live integration gates; [browser access](browser-access.md)
records the requested remembered-browser behavior. Other design/evidence/learning
requirements remain in scope.

The later [discovery-first usability addendum](usability-addendum.md) supersedes the
default navigation and verification-first priority in this original audit.
[Its separate A01–A22 record](usability-acceptance.md) verifies the implemented
feedback-to-next-round journey, contextual correction budget and provisional
selection. Rows below describe the broader original v2 scope; they are not a claim
that the new default discovery workflow remains absent.

This is a working gap audit, not proof of complete MVP delivery. Passing numerical,
service and browser tests does not prove real visual extraction or preference quality.

| Requirement group | Current evidence | Audit result / remaining work |
|---|---|---|
| §§1–2: reusable-avatar objective; intent, presentation, observations and suitability separate | Strict canonical/observation contracts, fixed reference feature schema, evidence policy; domain and learning tests | Implemented for tested cases; real image-confounding accuracy is not established |
| §3: provider and billing boundaries | Native Codex account/catalog/image/vision jobs verified live; community SIWC adapter signed-token mocks; server-selected route isolation | Native installation gate verified; live SIWC remains unverified for optional compatibility mode |
| §4: no-questionnaire onboarding, six-version board, scoped synchronized comparison, inspection, prompt and handoff screens | Chromium workflow tests; React screens; `test_multiple_depictions_one_candidate` | The default workflow is superseded by the implemented discovery journey and next-round UI; see the separate usability acceptance record |
| §4.4, §8.2: explicit choices only; neither/skip/tie, shortlist and depiction rejection semantics | Frozen reviews and `test_neither_skip_tie_undo_and_idempotency`; no navigation-to-feedback handlers | Tested at service level and scoped browser comparison |
| §5: immutable canonical records and deliberate adoption | Version/change-set service; canonical editor browser workflow; typed property/source/relationship ZIP test | Typed values, metadata, relation states and exact sources survive deliberate revision; old version remains unchanged |
| §5.3–5.4: confirmed intent is distinct from image compatibility | Independent property states, user locks, append-only links/observations | Tested; historical decision-source exports do not count as revised-version evidence |
| §6: safe import, independent finding classes, unknown geometry, character-space asymmetry | Assets validation/crops, strict findings, evidence editor, no-redesign compiler; ownership/drift tests | Implemented contracts and review flow; richer real-image consistency fixtures still needed |
| §7: morphology/state profiles, explained not-applicable slots, conservative coverage | `test_nonhumanoid_custom_profile_and_applicability`, state-study, duplicate-source and drift-disposition tests | Tested service behavior; multi-state final selection needs the complete scenario audit |
| §8: exact history, frozen evidence, idempotency, compensation, forks and locks | Domain tests for correction invalidation, boundaries, undo, repeated weight, inherited locks | Branch source ancestry is preserved; explicit unlock now traverses branch-adoption ancestry without changing parent history |
| §9.1–9.7 and Appendices B–C: fixed masked numerical baseline and scoped ranking | Reference/policy/ranking modules and numerical/domain tests | Implemented baseline; numerical passing results do not establish perceptual invariance |
| §9.8: inspectable preference hypotheses with supporting/contradicting IDs and user confirmation | No hypothesis store or user confirmation workflow found | **Missing**; qualitative evidence must remain distinct from observations and numerical models |
| §10: action-type policy, informative comparison, failure budgets, adaptive evidence priority and checkpoint recommendation | Basic `Planning.next_actions`; ranker informative pairs | Discovery next-round UI, contextual issue routing and bounded correction are now exercised in the usability acceptance record; richer strict-evidence scheduling and empirical acquisition evaluation remain separate |
| §11: compiler preserves exact target/hash, attachment roles and allowed changes | Compiler/API tests and browser prompt workflow | Core compiler verified; review batch limits/immutable prompt revision behavior in full scenario |
| §11.1: reasoning context includes actual observations | `Jobs.context` includes selected current links' reviewed observations, assessment, actual presentation and schema/extractor/observation IDs; `test_reasoning_context.py` checks intent separation, selected-only scope, ownership and superseded-link rejection | Gap fixed and service-tested; no extra live provider transmission was performed for this change |
| §12: architecture and server-owned execution context | FastAPI services, SQLite, narrow providers, React UI; ownership and mode tests | Implemented architecture; suggested directory layout is not itself a requirement |
| §13: live SIWC contract | Signed-token transport mocks and provider error tests | Native Codex replaces this installation's integration gate; compatibility-mode live verification is still unproven |
| §14: atomic events, strict writes, concurrency, durable jobs, stale/cancel/restart handling | Domain, SIWC, native Codex and session tests | Tested cases pass; cache/template/extractor provenance keys need a dedicated audit |
| §15: loopback authentication, Host/Origin/CSRF, safe assets, protected credentials, retention | API, image, provider, mode-isolation, remembered-session and revocation tests | Tested boundaries pass; Codex-owned cache retention is documented separately from application deletion |
| §16: complete honest handoff and external build review | ZIP checklist/spec/relations/manifest/coverage/events/provenance; checkpoint tests; prototype panel | Historical canonical decision sources now export with permissions and explicit non-current-evidence role; full prototype round trip still requires scenario evidence |
| §17.1: release-blocking cases | Targeted domain/learning/evaluation/provider/browser tests | Broad test coverage exists; a case-by-case gate audit is still required, particularly real-image confounding and the full manual scenario |
| §17.2: predictions before labels, lineage/source holdouts, diversity-only comparison and later satisfaction | `quality.py` prequential reports and disagreement tracking, explicitly inconclusive | **Partial**; observational report is not the requested empirical comparison against a diversity-only acquisition policy |
| §17.3: multi-candidate drift/correction/adoption/finalist/handoff scenario | Separate workflow tests cover individual pieces | **Incomplete**; no single complete scenario artifact proves the entire sequence yet; SIWC-specific portion is superseded for native use |
| §18: semantic v1 migration | Fresh-install migrations only; unversioned existing databases are rejected | No v1 installation was present; a safe legacy import/migration path and fixture validation remain unimplemented, not presumed complete |
| §19: complete M0–M5 deliverables | Current code, test results, live native artifacts and git history | **Not complete** until remaining functional and verification gaps are resolved |

Next implementation work should address the explicit gaps above. Do not turn this
matrix into a green release checklist merely by weakening its verification scope.
