# Discovery-first usability acceptance — 2026-10-15

Scope: the incremental [usability addendum](usability-addendum.md), UX-01–18 and
A01–22. Its default journey takes precedence over v2's numbered management screens
and verification-first scheduling. It does not remove strict qualification from
advanced comparisons or make a rendered image proof of a 3D model.

## Later user override: two candidates

The user's subsequent instruction, **“선택 후보를 2개로 고정해줘”**, supersedes the
addendum's illustrative four-to-six counts. Every new discovery/design-refinement
round now prepares exactly **two** candidates, and native batches accept at most
two pending candidates. Single-design observations/corrections remain contextual
views rather than fabricated extra style choices. Reference/library material and
historical larger rounds are retained; the board pages those records two at a
time, persists the selected pair across reload, and exports/generates only that
pair. When two directions are kept, each receives one development slot. With one
saved direction, broad exploration can include a fresh alternative. Explicit
**다른 방향 탐색** remains available.

The new contract and legacy-pair export are service-tested; an additional browser
walkthrough verifies two-card paging, recovery and pair-only export without
truncating the old four-candidate record. Counts in the actual demonstrations
below describe the historical runs before this override and have not been rewritten.

## Implemented journey

The default Korean workspace starts with **다양한 방향 탐색하기** or a multi-image
reference import. It assigns a project name when needed and prepares provisional
character proposals. The person reacts to visible images, keeps independent
directions, prepares feedback-informed designs, preserves selected parts, and uses
**이 디자인 사용** without editing a specification or configuring an evaluation
profile. Ordinary reactions do not replace the board or invoke a provider.

Private mode confirms a finite candidate count and reference transmission before
native generation. Community mode copies/exports prompts and imports externally
produced results. Images stay in their original slots; partial results, explicit
retry, cancellation, pending external returns and active-round recovery are part
of the same workspace. Advanced editing, strict evidence review, scoped learning,
provider/account settings, technical history and modeling handoff remain accessible.

## Reproducible workflow checks

- `apps/server/tests/test_discovery.py`: service invariants and controlled proposal
  fixtures. The complete Python suite contains **79 passing tests**.
- `apps/web/tests/discovery.spec.ts`: nine Chromium discovery walkthroughs.
- `apps/web/tests/workflow.spec.ts`: five retained Chromium management/authentication
  walkthroughs. **All 14 browser tests pass**, with one worker because the native
  fixture represents a single installation owner.
- TypeScript/Vite production build, Ruff checks/format and Git whitespace checks pass.

Browser fixtures include drawn whole-character images for framing and interaction
checks. The native browser transport is a mock. These tests establish workflow,
account/mode boundaries and the intended next designs, not the attractiveness of
results, live SIWC availability or perceptual extraction accuracy.

| Scenario | Evidence and observed behavior |
|---|---|
| A01 | Blank-project browser walkthroughs in both modes prepare proposals without a design editor. Native confirmation discloses a finite count; community exports usable starter instructions and return filenames. |
| A02 | Bulk-reference browser/service checks create independent, unreviewed directions without names or identity grouping. Repeated copies of the same asset do not inflate the visible direction count. |
| A03 | Unreviewed imports accept immediate reactions. Frozen shown evidence and the exploratory classification are retained; no observations or strict comparison events are invented. |
| A04 | The community walkthrough retains two directions and prepares one descendant for each direction. A fresh alternative remains available through broad/single-direction exploration or the explicit different-direction action. Unselected options remain neutral. |
| A05 | Neither/none, recoverable direction change and undo are checked in browser/service workflows. No least-bad winner or project reset is required. |
| A06 | Focused A/B, both, no preference, neither and skip act on the images actually shown, without internal IDs or a seal step. Existing strict sealed comparisons remain advanced. |
| A07 | Face preservation followed by different hair is checked through the ordinary-language dialog and canonical/reference assertions. Temporary anchors remain proposed; confirmed source locks are checked again before execution. |
| A08 | Both saved directions remain independently accessible and develop separately. Naming, revisiting and comparison controls are contextual. Component preservation stays local to its direction. |
| A09 | Missing profile/back views do not block the first or next design round. Qualified training remains separate. |
| A10 | Controlled planning changes the intended face/jaw design rather than the camera feature. The contextual problem panel distinguishes a faithful-but-unwanted shape from depiction drift. This is a workflow check, not a claim of live anatomical assessment. |
| A11 | Service/browser checks retain an unexpected view as an immediately visible independent provisional candidate, with a new version/direction and no rejection of the original. Corrections keep the original target and use its earlier reference when available. |
| A12 | Mock native partial-failure walkthrough preserves successes and positions, retries only missing work, and cancels remaining submissions. Service tests cover cancellation before startup and while a worker is in flight. |
| A13 | Community browser/service checks expose no generation route and submit no generation request. The real-file demonstration below made no provider calls from that mode. |
| A14 | Exact filenames match automatically. Partial/delayed imports retain earlier images; ambiguous files require a labeled choice with available thumbnails or explicit independent-reference status. Pending proposals have no fabricated thumbnails. |
| A15 | Selection records an immutable design snapshot, preserved parts, alternatives and unresolved coverage. An unconfigured coverage scope is retained explicitly. Selection and later exploration need no modeling acceptance criteria. |
| A16 | Browser/service checks undo reactions and explicitly unlock a part; future proposals use the corrected state. Old rounds, completed images and exported plans retain their historical inputs. |
| A17 | Browser reload preserves the active round and results without another generation request. Service restart marks queued/running batches interrupted and does not resubmit them. Late results keep their original candidate target. |
| A18 | A mock disconnected account leaves existing images, reactions and importing usable. Native failures stop or remain explicitly retryable; no billing fallback or invisible retry exists. |
| A19 | Existing-image library and retained advanced workflows are exercised. The actual version-6 local database was backed up and migrated to version 7; every pre-existing row in all **28 existing tables** compared identically immediately after migration. Old round/preference associations are not invented. This is not a semantic v1 migration claim. |
| A20 | Chromium checks exercise 1440×900 and 390×844, keyboard enlargement/Escape/focus return, touch-sized controls, visible selection/focus and no document overflow. Real generated-image screenshots were also inspected. Candidate positions remain stable while reactions and results arrive. |
| A21 | Controlled favored-A versus favored-B fixtures produce different canonical designs and source-reference plans, not just reordered cards. Preservation, undo, rejection recovery, deduplication and late confirmed-lock conflicts are tested. |
| A22 | The community browser scenario completes blank project → visible images → both directions → feedback-informed next round → preserved face/new hair → provisional selection without technical authoring/review pages. The native browser scenario completes bounded acquisition for both initial and feedback-informed rounds. |

