# Adaptive Avatar Style Explorer
## Discovery-First Usability Requirements Addendum

**Date:** October 15, 2026  
**Applies to:** The in-progress implementation supplied as `adaptive-avatar-style-explorer-main.zip`, its existing v2 specification, and its local Codex execution amendment.  
**Document type:** Incremental product and usability change request—not a v3 specification, a replacement architecture, or a request to restart implementation.  
**Status:** Requirements to implement and verify; not a claim that the changes already exist.

## 1. Requested outcome and precedence

The product must help a person who cannot yet describe their preferred style **discover a character design they actually want to use as a reusable 3D avatar**.

The main experience must be:

**See meaningfully different options → express a simple reaction → receive better-informed next options → develop promising directions → choose a design.**

Inspecting other views, reviewing generated-image fidelity, preparing prompts, and collecting modeling references support that experience. They must not become the work the user has to perform before discovery can begin.

This addendum changes the default journey, information hierarchy, feedback handling, and next-step behavior of the existing product. It does not prescribe component files, framework changes, database migrations, learning algorithms, or pixel-perfect layouts. Some requirements need supporting workflow behavior; hiding technical controls without providing that behavior does not satisfy them.

### Precedence over the existing specification

Where they conflict, the discovery-first requirements below supersede the default workflow and screen hierarchy in v2 §4, the verification-first action priority in §10.2, and any interpretation that makes modeling-reference completeness a prerequisite for selecting a style.

The existing distinction between design and depiction, strict qualification of reliable visual comparisons, and honest uncertainty remain. **Strict evidence qualification must not become a gate on expressing interest or receiving new exploratory suggestions.** Provisional exploration feedback and qualified visual-preference evidence serve different purposes.

Preserve existing authentication, account isolation, consent, usage controls, mode separation, immutable history, provenance, import/export permissions, and truthful 3D-readiness claims. The local Codex amendment remains applicable only to its authorized private mode. This document neither extends that authorization to other users nor revalidates external provider availability or terms.

## 2. What the supplied implementation already provides—and what is missing

The following observations come from source inspection, not a completed browser usability test. They identify the user-facing mismatch rather than assigning implementation work to files.

| Observed current experience | Required adjustment |
|---|---|
| The empty discovery board primarily asks the user to add a design. Its editor exposes a name, structure, character idea, property keys and states, and unresolved decisions. | Let the user start exploration without designing or formally describing the first candidate. Manual authoring remains optional. |
| The board displays existing design cards and can order them, but does not expose a central feedback-to-next-candidate journey. | Make each round a connected step toward the next useful options, not a static collection the user must populate. |
| Cards prominently display reference coverage, depiction counts, issue counts, and revisions. | Make the character image, the user's reaction, and the next discovery action primary. Show technical completeness when relevant. |
| Comparing requires selecting designs, a scope and view, and sealing a comparison before voting. | Offer immediate, appropriately scoped reactions. Capture the necessary decision context without asking users to operate an evidence transaction. |
| Unreviewed images may appear on cards, while the comparison view selects images through recorded observations. | Avoid the experience of opening a visible candidate only to find an empty comparison. Support provisional exploration directly from available images. |
| The prompt workspace is attached to a selected design version and initially emphasizes an additional profile view. Variant requests expose property keys. | Prepare new directions and targeted variants from the user's choices; additional views become a contextual option. |
| AI assistance is presented as optional task/model controls and textual suggestions. | Make bounded assistance produce actionable next options or prompt packs in the main journey. Keep task selection and model administration secondary. |
| Imports, image review, history branching, checkpoints, and handoff are available as separate tools. | Retain those capabilities, but orchestrate them so the user does not have to assemble the workflow manually. |
| Design-selection checkpoints already exist inside the handoff experience. | Make “I want to use this design” an accessible discovery outcome, independent of completing a modeling brief. |

The requested change is **not primarily a color, typography, or card-decoration refresh**. It is a change from a design/evidence management workspace to a guided visual exploration experience, with management tools available when needed.

## 3. Priority and release rule

**P0** means necessary to correct the core experience. **P1** means a useful enhancement that may follow once the P0 journey works. These are delivery priorities, not claims about implementation difficulty.

