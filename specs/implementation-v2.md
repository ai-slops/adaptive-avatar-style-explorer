# Adaptive Avatar Style Explorer
## Implementation Specification — Reusable 3D Character Design

**Version:** 2.0  
**Updated:** 2026-10-15  
**Language:** English  
**Status:** Implementable product and architecture specification; live SIWC authentication and end-to-end application behavior require installation-specific testing.  
**Supersedes:** Version 1.0 and the subsequent suggestion to learn composition/pose preferences as part of the target style.

> **Product objective:** Help a user discover, specify, and refine a character design they want to use as a reusable 3D avatar—not an attractive image tied to one camera angle, pose, expression, composition, or lighting setup.
>
> **Execution boundary:** Other users connect their own accounts through Sign in with ChatGPT (SIWC). The community application analyzes authorized inputs, learns from user actions, and produces text instructions and image-generation prompts. It does **not** generate images, submit prompts to a generator, or automate an external generation service. Users independently produce and import results. An optional private-owner image worker remains a separately deployed extension.

## 0. What changes in version 2

The primary candidate is now an **immutable character-design version**. Images are evidence about that version. Front, profile, back, seated, smiling, and close-up depictions are not automatically separate character candidates or separate preference votes.

The application separates three questions:

| Question | System responsibility |
|---|---|
| Which character design would the user choose to use? | Preference learning over character-design properties |
| Does this image faithfully depict that design under the requested conditions? | Identity, design-adherence, and presentation review |
| Is the design sufficiently specified and evaluated for reusable 3D implementation? | Coverage, unresolved-design decisions, and prototype validation tracking |

Camera, pose, framing, current expression, and lighting are **observation and test conditions**, not default taste dimensions. They remain important: they reveal different parts of the design, expose problems, and can confound judgments. Simply deleting camera fields from a feature vector does not make image-based preference learning viewpoint-invariant.

The default system objective is fixed to reusable-avatar design. An illustration-preference product, or an animation/posing-preference product, would require a separate objective and separate learning history; neither is implemented by this specification.

---

## 1. Goals, deliverables, and scope

### 1.1 User need

The user may know what they like when they see it but may not know modeling terminology or be able to write a complete character brief. They should be able to choose, shortlist, preserve parts, reject, or revise through a dedicated interface without repeatedly explaining their taste in ChatGPT's web chat.

The system should progressively suggest more relevant **design directions**, preserve alternatives, and request the most useful missing evidence. It must not promise that every round is better: useful exploration can produce rejected candidates.

### 1.2 Deliverables

The product produces:

1. A versioned canonical character specification with confirmed, proposed, inferred, and unspecified properties.
2. Preference evidence, competing design branches, and a shortlist of design versions.
3. A linked collection of actual depictions, requested test conditions, observed conditions, and consistency findings.
4. Self-contained text prompt packs for design variants, additional views, expression/pose studies, and correction requests.
5. A **3D design handoff pack**: chosen specification, approved references, component relationships, missing surfaces, unresolved alternatives, and acceptance checks for a later model build.
6. Optionally, feedback on externally produced 3D-prototype captures, linked to a declared model-build revision.

The end goal is a reusable 3D model. The MVP implements its **design-discovery and evaluation workflow**, not automatic mesh production. A generated turnaround sheet is not a finished or validated model.

### 1.3 Included and excluded work

The MVP includes the local application, SIWC analysis/planning, preference history, character/version management, imported-image review, multiview coverage, prompt export, external-result import, and modeling handoff.

It does not implement modeling, retopology, rigging, skinning, blendshape creation, physics simulation, texture baking, broadcasting, tracking, VRM conversion, or automated external image generation. It does not require VSeeFace, a particular file format, a particular modeling tool, or a humanoid character.

Existing renders and screenshots from a real prototype may be imported. The community MVP does not load executable DCC scenes or render new images from them. An interactive existing-model viewer can be specified separately later; it is not needed to complete this workflow and must not become an image-generation workaround.

### 1.4 Requirement language

**MUST** is release-blocking. **SHOULD** is a default that can change with a recorded rationale. **MAY** denotes an extension. Numeric limits and learning parameters below are proposed engineering defaults, not established psychological or production standards.

---

## 2. Character design versus presentation

### 2.1 Canonical design properties

A character design may include anatomy or other base structure, body proportions, neutral facial structure, eye design, hair shape and attachment, clothing shape and layers, accessories, palette, surface treatment, and intentional asymmetry.

Preserve the distinction between the character's **intended appearance system** and the particular source illustration. A cel-shaded material style intended for the final model belongs in the design. A dramatic spotlight, a vignette, lens distortion, or an illustrator's incidental brushwork does not automatically belong there.

A facial-expression *capability* or stylized eye-deformation rule can be an implementation requirement. A smile in the current image is a test state. Similarly, a character can have a persistent hunched body design or a defined neutral stance without making every momentary pose a design property.

### 2.2 Presentation conditions

Store these separately from the canonical design:

- Viewpoint, camera projection, distance/framing, crop, and visibility.
- Current pose, current expression, and current deformation state.
- Scene lighting, environment, background, and post-processing.
- Image execution defects, occlusion, and reference-generation artifacts.

These fields MUST NOT enter the MVP's preference feature schema, either directly or through automatically appended categorical features. Whole-image embeddings also must not serve as an unexamined substitute for design features.

### 2.3 What invariance means

The target is **the same chosen character remaining usable and recognizable across relevant conditions**. It does not mean identical pixels, a constant projected silhouette, frozen clothing folds, a fixed hairstyle outline in screen coordinates, or equal personal enjoyment of every possible view.

A design can legitimately have a weaker side profile or inconvenient hair volume when seated. The application should record the underlying design concern and propose a design revision—not conclude that the user dislikes side views or sitting.

Do not require a physically realistic solution for every stylized design. Record geometry, material, shader, deformation, and view-dependent stylization requirements separately. A planned view-dependent technique must be explicit and later tested; it must not silently excuse an inconsistent generated reference.

### 2.4 Diagnostic examples

| Observation | Correct treatment | Incorrect treatment |
|---|---|---|
| A low-angle portrait is selected | Record interest; test the design in matched neutral views | Learn “the user prefers low-angle cameras” |
| A profile redraw changes the nose and hairstyle | Flag identity/design drift; repair or deliberately fork | Treat it as proof that the canonical design has a bad profile |
| A faithful profile reveals an unwanted chin shape | Record a profile-specific design issue; propose chin geometry changes | Delete profile views from future testing |
| A smile changes apparent eye shape | Distinguish expected expression deformation from an eye-design change | Update the neutral eye requirement from this frame |
| Hair looks correct frontally but its back construction is undefined | Request or propose a back design, explicitly marked as new intent | Claim the front image already defines the hidden geometry |
| A user likes a whole reference image | Keep it as inspiration until attribution is clearer | Assert a confirmed preference for every depicted component |

---

## 3. Operating modes and SIWC boundaries

### 3.1 Community prompt-only mode

Each user runs a local installation, connects their own SIWC registration, and owns an isolated workspace. Allowed actions are import, display, non-generative image processing, text/vision analysis, local learning, prompt preparation, export, and manual external-result import.

Disallowed actions include image-generation APIs, automatic generator submissions, browser automation for generation, ComfyUI execution, image-producing agent tools, shell-based rendering, generated SVG illustrations, and automatic output retrieval. There is no generator credential field, generation endpoint, or Generate button.

Thumbnails, ordinary resizing, orientation correction, and user-selected crops are allowed. Generative upscaling, inpainting, background synthesis, and automatic completion of a missing view are not.

### 3.2 SIWC capability and deployment

Official documentation describes SIWC plan usage as an optional grant for eligible requests. It is separate from identity sign-in and does not expose the user's ChatGPT conversations or memories. The documented open-source/local flow is the baseline here. Paid or remotely hosted distribution requires resolving the applicable provider participation and registration requirements rather than replacing a loopback callback with a public URL. [S01]

Multiple users therefore means **each person can install and use the application with their own account**. This specification does not assume an approved centrally hosted multi-tenant service.

### 3.3 Subscription-only spending policy

Never use the operator's subscription for another user, accept an operator API-key fallback, or silently inherit an `OPENAI_API_KEY` from the environment. All authorized provider jobs bind to the requesting user's validated registration.

The provider offers app usage limits and optional credit usage. Current help says a sub-100% app limit prevents credit use for that app; credit permission and automatic credit purchases are separate controls. Ask the user to review those settings. The application cannot certify that provider-side settings remain unchanged without a documented verification interface. Do not invent a “no overage” request flag or a balance API. [S07]

Maintain a local per-session request budget, defaulting to explicit user-triggered analysis/planning. Local ranking and coverage refresh automatically after feedback. An optional session-scoped auto-prepare setting may authorize a bounded number of text-plan batches; show its remaining budget and a pause control. It must not restart provider work automatically after application restart, account switch, or a usage-limit reset. On a usage-limit error, stop new inference and retain offline comparisons and previously prepared exports. Local request counts are not a measurement of subscription tokens, remaining money, or reset time.

### 3.4 Private-owner extension

An optional private installation may later connect an image worker, but the community package contains no worker, credentials, command channel, or callable bridge to it. Authorization requires deployment configuration and a server-authenticated principal, not a submitted email or role flag.

Do not make the MVP depend on subscription-funded image automation. Its actual account, installation, artifact-return path, cancellation, and billing behavior require separate verification. Even in private mode, generated depictions go through the same identity and evidence review; generation does not create preference labels or prove 3D consistency.

---

## 4. User workflow

### 4.1 Start without a questionnaire

Ask for a project name and optionally an initial reference or short description. Show the purpose as “Find a character I want to use as a 3D avatar.” Do not require an art-style taxonomy, modeling knowledge, demographic information, or pose preferences.

With imported references, show a diverse inspiration board. With an explicitly licensed bundled reference collection, preserve attribution. With no images, offer text-only starter prompts and explain that visual comparison starts after the user imports images.

Selecting a written idea supplies **design-intent feedback**, not observed visual preference.

### 4.2 Separate exploration and verification

The normal loop is:

```text
Import references or externally generated images
  → propose or associate character-design versions
  → review actual depicted properties and identity consistency
  → compare designs with sufficient matched evidence
  → record design preference, partial locks, and design issues
  → choose: improve a design OR obtain missing evidence about it
  → prepare text-only prompts/instructions
  → user independently produces results elsewhere
  → import, assess, and update the relevant design evidence
  → confirm a design checkpoint and export the 3D handoff
```

A missing side view should often trigger an **evidence request for the existing version**, not another new character. Unknown back geometry may instead require a **design-decision proposal**. The interface must explain that distinction.

### 4.3 Main screens

**Explore designs:** Up to six distinct design versions, not six arbitrary images. Each card shows a representative imported depiction, evidence coverage, and unresolved issues. The representative depiction is not automatically the design's ground truth.

**Compare designs:** A and B with synchronized view slots and optional face/hair/outfit scopes. The same view is shown on both sides where available. An empty slot remains empty; it is never filled with a different character or an invented image. Record the actual evidence exposed during the decision.

**Inspect a design:** Its front/profile/back/detail depictions, proposed versus observed features, consistency issues, and missing requirements. Switching tabs is navigation, not a taste vote.

**Prompt workspace:** Text plans labeled “Design variant,” “Additional view,” “Unspecified-part design,” “Expression/pose study,” or “Correction.” Actions are Copy, Export, and Import result.

**Handoff:** Canonical design, preserved components, chosen alternatives, missing information, evidence provenance, and explicit model-build acceptance criteria.

### 4.4 Feedback controls

