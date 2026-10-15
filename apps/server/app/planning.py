"""Deterministic text compilation. No synthesis, command, tool, or generator adapter."""

import json

from .common import canonical, digest, require, uid
from .contracts import CheckpointInput, ModelBuildInput, PlanInput

PURPOSES = {
    "design_variant": "Design variant",
    "additional_view": "Additional view",
    "unspecified_part": "Unspecified-part design",
    "state_study": "Expression/pose study",
    "depiction_correction": "Correction",
}


class Planning:
    def __init__(self, service):
        self.service = service

    def compile(self, principal, project, data: PlanInput):
        s = self.service
        with s.database.connect() as db:
            state = s.owned(db, principal, project)
            s.sequence(state, data.expectedEventSequence)
            version = s.version(db, project, data.targetVersionId)
            spec = version["spec"]
            design = s.get(db, "designs", project, "design_id", version["design_id"])
            explicit_locks = s.reduce(db, project, design["branch_id"])["locks"].get(
                data.targetVersionId, []
            )
            confirmed = [
                key
                for key, prop in spec["properties"].items()
                if prop["state"] == "user_confirmed"
            ]
            locked = sorted(set(explicit_locks + confirmed))
            require(
                not set(data.changeDesignProperties) & set(locked),
                "Explicitly unlock preserved properties before proposing changes",
                409,
            )
            for key in data.changeDesignProperties:
                require(
                    key in spec["properties"] or key in spec["unresolvedDecisions"],
                    "Change target must name an existing property or unresolved decision",
                )
                if data.purpose == "unspecified_part":
                    require(
                        key not in spec["properties"]
                        or spec["properties"][key]["state"]
                        in ("unspecified", "proposed"),
                        "This property is already specified",
                    )
            references = []
            for order, ref in enumerate(data.references, 1):
                asset = s.get(db, "assets", project, "asset_id", ref.assetId)
                references.append(
                    {
                        **ref.model_dump(),
                        "attachmentOrder": order,
                        "sha256": asset["digest"],
                    }
                )
            preserve = sorted(
                set(spec["properties"]) - set(data.changeDesignProperties)
            )
            lines = [
                f"PURPOSE: {PURPOSES[data.purpose]} for {design['title']}, design revision {version['revision']}.",
                "OBJECTIVE: A reusable 3D avatar character design. This text requests an independently produced reference image.",
                f"CANONICAL DESIGN (SHA-256 {version['canonical_hash']}):",
                f"Morphology: {spec['morphology']}.",
            ]
            for key, prop in sorted(spec["properties"].items()):
                lines.append(
                    f"- {key}: {canonical(prop['value'])} [{prop['state']}]. {prop['notes']}"
                )
            lines.append(
                "COMPONENT RELATIONSHIPS: " + canonical(spec["componentRelations"])
            )
            lines.append(
                "PRESERVE: "
                + (
                    ", ".join(preserve)
                    or "No specified properties yet; do not invent confirmed intent."
                )
            )
            lines.append(
                "CONFIRMED PRESERVATION: " + (", ".join(locked) or "None recorded.")
            )
            lines.append(
                "Keep character-left and character-right in character space, independent of screen position."
            )
            if data.changeDesignProperties:
                lines.append(
                    "PROPOSE CHANGES ONLY TO: "
                    + ", ".join(data.changeDesignProperties)
                    + ". These are proposals requiring adoption as a new design version."
                )
            else:
                lines.append(
                    "NO REDESIGN: Preserve this exact character, face, hair, clothing and accessories. Correct depiction failures without changing the canonical design."
                )
            lines.append(
                "REQUESTED CONDITIONS (not observed facts): "
                + canonical(data.recipe.model_dump())
            )
            lines.append("REFERENCE ATTACHMENTS:")
            for ref in references:
                lines.append(
                    f"{ref['attachmentOrder']}. {ref['role']}: {ref['instruction']}. File hash {ref['sha256']}."
                )
                if ref["role"] == "view_example":
                    lines.append(
                        "Use this attachment only for presentation. Do not adopt its face, clothing or palette."
                    )
            if not references:
                lines.append(
                    "No image attachments. This is an unrendered text-only proposal."
                )
            unknown = sorted(
                [
                    key
                    for key, prop in spec["properties"].items()
                    if prop["state"] in ("unspecified", "proposed", "inferred")
                ]
                + spec["unresolvedDecisions"]
            )
            lines.append("UNRESOLVED / TENTATIVE: " + canonical(unknown))
            lines.append(
                "Unseen surfaces remain unknown. Any necessary new detail is a proposal, not recovered geometry. A 2D image does not validate a mesh, rig, camera, or all poses."
            )
            recipe, plan = uid(), uid()
            payload = {
                "schemaVersion": "2.0",
                "planId": plan,
                "revision": 1,
                "purpose": data.purpose,
                "targetDesignVersionId": data.targetVersionId,
                "canonicalSpecHash": version["canonical_hash"],
                "basedOnEventSequence": state["event_sequence"],
                "constraintsVersion": state["constraints_version"],
                "renderRecipeId": recipe,
                "evaluationSlotId": None,
                "changeDesignProperties": data.changeDesignProperties,
                "preserveDesignProperties": preserve,
                "references": references,
                "promptText": "\n".join(lines),
                "attachmentInstructions": "Attach the listed imported files in order in your independently chosen tool.",
                "unresolvedAssumptions": unknown,
                "executionMode": "prompt_only",
                "imageStatus": "not_generated",
            }
            db.execute(
                "INSERT INTO render_recipes VALUES (?,?,?,?)",
                (
                    project,
                    recipe,
                    canonical(data.recipe.model_dump()),
                    digest(data.recipe.model_dump()),
                ),
            )
            db.execute(
                "INSERT INTO prompt_plans VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    project,
                    plan,
                    1,
                    data.targetVersionId,
                    version["canonical_hash"],
                    recipe,
                    data.purpose,
                    canonical(data.changeDesignProperties),
                    canonical(payload),
                    state["event_sequence"],
                    state["constraints_version"],
                    "prompt_only",
                ),
            )
            return payload

    def plans(self, principal, project):
        with self.service.database.connect() as db:
            state = self.service.owned(db, principal, project)
            return [
                {
                    **json.loads(row["payload_json"]),
                    "freshness": "current"
                    if row["input_sequence"] == state["event_sequence"]
                    else "historical",
                }
                for row in db.execute(
                    "SELECT * FROM prompt_plans WHERE project_id=? ORDER BY rowid DESC",
                    (project,),
                )
            ]

    def next_actions(self, principal, project, version):
        evidence = self.service.evidence(principal, project, version)
        actions = []
        for finding in evidence["findings"]:
            details = json.loads(finding["details_json"])
            if finding["state"] == "open" and details["severity"] == "blocking":
                actions.append(
                    {
                        "action": "correct_unfaithful_depiction",
                        "reason": details["description"],
                        "findingId": finding["finding_id"],
                    }
                )
        for unknown in evidence["version"]["spec"]["unresolvedDecisions"]:
            actions.append(
                {"action": "resolve_unspecified_design_property", "reason": unknown}
            )
        for slot in evidence["slots"]:
            if slot["required"] and slot["status"] == "missing":
                actions.append(
                    {
                        "action": "request_missing_view",
                        "reason": f"Obtain reviewed {slot['view']} evidence",
                        "slot": slot,
                    }
                )
        if not actions:
            actions.append(
                {
                    "action": "prepare_handoff"
                    if evidence["referenceCoverage"]
                    else "request_missing_view",
                    "reason": "Confirm an honest handoff with unresolved checks"
                    if evidence["referenceCoverage"]
                    else "Configure a morphology-appropriate evaluation profile",
                }
            )
        return {"actions": actions[:4], "executionMode": "prompt_only"}

    def model_build(self, principal, project, data: ModelBuildInput):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            self.service.version(db, project, data.targetVersionId)
            build = uid()
            db.execute(
                "INSERT INTO model_builds VALUES (?,?,?,?,?,?)",
                (
                    project,
                    build,
                    data.targetVersionId,
                    data.artifactHash,
                    "user_reported",
                    canonical(
                        {
                            "label": data.label,
                            "testScope": data.testScope,
                            "artifactInspected": False,
                        }
                    ),
                ),
            )
            return {
                "buildId": build,
                "provenanceLevel": "user_reported",
                "artifactInspected": False,
            }

    def checkpoint(self, principal, project, data: CheckpointInput):
        coverage = self.service.evidence(principal, project, data.versionId)
        with self.service.database.connect() as db:
            s = self.service
            state = s.owned(db, principal, project)
            s.sequence(state, data.expectedEventSequence)
            if data.stage == "reference_handoff_ready":
                missing = [
                    slot["id"]
                    for slot in coverage["slots"]
                    if slot["required"] and slot["status"] == "missing"
                ]
                require(
                    (coverage["referenceCoverage"] is not None and not missing)
                    or data.acceptedGaps,
                    "Explicitly accept missing references or unconfigured profile",
                )
                open_issues = [f for f in coverage["findings"] if f["state"] == "open"]
                require(
                    not open_issues or data.acceptedGaps,
                    "Record accepted unresolved findings",
                )
            if data.stage == "prototype_reviewed_external":
                require(
                    data.sourceBuildId is not None,
                    "External review requires a declared build",
                )
                build = s.get(
                    db, "model_builds", project, "build_id", data.sourceBuildId
                )
                require(
                    build["target_version_id"] == data.versionId,
                    "Build belongs to another version",
                )
                require(
                    db.execute(
                        "SELECT 1 FROM depictions d JOIN depiction_links l ON d.project_id=l.project_id AND d.depiction_id=l.depiction_id WHERE d.project_id=? AND d.source_build_id=? AND l.version_id=? AND l.status IN ('compatible','partial')",
                        (project, data.sourceBuildId, data.versionId),
                    ).fetchone(),
                    "Import and review captures from this build first",
                )
            version = s.version(db, project, data.versionId)
            lineage = s.get(db, "designs", project, "design_id", version["design_id"])
            bundle, _ = s.freeze_bundle(
                db,
                project,
                data.versionId,
                [
                    link["link_id"]
                    for link in s.current_links(db, project, data.versionId)
                ],
                "whole",
                state["event_sequence"],
            )
            event = s.append(
                db,
                project,
                lineage["branch_id"],
                "confirm_checkpoint",
                data.model_dump(),
            )
            checkpoint = uid()
            db.execute(
                "INSERT INTO checkpoints VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    checkpoint,
                    data.versionId,
                    bundle,
                    event["eventId"],
                    data.stage,
                    "current",
                    canonical(data.model_dump()),
                ),
            )
            return {
                "checkpointId": checkpoint,
                "stage": data.stage,
                "status": "current",
                **event,
            }