All numbered requirements in §§4–10 are P0 unless explicitly marked P1. Suggested labels and candidate counts illustrate behavior; equivalent interfaces are acceptable. Provider limits and explicit user budgets may reduce batch sizes.

The core release gate is a complete path from a blank project to a second, feedback-informed candidate round **without requiring the user to author a design specification, review numeric features, configure test views, or visit a technical AI task panel**.

## 4. The primary journey

### UX-01 — Start without knowing the answer

Offer direct starting actions equivalent to **Explore different directions** and **Start from references**. A short description and a project name may be offered, but a working name can be assigned automatically. Neither an art-style taxonomy nor a character concept is required.

The application prepares a small, diverse initial set of candidate proposals. It must be able to do this before a manually authored design version exists. Automatically created proposals remain provisional; they do not become user-confirmed design facts.

With reference images, accept ordinary uploads and multiple references in one import action. Do not require a separate formally named design for every uploaded image. Where grouping is uncertain, retain the images as inspiration and offer a simple correction rather than forcing invented identity relationships.

With no images:

- **Private local generation mode:** Prepare first-round proposals and offer explicitly authorized generation using the available local integration.
- **SIWC prompt-only mode:** Prepare first-round prompts and clearly show how to generate externally and import results. Do not imply that images already exist.

An optional licensed starter collection may shorten this path, but acquiring such a collection is not a prerequisite for this addendum. Do not fabricate a visual gallery when only text is available.

### UX-02 — Use one continuous discovery workspace

The default workspace must answer three questions without technical navigation: **What am I comparing? What can I do with these options? What happens next?**

Keep the active candidate board or focused comparison, selected directions, and next-step control within one connected experience. A contextual panel, overlay, or dedicated focused comparison is acceptable if it returns to the same place with state intact.

Routine discovery must not require the sequence: create design → inspect evidence → choose an analysis task → open prompt workspace → manually create another design → configure comparison.

After ordinary feedback, the application saves the reaction and prepares the next useful step. The user may continue reacting, undo, or request the next round. Do not replace the board immediately after a single selection or launch undisclosed provider work from that selection.

The primary continuation label must reflect the current capability: for example, **Generate next options** in private generation mode and **Prepare next prompts** in prompt-only mode. Both continue the same discovery process.

### UX-03 — Make candidates visual, readable, and comparable

A discovery option represents a provisional character design or design direction—not a camera pose and not a database record. Show its best available relevant depiction as the main content, with a short working label and compact optional context.

Use approximately four to six distinct options for a broad round when practical. Fewer options are acceptable for a focused comparison or a constrained generation budget. Do not fill a round with duplicates simply to reach a count.

A representative image is evidence of what is depicted, not proof of hidden geometry. Related views remain grouped under the same design. The UI must distinguish a **different design** from **another view of the same design**.

Provide easy enlargement and preserve the complete character when presenting a whole-design option. Avoid arbitrary crops, inconsistent scale, clipped feet, or a decorative layout that makes actual design comparison difficult. Face or component comparisons may use intentional, clearly scoped crops.

Keep explanatory headers, technical metadata, and large empty placeholders from pushing the images and main reactions out of the working viewport. No visual preference may be collected from an ungenerated text card as though the user saw an image.

### UX-04 — Collect simple, optional-depth feedback

The normal action is a choice about use as an avatar, not a rating of illustration quality or a judgment about resemblance to the user's real-world identity. Copy should ask, for example, **Which character would you rather use?**

Support these meanings without requiring a written explanation:

| Action | Required interpretation |
|---|---|
| More like this / Keep exploring this | Positive exploratory interest in this option; not confirmation of every component or unseen surface. |
| Choose A / Choose B | A relative preference under the images and scope actually shown. |
| Both are worth exploring | Preserve both directions; not necessarily a numerical tie. |
| No preference | No clear relative preference; not proof that either is satisfactory. |
| Neither / None of these | The displayed options are not satisfactory; offer another direction rather than force a winner. |
| Skip / Cannot judge | Do not create a positive or negative taste label. |
| Keep this part | Preserve an explicitly selected visible component or agreed constraint within a stated scope. |
| The image is wrong / Hard to judge this image | Treat as depiction or observability feedback, not automatically as rejection of the character. |

These controls need not all be permanently visible. Keep the most common actions prominent and expose nuance contextually.

