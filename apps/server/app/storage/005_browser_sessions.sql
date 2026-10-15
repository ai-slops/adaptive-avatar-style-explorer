-- Only hashes of random browser bearer tokens are persisted. Provider budgets
-- and in-flight task authorizations deliberately remain process-local.
CREATE TABLE browser_sessions (
  token_digest TEXT PRIMARY KEY CHECK(length(token_digest)=64),
  execution_mode TEXT NOT NULL CHECK(execution_mode IN ('community_prompt_only','codex_local')),
  principal_id TEXT NOT NULL REFERENCES principals(principal_id),
  registration_id TEXT REFERENCES registrations(registration_id),
  csrf_token TEXT NOT NULL,
  created_at REAL NOT NULL,
  expires_at REAL NOT NULL,
  usage_paused INTEGER NOT NULL CHECK(usage_paused IN (0,1))
);
CREATE INDEX idx_browser_session_expiry ON browser_sessions(expires_at);