Primary controls are A, B, No preference, Neither, and Skip. Optional controls include Keep this component, Not my design, Bad depiction, Different character/design, and This part fails in this view/state.

“I like the character but not this pose” should exclude or qualify that depiction for the current comparison without training pose preference. “The sleeves are too bulky when the arms are raised” is a possible design/implementation issue, subject to whether the image actually depicts the intended sleeves.

Viewing, enlarging, hovering, or revisiting can prioritize review but MUST NOT create positive or negative taste labels by default. A shortlist action does not imply that every unselected candidate lost a comparison.

### 4.5 Progressive evidence collection

Do not demand an exhaustive character sheet for every broad idea. First narrow directions with limited, reasonably comparable evidence. Expand view coverage for the shortlist, and pose/expression checks for finalists or designs with relevant risks.

If imported references have uncontrolled presentations, the application may use user interest to choose the next prompts, but must label the resulting interpretation as a hypothesis. It must not turn an uncertain image-level attraction into a high-confidence design ranking.

---

## 5. Canonical data model

### 5.1 Entities

| Entity | Purpose |
|---|---|
| `Project` | User-owned reusable-avatar objective and settings |
| `Branch` | Alternative design direction and exact inherited history boundary |
| `CharacterDesign` | A design lineage, not an image |
| `DesignVersion` | Immutable canonical specification and parent revision |
| `Asset` | Immutable imported image bytes or a non-generative derivative |
| `Depiction` | An actual image/crop and its source provenance |
| `DepictionLink` | Reviewed association between a depiction and a design version |
| `FeatureObservation` | Actually visible character attributes, visibility, uncertainty, and observed presentation |
| `RenderRecipe` | Requested test conditions, separate from observed conditions |
| `EvaluationProfile` | Versioned required/recommended view and state slots |
| `EvidenceBundle` | Immutable subset of reviewed depictions for one version and profile |
| `ReviewSession` | A frozen A/B comparison context and exposed bundles |
| `FeedbackEvent` | Actual user action, exact scope, and evidence snapshot |
| `ValidationFinding` | Drift, ambiguity, visual suitability, or externally reported implementation issue |
| `PromptPlan` | Text-only instructions for one immutable target design and one requested output |
| `ModelBuild` | Optional reference to an externally produced model revision and declared provenance |
| `DesignCheckpoint` | User-approved design/handoff state, not automatic convergence |

### 5.2 Versioning rules

A new angle, pose, crop, lighting condition, or image retry does not create a `DesignVersion`. An intentional change to a design property does. Multiple image samples from the same prompt remain multiple depictions, not multiple designs.

The canonical specification is immutable after publication. An edit creates a new version with its parent and a property-level change set. A deliberate adoption of an accidental generated variation also creates a new version; the user must choose that action.

Properties that are unspecified remain unspecified. Proposed rear clothing details, unseen hair attachments, or hidden accessories are marked as proposals and require adoption before becoming confirmed specifications. Adding a back-detail requirement therefore creates a new design version even if the front appearance is unchanged.

### 5.3 Requirement records

A canonical property contains `value`, `state`, `sourceEventIds`, `sourceDepictionLinkIds`, and optional notes. Valid states are:

```text
unspecified | proposed | inferred | user_confirmed
```

The canonical state describes **intent**. It must not be used as a visual observation merely because an image was requested from it. Confirmed locks are user actions; the model cannot promote inferred properties into locks.

A lock preserves the design property, not a pixel coordinate. “Keep the hair ornament on the character's left side” is valid. “Keep it on the left side of every image” is not an equivalent requirement.

### 5.4 Depiction association is not proof

An external result can name the intended version and still depict something different. `DepictionLink` records `unreviewed`, `compatible`, `partial`, or `mismatch`, along with assessment source and per-region findings.

`compatible` means no material conflict was found for the reviewed visible scope. It does not mean geometrically verified. A face may be compatible while the back garment is not. Unreviewed/failed regions cannot populate a verified evidence slot or supply reliable features.

Do not automatically cluster characters as the same identity merely because their image embeddings are similar. Embeddings may retrieve possible links for review; they are not authoritative identity assignments.

### 5.5 Core TypeScript contracts

These are domain contracts. Public write schemas are narrower and MUST reject unknown fields. The server supplies ownership, hashes, revisions, capability flags, and derived eligibility.

```ts
type Region = "whole" | "face" | "hair" | "body" | "outfit"
            | "accessories" | "palette" | "surface" | "custom";
type PropertyState = "unspecified" | "proposed" | "inferred" | "user_confirmed";
type Purpose = "design_variant" | "additional_view" | "unspecified_part"
             | "state_study" | "depiction_correction";

interface DesignVersion {
  schemaVersion: "2.0";
  projectId: string;
  designId: string;
  designVersionId: string;
  revision: number;
  parentVersionId: string | null;
  canonicalSpecHash: string;
  morphology: "humanoid" | "non_humanoid" | "unspecified";
  properties: Record<string, {
    value: string | number | boolean | string[] | null;
    state: PropertyState;
    sourceEventIds: string[];
    sourceDepictionLinkIds: string[];
  }>;
  componentRelations: Array<{
    component: string;
    relation: "attached_to" | "layered_over" | "connected_to" | "symmetric_with";
    target: string;
    state: PropertyState;
  }>;
  unresolvedDecisions: string[];
}

interface Presentation {
  view: "front" | "front_three_quarter" | "character_left_profile"
      | "character_right_profile" | "back" | "back_three_quarter"
      | "top" | "bottom" | "other" | "unknown";
  projection: "orthographic" | "perspective" | "unknown";
  framing: "full_body" | "upper_body" | "face" | "detail" | "unknown";
  poseId: string | null;
  expressionId: string | null;
  lightingClass: string | null;
  backgroundClass: string | null;
  cameraParameters: Record<string, number> | null;
  source: "requested" | "user_reported" | "visually_estimated" | "renderer_metadata";
}

interface FeatureObservation {
  observationId: string;
  depictionLinkId: string;
  extractorVersion: string;
  featureSchemaVersion: "design-features-v2";
  region: Region;
  values: Record<string, string | number | null>;
  visibility: Record<string, "visible" | "occluded" | "out_of_frame" | "unknown">;
  confidence: Record<string, number>;
  observedPresentation: Presentation;
  qualityFlags: string[];
  geometricVerification: "none"; // MVP image analysis never verifies a mesh
}

interface EvidenceBundle {
  bundleId: string;
  designVersionId: string;
  evaluationProfileId: string;
  inputEventSequence: number;
  depictionLinkIds: string[];
  exposedRegions: Region[];
  observationIds: string[];
  evidenceHash: string;
}

interface PromptPlan {
  schemaVersion: "2.0";
  planId: string;
  revision: number;
  purpose: Purpose;
  targetDesignVersionId: string;
  canonicalSpecHash: string;
  basedOnEventSequence: number;
  constraintsVersion: number;
  renderRecipeId: string;
  evaluationSlotId: string | null;
  changeDesignProperties: string[];
  preserveDesignProperties: string[];
  references: Array<{
    assetId: string;
    attachmentOrder: number;
    role: "identity" | "component" | "material" | "view_example";
    instruction: string;
  }>;
  promptText: string;
  attachmentInstructions: string;
  unresolvedAssumptions: string[];
  executionMode: "prompt_only";
  imageStatus: "not_generated";
}
```

For `additional_view`, `state_study`, and `depiction_correction`, `changeDesignProperties` MUST be empty. A correction restores the intended design; it does not redesign it. A proposed permanent change uses a new design version and `design_variant` or `unspecified_part`.

A `view_example` is only a presentation reference. Its face, clothing, or palette must not silently enter the canonical specification.

---

## 6. Evidence review, consistency, and 3D meaning

### 6.1 Import pipeline

```text
Validate image bytes and user authorization
  → save immutable original and safe derivatives
  → record declared source and optional prompt revision
  → associate with an intended version, without assuming adherence
  → extract actual visible features and actual/estimated conditions
  → audit design and identity consistency
  → publish reviewed regions or retain unresolved findings
  → update coverage and eligible comparison candidates
```

A prompt attachment or generation seed does not establish adherence. Same prompt, seed, or service does not prove that independent views describe a common 3D object.

### 6.2 Distinct issue classes

Use separate finding kinds:

| Kind | Meaning | Next action |
|---|---|---|
| `presentation_mismatch` | Wrong requested angle, pose, crop, expression, or lighting | Retry that evidence request or revise the observed context |
| `identity_or_design_drift` | Different face, proportions, component, or confirmed property | Correct the depiction or explicitly adopt a variant |
| `design_unspecified` | Required unseen structure is not defined | Propose alternative designs for that property |
| `cross_view_conflict` | Depictions imply incompatible visible design details | Resolve references; do not average them |
| `design_suitability` | Faithful evidence reveals an unwanted character property | Propose a canonical design revision |
| `execution_defect` | Malformed or unusable external result | Exclude relevant regions without taste labels |
| `implementation_issue_reported` | An issue observed in an external model build | Link the exact build and request an implementation fix |

Findings carry severity, affected version, region, evidence links, whether user or model reported them, and `open`, `resolved`, `accepted_tradeoff`, or `dismissed` state. Model-generated findings are suggestions until reviewed; never imply direct inspection of unprovided geometry.

### 6.3 Visible consistency checks

Check only what the evidence makes observable: color placement, hairstyle parting and attachments, garment layers and length, accessory side, facial proportions under reasonably comparable states, and repeated component shapes. Record pose/expression-dependent changes rather than treating them all as drift.

Left/right labels are in **character space**. A character-left profile shows the character's left side. Do not infer that two profiles are equivalent unless symmetry is specified and the relevant properties support that assumption. Do not mirror an image as a substitute for an unobserved side.

A prompt can request an orthographic view. A generated illustration is still `projection: unknown` or visually estimated unless the projection has a reliable source. Exact focal length, camera pose, measurements, thickness, and hidden geometry must remain unknown when they cannot be observed.

### 6.4 Source and proof levels

Track these independently:

- **Concept depiction:** An illustration or externally generated image.
- **Model capture, user-reported:** A user states that the image came from a particular model build.
- **Artifact-inspected evidence:** A later trusted integration verifies a model artifact and captures; outside the MVP.

A supplied model hash is a provenance identifier, not proof that every image came from those bytes. Do not promote user-reported provenance to trusted inspection.

Even matching captures from the same model do not prove topology quality, skinning correctness, deformation limits, clipping under every motion, or runtime performance. These require explicit tests against the actual implementation. Record the scope of any external test report.

### 6.5 No hidden geometry invention

The application may propose how an unseen back, attachment, mouth interior, or garment layer could be designed. It must label that as a proposal, provide alternatives when relevant, and link its later adoption to a user event.

Do not claim to recover the user's intended hidden geometry from a single image. “Unknown” is a valid and useful state in both the interface and the handoff.

---

## 7. Evaluation profiles: varying conditions without learning pose taste

### 7.1 Evaluation is a design test plan

An `EvaluationProfile` defines which surfaces, conditions, and use states need evidence. It is task configuration, not a learned distribution of aesthetically preferred cameras.

The planner decides both **which design to investigate** and **which evidence would reduce uncertainty about it**. Evidence selection can be adaptive while the target remains pose- and composition-independent.

### 7.2 Starter profile for a humanoid avatar

These are staged defaults, not a requirement to create every image immediately.

