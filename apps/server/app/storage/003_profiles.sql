CREATE TABLE version_profiles (
  project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  version_id TEXT NOT NULL,
  profile_id TEXT NOT NULL,
  PRIMARY KEY(project_id,version_id),
  FOREIGN KEY(project_id,version_id) REFERENCES design_versions(project_id,version_id),
  FOREIGN KEY(project_id,profile_id) REFERENCES evaluation_profiles(project_id,profile_id)
);
INSERT INTO evaluation_profiles(project_id,profile_id,profile_json)
SELECT project_id,'unconfigured-v1','{"schemaVersion":"2.0","stage":"unconfigured","slots":[]}' FROM projects;
