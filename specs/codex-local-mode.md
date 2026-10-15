# Local Codex execution amendment

The user's 2026-10-15 instruction replaces SIWC as the desired integration for
this installation and explicitly includes image generation through Codex.
This amendment supersedes the prompt-only execution boundary of the v2 spec for
the local Codex mode. Character design/evidence separation, immutable versions,
reviewed observations, preference semantics and honest 3D handoff remain the target.

The product now needs a single-owner local Codex mode using the installed Codex
app-server and its managed ChatGPT login. The app must show connection status,
allow a user-triggered generation request from a versioned prompt, display progress
and cancellation, accept only structured native image-generation artifacts, and
import completed images as unreviewed depictions of the exact target version.

Use native app-server protocol and Codex-managed login. Never read provider tokens
into the browser or silently switch to an API-key billing path. Shell, external
apps, plugins, MCP servers, browser automation and sub-agents are unnecessary for
these bounded image/analysis tasks and should be disabled in the child runtime.

Generation is authorized only by server-selected local Codex mode and the
bootstrap-authenticated local owner. It is not enabled by a submitted role flag.
The SIWC prompt-only runtime remains independently selectable for compatibility;
its text-only request builder must not gain an image-generation capability.

The local Codex experience, including a completed native image turn and imported
artifact, is now the integration acceptance gate. A live SIWC login is no longer
required for the requested local Codex workflow. A public hosted or multi-tenant
Codex service is outside this scope.

Protocol evidence: installed codex-cli 0.162.1 generated schemas expose
`imageGeneration` items with result/savedPath/revisedPrompt/status; initialize,
account/read and model/list were successfully probed on 2026-10-15. A feature flag
and catalog alone are not proof of a completed image-generation turn.

Acceptance evidence on the same date: the native worker completed an image turn;
a separate application API job also completed and imported exactly one artifact
as unreviewed evidence of its original immutable version. Following the user's
explicit authorization to transmit that sample, a live vision-analysis turn also
completed and passed application validation as unconfirmed suggestions. Native
structured output requires closed objects; sparse feature maps use typed key/value
rows in transport and are restored only after validation. See STATUS.md for the
verification boundary.

References:
- https://learn.chatgpt.com/docs/app-server
- https://learn.chatgpt.com/docs/config-file/config-sample


## Discovery rounds

The [usability addendum](usability-addendum.md), UX-12, permits a single explicit
confirmation for a finite displayed set (one turn per selected candidate, at most
two, following the user's later fixed-pair instruction). This orchestrates the same native single-turn worker; it does not authorize
an open-ended agent loop. References require explicit transmission consent,
completed candidates cannot be retried, cancellation prevents later submissions,
and process restart never automatically resubmits the batch. Models remain a
secondary option with an available default. Community mode has no batch generation
route. See [usability acceptance](usability-acceptance.md) for the distinction between
mock workflow checks and live integration evidence.