| Stage | Slots | Main question |
|---|---|---|
| Direction screening | Neutral front or front-three-quarter; face and full-body where relevant | Is this a promising character direction? |
| Shortlist structure | Front, profile, back; opposite profile for asymmetry/unknown symmetry; face detail | Is the same design specified and satisfactory beyond the hero image? |
| Finalist state studies | Neutral, smile, blink, open mouth; raised arm, seated or other relevant pose | Do facial design, hair, clothing, and accessories remain suitable in use? |
| External prototype review | Captures from a declared common build under the required views/states | What actually needs revision in the implementation? |

For neutral structural views, request consistent scale, unobstructed important parts, simple lighting/background, and a consistent neutral pose. A symmetric relaxed stance or A-pose-like study can be useful; a T-pose is only requested when the downstream workflow calls for it. None of these 2D requests certifies a valid bind pose or rig.

For non-humanoid characters, replace anatomy-specific slots with applicable surfaces, articulation states, and component views. The application must not manufacture face or limb requirements for a design that does not have them.

### 7.3 View requirements are not framing preferences

A face crop reveals facial details but cannot satisfy a full-body proportion slot. A full-body image may not show enough detail to evaluate eyes or small ornaments. Different crops are useful because they expose different properties, not because the user is learning to prefer close-ups.

At final selection, do not automatically privilege the most flattering image. Show the selected version's required evidence and unresolved concerns together.

### 7.4 Coverage accounting

Each slot is `missing`, `imported_unreviewed`, `usable_concept_evidence`, `user_reported_model_evidence`, or `not_applicable`. Store issues separately. A slot with a blocking issue is not ready even if an image exists.

```text
reference_coverage = usable_required_slots / applicable_required_slots
```

This is only a completeness indicator for the chosen profile. It is not probability of preference, geometric consistency, or production readiness. If the denominator is zero, report “profile not configured,” not 100%.

`not_applicable` requires a recorded reason tied to morphology or project scope. The planner must not remove a difficult view merely to improve the percentage. Duplicates, different crops of one source, and multiple failed retries do not increase independent coverage.

### 7.5 Balanced comparisons

Compare A and B on the same relevant view/state slots. If only A has a reviewed back view, do not penalize B's absent back as an unattractive back. Mark the gap and request it if the comparison needs it.

A comparison can remain deliberately scoped: “Compare these faces from the front.” Save that scope. It is evidence about a frontally visible face-design difference, not complete evidence about the character or its profile.

---

## 8. Feedback semantics and event sourcing

### 8.1 Event contract

```ts
interface FeedbackInput {
  schemaVersion: "2.0";
  eventId: string;
  branchId: string;
  reviewSessionId: string | null;
  domain: "visual_design" | "design_intent" | "evidence_review" | "project";
  action: "compare" | "shortlist_add" | "shortlist_remove" | "reject_design"
        | "lock_property" | "unlock_property" | "flag_depiction"
        | "report_design_issue" | "adopt_variant" | "undo" | "reset"
        | "fork_branch" | "confirm_checkpoint";
  subjectVersionIds: string[];
  outcome?: "A" | "B" | "tie" | "neither" | "skip";
  region: Region;
  targetEventId?: string;
  details?: Record<string, unknown>; // validated per action, never a free pass-through
  expectedEventSequence: number;
  clientOccurredAt: string;
}
```

A design-intent comparison may have empty image bundles and an explicitly unrendered review state. It compares written specifications only; it is never eligible for the visual ranker.

The server derives the exposed evidence, canonical hashes, eligibility, masks, and training family from the sealed review session. It must reject client-provided training weights, principal IDs, capability flags, and claimed consistency approval.

### 8.2 Interpretation

An explicit eligible A/B choice creates one relative design observation. A tie is weak equality evidence, not rejection. Neither records dissatisfaction without inventing a direction. Skip, missing images, ignored cards, and navigation create no taste label.

A design rejection excludes that version from the ordinary shortlist without asserting which property caused it. A depiction rejection does not reject the canonical design. A design-level choice made with insufficient or confounded evidence is still preserved, but is marked `provisional_not_trained` and can drive the next evidence request.

A region choice trains only that region's feature model. A custom crop records its source coordinates and the design properties considered visible; a crop by itself does not establish an intrinsic feature.

### 8.3 Frozen evidence, corrections, and undo

Store the exact design versions, depiction links, observations, comparison basis, and evidence hash used at decision time. Newly imported views must not silently rewrite what the user previously saw or multiply that vote.

If a later review invalidates an earlier depiction's identity/adherence, append a correction event and invalidate affected training rows. Preserve the historical action and its original evidence snapshot. Do not automatically re-label the decision using unseen replacement images.

Undo is a compensating event. Replay effective history rather than adding an opposite preference. In the MVP, an event can be undone once; redo is a new ordinary action. Actions that invalidate confirmed checkpoints must mark those checkpoints outdated rather than silently editing an exported handoff.

### 8.4 Branches and repeated evidence

A branch fork records its parent and the exact inherited sequence. Future changes to the parent do not rewrite the child. Inherited evidence is counted once. Keep incompatible character directions separate rather than averaging them into one supposed ideal.

Correlated view-level judgments from the same comparison must not be treated as independent votes. Normalize total weight within an unordered design-version pair, branch preference epoch, and region to at most one. Preserve contextual disagreements as findings; do not hide them with a confidently averaged score. Repeated decisions can change the effective label distribution but cannot indefinitely increase confidence through repeated presentations of the same pair.

A preference reset starts a new epoch. Preserve or clear explicit locks only according to the user's separate choice. No automatic time decay is required in the MVP.

---

## 9. Preference learning

### 9.1 Separate intent, observation, and suitability

Canonical specifications drive prompt generation and constraint checking. Observed, reviewed character features drive visual preference learning. Design-intent choices can prioritize proposed variations, but have a separate evidence domain and never become visual labels.

Design suitability findings and technical feasibility are not equivalent to taste. The system may flag a difficult component without overriding a confirmed preference for it. Offer a documented tradeoff or implementation route rather than silently simplifying the character.

### 9.2 Feature schema

Start with bounded, interpretable character features and a fixed vocabulary. Appendix C defines a small starter schema. Unknown or occluded properties have explicit masks. Do not estimate full-body proportions from face-only images, neutral eye size from a blink, or material gloss from a single uncontrolled highlight.

Only use reviewed regions of `compatible` or eligible `partial` links. Extractor confidence, presentation uncertainty, preference uncertainty, and implementation-test confidence are different quantities.

Feature aggregation must preserve conflicting observations. Do not average front and profile screen-space measurements into an alleged 3D measurement. Use observations appropriate to each descriptor and comparable context; unresolved conflict remains missing for the affected feature.

Optional image embeddings may support duplicate detection, retrieval, and visual diversity. They are not the MVP's taste vector because whole-image similarity can include pose, lighting, and background. A future learned representation requires held-out nuisance tests before it replaces explicit features.

### 9.3 Eligibility before training

A visual pair is trainable only if:

1. It refers to two distinct immutable design versions owned by the same project and the correct branch history.
2. The exposed evidence supports the stated region and design attributes on both sides.
3. Observed presentation is sufficiently comparable under the versioned comparison policy; equal *requested* recipes are not enough.
4. There are no blocking identity, execution, or consistency issues in those attributes.
5. At least one comparable design-feature difference is observable.

Unknown presentation or a heavily occluded feature should lead to a scoped comparison or another evidence request, not a fabricated normalization. A same-version comparison can review rendering quality but is never an A-versus-B design preference.

Required presentation controls are scope-dependent. A cropped, well-isolated hair comparison need not match irrelevant background decoration; a proportion measurement may require stronger projection evidence. The qualification policy records which controls matter and why.

Use a matched-bundle comparison for broad whole-character decisions. Do not claim that a single frontal face pair validates a whole body or all angles.

### 9.4 Masked pairwise logistic baseline

For a branch and region, let `x_A` and `x_B` be normalized **observed** features from the frozen comparison evidence. Let `m_k` include only features visible, reliable, relevant, and comparable in both candidates:

```text
delta_k = (x_A - x_B) * m_k
p_k = sigmoid(w^T delta_k)

L(w) = (lambda / 2) * ||w||^2
     + sum_k a_k * [log(1 + exp(w^T delta_k)) - y_k * w^T delta_k]

Targets: A → 1; B → 0; explicit tie → 0.5
Initial base weights: decisive choice → 1; tie → 0.5
Family-normalized weight:
  a_k = base_k / max(1, sum of base weights in the same evidence family)
```

Use `lambda = 1`, float64, stable softplus, and a tested optimizer. Appendix B provides the numerical reference implementation and helpers. The tie treatment is a soft-equality approximation, not a full model of ties.

No eligible observations means **insufficient evidence**, not proof that all designs are equally satisfactory. Model convergence means numerical convergence, not that the user's preferences have been found.

### 9.5 Ranking with missing features

An unknown feature may be encoded as zero only together with its mask. It MUST NOT be ranked as though zero were an observed neutral preference.

For an existing board, choose a shared reliable feature basis within the relevant cohort and score designs on that basis. Show partial coverage. If there is no informative common basis, use diversity and evidence collection rather than a global score. Pairwise predictions with different masks are not automatically comparable as a universal scalar ranking.

Region models remain separate. Do not silently average “preferred face,” “preferred hair,” and “preferred outfit” into a whole-character preference without a defined aggregation rule or user-level whole-design evidence.

### 9.6 Uncertainty and acquisition

Use the regularized Hessian and a local pair-acquisition heuristic:

```text
H = lambda * I + sum_k a_k * p_k * (1-p_k) * delta_k * delta_k^T
v = delta^T * solve(H, delta)
I(A,B) = 0.5 * log(1 + p(A>B)*(1-p(A>B))*v)
```

This is an implementation heuristic, not a calibrated posterior guarantee. An indistinguishable feature pair has no feature-learning value even when its predicted probability is 0.5.

Keep three separate outputs: `predicted_relative_preference`, `evidence_coverage`, and `open_design_or_implementation_issues`. Do not disguise missing back views or geometric uncertainty inside a single aesthetic score.

### 9.7 Robustness is a workflow requirement

A high frontal preference score must not waive an important profile conflict. Finalists progress through a task-defined evaluation profile. Where views reveal conflicting design tradeoffs, show them explicitly and ask for a design decision through the normal comparison interface.

This MVP reduces presentation confounding through controlled evidence and provenance. It does not claim to mathematically identify a fully pose-invariant latent 3D preference from arbitrary 2D images.

### 9.8 Preference hypotheses

A hypothesis records its statement, region/property, supporting event IDs, contradicting event IDs, and `tentative`, `user_confirmed`, `contradicted`, or `retired` state. It must distinguish observations of appearance from user preferences about that appearance. Confirmation is a user action; more successful image extraction cannot confirm a taste hypothesis by itself.

Qualitative accessory or unusual-form feedback can guide text proposals without entering the numerical ranker. Keep such evidence visible rather than forcing every judgment into the starter feature schema.

---

## 10. Selecting the next action

### 10.1 Two independent decisions

The scheduler first chooses the useful action type, then selects a design or comparison. Valid action types are:

```text
compare_existing_designs
request_missing_view
resolve_unspecified_design_property
request_state_study
correct_unfaithful_depiction
propose_design_variant
prepare_handoff
```

A “request” means prepare text, not call a generator.

### 10.2 Initial priority policy

Prioritize a blocking inconsistency in a promising candidate, then a critical missing surface/state, then an informative design comparison, then a targeted variant or constraint-compliant alternative. This is a default, not a mandate to stop all exploration until every image is perfect.

Use explicit action budgets so the system cannot produce an endless cycle of correction prompts. After repeated failed depictions, retain the issue and suggest a different external production method or a human modeling decision in the handoff. Do not pretend the missing evidence has been obtained.