Do not require a manual “Seal comparison” step. The application must preserve the actual evidence shown as part of recording the user's action. Do not require numeric feature values, property keys, camera projection, or evidence status before accepting a reaction.

Unselected candidates are not automatically losers. Hover, dwell time, zoom, and revisits are not explicit taste votes. A bookmark is not a property lock. A lock must have a clear visible scope and be reversible.

### UX-05 — Make the next round visibly depend on feedback

The application—not the user—must turn accumulated choices into next-candidate proposals and usable prompts. Showing a taste summary or rearranging the same cards alone is insufficient.

A next step may be a comparison among already available options, a meaningful new design variant, a new direction, or a targeted observation of a promising design. Reuse existing material when it can answer the question; do not generate solely because the user clicked a navigation control.

For a six-option development round, a useful initial mix is three promising variants, two options that help resolve an uncertainty, and one different plausible direction. This is a starting policy, not a permanent quota.

Explain the purpose in one or two plain-language sentences, such as: “You kept these two directions. The next set develops both and includes one different alternative.” A brief reason may be expanded to the relevant prior choices. Do not assert a causal preference such as “you like angular faces” merely because selected images share that feature.

Every new proposal must differ meaningfully in its intended character design, unless it is explicitly labeled as an observation or correction. Renaming, recoloring a background, changing only a pose, or repeating essentially the same prompt does not constitute design exploration.

Users must be able to request **More like this**, **Try a different direction**, or **Focus on this part** without writing a new generation prompt. A fully described character specification must not be required to do so.

### UX-06 — Adapt focus without imposing a staged wizard

Use the following priorities to guide assistance, not as mandatory screens or irreversible gates:

| Current need | Default priority | What must not take over |
|---|---|---|
| Discover a direction | Diverse character options and broad reactions. | Completing every candidate's side/back views or evaluation plan. |
| Develop promising directions | Whole-design variants, informative comparisons, and some different alternatives. | Repeating nearly identical options or asking the user to tune every feature. |
| Refine a candidate | Targeted changes with explicit preserved parts and checks of the combined result. | Silently locking all features of a previously selected image. |
| Check a promising design | Relevant alternative views, expressions, or poses while holding identity fixed. | Learning pose taste or requiring exhaustive sheets for discarded concepts. |
| Choose a design | Record the user's choice and remaining uncertainties. | Requiring a production-ready model or complete modeling brief. |

Suggest a focus change from accumulated decisions or an explicit user request. Always allow returning to broad exploration, comparing an older option, or choosing a design earlier. Do not automatically declare the user's taste “found” because an algorithm converged.

A visible defect may justify checking a particular candidate sooner if it affects the decision being made. A missing back view or unconfigured modeling profile alone must not halt early exploration of all candidates.

### UX-07 — Support multiple promising directions

Users must be able to keep at least two different directions alive, name them optionally, and develop or compare them independently. Preserve the ability to return to a less recently explored direction.

Present these as understandable visual alternatives, not history sequence IDs. A history fork and a currently interesting design direction are different user concepts; users must not understand replay boundaries to explore both styles.

Do not average two different liked aesthetics into an unwanted compromise. Do not interpret activity on one direction as rejection of the others. Confirmed component locks are local to the relevant direction unless the user explicitly makes them broader.

### UX-08 — Refine parts without making the user a modeler

Offer visual or ordinary-language controls such as **Keep this face; try different hair**. The application translates the request into a bounded design-change proposal, an appropriate reference set, and generation instructions.

The user must not need names such as `hair.ornament_side`, observation confidence values, or a morphology-specific evaluation profile. Detailed controls may remain available as an advanced option.

Display what will remain and what will vary before requesting new results. A proposed temporary anchor is not a permanent lock. Do not silently modify a confirmed lock; ask for an explicit unlock or offer a separate alternative.

Combining liked parts produces a new whole-design candidate that must be judged as a combination. Separate preferences for one face, another hairstyle, and another outfit do not prove preference for the assembled character.

If the user only recognizes a liked part visually, a reference-based instruction is sufficient to continue exploration. Unspecified measurements and hidden structure remain unspecified.

## 5. Usefulness without false certainty

### UX-09 — Keep provisional exploration distinct from verified preference

