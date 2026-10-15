CREATE TABLE project_settings (
  project_id TEXT PRIMARY KEY REFERENCES projects(project_id) ON DELETE CASCADE,
  allow_image_analysis INTEGER NOT NULL DEFAULT 0 CHECK(allow_image_analysis IN (0,1))
);
CREATE TABLE job_requests (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  request_id TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  job_id TEXT NOT NULL,
  PRIMARY KEY(project_id,request_id),
  FOREIGN KEY(project_id,job_id) REFERENCES jobs(project_id,job_id)
);
CREATE UNIQUE INDEX idx_one_active_request ON jobs(registration_id) WHERE state IN ('queued','running');