### 10.3 Six-card exploration board

Start with up to three promising distinct design versions, an informative pair, and a diverse feasible alternative. Deduplicate versions and near-identical evidence. A pinned anchor is not a preference label.

As the shortlist stabilizes, use the same display area for **different evidence of the same finalist** in inspection mode, not as six new preference candidates. Keep exploration and inspection visually distinct.

### 10.4 Adaptive evidence priority

A simple uncalibrated priority can use:

```text
priority(design, slot) = relevance_to_current_decision
                      * unresolved_design_risk
                      * expected_observability_gain
                      / estimated_user_effort
```

These are versioned heuristic quantities. They choose what to inspect, not which pose the user should like. Do not derive them from dwell time or remove unflattering conditions to increase engagement.

### 10.5 Checkpoint recommendation

Suggest a checkpoint when a user-preferred version has enough reviewed coverage for the next downstream task and its unresolved decisions are explicit. Require user confirmation. The product can export an incomplete-but-honest handoff; it must not falsely mark it production-ready.

---

## 11. Prompt planning and external round trip

### 11.1 Typed reasoning tasks

Expose only these application jobs:

```text
describe_depictions
review_design_consistency
propose_next_actions
compile_prompt_pack
summarize_preferences
compile_design_handoff
```

All return validated JSON/text. The context contains the objective, immutable canonical spec, confirmed locks, actual observations, relevant feedback IDs, open issues, requested output schema, and authorized reference images. Imported text and images are untrusted data, not instructions that can alter policy.

### 11.2 Two kinds of controlled experiment

**Design experiment:** Hold presentation and other relevant properties fixed; vary a designated character property between design versions.

**Observation experiment:** Hold the character design fixed; vary viewpoint, pose, expression, or another test condition to reveal it.

A single plan must say which kind it is. Do not ask a generator to change the hairstyle while also producing “another view of the exact same design” and then treat the result as equivalent evidence.

### 11.3 Prompt compiler

Each prompt is self-contained and expands:

```text
Purpose and target design version
Canonical character description
Confirmed component/palette/asymmetry preservation rules
Allowed design changes, if any
Requested view, pose, expression, projection intent, crop, lighting, and background
Required reference attachments and their roles
Visible detail requirements
Explicit unknowns or proposed details
No-redesign instruction for observation-only requests
```

Use a fixed canonical-spec hash across an observation pack. Immutable `RenderRecipe` records contain requested conditions only. Actual returned conditions are assessed separately.

Export separate prompts per view/state by default. A single combined turnaround sheet may be requested as an optional convenience, but each panel must be imported/cropped and reviewed independently. A collage is not automatically a consistent model sheet.

### 11.4 Planner instruction template

```text
You plan evidence and text prompts for reusable 3D character design.
The user is choosing a character, not a photograph, pose, or composition.

Return only the supplied JSON schema. Never create images or execute tools.
Treat confirmed character requirements as binding and taste summaries as hypotheses.
Use only supplied evidence IDs. Do not invent user preferences or unseen geometry.

For each action, choose one:
- vary a character-design property in a new version;
- observe the same version under another relevant condition;
- propose a previously unspecified design property;
- correct a depiction that failed to follow the design.

Do not learn camera, pose, expression-state, framing, lighting, or background tastes.
Do identify design properties that fail in a relevant view or state.
Keep requested conditions separate from observed conditions.
Do not equate a requested orthographic view with verified camera metadata.
Do not equate matching 2D images with a validated 3D model.

Every exported prompt must explain the reference attachments, preserved identity,
allowed changes, test conditions, and unresolved assumptions without relying on
internal application IDs being understood by an external generator.
```

### 11.5 Example: observation-only profile request

```text
PURPOSE: Inspect the profile of the already selected character design.
This is not a new character or a hairstyle/outfit redesign.

Use reference attachment 1 for the same face, head/body proportions, hair shape,
clothing, palette, and accessories. Use attachment 2 only for the approved hair
ornament detail. Keep the ornament on the character's left side, not a fixed
screen side. Preserve all already defined details.

Show the character's left profile in a neutral expression and neutral standing
pose. Request an orthographic-style structural view, with the entire relevant
silhouette visible, plain background, and soft neutral lighting. Do not add
cinematic perspective, a beauty pose, or unrelated props.

Keep the front and side parts of the approved design consistent. Do not replace
the nose, jaw, hair attachment, garment layers, or ornament to improve this view.
If an unseen detail is not defined by the references, any necessary addition is
a proposal to review, not an approved permanent feature.
```

The compiler must replace generic attachment descriptions with the actual project's canonical description and manifest. An external generator may still fail to follow this prompt; the import process checks the result.

### 11.6 Importing external results

Require a plan/revision mapping or an explicit unassociated-reference choice. Allow several depictions per plan. Store optional service/model/seed/prompt modifications as reported metadata, not as reproducibility guarantees.

Import does not imply approval. A result first enters review. A missing requested view stays missing if the returned image shows another angle. A profile result with a redesigned face triggers a correction or explicit variant adoption.

The application must not automatically open, submit to, monitor, or retrieve from the external generator. Copying and exporting prompt text are the entire outbound generation workflow in community mode.

### 11.7 Output validation

The server validates schema, target version, canonical hash, referenced assets and their ownership, requested slot, preservation rules, allowed changes, and event-sequence freshness. It rejects proposed IDs/capabilities supplied by the LLM and inserts trusted fields itself.

Use at most one schema-repair attempt within the request budget. Refusal, incomplete stream, contradiction, or failed validation produces a failed/stale plan, not an automatic synthesis fallback.

---

## 12. Architecture and implementation stack

Use React/TypeScript for the browser UI, Python/FastAPI for a loopback backend, Pydantic for strict contracts, SQLite for transactional storage, an on-disk image store, HTTPX or a tested SDK for SIWC transport, and NumPy for the baseline preference model. Pin actual versions in lockfiles and test them; this specification does not assert current package versions.

```text
Local browser UI
  ├─ design board and synchronized comparisons
  ├─ evidence/consistency inspection
  ├─ text prompt workspace
  └─ 3D design handoff
       │ same-origin authenticated application API
       ▼
Application service
  ├─ user/session authorization and prompt-only policy
  ├─ immutable design and evidence repositories
  ├─ event store and deterministic reducers
  ├─ comparison eligibility and preference ranker
  ├─ evaluation-profile and next-action planner
  ├─ prompt compiler and external-result importer
  └─ durable jobs and exports
       ├─ SQLite + immutable image assets
       ├─ CPU feature/ranking worker
       └─ SIWC adapter + per-user protected credentials
                 ▼
          text/vision reasoning only

Independent external generator or modeling tool
  User exports instructions → works outside the app → manually imports results
```

The event store and user-confirmed requirements are authoritative. LLM descriptions, proposed links, preferences summaries, and consistency audits are replaceable derived artifacts.

### 12.1 Suggested repository

```text
apps/web/
apps/server/app/
  auth/                    # SIWC, local sessions, token storage
  contracts/               # strict schemas and generated frontend types
  domain/designs/          # canonical specs, versions, locks
  domain/evidence/         # links, observations, bundles, validation findings
  domain/reviews/          # frozen comparisons and eligibility
  domain/events/           # reducers, undo, epochs, forks
  learning/                # features, masked ranker, family weighting
  planning/                # next action, profiles, typed prompts
  providers/siwc/          # narrow request builder and streaming
  storage/                 # migrations, repositories, immutable assets
  jobs/                    # durable job state machine
  exports/                 # prompt and 3D design handoff packs
schemas/
fixtures/
specs/
extensions/private_owner/  # absent from community package/build
```

### 12.2 Policy context

Construct on the server:

```ts
interface ExecutionContext {
  principalId: string;
  projectId: string;
  registrationId: string | null;
  mode: "community_prompt_only" | "private_owner";
  allowImageAnalysis: boolean;
  allowPromptPreparation: boolean;
  allowImageGeneration: boolean; // always false in community mode
  inputEventSequence: number;
  constraintsVersion: number;
}
```

Check authorization at enqueue and immediately before execution. The community runtime has no executor for generation even if malformed data claims otherwise.

---

## 13. SIWC implementation contract

External integration facts in this section were checked against the cited official documentation on 2026-10-15. Revalidate before release. These notes are not a substitute for a live sign-in and inference smoke test.

### 13.1 Local authorization

Implement the official local registration flow. Use a stable opaque host ID, fresh state/nonce/S256 PKCE per attempt, and the system browser. Initial authorization uses `dynamic_agent_client`; exchange the code with the issued client ID returned by registration and retain it for reauthorization. Validate the ID token and the granted—not merely requested—plan-use scope. Keep the loopback scheme, hostname, and path stable; the selected port may vary between attempts. [S02]

```text
authorize: https://auth.openai.com/api/accounts/authorize
token:     https://auth.openai.com/api/accounts/oauth/token
resource:  https://api.openai.com/v1
callback:  http://127.0.0.1:<available-port>/auth/callback
scopes:    openid profile email offline_access
           resource.invoke chatgpt.tokens.use.direct
```

Use the complete official registration contract for query fields, issued-client handling, callback validation, and ID-token verification. Do not borrow another application's OAuth registration or use browser cookies. The official cookbook is an additional implementation reference. [S02, S08]

### 13.2 Account and credential handling

Associate credentials with the validated issuer, subject, and issued client ID, not email alone. Keep registrations separate, validate returning identity before replacement, and serialize refreshes so rotating refresh tokens do not race. Use the discovery document's revocation endpoint on sign-out where possible; distinguish local sign-out from confirmed remote revocation. [S03]

Use a protected OS credential store or atomic owner-only credential files outside project assets and model context. The browser gets an application session, never the provider token. A local offline profile requires explicit binding to a validated registration. Account switching cancels/pauses pending work bound to the old identity; it never moves that work to the new account.

### 13.3 Model discovery and responses

Use `GET /v1/models` with the active OAuth bearer token. The documented SIWC catalog contains `models`; display listed entries in provider order and use their `slug`. Call `POST /v1/responses` with the same registration's token. Do not assume a hard-coded model name or ordinary API-key catalog shape. Read the stream through `response.completed`; partial output is not success. [S04]

Use a narrow request builder:

```json
{
  "model": "<selected admitted model slug>",
  "instructions": "<typed task instructions>",
  "input": [{"role": "user", "content": "<bounded task context>"}],
  "store": false,
  "stream": true
}
```

For image analysis, include only authorized image inputs accepted by the selected model. Keep the application’s job and project identifiers locally rather than adding unsupported metadata fields.

### 13.4 Preview restrictions and output parsing

The current SIWC HTTP route requires an input array, `store: false`, and `stream: true`; send context in the request rather than using persistent conversation IDs. Hosted image generation is unsupported on this route. Image input depends on model acceptance. Several generic API parameters, including temperature and `max_output_tokens`, are unsupported, so omit optional fields unless explicitly admitted. The full current restriction list is authoritative. [S05]

The community adapter sends no tools. Validate JSON in the application; use a provider structured-output option only after a compatibility test. Never treat an unsupported option as permission to switch to another billing path or agent runtime.

Disable automatic SDK retries. A bounded repair/retry is an explicit budgeted attempt. Output size is constrained by task design, parser limits, and cancellation; local cancellation does not guarantee that no provider usage occurred.

### 13.5 Error recovery

Preserve status, safe diagnostic body shape, error code, and request ID. Admission failures may have a `detail` field instead of a standard error object. Recognize these documented codes without assuming an exhaustive list: [S06]