A reaction to an unreviewed but visible image must still be useful. It may influence which references, directions, or proposed variants are shown next without being admitted as a strict, presentation-controlled training example.

Maintain the user-facing distinction between:

1. **Exploratory interest:** What the user wants to see more of, based on the image actually shown.
2. **Qualified design-preference evidence:** A scoped comparison supported by sufficiently comparable observations.
3. **Design and production decisions:** Confirmed preserved parts, an explicitly chosen design, and separately assessed modeling readiness.

The application must not say “I learned your 3D style” from a single attractive portrait. Equally, it must not say “insufficient evidence” and become unable to suggest anything until the user manually reviews multiple views.

An early full-character impression is valid as an exploratory reaction to the available depiction. It is not equivalent to a qualified all-angle whole-character preference. Keep existing strict qualification where applicable; do not bypass it by marking all imports compatible or inventing observed features.

AI-extracted properties may be shown as suggestions. The normal journey must not require the user to approve a long list of inferred attributes after every image. Ask for a concise visual clarification only when it materially changes the next action or a consequential decision.

Unknown features, uncertainty about reproduction, and limited evidence should guide what happens next. They must not dominate every card as warnings or be converted into aesthetic penalties.

### UX-10 — Make views and poses serve design discovery

Camera angle, framing, pose, expression, lighting, and background are observation conditions, not preference targets for this product. Keep them reasonably comparable when judging a design change, and vary them deliberately when checking the same design.

Offer other views progressively for shortlisted candidates or a specific uncertainty. Do not open a mostly empty multiview matrix as the default early comparison. Never fabricate missing views or imply that a generated turnaround is a validated 3D reconstruction.

When another view is disliked, distinguish these cases with simple contextual choices:

| What happened | Appropriate next step |
|---|---|
| The intended design is depicted faithfully, but the revealed shape is unwanted. | Propose a design change and check that liked aspects remain. |
| The generator changed the character unintentionally. | Treat it as a reproduction problem; do not lower preference for the original design automatically. |
| The newly visible area was never specified. | Present alternatives for that design decision, rather than claim one is the previously established truth. |
| The pose, crop, or lighting prevents judgment. | Defer the judgment or prepare a clearer depiction without learning a pose preference. |
| The unexpected result is attractive in its own right. | Let the user keep it as a separate provisional option, without silently replacing its original target. |

Allow checking a face in profile or an outfit in a relevant pose, but do not infer actual rigging, garment deformation, topology, or runtime readiness from generated pictures.

Do not let correction requests repeat indefinitely. After repeated failures, explain the unresolved issue and offer to continue elsewhere, keep it pending, or try another production method. Changing a preserved design must not be the hidden cost of escaping the loop.

### UX-11 — Separate “I found my design” from “ready to model”

Expose an action equivalent to **Use this design** from the main discovery experience. It records the selected candidate and provides a compact summary of preserved features, relevant references, alternatives, and unresolved choices.

Selecting a style must not require entering model-build acceptance criteria, manually accepting every missing reference, or finishing an evaluation profile. Give a truthful brief caveat when important views remain unchecked; retain those gaps automatically rather than forcing the user to retype them.

Keep these outcomes distinct: **design chosen**, **reference brief prepared**, and **actual 3D model reviewed**. No single percentage should merge them. Existing handoff and prototype tools remain available as a separate next activity.

The selected snapshot remains recoverable. Later experimentation must not silently overwrite it. The user can continue exploring or explicitly replace the choice.

## 6. Acquisition modes within the same journey

### UX-12 — Private local generation: integrate the existing capability

Retain the supplied implementation's authorized private local Codex generation mode. The user should not have to open a prompt editor, choose a technical task, and manually import each successful result merely to complete a discovery round.

Present the proposed options, the bounded work to be requested, relevant reference transmission, and any available usage information. Use an appropriate available model by default; expose model changes in secondary controls rather than demand a catalog selection on every action.

One clearly authorized action may cover a finite disclosed round when supported by the existing permission and execution rules. It must not authorize endless generation. Where operations require separate approvals, keep them in context without repeating unrelated setup.

Show progress and partial completion within the round. Successful results return to their original candidate slots automatically as provisional depictions. A failed option must not hide the successful options or force regeneration of the whole set.

