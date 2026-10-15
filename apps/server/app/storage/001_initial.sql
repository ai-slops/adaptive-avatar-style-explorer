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