| Code | Application action |
|---|---|
| `subscription_sharing_user_not_eligible` | Explain unavailability; no OAuth/retry loop |
| `subscription_sharing_usage_limit_exceeded` | Pause inference; retain offline functions |
| `subscription_sharing_usage_unavailable` | Preserve credentials; bounded recovery only |
| `subscription_sharing_unsupported_capability` | Correct request/capability; do not retry unchanged |
| `subscription_sharing_route_not_supported` | Inspect method and endpoint |

Do not interpret every 401 as an expired token, infer a reset time from a usage error, or erase credentials on a temporary routing failure. Incomplete/failed/interrupted streams never publish current prompt packs. Recovery paths require installation-specific tests. [S06]

---

## 14. Persistence, concurrency, and application API

### 14.1 Storage contract

Appendix A supplies a fresh-install SQLite baseline. It uses project-scoped foreign keys for the core evidence/design graph and explicit owner binding for provider jobs. JSON fields require strict application validation; SQL does not replace authorization or the typed schemas.

Store original assets and derivative hashes with project-local paths. Deduplication is project-scoped. Do not expose a cross-user content-existence oracle. Every repository call receives the authenticated principal and verifies project ownership.

Design versions, published recipes, observations, sealed bundles, and prompt revisions are immutable through application services. Corrections create new records/events. A single transaction appends the next project event sequence and updates the derived state or queues its recomputation.

### 14.2 Review transaction

Opening a comparison seals its exposed evidence, basis/masks, qualification result, and current versions. Submitting feedback checks expected sequence and review ownership, derives the training family, appends the event idempotently, and updates the effective model state.

The same client event ID and payload return the original result on retry. Reuse with different payload returns a conflict. Client time is metadata; server sequence defines order.

### 14.3 Jobs

Use `queued`, `running`, `succeeded`, `failed`, `cancelled`, `stale`, and `needs_reauth`. Bind each job to principal, project, registration, input sequence, canonical version/hash, constraints version, and request budget.

If the design or feedback changes during inference, retain the output as stale and do not promote it to the active plan. An interrupted process must not blindly resubmit a possibly consumed provider request. Show uncertainty and require an explicit new attempt where completion is unknown.

### 14.4 Application API

These are this application's routes, not OpenAI endpoints. All object access is project-authorized; mutations use typed bodies and idempotency checks.

| Method and route | Function |
|---|---|
| `POST /api/auth/siwc/start` | Begin a local authorization attempt |
| `GET /auth/callback` | Validate the pending OAuth callback |
| `GET /api/auth/registrations` | List local saved registrations without secrets |
| `POST /api/auth/active-registration` | Switch to an already validated registration |
| `POST /api/auth/sign-out` | End local session and attempt revocation |
| `GET /api/provider/models` | Active user's model catalog |
| `POST /api/projects` | Create isolated reusable-avatar project |
| `POST /api/projects/{p}/assets` | Import actual image bytes |
| `POST /api/projects/{p}/designs` | Create a design lineage and initial specification |
| `POST /api/projects/{p}/designs/{d}/versions` | Publish a new immutable design version |
| `POST /api/projects/{p}/depictions` | Describe an imported depiction and optional plan mapping |
| `POST /api/projects/{p}/depiction-links` | Propose an association with a design version |
| `POST /api/projects/{p}/evidence-reviews` | Append assessment/correction of a depiction link |
| `GET /api/projects/{p}/design-versions/{v}/evidence` | Reviewed depictions, coverage, and findings |
| `POST /api/projects/{p}/review-sessions` | Seal a comparison of two design versions |
| `POST /api/projects/{p}/feedback` | Append a validated user action |
| `GET /api/projects/{p}/preferences` | Effective models, hypotheses, and evidence limitations |
| `POST /api/projects/{p}/next-actions` | Plan bounded text-only next actions |
| `POST /api/projects/{p}/prompt-packs` | Compile/export text plans with references |
| `POST /api/projects/{p}/external-results` | Import and map independently produced images |
| `POST /api/projects/{p}/model-builds` | Register reported external build provenance, not render it |
| `POST /api/projects/{p}/checkpoints` | Confirm a design/handoff state |
| `POST /api/projects/{p}/exports` | Export a prompt pack or 3D design handoff |
| `GET /api/projects/{p}/jobs/{j}` | Inspect authorized job state |
| `POST /api/projects/{p}/jobs/{j}/cancel` | Stop local processing/request stream where possible |
| `DELETE /api/projects/{p}` | Delete project data under the retention policy |

There is no `/generate`, `/render`, `/proxy`, arbitrary provider URL, shell, or external-workflow route.

### 14.5 Initial limits

Start with six design cards, four plans per preparation action, one active SIWC request per registration, one optional repair attempt, and explicit session budgets. Accept a conservative set of raster formats such as PNG/JPEG/WebP; validate decoded size and decompression limits. Limit analysis inputs to the evidence necessary for the current task rather than uploading every view on every request.

Persist request/cache keys containing project, design hash, observation versions, schema, model slug, and extractor/prompt-template versions. Caching must never reuse another user's evidence or a result prepared for different locks.

---

## 15. Security, privacy, and no-generation enforcement

Bind the local service to loopback, use a local-launch bootstrap secret, validate Host/Origin, protect mutations against CSRF, and keep application sessions separate from provider tokens. Loopback alone is not authentication.

Treat imported captions, prompts, filenames, manifests, and image text as untrusted. They cannot change credentials, tool lists, network policy, mode, design locks, or permission state. Validate model output as data and never execute it.

Non-executable export files may include Markdown, JSON, JSONL, and imported reference images. They must not include credentials, executable generator workflows, macros, scripts disguised as images, or automatically executed commands.

Before image analysis, obtain project-level consent to transmit selected images to the provider. Offer local/manual feature entry and an offline-only mode. Remove unnecessary location metadata from derivatives while preserving privately stored originals and provenance. Do not assert redistribution rights merely because an image was publicly viewable or AI-generated.

No-generation enforcement must exist in the UI, task allowlist, backend contracts, execution registry, outbound policy, package contents, and tests. A hidden button or the provider's current lack of image generation is not sufficient enforcement. Even if SIWC later supports image generation, community behavior stays prompt-only until the product requirement changes.

Deletion removes project assets, events, observations, vectors, exports, and caches according to an explicit retention policy. Sign-out, provider disconnection, and deletion of local project data are different actions and must be presented separately.

---

## 16. 3D design handoff and completion states

### 16.1 Handoff content

The final pack must contain the chosen canonical version/hash, intended morphology, proportions and neutral facial structure, hair/clothing/accessory components, layer/attachment relationships, character-space asymmetry, palette/material intent, preserved features, and explicit unresolved details.

Include reviewed front/profile/back/detail references where available, reference-to-property mappings, conflicting references and their resolution, view/state evidence, and the text prompts still needed. Distinguish approved visual evidence from reference inspiration and unrendered proposals.

Include downstream tests: consistent identity across views, intended silhouette and volume, expression appearance, component visibility, garment/accessory behavior in relevant poses, and any declared view-dependent stylization. Technical tests such as topology, weights, collision, and runtime performance remain pending until an actual model implementation is tested.

Do not invent triangle budgets, texture limits, expression counts, VRM versions, or engine requirements before the downstream target is known. Keep them as progressive implementation fields rather than onboarding requirements.

### 16.2 Completion states

| State | Meaning |
|---|---|
| `exploring` | Character direction remains open |
| `design_selected` | User selected an immutable character specification |
| `reference_handoff_ready` | Required concept references are reviewed, or gaps/tradeoffs are explicitly accepted |
| `prototype_reviewed_external` | User reviewed identified external model-build evidence; test scope recorded |

The application MUST NOT automatically assign `production_ready`, `rig_verified`, or `all_poses_valid`. A 100% concept-reference coverage score cannot promote a design to externally tested model status.

### 16.3 Export layout

```text
avatar-design-handoff/
  README.md
  character-spec.json
  character-spec.md
  component-relations.json
  confirmed-requirements.json
  unresolved-decisions.md
  view-and-state-coverage.json
  validation-findings.json
  modeling-acceptance-checklist.md
  reference-manifest.json
  references/                       # existing files, only with export permission
  prompt-pack.json
  prompts/                          # self-contained text, no execution workflows
  preference-evidence.jsonl
  model-build-evidence.json          # only when reported external builds exist
  reproducibility.json              # versions/hashes; no false generator guarantees
```

All records state whether they express confirmed intent, tentative preference, actual 2D observation, or externally reported implementation evidence.

### 16.4 Continuing after a prototype exists

The user independently produces a prototype, registers its build identifier/hash, imports captures, and reports issues. The app distinguishes a design change from an implementation correction. An implementation fix may keep the canonical design version while producing a new `ModelBuild`; a changed nose, outfit, or hair design creates a new `DesignVersion` as well.

After either change, request regression evidence for affected surfaces/states rather than restarting all style exploration. Reuse unaffected requirements but do not claim an earlier model-build test automatically validates the new build.

---

## 17. Acceptance tests and evaluation

### 17.1 Release-blocking behavior

| Area | Required test |
|---|---|
| Candidate identity | Six depictions of one version remain one design candidate |
| Versioning | A camera/pose retry preserves the version; an adopted design change creates a version |
| Identity drift | A mismatching profile is excluded from affected evidence and taste training |
| Hidden surfaces | Missing back detail remains unknown until a proposal is adopted |
| Presentation confounding | Same requested recipes but different observed views do not qualify automatically |
| Learning | Camera/pose/background keys cannot enter the feature schema; missing features are pair-masked |
| Correlation | Repeated views/crops cannot multiply the effective weight of one design comparison |
| Partial feedback | Hair-only choice does not train face/body preference |
| Review provenance | New images do not rewrite the evidence used for a previous decision |
| Coverage | Duplicates, wrong views, and blocked slots do not improve required coverage |
| Asymmetry | Left/right accessory rules remain in character space; missing sides are not mirrored |
| Prompt policy | Observation-only plans have no design changes and preserve the canonical hash |
| No generation | Actual job registry/network traces show no synthesis, submission, or retrieval path |
| Readiness | Concept sheets never imply inspected geometry, valid rigging, or production readiness |
| Accounts and jobs | Cross-user references and payer switches are rejected at enqueue and execution |
| SIWC | Live callback, admitted model, terminal stream, error recovery, and usage pause are tested |
| Lifecycle | Idempotency, stale jobs, undo/reset/fork replay, export, and deletion preserve invariants |

Tests for nuisance invariance must distinguish two levels: numerical tests prove that excluded metadata does not affect the ranker; image/evidence tests evaluate whether extraction and comparison qualification actually resist visual confounding. Passing the former alone does not establish the latter.

### 17.2 Preference-quality evaluation

Record predictions before collecting labels. Hold out whole design lineages and near-duplicate sources where possible; splitting views of the same character between train and test can inflate results. Compare against a diversity-only baseline on similar candidate pools.

Track pre-feedback relative prediction quality, satisfaction with the selected design after additional views, unresolved design issues, and how often later evidence reverses an earlier choice. Report small samples as inconclusive. Do not optimize engagement, repeated prompt consumption, or model-written judgments of its own suggestions.

### 17.3 Manual end-to-end scenario

Import several character references, establish two candidate designs, and compare matched frontal evidence. Shortlist A and preserve its hair ornament on character-left. Prepare prompts for A's profile and back without creating images.

Import a profile that changes A's hairstyle and a back view with an unspecified clasp. The profile becomes a drift finding, not an A rejection. The clasp is a proposal, not a confirmed recovered detail. Import a corrected profile, then explicitly adopt a chosen back construction into a new design version.

