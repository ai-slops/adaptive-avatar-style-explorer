export type Region =
  | "whole"
  | "face"
  | "hair"
  | "body"
  | "outfit"
  | "accessories"
  | "palette"
  | "surface"
  | "custom";
export type PropertyState =
  "unspecified" | "proposed" | "inferred" | "user_confirmed";
export type Property = {
  value: string | number | boolean | string[] | null;
  state: PropertyState;
  sourceEventIds: string[];
  sourceDepictionLinkIds: string[];
  notes: string;
};
export type Spec = {
  morphology: "humanoid" | "non_humanoid" | "unspecified";
  properties: Record<string, Property>;
  componentRelations: {
    component: string;
    relation:
      "attached_to" | "layered_over" | "connected_to" | "symmetric_with";
    target: string;
    state: PropertyState;
  }[];
  unresolvedDecisions: string[];
};
export type Project = {
  project_id: string;
  title: string;
  event_sequence: number;
};
export type Version = {
  version_id: string;
  design_id: string;
  revision: number;
  canonical_hash: string;
  parent_version_id: string | null;
  spec: Spec;
};
export type Design = {
  design_id: string;
  title: string;
  branch_id: string;
  versions: Version[];
};
export type Presentation = {
  view: string;
  projection: string;
  framing: string;
  poseId: string | null;
  expressionId: string | null;
  lightingClass: string | null;
  backgroundClass: string | null;
  source: string;
};
export type Attribute = {
  value: string | number | null;
  confidence: number;
  visibility: string;
};
export type Observation = {
  region: Region;
  attributes: Record<string, Attribute>;
  observedPresentation: Presentation;
};
export type Link = {
  link_id: string;
  status: string;
  depiction_id: string;
  depiction: { asset_id: string; source_kind: string; metadata_json: string };
  assessment: { reviewedRegions: Region[] };
  observations: Observation[];
};
export type Slot = {
  poseId?: string;
  expressionId?: string;
  region?: Region;
  notApplicableReason?: string | null;
  notApplicableBasis?: "morphology" | "project_scope" | null;
  id: string;
  view: string;
  framing: string;
  required: boolean;
  status: string;
  linkIds: string[];
};
export type Evidence = {
  evaluationProfileId: string;
  evaluationProfile: { stage: string; slots: Slot[] };
  version: Version;
  links: Link[];
  slots: Slot[];
  referenceCoverage: number | null;
  coverageMeaning: string;
  findings: {
    finding_id: string;
    state: string;
    kind: string;
    details_json: string;
  }[];
};
export type Plan = {
  planId: string;
  revision: number;
  purpose: string;
  targetDesignVersionId: string;
  canonicalSpecHash: string;
  promptText: string;
  references: {
    assetId: string;
    attachmentOrder: number;
    role: string;
    instruction: string;
  }[];
  freshness: string;
};
export type Ranking = {
  state: string;
  basis: string[];
  ranked: { versionId: string; relativeScore: number }[];
  unranked: { versionId: string; reason: string }[];
  boardVersionIds: string[];
  informativePairs: {
    versionA: string;
    versionB: string;
    informationHeuristic: number;
    predictedRelativePreference: number;
  }[];
};
export type Preferences = {
  rankings: Record<string, Ranking>;
  contextualDisagreements: {
    region: string;
    eventIds: string[];
    message: string;
  }[];
  shortlist: string[];
  rejected: string[];
  locks: Record<string, string[]>;
  activeEventIds: string[];
  undoableEvents: { eventId: string; action: string }[];
  state: string;
  models: Record<string, { effectiveWeight: number; eventIds: string[] }>;
  limitations: string;
};

export type SessionInfo = {
  mode: "codex_local" | "community_prompt_only";
  allowImageGeneration: boolean;
  registrationId: string | null;
  remainingRequests: number;
  usagePaused: boolean;
  profile: string;
};
export type Registration = {
  registration_id: string;
  issued_client_id: string;
  grant_state: string;
  display_name: string;
};
export type Job = {
  planId?: string;
  promptRevision?: number;
  jobId: string;
  state: string;
  task: string;
  versionId: string;
  result: {
    assetId?: string;
    phase?: string;
    suggestions?: {
      summary: string;
      observations: { linkId: string; observation: Observation }[];
      findings: {
        linkId: string | null;
        finding: { kind: string; description: string };
      }[];
      nextActions: { kind: string; reason: string }[];
    };
    error?: string;
    message?: string;
  } | null;
};

export type ModelBuild = {
  build_id: string;
  target_version_id: string;
  artifact_hash: string | null;
  provenance_level: "user_reported";
  report_json: string;
};
