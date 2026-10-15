CREATE TABLE codex_jobs (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  job_id TEXT NOT NULL,
  principal_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  task TEXT NOT NULL CHECK(task IN ('generate_image','describe_depictions','review_design_consistency','propose_next_actions','compile_prompt_pack','summarize_preferences','compile_design_handoff')),
  state TEXT NOT NULL CHECK(state IN ('queued','running','succeeded','failed','cancelled','stale','needs_reauth')),
  version_id TEXT NOT NULL,
  canonical_hash TEXT NOT NULL,
  input_sequence INTEGER NOT NULL,
  constraints_version INTEGER NOT NULL,
  model TEXT NOT NULL,
  account_fingerprint TEXT NOT NULL,
  thread_id TEXT,
  turn_id TEXT,
  request_json TEXT NOT NULL CHECK(json_valid(request_json)),
  result_json TEXT CHECK(result_json IS NULL OR json_valid(result_json)),
  PRIMARY KEY(project_id,job_id),
  UNIQUE(project_id,request_id),
  FOREIGN KEY(principal_id,project_id) REFERENCES projects(principal_id,project_id),
  FOREIGN KEY(project_id,version_id,canonical_hash) REFERENCES design_versions(project_id,version_id,canonical_hash)
);
CREATE UNIQUE INDEX idx_codex_active_owner ON codex_jobs(principal_id) WHERE state IN ('queued','running');
