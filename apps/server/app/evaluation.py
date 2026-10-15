"""User-owned, versioned evaluation plans and explicit finding dispositions."""

from .common import canonical, require, uid
from .contracts import EvaluationProfileInput, FindingResolutionInput


class Evaluation:
    def __init__(self, service):
        self.service = service

    def publish_profile(self, principal, project, data: EvaluationProfileInput):
        s = self.service
        with s.database.connect() as db:
            state = s.owned(db, principal, project)
            s.sequence(state, data.expectedEventSequence)
            version = s.version(db, project, data.versionId)
            lineage = s.get(db, "designs", project, "design_id", version["design_id"])
            profile_id = uid()
            profile = {
                "schemaVersion": "2.0",
                "stage": data.stage,
                "slots": [slot.model_dump() for slot in data.slots],
                "changeRationale": data.changeRationale,
            }
            db.execute(
                "INSERT INTO evaluation_profiles VALUES (?,?,?)",
                (project, profile_id, canonical(profile)),
            )
            db.execute(
                "INSERT INTO version_profiles VALUES (?,?,?) ON CONFLICT(project_id,version_id) DO UPDATE SET profile_id=excluded.profile_id",
                (project, data.versionId, profile_id),
            )
            event = s.append(
                db,
                project,
                lineage["branch_id"],
                "correct_evidence",
                {
                    "kind": "evaluation_profile_changed",
                    "versionId": data.versionId,
                    "profileId": profile_id,
                    "rationale": data.changeRationale,
                },
                "project",
            )
            return {"profileId": profile_id, **event}

    def resolve(self, principal, project, finding_id, data: FindingResolutionInput):
        s = self.service
        with s.database.connect() as db:
            state = s.owned(db, principal, project)
            s.sequence(state, data.expectedEventSequence)
            finding = s.get(db, "findings", project, "finding_id", finding_id)
            require(
                finding["state"] == "open", "Finding already has a disposition", 409
            )
            version = s.version(db, project, finding["version_id"])
            design = s.get(db, "designs", project, "design_id", version["design_id"])
            db.execute(
                "UPDATE findings SET state=? WHERE project_id=? AND finding_id=?",
                (data.state, project, finding_id),
            )
            return s.append(
                db,
                project,
                design["branch_id"],
                "correct_evidence",
                {
                    "kind": "finding_disposition",
                    "findingId": finding_id,
                    "state": data.state,
                    "rationale": data.rationale,
                },
                "evidence_review",
            )