Selection, navigation, and passive viewing must not launch new generation automatically. No silent paid-API fallback or unbounded retry is allowed. Cancellation must prevent additional work from being started and request cancellation of in-flight work where supported. Explain that a provider may still finish an already submitted operation or consume allowance; do not promise otherwise. A retry is a new explicit action; completed work must not be duplicated.

### UX-13 — SIWC prompt-only: an assisted external round trip

For other users, preserve their individual SIWC connection for authorized analysis and text work. The application prepares prompts and reference instructions; **it must not submit image-generation requests in this mode**.

Keep the discovery workspace, preference behavior, directions, and refinement controls equivalent to the private experience. Only acquisition differs:

**Prepare next prompts → copy/export the set → user generates externally → import results into that round → compare.**

A prompt pack must be immediately usable without the user inventing the actual character design or rewriting the instructions. Include understandable candidate labels, the intended difference, relevant reference attachments, and return-matching guidance. “Try something you like” is not an actionable next-candidate proposal.

Support one action to copy or export the round, and one import entry point for multiple results. Preserve where the user left off while they work externally. Handle partial and delayed returns without requiring the entire round to be completed.

When a result can be associated confidently from its return context, do not require repeated design-version selection. For ambiguous matches, show thumbnail-based choices and allow “not sure” or “independent reference.” Do not guess identity silently.

Pending options must say that they need an externally produced image. Do not display false generation progress, a nonfunctional Generate button, or a success notice implying an image was created. An imported result is not automatically proof that its prompt was followed.

### UX-14 — Make connection and limits understandable without making them the product

Show the active mode and meaningful connection state unobtrusively. Put authentication, account switching, privacy, usage budgets, and advanced model controls in settings or a contextual interruption only when necessary.

Respect existing consent scopes. Reduce redundant setup, but do not broaden image transmission permission because the UI became simpler. Clearly indicate when images will leave the device, and allow the user to decline while retaining local browsing and saved work.

When authorization or allowance is unavailable, explain what stopped and what still works. Existing images, saved feedback, and pending prompt packs must remain accessible. New AI proposals may require reconnecting or resuming an allowed budget; never fake them or silently switch billing paths.

Do not promise that a subscription implies unlimited operation or guaranteed zero charges. Preserve the configured subscription-only/no-paid-fallback policy and show uncertainty rather than invented exact remaining usage.

## 7. Default hierarchy and interaction quality

### UX-15 — Progressively disclose management tools

The primary workspace contains candidate images, simple reactions, the current direction or shortlist, and the next action. Candidate inspection, supporting references, and concise reasoning are contextual. Detailed specifications, evidence assessments, learning diagnostics, technical history, provider tasks, and modeling handoff are secondary or advanced.

The implementation may keep existing pages and capabilities. It must not require all of them to remain equally prominent in the default navigation or appear as a numbered sequence users believe they must complete.

Do not use reference-coverage percentages, effective comparison weights, canonical hashes, or missing-view counts as the headline measure of discovery progress. Prefer factual summaries such as “Two directions saved” or “Face preserved; outfit still open.” A low-evidence hypothesis must be labeled as tentative, not presented as a stable taste profile.

Manual editing and expert review must remain available; they must no longer be the only route forward.

### UX-16 — Make decisions easy to inspect and undo

Offer immediate undo for consequential reactions, rejection, and component locks. Undo must affect future suggestions, not just the icon shown on a card. Previously exported prompts and already generated images remain historical outputs; explain when they were based on an earlier choice.

Keep a compact, recoverable history of rounds, shortlisted options, and the selected design. Do not require resetting all learning to recover a rejected candidate or revisiting a direction.

Persist the current round, selected directions, preserved parts, pending external results, and in-progress job references across reloads. Reloading or reconnecting must not resubmit generation or analysis automatically. Late results stay attached to the round and candidate they were requested for, not whichever candidate is now open.

### UX-17 — Keep the visual task operable

At a normal desktop viewport, users must be able to see a useful candidate image and its main reaction/continuation controls without scrolling past a long technical form. At narrower sizes, reduce the number of simultaneous candidates or use a focused comparison rather than shrink them into illegible thumbnails.

On a representative desktop size of 1440×900 and a narrow viewport of 390×844, the main journey must have no unintended horizontal overflow. These are acceptance fixtures, not a prescribed layout.

