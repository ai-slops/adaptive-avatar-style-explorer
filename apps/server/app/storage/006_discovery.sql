CREATE TABLE discovery_workspace (
  project_id TEXT PRIMARY KEY REFERENCES projects(project_id) ON DELETE CASCADE,
  revision INTEGER NOT NULL DEFAULT 0,
  active_round_id TEXT
);
CREATE TABLE discovery_rounds (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  round_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  request_id TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  based_revision INTEGER NOT NULL,
  feedback_hash TEXT NOT NULL,
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  PRIMARY KEY(project_id,round_id),
  UNIQUE(project_id,request_id)
);
CREATE TABLE discovery_candidates (
  project_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  round_id TEXT NOT NULL,
  position INTEGER NOT NULL,
  direction_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  PRIMARY KEY(project_id,candidate_id),
  FOREIGN KEY(project_id,round_id) REFERENCES discovery_rounds(project_id,round_id) ON DELETE CASCADE,
  FOREIGN KEY(project_id,version_id) REFERENCES design_versions(project_id,version_id)
);
CREATE TABLE discovery_reactions (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  reaction_id TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  request_hash TEXT NOT NULL,
  action TEXT NOT NULL,
  target_reaction_id TEXT,
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  PRIMARY KEY(project_id,reaction_id),
  UNIQUE(project_id,sequence)
);
CREATE TABLE discovery_inspirations (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  inspiration_id TEXT NOT NULL,
  asset_id TEXT NOT NULL,
  depiction_id TEXT NOT NULL,
  PRIMARY KEY(project_id,inspiration_id),
  FOREIGN KEY(project_id,asset_id) REFERENCES assets(project_id,asset_id),
  FOREIGN KEY(project_id,depiction_id) REFERENCES depictions(project_id,depiction_id)
);
CREATE TABLE discovery_batches (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  batch_id TEXT NOT NULL,
  principal_id TEXT NOT NULL,
  round_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  state TEXT NOT NULL,
  payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  PRIMARY KEY(project_id,batch_id),
  UNIQUE(project_id,request_id),
  FOREIGN KEY(project_id,round_id) REFERENCES discovery_rounds(project_id,round_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX idx_discovery_active_owner ON discovery_batches(principal_id) WHERE state IN ('queued','running');
CREATE TABLE discovery_imports (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  request_id TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  result_json TEXT NOT NULL CHECK(json_valid(result_json)),
  PRIMARY KEY(project_id,request_id)
);
