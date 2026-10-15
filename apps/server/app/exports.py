"""In-memory non-executable exports. Only permissioned imported references are included."""

import io
import json
import zipfile

from .common import canonical
from .quality import quality_report

CHECKLIST = """# Modeling acceptance checklist

- [ ] Confirm identity, silhouette and component volume across required views.
- [ ] Resolve undefined surfaces, attachment construction, layers and asymmetry.
- [ ] Test neutral face, smile, blink and mouth movement where applicable.
- [ ] Test garment/accessory behavior in relevant articulation states.
- [ ] Test any declared view-dependent stylization.
- [ ] Inspect actual topology, skin weights, clipping and collision as applicable.
- [ ] Define downstream target and then test runtime performance and format needs.

Concept references do not verify geometry, a rig, or all poses. Technical checks
remain pending until the actual model implementation is tested.
"""


class Exports:
    def __init__(self, service, assets, planning):
        self.service, self.assets, self.planning = service, assets, planning

    def build(self, principal, project, version_id, kind="handoff"):
        s = self.service
        evidence = s.evidence(principal, project, version_id)
        plans = [
            p
            for p in self.planning.plans(principal, project)
            if p["targetDesignVersionId"] == version_id
        ]
        version = evidence["version"]
        spec = version["spec"]
        files = {}

        def json_file(name, value):
            files[name] = json.dumps(
                value, indent=2, ensure_ascii=False, allow_nan=False
            )

        json_file("prompt-pack.json", plans)
        for plan in plans:
            files[f"prompts/{plan['planId']}-r{plan['revision']}.md"] = plan[
                "promptText"
            ]
        if kind == "handoff":
            with s.database.connect() as db:
                state = s.owned(db, principal, project)
                design = s.get(
                    db, "designs", project, "design_id", version["design_id"]
                )
                effective = s.reduce(db, project, design["branch_id"])
                json_file(
                    "preference-evaluation.json",
                    quality_report(s, db, project, design["branch_id"]),
                )
                json_file(
                    "character-spec.json",
                    {"evidenceKind": "canonical_intent", **version},
                )
                files["character-spec.md"] = (
                    "# Character specification\n\n"
                    + f"Revision: {version['revision']}\n\nCanonical SHA-256: {version['canonical_hash']}\n\nMorphology: {spec['morphology']}\n\n"
                    + "\n".join(
                        f"- {key}: {canonical(prop['value'])} ({prop['state']})"
                        for key, prop in spec["properties"].items()
                    )
                )
                json_file("component-relations.json", spec["componentRelations"])
                json_file(
                    "confirmed-requirements.json",
                    {
                        "confirmedIntent": {
                            k: v
                            for k, v in spec["properties"].items()
                            if v["state"] == "user_confirmed"
                        },
                        "explicitPropertyLocks": effective["locks"],
                        "preservedPropertiesForSelectedVersion": s.inherited_locks(
                            db, project, version_id, effective["locks"]
                        ),
                    },
                )
                files["unresolved-decisions.md"] = (
                    "# Unresolved decisions\n\n"
                    + "\n".join(
                        f"- {item}"
                        for item in spec["unresolvedDecisions"]
                        + [
                            f"{k}: {p['state']}"
                            for k, p in spec["properties"].items()
                            if p["state"] != "user_confirmed"
                        ]
                        + [
                            f"Relationship: {relation['component']} {relation['relation']} {relation['target']} ({relation['state']})"
                            for relation in spec["componentRelations"]
                            if relation["state"] != "user_confirmed"
                        ]
                    )
                )
                json_file(
                    "view-and-state-coverage.json",
                    {
                        "evidenceKind": "reviewed_2d_observation",
                        "referenceCoverage": evidence["referenceCoverage"],
                        "slots": evidence["slots"],
                        "meaning": evidence["coverageMeaning"],
                    },
                )
                json_file("validation-findings.json", evidence["findings"])
                files["modeling-acceptance-checklist.md"] = CHECKLIST
                files["preference-evidence.jsonl"] = "\n".join(
                    canonical(
                        {
                            **event,
                            "payload": json.loads(event["payload_json"]),
                            "effective": event["event_id"]
                            in effective["activeEventIds"],
                        }
                    )
                    for event in s.history(db, project, design["branch_id"])
                )
                builds = [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM model_builds WHERE project_id=? AND target_version_id=?",
                        (project, version_id),
                    )
                ]
                if builds:
                    json_file(
                        "model-build-evidence.json",
                        {
                            "evidenceKind": "externally_reported_not_inspected",
                            "builds": builds,
                        },
                    )
                checkpoints = [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM checkpoints WHERE project_id=? AND version_id=?",
                        (project, version_id),
                    )
                ]
                json_file(
                    "reproducibility.json",
                    {
                        "schema": "2.0",
                        "featureSchema": "design-features-v2",
                        "canonicalHash": version["canonical_hash"],
                        "eventSequence": state["event_sequence"],
                        "checkpoints": checkpoints,
                        "guarantees": "No generator reproducibility, geometric or production-readiness guarantee.",
                    },
                )
                manifest = []
                reference_links = [(link, True) for link in evidence["links"]]
                included_links = {link["link_id"] for link in evidence["links"]}
                source_ids = {
                    source
                    for prop in spec["properties"].values()
                    for source in prop["sourceDepictionLinkIds"]
                }
                for source_id in sorted(source_ids - included_links):
                    source = s.get(db, "depiction_links", project, "link_id", source_id)
                    source["depiction"] = s.get(
                        db,
                        "depictions",
                        project,
                        "depiction_id",
                        source["depiction_id"],
                    )
                    source["assessment"] = json.loads(source["assessment_json"])
                    source["observations"] = [
                        json.loads(row[0])
                        for row in db.execute(
                            "SELECT observed_json FROM observations WHERE project_id=? AND link_id=?",
                            (project, source_id),
                        )
                    ]
                    reference_links.append((source, False))
                for link, current_evidence in reference_links:
                    depiction = link["depiction"]
                    asset = s.get(
                        db, "assets", project, "asset_id", depiction["asset_id"]
                    )
                    metadata = json.loads(depiction["metadata_json"])
                    included = metadata["exportPermission"]
                    item = {
                        "linkId": link["link_id"],
                        "versionId": link["version_id"],
                        "targetVersionId": version_id,
                        "referenceRole": "current_version_evidence"
                        if current_evidence
                        else "design_decision_source",
                        "countsAsCurrentEvidence": current_evidence,
                        "sourceReviewSuperseded": bool(
                            db.execute(
                                "SELECT 1 FROM depiction_links WHERE project_id=? AND supersedes_link_id=?",
                                (project, link["link_id"]),
                            ).fetchone()
                        ),
                        "assetId": asset["asset_id"],
                        "originalSha256": asset["digest"],
                        "parentAssetId": asset["parent_asset_id"],
                        "assetProvenance": json.loads(asset["provenance_json"]),
                        "reviewStatus": link["status"],
                        "canonicalPropertyKeys": [
                            key
                            for key, prop in spec["properties"].items()
                            if link["link_id"] in prop["sourceDepictionLinkIds"]
                        ],
                        "evidenceKind": "user_reported_model_capture"
                        if depiction["source_build_id"]
                        else "2d_concept_depiction",
                        "sourceBuildId": depiction["source_build_id"],
                        "sourcePlanId": depiction["origin_plan_id"],
                        "sourcePromptRevision": depiction["origin_prompt_revision"],
                        "generationProvenance": {
                            key: metadata[key]
                            for key in (
                                "provider",
                                "jobId",
                                "threadId",
                                "turnId",
                                "toolCallId",
                                "revisedPrompt",
                                "staleAtCompletion",
                            )
                            if key in metadata
                        },
                        "exportPermission": included,
                        "observations": link["observations"],
                        "assessment": link["assessment"],
                    }
                    if included:
                        name = f"references/{asset['asset_id']}.png"
                        files[name] = (
                            self.assets.root / f"{asset['storage_key']}.png"
                        ).read_bytes()
                        item["file"] = name
                        item["fileMeaning"] = (
                            "Non-generative metadata-stripped display derivative, not original bytes"
                        )
                    manifest.append(item)
                json_file("reference-manifest.json", manifest)
            files["README.md"] = f"""# Avatar design handoff

Design: {design["title"]}, revision {version["revision"]}.
Canonical hash: {version["canonical_hash"]}.

This pack separates confirmed intent, tentative proposals, reviewed 2D observations,
and externally reported model evidence. Missing information remains unresolved.
See the coverage, findings and acceptance checklist before beginning a model build.
Reference files are included only with recorded export permission. Imported
references are evidence, not a guarantee of ownership or redistribution rights.

Text prompts are for independent external use. No images were generated by this
application. No model artifact, topology, rig or production readiness was inspected.
"""
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr("avatar-design-handoff/" + name, content)
        return output.getvalue()