Core actions must be usable by keyboard and touch, have visible focus and selected states, and not rely only on hover, color, or an unexplained star. Enlargement must be dismissible and return focus to the originating candidate.

Keep visible and accessible labels consistent with the actual effect. Use one selected interface language consistently through the core journey; technical English and localized generation controls must not form an accidental language mixture. Prompt/export language may be selected separately.

Do not automatically reorder the visible board during an unfinished decision because a new score or image arrived. Show new arrivals without changing the identity of an option under the user's pointer. Feedback saving should not make already available images unusable; failed saves must be indicated and recoverable.

## 8. Preserve the work already implemented

### UX-18 — Add the journey without discarding the workspace

Existing projects must open with their images, design revisions, reference permissions, explicit comparisons, locks, rejected options, branches, prompts, checkpoints, and provenance intact. No destructive “start over” or mandatory re-upload is acceptable.

When old records lack enough information to infer a discovery round or a direction confidently, show them as an existing library from which the user can select a starting point. Do not invent historical preferences or pretend an old prompt was part of a newly completed round.

Keep strict evidence review, advanced design editing, and handoff usable for users who need them. Protect consequential confirmed decisions while making provisional exploration lighter.

Do not remove private local generation merely because community users are prompt-only. Do not expose private generation to community users in order to unify the visual layout.

## 9. Explicitly not sufficient

The following do not satisfy this addendum:

- Restyling the same forms, moving them into a wizard, or changing “Add a design” to “Discover” while still requiring a manually authored design.
- Adding a Next button that only opens the existing missing-view form or repeats a generic prompt unrelated to prior feedback.
- Displaying AI suggestions as prose while requiring the user to translate them into property keys and manually populate the next board.
- Disabling comparison for unreviewed images without allowing meaningful provisional exploration, or making everything “reviewed” to avoid the problem.
- Generating six poses of one character and presenting them as six style directions, or treating hidden/unselected candidates as rejected.
- Claiming a design is complete because a coverage score increased, or requiring a complete modeling brief before a user may choose their style.

An infinite feed, mandatory chat interface, advanced preference questionnaire, full 3D editor, new generation provider, and complete backend rewrite are not required. Conversation or free-text feedback may supplement the visual loop but may not become its mandatory replacement.

## 10. Acceptance scenarios

Use representative character images, including incomplete and inconsistent views, for human walkthroughs. Mock providers are appropriate for repeatable workflow checks and capability-boundary tests, but mock images do not prove visual quality, preference accuracy, or live provider reliability.

