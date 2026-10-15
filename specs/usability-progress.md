# Discovery-first usability implementation status

Requirements: [usability-addendum.md](usability-addendum.md), copied unchanged from
`.local/adaptive-avatar-style-explorer-usability-addendum.en.md`.

## Current delivery boundary

This commit supplies the **server-side discovery workflow**, alongside the existing
advanced workspace. It does **not** complete the usability addendum or its release
gate. The default browser interface is unchanged. Work stops after this commit at
the user's requested checkpoint.

Implemented server behavior:

- Prepare distinct, provisional character proposals from a blank project without
  manual design authoring. Plans contain actual character instructions, not images.
- Save exploratory reactions with the exact depicted evidence separately from
  qualified preference training. Save multiple directions, preserve a visible part,
  undo a decision, and use corrected decisions in subsequent design proposals.
- Record an immutable chosen-design snapshot with automatically retained evidence
  gaps, independently of modeling acceptance criteria. Replacing a different chosen
  design requires an explicit flag; prior snapshots remain in reaction history.
- Persist rounds and candidate positions, accept partial external returns by exact
  return filename or explicit association, and retain ambiguous images as independent
  inspiration when explicitly requested. Existing designs can be selected from a
  library without inventing prior discovery rounds or preferences.
- Export a round's prompts, return manifest, and permitted selected-source reference
  files. Exporting does not authorize generation or reference transmission.
- In private mode, explicitly authorize a finite native batch. Each result returns
  to its original slot. Failures leave successful results accessible; a new explicit
  retry accepts only candidates without successful images. Reference transmission
  requires consent. Cancellation stops remaining submissions. Restart marks pending
  batches interrupted rather than resubmitting them.
- Community mode exposes no discovery image-generation route.

## Verification and limits

`apps/server/tests/test_discovery.py` verifies the server workflow using synthetic
fixture images and mocked Codex transport. It covers blank proposals, multi-direction
feedback, preservation/undo, changed-favorite planning, immutable selection, delayed
imports, permissions, account isolation, partial native success, explicit retry,
pre-submission and in-flight cancellation, restart recovery, and the community API
capability boundary. Existing server tests are also run.

These checks do not demonstrate that generated characters are visually desirable,
that a live provider completed the new batch workflow, or that a person can finish
the addendum's journey in the browser. Earlier live integration checks predate this
workflow and are not acceptance evidence for this change.

## Remaining required work

- Connect a consistent Korean, image-first default workspace to these APIs; provide
  onboarding, contextual comparison, saved directions, visible preserve/vary scopes,
  finite generation consent/progress/cancel/retry, and chosen-design recovery.
- Add multi-image upload and thumbnail matching, with a direct way to begin a round
  from independent inspirations. Storing inspiration alone does not satisfy UX-01/02.
- Finish contextual view/correction behavior, including faithful-but-unwanted shapes,
  reference choice for drift correction, ambiguous hidden structure, and actionable
  UI recovery after bounded correction attempts.
- Preserve access to advanced editing, evidence review, authentication/settings,
  usage controls, and handoff while removing numbered mandatory navigation from
  the default discovery experience.
- Verify keyboard/touch/enlargement focus return, stable slots, reload recovery,
  desktop 1440×900 and narrow 390×844 layouts, and populated-project migration.
- Complete and report A01–A22 acceptance walkthroughs, including the requested
  acquisition demonstration in each mode. Distinguish mock workflow checks from
  live provider results and subjective visual quality.

Do not describe the usability addendum as implemented until those steps pass.
