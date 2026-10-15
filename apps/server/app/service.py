"""Offline domain services. Published evidence is append-only; every call is owner scoped."""

import json
from datetime import UTC, datetime

import numpy as np

from .common import canonical, digest, require, uid
from .contracts import (
    DepictionInput,
    DesignInput,
    EvidenceReviewInput,
    FeedbackInput,
    LinkInput,
    ReviewInput,
    VersionInput,
)
from .learning.policy import qualify
from .learning.ranking import rank_cohort
from .learning.reference import FEATURE_NAMES, family_weights, fit_pairwise


class Service:
    def __init__(self, database):
        self.database = database

    def principal(self, principal_id, display_name="Offline profile"):
        with self.database.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO principals VALUES (?,?)",
                (principal_id, display_name),
            )

    def owned(self, db, principal, project):
        row = db.execute(
            "SELECT * FROM projects WHERE project_id=? AND principal_id=?",
            (project, principal),
        ).fetchone()
        require(row is not None, "Project not found", 404)
        return dict(row)

    def get(self, db, table, project, column, key):
        # Table and column come exclusively from service code, never request input.
        row = db.execute(
            f"SELECT * FROM {table} WHERE project_id=? AND {column}=?", (project, key)
        ).fetchone()
        require(row is not None, "Record not found", 404)
        return dict(row)

    def sequence(self, project, expected):
        require(
            project["event_sequence"] == expected,
            "Project changed; reload before applying this action",
            409,
        )

    def append(
        self,
        db,
        project,
        branch,
        action,
        payload,
        domain="project",
        event_id=None,
        review=None,
        target=None,
        request_hash=None,
    ):
        event_id = event_id or uid()
        sequence = db.execute(
            "UPDATE projects SET event_sequence=event_sequence+1 WHERE project_id=? RETURNING event_sequence",
            (project,),
        ).fetchone()[0]
        db.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                project,
                event_id,
                sequence,
                branch,
                review,
                domain,
                action,
                target,
                canonical(payload),
                request_hash or digest(payload),
                datetime.now(UTC).isoformat(),
            ),
        )
        # Any newer decision conservatively invalidates previous handoff checkpoints.
        db.execute(
            "UPDATE checkpoints SET status='outdated' WHERE project_id=? AND status='current'",
            (project,),
        )
        return {"eventId": event_id, "eventSequence": sequence, **payload}

    def projects(self, principal):
        with self.database.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM projects WHERE principal_id=? ORDER BY rowid DESC",
                    (principal,),
                )
            ]

    def create_project(self, principal, title):
        project = uid()
        with self.database.connect() as db:
            db.execute(
                "INSERT INTO projects(project_id,principal_id,title) VALUES (?,?,?)",
                (project, principal, title),
            )
            db.execute(
                "INSERT INTO branches(project_id,branch_id) VALUES (?,?)",
                (project, "main"),
            )
            profile = {
                "schemaVersion": "2.0",
                "stage": "shortlist",
                "slots": [
                    {
                        "id": "front",
                        "view": "front",
                        "framing": "full_body",
                        "required": True,
                    },
                    {
                        "id": "left",
                        "view": "character_left_profile",
                        "framing": "full_body",
                        "required": True,
                    },
                    {
                        "id": "right",
                        "view": "character_right_profile",
                        "framing": "full_body",
                        "required": True,
                    },
                    {
                        "id": "back",
                        "view": "back",
                        "framing": "full_body",
                        "required": True,
                    },
                    {
                        "id": "detail",
                        "view": "front",
                        "framing": "detail",
                        "required": False,
                    },
                ],
            }
            db.execute(
                "INSERT INTO evaluation_profiles VALUES (?,?,?)",
                (project, "structure-v1", canonical(profile)),
            )
            db.execute(
                "INSERT INTO evaluation_profiles VALUES (?,?,?)",
                (
                    project,
                    "unconfigured-v1",
                    canonical(
                        {"schemaVersion": "2.0", "stage": "unconfigured", "slots": []}
                    ),
                ),
            )
            return self.owned(db, principal, project)

    def profile(self, db, project, version_id):
        original = self.version(db, project, version_id)
        version = original
        while version:
            row = db.execute(
                "SELECT profile_id FROM version_profiles WHERE project_id=? AND version_id=?",
                (project, version["version_id"]),
            ).fetchone()
            if row:
                return self.get(
                    db, "evaluation_profiles", project, "profile_id", row[0]
                )
            if not version["parent_version_id"]:
                break
            version = self.version(db, project, version["parent_version_id"])
            if version["spec"]["morphology"] != original["spec"]["morphology"]:
                break
        return self.get(
            db,
            "evaluation_profiles",
            project,
            "profile_id",
            "structure-v1"
            if original["spec"]["morphology"] == "humanoid"
            else "unconfigured-v1",
        )

    def validate_sources(self, db, project, spec):
        for prop in spec["properties"].values():
            for event in prop["sourceEventIds"]:
                self.get(db, "events", project, "event_id", event)
            for link in prop["sourceDepictionLinkIds"]:
                self.get(db, "depiction_links", project, "link_id", link)

    def create_design(self, principal, project, data: DesignInput):
        with self.database.connect() as db:
            self.owned(db, principal, project)
            self.get(db, "branches", project, "branch_id", data.branchId)
            spec = data.spec.model_dump()
            self.validate_sources(db, project, spec)
            design, version = uid(), uid()
            db.execute(
                "INSERT INTO designs VALUES (?,?,?,?)",
                (project, design, data.branchId, data.title),
            )
            event = self.append(
                db,
                project,
                data.branchId,
                "adopt_variant",
                {"versionId": version, "spec": spec, "reason": "Initial design intent"},
                "design_intent",
            )
            db.execute(
                "INSERT INTO design_versions VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    version,
                    design,
                    1,
                    None,
                    digest(spec),
                    canonical(spec),
                    event["eventSequence"],
                ),
            )
            return self.version(db, project, version)

    def version(self, db, project, version):
        row = self.get(db, "design_versions", project, "version_id", version)
        row["spec"] = json.loads(row.pop("canonical_json"))
        return row

    def new_version(self, principal, project, design, data: VersionInput):
        with self.database.connect() as db:
            state = self.owned(db, principal, project)
            self.sequence(state, data.expectedEventSequence)
            lineage = self.get(db, "designs", project, "design_id", design)
            parent = self.version(db, project, data.parentVersionId)
            require(parent["design_id"] == design, "Parent belongs to another lineage")
            spec = data.spec.model_dump()
            self.validate_sources(db, project, spec)
            require(
                digest(spec) != parent["canonical_hash"],
                "No design change: import a new depiction instead",
            )
            locks = self.reduce(db, project, lineage["branch_id"])["locks"]
            for key in self.inherited_locks(db, project, data.parentVersionId, locks):
                require(
                    spec["properties"].get(key, {}).get("value")
                    == parent["spec"]["properties"].get(key, {}).get("value"),
                    f"Unlock {key} explicitly before changing it",
                    409,
                )
            version = uid()
            revision = db.execute(
                "SELECT MAX(revision)+1 FROM design_versions WHERE project_id=? AND design_id=?",
                (project, design),
            ).fetchone()[0]
            changes = [
                key
                for key in set(spec["properties"]) | set(parent["spec"]["properties"])
                if spec["properties"].get(key) != parent["spec"]["properties"].get(key)
            ]
            event = self.append(
                db,
                project,
                lineage["branch_id"],
                "adopt_variant",
                {
                    "versionId": version,
                    "parentVersionId": data.parentVersionId,
                    "changes": changes,
                    "changeSet": {
                        **{
                            key: {
                                "before": parent["spec"]["properties"].get(key),
                                "after": spec["properties"].get(key),
                            }
                            for key in changes
                        },
                        **{
                            key: {"before": parent["spec"][key], "after": spec[key]}
                            for key in (
                                "morphology",
                                "componentRelations",
                                "unresolvedDecisions",
                            )
                            if parent["spec"][key] != spec[key]
                        },
                    },
                    "reason": data.reason,
                },
                "design_intent",
            )
            db.execute(
                "INSERT INTO design_versions VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    version,
                    design,
                    revision,
                    data.parentVersionId,
                    digest(spec),
                    canonical(spec),
                    event["eventSequence"],
                ),
            )
            return self.version(db, project, version)

    def designs(self, principal, project, branch_id="main"):
        with self.database.connect() as db:
            self.owned(db, principal, project)
            branch = self.get(db, "branches", project, "branch_id", branch_id)
            result = []
            for row in db.execute(
                "SELECT * FROM designs WHERE project_id=? ORDER BY rowid", (project,)
            ):
                design = dict(row)
                design["versions"] = [
                    self.version(db, project, r[0])
                    for r in db.execute(
                        "SELECT version_id FROM design_versions WHERE project_id=? AND design_id=? ORDER BY revision DESC",
                        (project, row["design_id"]),
                    )
                ]
                design["versions"] = [
                    v
                    for v in design["versions"]
                    if self.visible_in_branch(
                        db, project, branch, design["branch_id"], v["created_sequence"]
                    )
                ]
                if design["versions"]:
                    result.append(design)
            return result

    def create_depiction(self, principal, project, data: DepictionInput):
        with self.database.connect() as db:
            self.owned(db, principal, project)
            self.get(db, "assets", project, "asset_id", data.assetId)
            if data.originPlanId:
                require(
                    db.execute(
                        "SELECT 1 FROM prompt_plans WHERE project_id=? AND plan_id=? AND revision=?",
                        (project, data.originPlanId, data.originPromptRevision),
                    ).fetchone(),
                    "Unknown prompt revision",
                    404,
                )
            if data.sourceBuildId:
                self.get(db, "model_builds", project, "build_id", data.sourceBuildId)
            depiction = uid()
            db.execute(
                "INSERT INTO depictions VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    depiction,
                    data.assetId,
                    data.sourceKind,
                    data.originPlanId,
                    data.originPromptRevision,
                    data.sourceBuildId,
                    canonical(
                        {
                            "caption": data.caption,
                            "exportPermission": data.exportPermission,
                            "explicitlyUnassociated": data.explicitlyUnassociated,
                        }
                    ),
                ),
            )
            event = self.append(
                db,
                project,
                "main",
                "correct_evidence",
                {"kind": "depiction_imported", "depictionId": depiction},
                "evidence_review",
            )
            return {"depictionId": depiction, **event}

    def create_link(self, principal, project, data: LinkInput):
        with self.database.connect() as db:
            self.owned(db, principal, project)
            depiction = self.get(
                db, "depictions", project, "depiction_id", data.depictionId
            )
            self.version(db, project, data.versionId)
            if depiction["source_build_id"]:
                build = self.get(
                    db,
                    "model_builds",
                    project,
                    "build_id",
                    depiction["source_build_id"],
                )
                require(
                    build["target_version_id"] == data.versionId,
                    "Capture build targets another design version",
                )
            link = uid()
            db.execute(
                "INSERT INTO depiction_links VALUES (?,?,?,?,?,?,?)",
                (
                    project,
                    link,
                    data.depictionId,
                    data.versionId,
                    "unreviewed",
                    canonical({"reviewedRegions": []}),
                    None,
                ),
            )
            version = self.version(db, project, data.versionId)
            design = self.get(db, "designs", project, "design_id", version["design_id"])
            event = self.append(
                db,
                project,
                design["branch_id"],
                "correct_evidence",
                {
                    "kind": "depiction_associated",
                    "linkId": link,
                    "versionId": data.versionId,
                },
                "evidence_review",
            )
            return {"linkId": link, **event}

    def evidence_review(self, principal, project, data: EvidenceReviewInput):
        with self.database.connect() as db:
            state = self.owned(db, principal, project)
            self.sequence(state, data.expectedEventSequence)
            old = self.get(db, "depiction_links", project, "link_id", data.linkId)
            require(
                not db.execute(
                    "SELECT 1 FROM depiction_links WHERE project_id=? AND supersedes_link_id=?",
                    (project, data.linkId),
                ).fetchone(),
                "Review has already been superseded",
                409,
            )
            design = self.get(
                db,
                "designs",
                project,
                "design_id",
                self.version(db, project, old["version_id"])["design_id"],
            )
            link = uid()
            assessment = {"reviewedRegions": data.reviewedRegions, "reviewer": "user"}
            db.execute(
                "INSERT INTO depiction_links VALUES (?,?,?,?,?,?,?)",
                (
                    project,
                    link,
                    old["depiction_id"],
                    old["version_id"],
                    data.status,
                    canonical(assessment),
                    old["link_id"],
                ),
            )
            for obs in data.observations:
                db.execute(
                    "INSERT INTO observations VALUES (?,?,?,?,?,?,?)",
                    (
                        project,
                        uid(),
                        link,
                        obs.region,
                        "design-features-v2",
                        "manual-v1",
                        canonical(obs.model_dump()),
                    ),
                )
            for finding in data.findings:
                if finding.kind == "implementation_issue_reported":
                    depiction = self.get(
                        db, "depictions", project, "depiction_id", old["depiction_id"]
                    )
                    require(
                        depiction["source_build_id"],
                        "Implementation issues require a declared model build",
                    )
                db.execute(
                    "INSERT INTO findings VALUES (?,?,?,?,?,?,?)",
                    (
                        project,
                        uid(),
                        old["version_id"],
                        link,
                        finding.kind,
                        "open",
                        canonical(finding.model_dump()),
                    ),
                )
            event = self.append(
                db,
                project,
                design["branch_id"],
                "correct_evidence",
                {"oldLinkId": old["link_id"], "newLinkId": link, "status": data.status},
                "evidence_review",
            )
            return {"linkId": link, **event}

    def current_links(self, db, project, version):
        rows = db.execute(
            """SELECT l.* FROM depiction_links l WHERE l.project_id=? AND l.version_id=?
          AND NOT EXISTS (SELECT 1 FROM depiction_links newer WHERE newer.project_id=l.project_id AND newer.supersedes_link_id=l.link_id)""",
            (project, version),
        )
        return [dict(r) for r in rows]

    def link_observations(self, db, project, link, region):
        if link["status"] not in ("compatible", "partial"):
            return []
        approved = json.loads(link["assessment_json"])["reviewedRegions"]
        findings = [
            json.loads(r[0])
            for r in db.execute(
                "SELECT details_json FROM findings WHERE project_id=? AND link_id=? AND state IN ('open','accepted_tradeoff')",
                (project, link["link_id"]),
            )
        ]
        result = []
        for row in db.execute(
            "SELECT observed_json FROM observations WHERE project_id=? AND link_id=?",
            (project, link["link_id"]),
        ):
            obs = json.loads(row[0])
            if obs["region"] not in approved and "whole" not in approved:
                continue
            if region != "whole" and obs["region"] not in (region, "whole"):
                continue
            if any(
                f["severity"] == "blocking"
                and (
                    f["region"] in ("whole", obs["region"], region)
                    or obs["region"] == "whole"
                    or region == "whole"
                )
                for f in findings
            ):
                continue
            result.append(obs)
        return result

    def source_family(self, db, project, link_id):
        link = self.get(db, "depiction_links", project, "link_id", link_id)
        depiction = self.get(
            db, "depictions", project, "depiction_id", link["depiction_id"]
        )
        asset = self.get(db, "assets", project, "asset_id", depiction["asset_id"])
        while asset["parent_asset_id"]:
            asset = self.get(
                db, "assets", project, "asset_id", asset["parent_asset_id"]
            )
        return json.loads(asset["provenance_json"]).get("pixelHash", asset["digest"])

    def evidence(self, principal, project, version):
        with self.database.connect() as db:
            self.owned(db, principal, project)
            spec = self.version(db, project, version)
            links = self.current_links(db, project, version)
            profile_record = self.profile(db, project, version)
            profile = json.loads(profile_record["profile_json"])
            slots = profile["slots"]
            coverage = []
            used_sources = set()
            for slot in slots:
                status, matching = (
                    (
                        "not_applicable"
                        if slot.get("notApplicableReason")
                        else "missing"
                    ),
                    [],
                )
                for link in links:
                    source = self.source_family(db, project, link["link_id"])
                    if source in used_sources:
                        continue
                    if status == "not_applicable":
                        continue
                    if (
                        "whole"
                        not in json.loads(link["assessment_json"])["reviewedRegions"]
                        and slot.get("region", "whole")
                        not in json.loads(link["assessment_json"])["reviewedRegions"]
                    ):
                        continue
                    for obs in self.link_observations(
                        db, project, link, slot.get("region", "whole")
                    ):
                        p = obs["observedPresentation"]
                        if (
                            p["view"] == slot["view"]
                            and p["framing"] == slot["framing"]
                            and p["poseId"] == slot.get("poseId", "neutral")
                            and p["expressionId"] == slot.get("expressionId", "neutral")
                        ):
                            depiction = self.get(
                                db,
                                "depictions",
                                project,
                                "depiction_id",
                                link["depiction_id"],
                            )
                            matching.append(link["link_id"])
                            if depiction["source_build_id"]:
                                status = "user_reported_model_evidence"
                            elif status != "user_reported_model_evidence":
                                status = "usable_concept_evidence"
                if matching:
                    used_sources.add(self.source_family(db, project, matching[0]))
                coverage.append(
                    {**slot, "status": status, "linkIds": sorted(set(matching))}
                )
            required = [
                s for s in coverage if s["required"] and s["status"] != "not_applicable"
            ]
            for link in links:
                link["depiction"] = self.get(
                    db, "depictions", project, "depiction_id", link["depiction_id"]
                )
                link["assessment"] = json.loads(link.pop("assessment_json"))
                link["observations"] = [
                    json.loads(r[0])
                    for r in db.execute(
                        "SELECT observed_json FROM observations WHERE project_id=? AND link_id=?",
                        (project, link["link_id"]),
                    )
                ]
            findings = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM findings WHERE project_id=? AND version_id=?",
                    (project, version),
                )
            ]
            return {
                "version": spec,
                "links": links,
                "slots": coverage,
                "evaluationProfileId": profile_record["profile_id"],
                "evaluationProfile": profile,
                "referenceCoverage": sum(
                    s["status"]
                    in ("usable_concept_evidence", "user_reported_model_evidence")
                    for s in required
                )
                / len(required)
                if required
                else None,
                "coverageMeaning": "Reference completeness only; geometry and rigging remain unverified",
                "findings": findings,
            }

    def freeze_bundle(self, db, project, version, link_ids, region, sequence):
        self.version(db, project, version)
        require(len(link_ids) == len(set(link_ids)), "Duplicate link in comparison")
        frozen, observations = [], []
        current = {l["link_id"]: l for l in self.current_links(db, project, version)}
        for link_id in link_ids:
            require(
                link_id in current,
                "Evidence is superseded or belongs to another design version",
                409,
            )
            link = current[link_id]
            obs = self.link_observations(db, project, link, region)
            depiction = self.get(
                db, "depictions", project, "depiction_id", link["depiction_id"]
            )
            frozen.append({"link": link, "depiction": depiction, "observations": obs})
            observations.extend(obs)
        payload = {"versionId": version, "region": region, "items": frozen}
        bundle = uid()
        db.execute(
            "INSERT INTO evidence_bundles VALUES (?,?,?,?,?,?,?)",
            (
                project,
                bundle,
                version,
                self.profile(db, project, version)["profile_id"],
                sequence,
                digest(payload),
                canonical(payload),
            ),
        )
        for ordinal, link_id in enumerate(link_ids):
            db.execute(
                "INSERT INTO bundle_items VALUES (?,?,?,?,?,?)",
                (project, bundle, version, link_id, ordinal, canonical([region])),
            )
        return bundle, observations

    def review(self, principal, project, data: ReviewInput):
        with self.database.connect() as db:
            state = self.owned(db, principal, project)
            self.sequence(state, data.expectedEventSequence)
            require(
                data.versionA != data.versionB,
                "A design cannot be compared against itself",
            )
            require(
                data.domain == "visual_design" or not (data.linkIdsA or data.linkIdsB),
                "Written intent reviews must not claim visual exposure",
            )
            branch = self.get(db, "branches", project, "branch_id", data.branchId)
            for version in (data.versionA, data.versionB):
                v = self.version(db, project, version)
                design = self.get(db, "designs", project, "design_id", v["design_id"])
                require(
                    self.visible_in_branch(
                        db, project, branch, design["branch_id"], v["created_sequence"]
                    ),
                    "Version is outside this branch history",
                )
            ba, oa = self.freeze_bundle(
                db,
                project,
                data.versionA,
                data.linkIdsA,
                data.region,
                state["event_sequence"],
            )
            bb, ob = self.freeze_bundle(
                db,
                project,
                data.versionB,
                data.linkIdsB,
                data.region,
                state["event_sequence"],
            )
            qualification = {
                **qualify(oa, ob, data.region, data.domain),
                "domain": data.domain,
            }
            if data.domain == "visual_design" and {
                self.source_family(db, project, link) for link in data.linkIdsA
            } & {self.source_family(db, project, link) for link in data.linkIdsB}:
                qualification["eligible"] = False
                qualification["reasons"].append(
                    "The two sides share an original image source; conflicting feature entries are not independent design evidence"
                )
            prior = self._preferences(db, project, data.branchId)["models"].get(
                data.region
            )
            prediction = None
            if qualification["eligible"] and prior and prior["state"] == "fitted":
                logit = float(
                    np.array(prior["coefficients"])
                    @ np.array(qualification["difference"])
                )
                prediction = {
                    "probabilityA": float(np.exp(-np.logaddexp(0, -logit))),
                    "supportingEventIds": prior["eventIds"],
                    "recordedBeforeFeedback": True,
                }
            qualification["preFeedbackPrediction"] = prediction
            review = uid()
            db.execute(
                "INSERT INTO review_sessions VALUES (?,?,?,?,?,?)",
                (
                    project,
                    review,
                    data.branchId,
                    data.region,
                    state["event_sequence"],
                    canonical(qualification),
                ),
            )
            for side, version, bundle in [
                ("A", data.versionA, ba),
                ("B", data.versionB, bb),
            ]:
                db.execute(
                    "INSERT INTO review_items VALUES (?,?,?,?,?)",
                    (project, review, side, version, bundle),
                )
            return {
                "reviewSessionId": review,
                "qualification": qualification,
                "bundles": {"A": ba, "B": bb},
                "eventSequence": state["event_sequence"],
            }

    def visible_in_branch(self, db, project, branch, source_branch, sequence):
        if branch["branch_id"] == source_branch:
            return True
        if branch["parent_branch_id"] is None or sequence > branch["parent_sequence"]:
            return False
        parent = self.get(
            db, "branches", project, "branch_id", branch["parent_branch_id"]
        )
        return self.visible_in_branch(db, project, parent, source_branch, sequence)

    def history(self, db, project, branch_id, through=None):
        branch = self.get(db, "branches", project, "branch_id", branch_id)
        inherited = (
            self.history(
                db, project, branch["parent_branch_id"], branch["parent_sequence"]
            )
            if branch["parent_branch_id"]
            else []
        )
        local = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM events WHERE project_id=? AND branch_id=? AND sequence<=? ORDER BY sequence",
                (project, branch_id, through if through is not None else 2**62),
            )
        ]
        return inherited + local

    def inherited_locks(self, db, project, version_id, locks):
        result = set()
        while version_id:
            result.update(locks.get(version_id, []))
            version_id = self.version(db, project, version_id)["parent_version_id"]
        return sorted(result)

    def reduce(self, db, project, branch_id):
        history = self.history(db, project, branch_id)
        undone = {e["target_event_id"] for e in history if e["action"] == "undo"}
        active = [
            e for e in history if e["event_id"] not in undone and e["action"] != "undo"
        ]
        shortlist, rejected, locks, epoch, comparisons = set(), set(), {}, 0, []
        for e in active:
            p = json.loads(e["payload_json"])
            action = e["action"]
            subjects = p.get("subjectVersionIds", [])
            v = subjects[0] if subjects else None
            if action == "shortlist_add":
                shortlist.add(v)
                rejected.discard(v)
            elif action in ("shortlist_remove", "reject_design"):
                shortlist.discard(v)
                if action == "reject_design":
                    rejected.add(v)
            elif action == "adopt_variant":
                version_id = p.get("versionId")
                if version_id:
                    published = self.version(db, project, version_id)
                    for key, prop in published["spec"]["properties"].items():
                        if prop["state"] == "user_confirmed":
                            locks.setdefault(version_id, set()).add(key)
            elif action == "lock_property":
                locks.setdefault(v, set()).add(p["propertyKey"])
            elif action == "unlock_property":
                version_id = v
                while version_id:
                    locks.setdefault(version_id, set()).discard(p["propertyKey"])
                    version_id = self.version(db, project, version_id)[
                        "parent_version_id"
                    ]
            elif action == "reset":
                epoch += 1
                comparisons = []
                if not p["preserveLocks"]:
                    locks = {}
            elif action == "compare":
                comparisons.append(e)
        return {
            "shortlist": sorted(shortlist),
            "rejected": sorted(rejected),
            "locks": {v: sorted(keys) for v, keys in locks.items()},
            "epoch": epoch,
            "comparisons": comparisons,
            "activeEventIds": [e["event_id"] for e in active],
            "undoableEvents": [
                {"eventId": e["event_id"], "action": e["action"]}
                for e in active
                if e["action"]
                in (
                    "compare",
                    "shortlist_add",
                    "shortlist_remove",
                    "reject_design",
                    "lock_property",
                    "unlock_property",
                    "reset",
                )
            ],
        }

    def feedback(self, principal, project, data: FeedbackInput):
        with self.database.connect() as db:
            state = self.owned(db, principal, project)
            request = data.model_dump()
            old = db.execute(
                "SELECT * FROM events WHERE project_id=? AND event_id=?",
                (project, data.eventId),
            ).fetchone()
            if old:
                require(
                    old["request_hash"] == digest(request),
                    "Event ID reused with a different request",
                    409,
                )
                return {
                    "eventId": old["event_id"],
                    "eventSequence": old["sequence"],
                    **json.loads(old["payload_json"]),
                }
            self.sequence(state, data.expectedEventSequence)
            branch = self.get(db, "branches", project, "branch_id", data.branchId)
            payload = dict(request)
            if data.action == "compare":
                review = self.get(
                    db, "review_sessions", project, "review_id", data.reviewSessionId
                )
                require(
                    review["branch_id"] == data.branchId,
                    "Review belongs to another branch",
                )
                require(
                    review["region"] == data.region,
                    "Review region does not match feedback",
                )
                require(
                    review["input_sequence"] == state["event_sequence"],
                    "Review is stale; reopen the comparison",
                    409,
                )
                q = json.loads(review["qualification_json"])
                require(
                    data.domain == q["domain"],
                    "Feedback domain differs from sealed review",
                )
                sides = list(
                    db.execute(
                        "SELECT * FROM review_items WHERE project_id=? AND review_id=? ORDER BY side",
                        (project, data.reviewSessionId),
                    )
                )
                require(len(sides) == 2, "Review is not complete")
                payload["subjectVersionIds"] = [s["version_id"] for s in sides]
                payload["trainingStatus"] = (
                    "qualified"
                    if q["eligible"] and data.outcome in ("A", "B", "tie")
                    else "provisional_not_trained"
                )
            else:
                require(
                    data.domain == "project",
                    "This action belongs in the project domain",
                )
                for version in data.subjectVersionIds:
                    v = self.version(db, project, version)
                    design = self.get(
                        db, "designs", project, "design_id", v["design_id"]
                    )
                    require(
                        self.visible_in_branch(
                            db,
                            project,
                            branch,
                            design["branch_id"],
                            v["created_sequence"],
                        ),
                        "Version is outside branch history",
                    )
                if data.action in ("lock_property", "unlock_property"):
                    prop = self.version(db, project, data.subjectVersionIds[0])["spec"][
                        "properties"
                    ].get(data.propertyKey)
                    require(
                        prop is not None and prop["value"] is not None,
                        "Cannot preserve an undefined property",
                    )
                if data.action == "undo":
                    history = self.history(db, project, data.branchId)
                    target = next(
                        (e for e in history if e["event_id"] == data.targetEventId),
                        None,
                    )
                    require(
                        target is not None, "Target event is not in branch history", 404
                    )
                    require(
                        target["action"]
                        in (
                            "compare",
                            "shortlist_add",
                            "shortlist_remove",
                            "reject_design",
                            "lock_property",
                            "unlock_property",
                            "reset",
                        ),
                        "This record cannot be undone",
                    )
                    require(
                        not any(
                            e["action"] == "undo"
                            and e["target_event_id"] == data.targetEventId
                            for e in history
                        ),
                        "Event already undone",
                        409,
                    )
                if data.action == "fork_branch":
                    child = uid()
                    db.execute(
                        "INSERT INTO branches(project_id,branch_id,parent_branch_id,parent_sequence) VALUES (?,?,?,?)",
                        (project, child, data.branchId, state["event_sequence"]),
                    )
                    payload["childBranchId"] = child
            return self.append(
                db,
                project,
                data.branchId,
                data.action,
                payload,
                data.domain,
                data.eventId,
                data.reviewSessionId,
                data.targetEventId,
                digest(request),
            )

    def preferences(self, principal, project, branch_id="main"):
        with self.database.connect() as db:
            self.owned(db, principal, project)
            return self._preferences(db, project, branch_id)

    def _preferences(self, db, project, branch_id):
        state = self.reduce(db, project, branch_id)
        raw_locks = state["locks"]
        state["locks"] = {
            row[0]: self.inherited_locks(db, project, row[0], raw_locks)
            for row in db.execute(
                "SELECT version_id FROM design_versions WHERE project_id=?",
                (project,),
            )
        }
        rows = []
        for event in state.pop("comparisons"):
            payload = json.loads(event["payload_json"])
            if payload["outcome"] not in ("A", "B", "tie"):
                continue
            review = self.get(
                db, "review_sessions", project, "review_id", event["review_id"]
            )
            q = json.loads(review["qualification_json"])
            if not q["eligible"]:
                continue
            sides = list(
                db.execute(
                    "SELECT * FROM review_items WHERE project_id=? AND review_id=? ORDER BY side",
                    (project, event["review_id"]),
                )
            )
            invalidated = False
            for side in sides:
                bundle = self.get(
                    db, "evidence_bundles", project, "bundle_id", side["bundle_id"]
                )
                for item in json.loads(bundle["frozen_json"])["items"]:
                    # A later correction never rewrites exposure. Conservatively retire that row.
                    if db.execute(
                        "SELECT 1 FROM depiction_links WHERE project_id=? AND supersedes_link_id=?",
                        (project, item["link"]["link_id"]),
                    ).fetchone():
                        invalidated = True
            if invalidated:
                continue
            # Canonical orientation makes A/B reversal share one family and consistent vectors.
            versions = [s["version_id"] for s in sides]
            delta = np.array(q["difference"])
            target = {"A": 1.0, "B": 0.0, "tie": 0.5}[payload["outcome"]]
            if versions[0] > versions[1]:
                delta, target = -delta, 1 - target
            rows.append(
                {
                    "region": review["region"],
                    "delta": delta,
                    "target": target,
                    "weight": 0.5 if payload["outcome"] == "tie" else 1.0,
                    "family": canonical(
                        [sorted(versions), state["epoch"], review["region"]]
                    ),
                    "eventId": event["event_id"],
                }
            )
        models = {}
        for region in sorted({r["region"] for r in rows}):
            group = [r for r in rows if r["region"] == region]
            weights = family_weights(
                [r["family"] for r in group], np.array([r["weight"] for r in group])
            )
            model = fit_pairwise(
                np.array([r["delta"] for r in group]),
                np.array([r["target"] for r in group]),
                weights,
            )
            models[region] = {
                "state": "fitted" if model.converged else "insufficient_evidence",
                "coefficients": model.coefficients.tolist()
                if model.converged
                else None,
                "hessian": model.hessian.tolist() if model.converged else None,
                "effectiveWeight": model.effective_weight,
                "eventIds": [r["eventId"] for r in group],
                "featureNames": list(FEATURE_NAMES),
            }
        branch = self.get(db, "branches", project, "branch_id", branch_id)
        candidates = []
        for design in db.execute(
            "SELECT * FROM designs WHERE project_id=? ORDER BY rowid", (project,)
        ):
            for row in db.execute(
                "SELECT * FROM design_versions WHERE project_id=? AND design_id=? ORDER BY revision DESC",
                (project, design["design_id"]),
            ):
                if self.visible_in_branch(
                    db, project, branch, design["branch_id"], row["created_sequence"]
                ):
                    if row["version_id"] not in state["rejected"]:
                        links = self.current_links(db, project, row["version_id"])
                        candidates.append(
                            {"versionId": row["version_id"], "links": links}
                        )
                    break
        rankings = {}
        for region in ("whole", *models):
            if region in rankings:
                continue
            observations = [
                {
                    "versionId": c["versionId"],
                    "sourceFamilies": [
                        self.source_family(db, project, l["link_id"])
                        for l in c["links"]
                    ],
                    "observations": [
                        o
                        for l in c["links"]
                        for o in self.link_observations(db, project, l, region)
                    ],
                }
                for c in candidates
            ]
            rankings[region] = rank_cohort(observations, models.get(region), region)
        disagreements = []
        for family in {r["family"] for r in rows}:
            group = [r for r in rows if r["family"] == family]
            if any(r["target"] > 0.5 for r in group) and any(
                r["target"] < 0.5 for r in group
            ):
                disagreements.append(
                    {
                        "eventIds": [r["eventId"] for r in group],
                        "region": group[0]["region"],
                        "message": "Choices differ across repeated contexts. Review the frozen evidence before generalizing.",
                    }
                )
        return {
            **state,
            "models": models,
            "rankings": rankings,
            "contextualDisagreements": disagreements,
            "state": "fitted" if models else "insufficient_evidence",
            "limitations": "Region models are separate. No universal ranking without a common observed feature basis. Numerical convergence is not preference certainty.",
        }