| ID | Scenario | Observable pass condition |
|---|---|---|
| A01 | A new user has no references or idea. | They can request initial options without completing a design editor or taxonomy. Local mode offers bounded generation; prompt-only mode produces a usable starter pack and a clear return path. |
| A02 | The user imports several unrelated inspirations. | A single import entry point accepts them. The user can explore from them without naming and specifying every character or asserting they share an identity. |
| A03 | The first images are visible but unreviewed. | The user can express interest immediately. The app retains provisional semantics and can prepare relevant next proposals without numeric feature review or a full character sheet. |
| A04 | The user selects two options from a broad round. | Both remain active. The next plan visibly develops those choices and retains a meaningful alternative; unselected options are not all marked disliked. |
| A05 | The user dislikes every option. | “None of these” produces a recoverable change of direction without selecting a least-bad winner, resetting the project, or entering an explanation. |
| A06 | Two options are available for comparison. | Reactions are available in the same focused context without selecting internal version IDs, creating a manual review transaction, or sealing a comparison. |
| A07 | The user keeps a face and asks for different hair. | The next proposal states the preservation/change boundary, needs no property-key input, and does not silently turn all of the image's features into locks. |
| A08 | The user likes two substantially different styles. | Both can be developed and revisited separately. Neither is silently averaged away, overwritten, or rejected when the other is explored. |
| A09 | Discovery candidates lack profiles and back views. | The normal next action remains useful style exploration. Missing views do not force completion of evaluation forms; any provisional preference remains appropriately limited. |
| A10 | A finalist's profile reveals an unwanted jaw shape. | The user can request a jaw-related design alternative while preserving liked aspects, rather than training a preference against profile views. |
| A11 | The profile depicts a different face, but that accidental result is interesting. | The original is not automatically penalized or replaced. The user can request correction or keep the result as a separate provisional option. |
| A12 | Local generation succeeds for only part of a round. | Successful images appear in their intended slots; failed and pending slots are clear. The user can continue, cancel remaining work, or explicitly retry failed work without regenerating successes. |
| A13 | A prompt-only user requests another round. | The app creates only analysis/text work and usable prompts. No native or indirect image-generation request occurs. Actual images appear only after import. |
| A14 | External results arrive in several batches, including an ambiguous file. | The round resumes with existing results intact. Clear matches need no repeated setup; ambiguous matches receive a thumbnail-based choice and may remain unassociated. |
| A15 | The user is satisfied after seeing only a few views. | “Use this design” records the choice with honest unresolved coverage. Modeling acceptance criteria and prototype tests are not mandatory fields. |
| A16 | A user undoes a reaction or unlocks a part. | Future proposals use the corrected state. Existing external prompts or finished jobs are not silently rewritten, and no prior candidate is lost. |
| A17 | The page reloads during local work or an external round trip. | The active context and pending status are restored. No request is automatically repeated, and late results retain their original target. |
| A18 | The account disconnects or its allowed usage stops. | The app explains the interruption without losing local decisions or images. No paid fallback or invisible retry occurs; browsing and importing remain available. |
| A19 | An existing populated project is opened after the update. | Its data and permissions remain intact and useful in the new journey. Unknown historical associations remain unknown; no mandatory reset or re-import occurs. |
| A20 | The main loop is used with keyboard, touch, and the two specified viewport fixtures. | Images and reactions remain usable, focus and selection are visible, language is consistent, and no unintended overflow or interaction-shifting reordering occurs. |
| A21 | Feedback-informed behavior is tested with controlled planning fixtures. | Changing which candidate is favored changes the intended next designs or their reference/variation plan—not just the order or summary. A preserved component stays preserved; a rejected one is not repeatedly proposed without a stated exploration reason. |
| A22 | The implementation has a visually polished interface. | A tester can still complete A01 → A03 → A04 and request a second round without technical authoring/review screens. Visual polish alone does not pass the release gate. |

### End-to-end demonstration to request from the implementer

Demonstrate a blank project becoming a feedback-informed second round, then preserve a component, retain a second direction, and choose a provisional final design. Perform the acquisition step once in each mode: authorized private generation and SIWC prompt-only external return. Also demonstrate resuming an existing project without data loss.

Report which demonstrations used live providers and which used mocks. Report workflow completion separately from whether the generated characters were actually preferred. Do not claim that all later candidates must be more appealing; informative rejection and continued uncertainty are legitimate outcomes.

### P1 enhancements after the core loop works

Useful follow-on improvements include configurable exploration breadth, side-by-side round history, editable plain-language preference hypotheses, richer region selection, bulk import match review, and a properly licensed starter reference collection. They must not delay the P0 continuous discovery journey or introduce new mandatory setup.

## 11. Practical acceptance summary

After this change, the user should spend most of their time **looking, choosing, and occasionally saying what to keep or change**. The application should do the work of preparing the next options, organizing their results, remembering decisions, and proposing when another view would be useful.

The user should not need to understand the system's evidence model to benefit from it. The evidence model must nevertheless continue to prevent false certainty, accidental design replacement, unauthorized generation, and misleading 3D-readiness claims.

## Appendix: Review basis and limits

This addendum was prepared from the uploaded archive and the prior conversation's clarified objective. Its implementation observations were checked against the supplied `README.md`, `specs/implementation-v2.md`, `specs/codex-local-mode.md`, the main web workspace and its DesignEditor, Compare, Inspect, EvidenceEditor, Prompts, Reasoning, Codex, and Handoff views, and the supplied planning/qualification behavior. These are evidence references, not instructions about which files to edit.

The assessment is a **static source review**. A browser build was attempted, but package retrieval failed in the review environment; no rendered browser walkthrough or live integration test was completed for this review. Existing repository verification reports were not independently rerun and are not acceptance evidence for these new usability requirements.

No changes to application source code, provider configuration, or existing project data are included with this document. No API availability or billing claim from an earlier discussion is newly verified here; the requirements preserve the implementation's stated operating boundaries.