Compare the revised design using sufficient matched evidence. Request expression/pose studies for the finalist. Confirm and export its handoff with any untested model checks still pending. Repeat with a second SIWC user and verify complete data and payer isolation.

---

## 18. Migration from version 1

This is a semantic migration, not a rename of `VisualCandidate`.

Back up the original database and preserve source assets/events. Convert each previously independent image candidate into an initially unverified depiction associated with a tentative design version. Group multiple images under one version only after review; do not guess identity from filenames or embeddings.

Map prior feedback to its original image evidence and mark it `legacy_unqualified` until it meets the new comparison policy. Keep useful shortlist, explicit component-lock, and design-intent history without inventing matched multiview evidence. Do not backfill unseen poses or interpret old image preference as pose preference.

Replace the feature schema with `design-features-v2`. Quarantine old `style.rendering` features that might mix intrinsic surface style and image treatment; review before reusing them. Rebuild derived rankings from qualified observations; preserve the original model snapshot as historical, not current.

Prompt revisions remain immutable. Previously exported single-image packs remain available but are not relabeled as complete 3D reference packs. Add explicit design-version, depiction-link, and evaluation-slot mapping for future imports.

Appendix A is a **fresh-install schema**, not a safe in-place migration script. Implement and test the migration separately on a copy of real v1 data before replacing an existing installation.

---

## 19. Implementation sequence

| Milestone | Deliverable | Exit condition |
|---|---|---|
| M0 | Contracts, invariants, schema, mock SIWC provider | Design/evidence separation and no-generation policy testable |
| M1 | Offline design versions, imports, links, bundles, feedback | Users can compare designs without an LLM or GPU |
| M2 | Masked ranker, evidence qualification, findings, profile coverage | Pose/camera do not become taste features; missing views stay explicit |
| M3 | Individual local SIWC, streaming, authorization, usage pause | Actual account passes text/vision smoke tests |
| M4 | Text-only next-action planner, prompt packs, manual imports | Complete multiview prompt round trip with no synthesis path |
| M5 | Handoff, external prototype evidence, migration, evaluation | Selected design can be passed to a model maker with honest limitations |
| Optional | Private owner worker or separately specified model viewer | Isolated implementation and separate capability/billing tests |
| Separate launch gate | Centrally hosted distribution | Provider integration, tenancy, and deployment requirements resolved |

**MVP definition of done:** Another person can install the app, connect their own SIWC account, progressively select a reusable character design from imported evidence, obtain only text prompts for new views or variants, import independently produced results, and export a 3D-oriented design handoff. They need not repeatedly explain taste in ChatGPT's web interface, and the application never mistakes a preferred picture, pose, or camera setup for the desired model.


---

## Appendix A. Fresh-install SQLite baseline

Execute this migration with foreign keys enabled on **every database connection**. SQLite JSON functions must be available in the packaged runtime; startup should fail with a clear compatibility error if they are missing. This is a community-mode schema, not a private-worker schema or an in-place v1 migration.

JSON columns hold the versioned domain contracts described above. SQL checks do not replace typed application validation. Secret material is stored outside this database; `secret_ref` is only an opaque credential-store reference. Timestamps omitted from some normalized tables should be added as operational metadata in implementation without changing their identity semantics.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE principals (
  principal_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL
);
CREATE TABLE registrations (
  registration_id TEXT PRIMARY KEY,
  principal_id TEXT NOT NULL REFERENCES principals(principal_id),
  issuer TEXT NOT NULL,
  subject TEXT NOT NULL,
  issued_client_id TEXT NOT NULL CHECK(issued_client_id <> 'dynamic_agent_client'),
  secret_ref TEXT,
  grant_state TEXT NOT NULL CHECK(grant_state IN ('identity_only','plan_enabled','disconnected')),
  UNIQUE(principal_id, registration_id),
  UNIQUE(issuer, subject, issued_client_id)
);
CREATE TABLE projects (
  project_id TEXT PRIMARY KEY,
  principal_id TEXT NOT NULL REFERENCES principals(principal_id),
  title TEXT NOT NULL,
  objective TEXT NOT NULL DEFAULT 'reusable_3d_avatar'
    CHECK(objective = 'reusable_3d_avatar'),
  event_sequence INTEGER NOT NULL DEFAULT 0 CHECK(event_sequence >= 0),
  constraints_version INTEGER NOT NULL DEFAULT 0 CHECK(constraints_version >= 0),
  UNIQUE(principal_id, project_id)
);
CREATE TABLE branches (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  branch_id TEXT NOT NULL,
  parent_branch_id TEXT,
  parent_sequence INTEGER,
  preference_epoch INTEGER NOT NULL DEFAULT 0 CHECK(preference_epoch >= 0),
  PRIMARY KEY(project_id, branch_id),
  FOREIGN KEY(project_id, parent_branch_id) REFERENCES branches(project_id, branch_id),
  CHECK((parent_branch_id IS NULL) = (parent_sequence IS NULL)),
  CHECK(parent_sequence IS NULL OR parent_sequence >= 0),
  CHECK(parent_branch_id IS NULL OR parent_branch_id <> branch_id)
);
CREATE TABLE designs (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  design_id TEXT NOT NULL,
  branch_id TEXT NOT NULL,
  title TEXT NOT NULL,
  PRIMARY KEY(project_id, design_id),
  FOREIGN KEY(project_id, branch_id) REFERENCES branches(project_id, branch_id)
);
CREATE TABLE design_versions (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  version_id TEXT NOT NULL,
  design_id TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK(revision >= 1),
  parent_version_id TEXT,
  canonical_hash TEXT NOT NULL CHECK(length(canonical_hash) = 64),
  canonical_json TEXT NOT NULL CHECK(json_valid(canonical_json)),
  created_sequence INTEGER NOT NULL CHECK(created_sequence >= 0),
  PRIMARY KEY(project_id, version_id),
  UNIQUE(project_id, design_id, revision),
  UNIQUE(project_id, design_id, version_id),
  UNIQUE(project_id, version_id, canonical_hash),
  FOREIGN KEY(project_id, design_id) REFERENCES designs(project_id, design_id),
  FOREIGN KEY(project_id, design_id, parent_version_id)
    REFERENCES design_versions(project_id, design_id, version_id),
  CHECK(parent_version_id IS NULL OR parent_version_id <> version_id)
);
CREATE TABLE assets (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  asset_id TEXT NOT NULL,
  digest TEXT NOT NULL CHECK(length(digest) = 64),
  storage_key TEXT NOT NULL,
  mime_type TEXT NOT NULL CHECK(mime_type IN ('image/png','image/jpeg','image/webp')),
  width INTEGER NOT NULL CHECK(width > 0),
  height INTEGER NOT NULL CHECK(height > 0),
  parent_asset_id TEXT,
  provenance_json TEXT NOT NULL CHECK(json_valid(provenance_json)),
  PRIMARY KEY(project_id, asset_id),
  FOREIGN KEY(project_id, parent_asset_id) REFERENCES assets(project_id, asset_id)
);
CREATE TABLE render_recipes (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  recipe_id TEXT NOT NULL,
  requested_json TEXT NOT NULL CHECK(json_valid(requested_json)),
  control_hash TEXT NOT NULL CHECK(length(control_hash) = 64),
  PRIMARY KEY(project_id, recipe_id)
);
CREATE TABLE evaluation_profiles (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  profile_id TEXT NOT NULL,
  profile_json TEXT NOT NULL CHECK(json_valid(profile_json)),
  PRIMARY KEY(project_id, profile_id)
);
CREATE TABLE prompt_plans (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  plan_id TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK(revision >= 1),
  target_version_id TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  recipe_id TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK(purpose IN (
    'design_variant','additional_view','unspecified_part','state_study','depiction_correction')),
  changes_json TEXT NOT NULL CHECK(json_valid(changes_json) AND json_type(changes_json)='array'),
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  input_sequence INTEGER NOT NULL CHECK(input_sequence >= 0),
  constraints_version INTEGER NOT NULL CHECK(constraints_version >= 0),
  execution_mode TEXT NOT NULL CHECK(execution_mode='prompt_only'),
  PRIMARY KEY(project_id, plan_id, revision),
  FOREIGN KEY(project_id, target_version_id, canonical_hash)
    REFERENCES design_versions(project_id, version_id, canonical_hash),
  FOREIGN KEY(project_id, recipe_id) REFERENCES render_recipes(project_id, recipe_id),
  CHECK(purpose NOT IN ('additional_view','state_study','depiction_correction')
        OR json_array_length(changes_json)=0)
);
CREATE TABLE model_builds (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  build_id TEXT NOT NULL,
  target_version_id TEXT NOT NULL,
  artifact_hash TEXT,
  provenance_level TEXT NOT NULL CHECK(provenance_level='user_reported'),
  report_json TEXT NOT NULL CHECK(json_valid(report_json)),
  PRIMARY KEY(project_id, build_id),
  FOREIGN KEY(project_id, target_version_id) REFERENCES design_versions(project_id, version_id),
  CHECK(artifact_hash IS NULL OR length(artifact_hash)=64)
);
CREATE TABLE depictions (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  depiction_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  source_kind TEXT NOT NULL CHECK(source_kind IN (
    'reference','external_result','private_owner_result','model_capture_user_reported')),
  origin_plan_id TEXT,
  origin_prompt_revision INTEGER,
  source_build_id TEXT,
  metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json)),
  PRIMARY KEY(project_id, depiction_id),
  FOREIGN KEY(project_id, asset_id) REFERENCES assets(project_id, asset_id),
  FOREIGN KEY(project_id, origin_plan_id, origin_prompt_revision)
    REFERENCES prompt_plans(project_id, plan_id, revision),
  FOREIGN KEY(project_id, source_build_id) REFERENCES model_builds(project_id, build_id),
  CHECK((origin_plan_id IS NULL)=(origin_prompt_revision IS NULL)),
  CHECK((source_kind='model_capture_user_reported')=(source_build_id IS NOT NULL))
);
CREATE TABLE depiction_links (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  link_id TEXT NOT NULL,
  depiction_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('unreviewed','compatible','partial','mismatch')),
  assessment_json TEXT NOT NULL CHECK(json_valid(assessment_json)),
  supersedes_link_id TEXT,
  PRIMARY KEY(project_id, link_id),
  UNIQUE(project_id, link_id, version_id),
  FOREIGN KEY(project_id, depiction_id) REFERENCES depictions(project_id, depiction_id),
  FOREIGN KEY(project_id, version_id) REFERENCES design_versions(project_id, version_id),
  FOREIGN KEY(project_id, supersedes_link_id) REFERENCES depiction_links(project_id, link_id),
  CHECK(supersedes_link_id IS NULL OR supersedes_link_id <> link_id)
);
CREATE TABLE observations (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  observation_id TEXT NOT NULL,
  link_id TEXT NOT NULL,
  region TEXT NOT NULL,
  feature_schema TEXT NOT NULL CHECK(feature_schema='design-features-v2'),
  extractor_version TEXT NOT NULL,
  observed_json TEXT NOT NULL CHECK(json_valid(observed_json)),
  PRIMARY KEY(project_id, observation_id),
  FOREIGN KEY(project_id, link_id) REFERENCES depiction_links(project_id, link_id)
);
CREATE TABLE evidence_bundles (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  bundle_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  input_sequence INTEGER NOT NULL CHECK(input_sequence >= 0),
  evidence_hash TEXT NOT NULL CHECK(length(evidence_hash)=64),
  frozen_json TEXT NOT NULL CHECK(json_valid(frozen_json)),
  PRIMARY KEY(project_id, bundle_id),
  UNIQUE(project_id, bundle_id, version_id),
  FOREIGN KEY(project_id, version_id) REFERENCES design_versions(project_id, version_id),
  FOREIGN KEY(project_id, profile_id) REFERENCES evaluation_profiles(project_id, profile_id)
);
CREATE TABLE bundle_items (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  bundle_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  link_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
  exposed_regions_json TEXT NOT NULL CHECK(json_valid(exposed_regions_json)),
  PRIMARY KEY(project_id, bundle_id, link_id),
  UNIQUE(project_id, bundle_id, ordinal),
  FOREIGN KEY(project_id, bundle_id, version_id)
    REFERENCES evidence_bundles(project_id, bundle_id, version_id),
  FOREIGN KEY(project_id, link_id, version_id)
    REFERENCES depiction_links(project_id, link_id, version_id)
);
CREATE TABLE review_sessions (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  review_id TEXT NOT NULL,
  branch_id TEXT NOT NULL,
  region TEXT NOT NULL,
  input_sequence INTEGER NOT NULL CHECK(input_sequence >= 0),
  qualification_json TEXT NOT NULL CHECK(json_valid(qualification_json)),
  PRIMARY KEY(project_id, review_id),
  UNIQUE(project_id, branch_id, review_id),
  FOREIGN KEY(project_id, branch_id) REFERENCES branches(project_id, branch_id)
);
CREATE TABLE review_items (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  review_id TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN ('A','B')),
  version_id TEXT NOT NULL,
  bundle_id TEXT NOT NULL,
  PRIMARY KEY(project_id, review_id, side),
  UNIQUE(project_id, review_id, version_id),
  FOREIGN KEY(project_id, review_id) REFERENCES review_sessions(project_id, review_id),
  FOREIGN KEY(project_id, bundle_id, version_id)
    REFERENCES evidence_bundles(project_id, bundle_id, version_id)
);
CREATE TABLE events (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  event_id TEXT NOT NULL,
  sequence INTEGER NOT NULL CHECK(sequence >= 1),
  branch_id TEXT NOT NULL,
  review_id TEXT,
  domain TEXT NOT NULL CHECK(domain IN ('visual_design','design_intent','evidence_review','project')),
  action TEXT NOT NULL CHECK(action IN (
    'compare','shortlist_add','shortlist_remove','reject_design','lock_property','unlock_property',
    'flag_depiction','report_design_issue','adopt_variant','undo','reset','fork_branch',
    'confirm_checkpoint','correct_evidence')),
  target_event_id TEXT,
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  request_hash TEXT NOT NULL CHECK(length(request_hash)=64),
  server_occurred_at TEXT NOT NULL,
  PRIMARY KEY(project_id, event_id),
  UNIQUE(project_id, sequence),
  FOREIGN KEY(project_id, branch_id) REFERENCES branches(project_id, branch_id),
  FOREIGN KEY(project_id, branch_id, review_id)
    REFERENCES review_sessions(project_id, branch_id, review_id),
  FOREIGN KEY(project_id, target_event_id) REFERENCES events(project_id, event_id),
  CHECK(action <> 'compare' OR review_id IS NOT NULL),
  CHECK(action <> 'undo' OR target_event_id IS NOT NULL),
  CHECK(target_event_id IS NULL OR target_event_id <> event_id)
);
CREATE TABLE findings (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  finding_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  link_id TEXT,
  kind TEXT NOT NULL CHECK(kind IN (
    'presentation_mismatch','identity_or_design_drift','design_unspecified','cross_view_conflict',
    'design_suitability','execution_defect','implementation_issue_reported')),
  state TEXT NOT NULL CHECK(state IN ('open','resolved','accepted_tradeoff','dismissed')),
  details_json TEXT NOT NULL CHECK(json_valid(details_json)),
  PRIMARY KEY(project_id, finding_id),
  FOREIGN KEY(project_id, version_id) REFERENCES design_versions(project_id, version_id),
  FOREIGN KEY(project_id, link_id, version_id)
    REFERENCES depiction_links(project_id, link_id, version_id)
);
CREATE TABLE preference_snapshots (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  snapshot_id TEXT NOT NULL,
  branch_id TEXT NOT NULL,
  through_sequence INTEGER NOT NULL CHECK(through_sequence >= 0),
  feature_schema TEXT NOT NULL CHECK(feature_schema='design-features-v2'),
  state_json TEXT NOT NULL CHECK(json_valid(state_json)),
  PRIMARY KEY(project_id, snapshot_id),
  FOREIGN KEY(project_id, branch_id) REFERENCES branches(project_id, branch_id)
);
CREATE TABLE jobs (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  job_id TEXT NOT NULL,
  principal_id TEXT NOT NULL,
  registration_id TEXT NOT NULL,
  task TEXT NOT NULL CHECK(task IN (
    'describe_depictions','review_design_consistency','propose_next_actions',
    'compile_prompt_pack','summarize_preferences','compile_design_handoff')),
  execution_mode TEXT NOT NULL CHECK(execution_mode='prompt_only'),
  state TEXT NOT NULL CHECK(state IN (
    'queued','running','succeeded','failed','cancelled','stale','needs_reauth')),
  input_sequence INTEGER NOT NULL CHECK(input_sequence >= 0),
  request_json TEXT NOT NULL CHECK(json_valid(request_json)),
  result_json TEXT CHECK(result_json IS NULL OR json_valid(result_json)),
  PRIMARY KEY(project_id, job_id),
  FOREIGN KEY(principal_id, project_id) REFERENCES projects(principal_id, project_id),
  FOREIGN KEY(principal_id, registration_id)
    REFERENCES registrations(principal_id, registration_id)
);
CREATE TABLE checkpoints (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  checkpoint_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  bundle_id TEXT NOT NULL,
  confirmation_event_id TEXT NOT NULL,
  stage TEXT NOT NULL CHECK(stage IN (
    'design_selected','reference_handoff_ready','prototype_reviewed_external')),
  status TEXT NOT NULL CHECK(status IN ('current','outdated')),
  acceptance_json TEXT NOT NULL CHECK(json_valid(acceptance_json)),
  PRIMARY KEY(project_id, checkpoint_id),
  FOREIGN KEY(project_id, bundle_id, version_id)
    REFERENCES evidence_bundles(project_id, bundle_id, version_id),
  FOREIGN KEY(project_id, confirmation_event_id) REFERENCES events(project_id, event_id)
);
CREATE INDEX idx_links_version ON depiction_links(project_id, version_id, status);
CREATE INDEX idx_findings_version ON findings(project_id, version_id, state);
CREATE INDEX idx_events_branch ON events(project_id, branch_id, sequence);
CREATE INDEX idx_jobs_state ON jobs(principal_id, registration_id, state);
```

## Appendix B. Executable reference preference components

This is CPU-based NumPy reference code, not a complete application. Supply only qualified, non-retracted observations. A fit that does not converge must not silently replace the last valid snapshot; fall back to diversity/evidence collection.

The helpers implement fixed design-only feature encoding, joint visibility masks, normalized repeated-evidence weights, and a simple observed-control equivalence check. Full comparison qualification also requires ownership, design identity, evidence provenance, per-region adherence, meaningful differences, and an appropriate review scope.

`observed_controls_match` is only for categorical controls already normalized by a versioned policy. Numeric camera parameters require a tolerance-aware comparison when applicable. Matching requested settings alone never calls this helper with fabricated observed values.

```python
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PairwiseFit:
    coefficients: np.ndarray
    hessian: np.ndarray
    converged: bool
    effective_weight: float