## Actual local demonstrations and limits

**Native acquisition:** a new local project, **사용성 확인 · 새 탐색**, requested
one explicitly bounded batch of **two native turns with no reference images**.
Both completed through the real application's queue/import path and appeared as
unreviewed, full-character depictions in their intended slots. The two test
reactions retained both directions and preserved the first face. A second plan
contains separate hair alternatives and a different design direction. Those
reactions are controlled workflow decisions, not claims about the user's taste.

After the user's explicit authorization (including continuing permission for these
generated test references), the UI submitted a second finite batch of **two turns**
using only the two new test images as references. Both succeeded in their intended
slots. The second plan contained three proposals; the different alternative was
left ungenerated under the disclosed two-turn allowance. The live demonstration
therefore used **four turns total**, with no automatic retry or personal-image
transmission. The face-preserving hair alternative and the separate urban style
are actual results, still classified as unreviewed depictions.

While the user continued exploring the original project, final snapshot checks
ran against an **isolated database copy** of that generated project. Selecting the
new candidate retained two directions, the face anchor and five unchecked slots;
subsequent exploration and reload preserved the exact snapshot without provider
work. This final copy check is a service check, not a claim that a synthetic final
choice was imposed on the user's active project. Browser selection/recovery is
also covered by the community demonstration and the repeatable browser tests.

**Community external return:** an isolated prompt-only installation exported the
starter ZIP, imported two actual PNGs produced outside that installation (the
native test outputs), retained both directions, preserved a face, prepared and
exported a second four-candidate prompt set, and chose an earlier provisional
design. The resulting state retained two directions and `design_chosen`.
No generation or analysis request was submitted by that mode. Importing these
files does not prove that a later variant prompt was followed. Live SIWC callback,
analysis and account admission were not exercised by this demonstration.

Local evidence remains outside Git with application data:

- `.data/usability-live-run.json`: finite native request IDs, original targets and results.
- `.data/usability-community-demo/report.json`: external-return and selection summary.
- `.data/usability-choice-verification/report.json`: isolated-copy choice and recovery check.
- `.data/usability-migration-check.json` and `.data/pre-discovery-backup.sqlite`:
  migration comparison and private backup.
- `.data/community-demo-starter-prompts.zip` and
  `.data/community-demo-second-prompts.zip`: actual exported prompt bundles.
- `/tmp/discovery-live-initial-desktop.png`,
  `/tmp/discovery-live-initial-mobile.png`, `/tmp/discovery-live-confirmation.png`,
  `/tmp/discovery-community-second-prompts.png` and
  `/tmp/discovery-community-chosen.png`: local walkthrough captures.

The implementation passes the addendum's tested workflow release gate. It does
not establish that any later design must be preferred, recover hidden geometry,
validate a rig or model, or complete every original v2 research/legacy acceptance
item. The [original open audit](ACCEPTANCE.md) retains those distinct limits.