def fit_pairwise(
    differences: np.ndarray,
    targets: np.ndarray,
    weights: np.ndarray | None = None,
    l2: float = 1.0,
    max_steps: int = 50,
    tolerance: float = 1e-8,
) -> PairwiseFit:
    """Fit on observed feature differences; never synthesize user labels."""
    D = np.asarray(differences, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    if D.ndim != 2 or D.shape[1] < 1 or y.shape != (D.shape[0],):
        raise ValueError("Expected differences (n,d), d>=1, and targets (n,).")
    a = np.ones(len(y)) if weights is None else np.asarray(weights, dtype=np.float64)
    if a.shape != y.shape:
        raise ValueError("Weights must have shape (n,).")
    if not all(np.isfinite(v).all() for v in (D, y, a)):
        raise ValueError("All training values must be finite.")
    if np.any((y < 0) | (y > 1)) or np.any(a < 0):
        raise ValueError("Targets must be in [0,1]; weights must be nonnegative.")
    if not np.isfinite(l2) or l2 <= 0 or max_steps < 1:
        raise ValueError("Use positive finite regularization and at least one step.")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Tolerance must be positive and finite.")
    if np.any(np.abs(D) > 2.00000001):
        raise ValueError("Feature differences must use the specified [-2,2] scale.")

    w = np.zeros(D.shape[1], dtype=np.float64)
    prior = l2 * np.eye(D.shape[1], dtype=np.float64)

    def objective(v: np.ndarray) -> float:
        z = D @ v
        return float(0.5 * l2 * (v @ v) + a @ (np.logaddexp(0, z) - y * z))

    def derivatives(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = D @ v
        p = np.exp(-np.logaddexp(0, -z))
        gradient = l2 * v + D.T @ (a * (p - y))
        curvature = a * p * (1 - p)
        hessian = prior + D.T @ (curvature[:, None] * D)
        return gradient, hessian

    if a.sum() == 0:
        return PairwiseFit(w, prior, True, 0.0)

    for _ in range(max_steps):
        gradient, hessian = derivatives(w)
        if np.linalg.norm(gradient, ord=np.inf) <= tolerance:
            break
        step = np.linalg.solve(hessian, gradient)
        current_loss = objective(w)
        decrease = float(gradient @ step)
        rate = 1.0
        while rate >= 2.0 ** -20:
            trial = w - rate * step
            if objective(trial) <= current_loss - 1e-4 * rate * decrease:
                w = trial
                break
            rate *= 0.5
        else:
            break

    gradient, hessian = derivatives(w)
    return PairwiseFit(
        coefficients=w,
        hessian=hessian,
        converged=bool(np.linalg.norm(gradient, ord=np.inf) <= tolerance),
        effective_weight=float(a.sum()),
    )


def comparison_prediction(model: PairwiseFit, difference: np.ndarray) -> tuple[float, float]:
    """Return relative A-over-B probability and the stated acquisition heuristic."""
    d = np.asarray(difference, dtype=np.float64)
    if d.shape != model.coefficients.shape or not np.isfinite(d).all():
        raise ValueError("Comparison vector has an invalid shape or value.")
    if np.any(np.abs(d) > 2.00000001):
        raise ValueError("Comparison vector must use the specified [-2,2] scale.")
    logit = float(model.coefficients @ d)
    p = float(np.exp(-np.logaddexp(0, -logit)))
    variance = max(0.0, float(d @ np.linalg.solve(model.hessian, d)))
    information = 0.5 * float(np.log1p(p * (1 - p) * variance))
    return p, information


# Fixed design-only schema. Never derive this list from arbitrary LLM output.
NUMERIC = {
    "body.head_ratio": (0.08, 0.60),
    "face.angularity": (0.0, 1.0),
    "face.eye_exaggeration": (0.0, 1.0),
    "hair.volume": (0.0, 1.0),
    "outfit.ornament_density": (0.0, 1.0),
    "outfit.layering": (0.0, 1.0),
    "palette.saturation": (0.0, 1.0),
    "palette.lightness": (0.0, 1.0),
    "palette.contrast": (0.0, 1.0),
    "material.gloss": (0.0, 1.0),
}
CATEGORIES = {
    "form.stylization": (
        "anime_proportioned", "cartoon_proportioned", "naturalistic",
        "chibi", "geometric", "hybrid", "other",
    ),
    "hair.length": ("bald", "very_short", "short", "medium", "long", "very_long", "other"),
    "hair.structure": ("straight", "wavy", "curly", "coiled", "spiky", "mixed", "other"),
    "outfit.structure": (
        "casual", "formal", "uniform", "fantasy", "techwear", "historical", "minimal", "other",
    ),
}
FEATURE_NAMES = tuple(NUMERIC) + tuple(
    f"{key}={value}" for key, values in CATEGORIES.items() for value in values
)


def encode_observed(attributes: dict, min_confidence: float = 0.6) -> tuple[np.ndarray, np.ndarray]:
    """Encode reviewed visual observations, not canonical intentions or render settings.

    Each attribute is {value, confidence, visibility}. Missing/occluded entries
    have an all-false mask. The caller first enforces provenance and comparability.
    """
    if not np.isfinite(min_confidence) or not 0 <= min_confidence <= 1:
        raise ValueError("Invalid extraction-confidence threshold.")
    if not isinstance(attributes, dict):
        raise ValueError("Attributes must be an object.")
    unknown = set(attributes) - (set(NUMERIC) | set(CATEGORIES))
    if unknown:
        raise ValueError(f"Unknown or non-design feature keys: {sorted(unknown)}")
    x = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    mask = np.zeros(len(FEATURE_NAMES), dtype=bool)
    offset = 0
    for key in (*NUMERIC, *CATEGORIES):
        width = 1 if key in NUMERIC else len(CATEGORIES[key])
        row = attributes.get(key)
        if row is None:
            offset += width
            continue
        if not isinstance(row, dict) or set(row) != {"value", "confidence", "visibility"}:
            raise ValueError("Use exactly value, confidence, and visibility per attribute.")
        c, vis, value = row["confidence"], row["visibility"], row["value"]
        if isinstance(c, bool) or not isinstance(c, (int, float)) or not np.isfinite(c) or not 0 <= c <= 1:
            raise ValueError("Invalid extraction confidence.")
        if vis not in ("visible", "occluded", "out_of_frame", "unknown"):
            raise ValueError("Invalid visibility.")
        if value is not None:
            if key in NUMERIC:
                lo, hi = NUMERIC[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("Numeric attribute requires a real number.")
                if not np.isfinite(value) or not lo <= value <= hi:
                    raise ValueError("Numeric attribute outside fixed schema bounds.")
            elif not isinstance(value, str) or value not in CATEGORIES[key]:
                raise ValueError("Unknown categorical value.")
        if value is not None and vis == "visible" and c >= min_confidence:
            if key in NUMERIC:
                lo, hi = NUMERIC[key]
                x[offset] = 2 * (value - lo) / (hi - lo) - 1
            else:
                x[offset + CATEGORIES[key].index(value)] = 1
            mask[offset:offset + width] = True
        offset += width
    return x, mask


def masked_difference(left: tuple[np.ndarray, np.ndarray],
                      right: tuple[np.ndarray, np.ndarray],
                      scope: np.ndarray | None = None) -> np.ndarray:
    """Use only jointly visible, reliable features within the qualified scope."""
    xa, ma = left
    xb, mb = right
    expected = (len(FEATURE_NAMES),)
    for x, m in (left, right):
        if x.shape != expected or m.shape != expected or m.dtype != bool:
            raise ValueError("Invalid feature vector/mask shape or dtype.")
        if not np.isfinite(x).all() or np.any(np.abs(x) > 1.00000001):
            raise ValueError("Invalid normalized feature vector.")
    if scope is None:
        scope = np.ones(expected, dtype=bool)
    if scope.shape != expected or scope.dtype != bool:
        raise ValueError("Invalid scope mask.")
    return (xa - xb) * (ma & mb & scope)


def family_weights(families: list[str], base_weights: np.ndarray) -> np.ndarray:
    """Cap correlated evidence at total weight 1 per server-derived family."""
    base = np.asarray(base_weights, dtype=np.float64)
    if base.shape != (len(families),) or not np.isfinite(base).all() or np.any(base < 0):
        raise ValueError("Invalid family weights.")
    if any(not isinstance(f, str) or not f for f in families):
        raise ValueError("Each row requires a nonempty server-derived family.")
    totals: dict[str, float] = {}
    for family, weight in zip(families, base):
        totals[family] = totals.get(family, 0.0) + float(weight)
    return np.array([weight / max(1.0, totals[family])
                     for family, weight in zip(families, base)], dtype=np.float64)


def observed_controls_match(left: dict, right: dict, required_keys: tuple[str, ...]) -> bool:
    """Small per-slot check; full qualification also checks identity and visibility.

    Pass observed controls only. Matching requested recipes is not evidence.
    Exact numeric camera parameters require a different tolerance-aware policy.
    """
    if not required_keys:
        raise ValueError("A comparison policy must declare its relevant controls.")
    for key in required_keys:
        a, b = left.get(key), right.get(key)
        if a is None or b is None or a == "unknown" or b == "unknown" or a != b:
            return False
    return True
```

## Appendix C. Starter feature schema and scope mapping

`design-features-v2` has 39 dimensions: ten normalized numeric values and categorical blocks of 7, 7, 7, and 8 values. The ordering is fixed in Appendix B. Categorical blocks use one-hot values; unknown is an all-false mask, not the `other` category.

| Numeric property | Bounds | Observation requirement |
|---|---|---|
| `body.head_ratio` | 0.08–0.60 | Head height/full character height; appropriate full-body, comparable neutral views only |
| `face.angularity` | 0–1 | Rounded to angular neutral facial contours; do not infer full facial geometry from one contour |
| `face.eye_exaggeration` | 0–1 | Naturalistic to exaggerated eye design; neutral, sufficiently visible eyes |
| `hair.volume` | 0–1 | Relative hairstyle silhouette volume under comparable views; not a reconstructed volumetric measurement |
| `outfit.ornament_density` | 0–1 | Visible garment ornamentation, excluding background decoration |
| `outfit.layering` | 0–1 | Visible garment-layer complexity; unseen layers remain unknown |
| `palette.saturation` | 0–1 | Character palette, with lighting/background confounding controlled |
| `palette.lightness` | 0–1 | Intended-looking character surface palette under comparable neutral conditions |
| `palette.contrast` | 0–1 | Separation of major character colors, not photographic contrast |
| `material.gloss` | 0–1 | Observed finish supported by suitable evidence; do not infer from one uncontrolled highlight |

Most 0–1 descriptors are coarse engineering judgments, not calibrated physical measurements. Retain extractor version, source, visibility, and uncertainty. A threshold such as 0.6 gates an initial workflow; it does not turn an LLM confidence value into a calibrated probability.

`form.stylization` describes the visible character's shape language, not the camera, photograph style, scene lighting, or quality of illustration. Intentional surface/shader requirements still belong in the canonical specification; they do not become observed visual features unless suitable evidence supports them. The baseline need not score every canonical requirement.

Suggested scope mappings are face → `face.*`; hair → `hair.*`; body → `body.*` and applicable `form.*`; outfit → `outfit.*`; palette → `palette.*`; surface → `material.*`. A whole-character comparison uses an appropriate common basis rather than every feature unconditionally. Accessory and custom-region feedback may initially be qualitative and prompt-planning evidence until a versioned descriptor schema is added.

Map the domain `FeatureObservation` dictionaries to Appendix B's `{value, confidence, visibility}` per-attribute structure. Do not pass its `observedPresentation` into the encoder. Validate and apply per-region consistency findings before encoding.

Numeric values use `2*(value-min)/(max-min)-1`. Reject values outside the schema bounds. Never refit normalization to each candidate batch. Change the schema version and replay qualified evidence when adding descriptors or vocabularies.

For categories, the entire block shares a visibility mask. Do not mask only the chosen category; differences between two observed categories need the complete one-hot block. All masks are intersected with the comparison scope before training.

## Appendix D. Verification status and implementation cautions

The fresh-install SQL in Appendix A and the Python helpers in Appendix B were executed during preparation of this version. **45 automated local tests passed: 27 numerical/feature-policy tests and 18 database-contract tests.**

The tests covered design-only feature keys, fixed encoding dimensions, missing/occluded/low-confidence masks, region scope, bounds, categories, empty learning state, pair/label reversal, soft ties, identical features, family-weight caps, duplicate-comparison curvature, observed-condition matching, invalid numeric input, and regularized Hessian positivity.

Database checks covered foreign-key integrity, project-scoped assets, version-consistent bundles, same-version A/B rejection, observation-only plan change restrictions, prompt-only mode, canonical hashes, user/payer isolation, task allowlisting, findings tied to the correct design, limits on model-provenance claims, cascading project deletion, multiple depictions per design, prompt-revision pairing, JSON validation, and prohibition of an automatic production-ready checkpoint.

These are **reference-component tests**, not a claim that an application was implemented or deployed. They do not verify real visual preference accuracy, actual image-based pose invariance, UI exposure tracking, provider usage settings, OAuth login, SIWC model admission, live streaming/recovery, external generation, hosted deployment eligibility, 3D geometry, rigs, or production security. Those remain release tests in Section 17.

SQL constraints protect a useful subset of invariants. The service layer still MUST enforce immutable published records, exactly two complete comparison sides before sealing, allowed state transitions, semantic JSON validation, event-sequence atomics, per-property locks, lineage inheritance, authenticated access, image safety, and complete evidence qualification. A passing SQLite migration does not implement those behaviors.

The numerical ranker assumes the caller supplies qualified observations and genuine labels. It cannot detect identity drift, infer 3D structure, or distinguish a pose-related attraction when an upstream component has incorrectly encoded it as a character feature.

A companion reference bundle can contain the same SQL and Python code, their test runner, and the test report. The implementation specification remains self-contained: the code and operational requirements are included here.

## Sources and revalidation points

The following official sources were reviewed on **2026-10-15**. They support external SIWC capabilities and constraints. The application architecture, UX, data contracts, learning policy, numerical defaults, and evaluation design in this document are proposed implementation decisions, not guarantees made by OpenAI.

**[S01] OpenAI — ChatGPT plan usage overview.** Optional plan-use permission, account-context boundary, local/open-source flow, and separate participation path for paid or remotely hosted apps.  
`https://developers.openai.com/siwc/token-sharing-open-source`

**[S02] OpenAI — Registration and sign-in.** Dynamic registration, host identity, OAuth parameters, loopback callback, issued client ID, granted scopes, and token validation. Follow the complete current protocol rather than implementing only the abbreviated example.  
`https://developers.openai.com/siwc/token-sharing-open-source/sign-in`

**[S03] OpenAI — Accounts and sessions.** Account isolation, reauthorization, refresh rotation, and revocation.  
`https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions`

**[S04] OpenAI — Models and inference.** Current account-specific catalog, public Responses route, bearer OAuth credential, streaming, and completed-response handling.  
`https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference`

**[S05] OpenAI — Preview limitations.** Required HTTP request settings, unsupported parameters/tools, and permitted model-dependent inputs.  
`https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations`

**[S06] OpenAI — Errors and recovery.** Permission/admission failures, structured error codes, usage pauses, and session recovery.  
`https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery`

**[S07] OpenAI Help — Using your ChatGPT plan in other apps and sites.** App limits, plan allowance, optional credit use, automatic-purchase distinction, and account-context boundaries.  
`https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites`

**[S08] OpenAI Cookbook — Integrating Sign in with ChatGPT in your Opensource App.** Additional registration and implementation walkthrough.  
`https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt`
