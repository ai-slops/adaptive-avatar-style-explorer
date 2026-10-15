"""Discovery rounds orchestrate existing immutable designs and unreviewed depictions.

Exploratory reactions are separately frozen and never enter the strict ranker.
Only an explicit bounded batch action can invoke the native provider.
"""

import asyncio
import io
import json
import zipfile
from copy import deepcopy
from pathlib import Path

from .common import DomainError, canonical, digest, require, uid
from .contracts import (
    CanonicalInput,
    CodexGenerationInput,
    DepictionInput,
    DesignInput,
    LinkInput,
    PlanInput,
    RecipeInput,
    ReferenceInput,
)
from .discovery_planner import PART_KEYS, develop, prop, seed, signature

PART_NAMES = {
    "face": "얼굴",
    "hair": "머리",
    "outfit": "의상",
    "body": "체형",
    "accessories": "장식",
    "palette": "색상",
}


class Discovery:
    def __init__(self, service, assets, planning, native=None):
        self.service, self.assets, self.planning, self.native = (
            service,
            assets,
            planning,
            native,
        )
        self.tasks = {}
        with service.database.connect() as db:
            rows = list(
                db.execute(
                    "SELECT * FROM discovery_batches WHERE state IN ('queued','running')"
                )
            )
            for row in rows:
                payload = json.loads(row["payload_json"])
                payload["message"] = (
                    "앱이 중단되었습니다. 완료 여부를 확인한 뒤 남은 후보만 다시 요청해 주세요. 자동 재요청하지 않습니다."
                )
                db.execute(
                    "UPDATE discovery_batches SET state='interrupted',payload_json=? WHERE project_id=? AND batch_id=?",
                    (canonical(payload), row["project_id"], row["batch_id"]),
                )

    def workspace(self, db, principal, project):
        self.service.owned(db, principal, project)
        db.execute(
            "INSERT OR IGNORE INTO discovery_workspace(project_id) VALUES (?)",
            (project,),
        )
        return dict(
            db.execute(
                "SELECT * FROM discovery_workspace WHERE project_id=?", (project,)
            ).fetchone()
        )

    def candidate(self, db, project, candidate_id):
        row = self.service.get(
            db, "discovery_candidates", project, "candidate_id", candidate_id
        )
        return {**row, **json.loads(row["payload_json"])}

    def effective(self, db, project):
        rows = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM discovery_reactions WHERE project_id=? ORDER BY sequence",
                (project,),
            )
        ]
        undone = {row["target_reaction_id"] for row in rows if row["action"] == "undo"}
        active = [
            {**row, "payload": json.loads(row["payload_json"])}
            for row in rows
            if row["action"] != "undo" and row["reaction_id"] not in undone
        ]
        directions = {}
        preserved = {}
        names = {}
        selection = None
        rejected = set()
        wrong = set()
        last = None
        for row in active:
            p = row["payload"]
            action = row["action"]
            candidates = p.get("candidates", [])
            if action in ("interest", "choose_a", "choose_b", "both"):
                chosen = (
                    candidates
                    if action in ("interest", "both")
                    else [candidates[0 if action == "choose_a" else 1]]
                )
                for c in chosen:
                    directions[c["directionId"]] = c["candidateId"]
            elif action == "release_direction":
                directions.pop(candidates[0]["directionId"], None)
            elif action == "neither":
                declined = {c["candidateId"] for c in candidates}
                rejected.update(declined)
                directions = {
                    did: cid for did, cid in directions.items() if cid not in declined
                }
            elif action == "image_wrong":
                wrong.update(p["linkIds"])
            elif action == "keep_part":
                c = candidates[0]
                preserved.setdefault(c["directionId"], {})[p["part"]] = {
                    "linkId": p["linkIds"][0],
                    "candidateId": c["candidateId"],
                    "reactionId": row["reaction_id"],
                }
            elif action == "unlock_part":
                preserved.setdefault(candidates[0]["directionId"], {}).pop(
                    p["part"], None
                )
            elif action == "rename_direction":
                names[candidates[0]["directionId"]] = p["name"]
            elif action == "use_design":
                selection = p["selection"]
            if action not in ("rename_direction", "use_design"):
                last = action
        return {
            "directions": directions,
            "preserved": preserved,
            "names": names,
            "selection": selection,
            "rejected": sorted(rejected),
            "wrongLinks": sorted(wrong),
            "active": active,
            "feedbackHash": digest([row["reaction_id"] for row in active]),
            "lastAction": last,
        }

    def link(self, db, project, link_id):
        link = self.service.get(db, "depiction_links", project, "link_id", link_id)
        depiction = self.service.get(
            db, "depictions", project, "depiction_id", link["depiction_id"]
        )
        asset = self.service.get(
            db, "assets", project, "asset_id", depiction["asset_id"]
        )
        return {
            "linkId": link_id,
            "versionId": link["version_id"],
            "assetId": asset["asset_id"],
            "status": link["status"],
            "sourceKind": depiction["source_kind"],
            "exportPermission": json.loads(depiction["metadata_json"])[
                "exportPermission"
            ],
            "digest": asset["digest"],
            "assessment": json.loads(link["assessment_json"]),
            "observations": [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT observed_json FROM observations WHERE project_id=? AND link_id=?",
                    (project, link_id),
                )
            ],
        }

    def representative(self, db, project, version):
        links = self.service.current_links(db, project, version)
        if not links:
            return None
        chosen = next(
            (link for link in links if link["status"] == "compatible"), links[-1]
        )
        return self.link(db, project, chosen["link_id"])

    def card(self, db, project, candidate):
        image = (
            self.link(db, project, candidate["primaryLinkId"])
            if candidate.get("primaryLinkId")
            else None
        )
        if not image and not candidate.get("needsNewResult", False):
            image = self.representative(db, project, candidate["version_id"])
        job = None
        if candidate.get("jobId"):
            row = db.execute(
                "SELECT job_id,state,task,result_json FROM codex_jobs WHERE project_id=? AND job_id=?",
                (project, candidate["jobId"]),
            ).fetchone()
            if row:
                job = {
                    "jobId": row["job_id"],
                    "state": row["state"],
                    "task": row["task"],
                    "result": json.loads(row["result_json"])
                    if row["result_json"]
                    else None,
                }
        if not image and job and (job.get("result") or {}).get("linkId"):
            image = self.link(db, project, job["result"]["linkId"])
        return {
            "candidateId": candidate["candidate_id"],
            "directionId": candidate["direction_id"],
            "roundId": candidate["round_id"],
            "versionId": candidate["version_id"],
            "position": candidate["position"],
            "label": candidate["label"],
            "purpose": candidate["purpose"],
            "kind": candidate["kind"],
            "preserveParts": candidate.get("preserveParts", []),
            "varyPart": candidate.get("varyPart"),
            "sourceCandidateId": candidate.get("sourceCandidateId"),
            "sourceLinkIds": candidate.get("sourceLinkIds", []),
            "image": image,
            "returnName": candidate["returnName"],
            "prompt": candidate.get("prompt"),
            "job": job,
            "error": candidate.get("error"),
        }

    def state(self, principal, project):
        with self.service.database.connect() as db:
            workspace = self.workspace(db, principal, project)
            effective = self.effective(db, project)
            rounds = []
            for row in db.execute(
                "SELECT * FROM discovery_rounds WHERE project_id=? ORDER BY ordinal DESC",
                (project,),
            ):
                payload = json.loads(row["payload_json"])
                rounds.append(
                    {
                        "roundId": row["round_id"],
                        "ordinal": row["ordinal"],
                        "basedRevision": row["based_revision"],
                        "historicalFeedback": row["feedback_hash"]
                        != effective["feedbackHash"],
                        **payload,
                        "candidates": [
                            self.card(
                                db,
                                project,
                                {**dict(c), **json.loads(c["payload_json"])},
                            )
                            for c in db.execute(
                                "SELECT * FROM discovery_candidates WHERE project_id=? AND round_id=? ORDER BY position",
                                (project, row["round_id"]),
                            )
                        ],
                    }
                )
            directions = []
            for direction_id, candidate_id in effective["directions"].items():
                c = self.candidate(db, project, candidate_id)
                directions.append(
                    {
                        "directionId": direction_id,
                        "label": effective["names"].get(direction_id, c["label"]),
                        "candidate": self.card(db, project, c),
                        "preserved": effective["preserved"].get(direction_id, {}),
                    }
                )
            library = []
            for row in db.execute(
                "SELECT v.version_id,d.title,v.revision FROM design_versions v JOIN designs d ON v.project_id=d.project_id AND v.design_id=d.design_id WHERE v.project_id=? ORDER BY v.created_sequence DESC",
                (project,),
            ):
                library.append(
                    {
                        "versionId": row["version_id"],
                        "label": f"{row['title']} · {row['revision']}",
                        "image": self.representative(db, project, row["version_id"]),
                    }
                )
            batches = [
                {
                    "batchId": row["batch_id"],
                    "roundId": row["round_id"],
                    "state": row["state"],
                    **json.loads(row["payload_json"]),
                }
                for row in db.execute(
                    "SELECT * FROM discovery_batches WHERE project_id=? ORDER BY rowid DESC LIMIT 20",
                    (project,),
                )
            ]
            inspirations = [
                {"inspirationId": row["inspiration_id"], "assetId": row["asset_id"]}
                for row in db.execute(
                    "SELECT * FROM discovery_inspirations WHERE project_id=?",
                    (project,),
                )
            ]
            return {
                "revision": workspace["revision"],
                "activeRoundId": workspace["active_round_id"],
                "rounds": rounds,
                "directions": directions,
                "selection": effective["selection"],
                "rejected": effective["rejected"],
                "wrongLinks": effective["wrongLinks"],
                "history": [
                    {
                        "reactionId": row["reaction_id"],
                        "action": row["action"],
                        "labels": [
                            c["label"] for c in row["payload"].get("candidates", [])
                        ],
                        "part": row["payload"].get("part"),
                        "canUndo": True,
                    }
                    for row in reversed(effective["active"])
                ][:50],
                "library": library,
                "inspirations": inspirations,
                "batches": batches,
                "nextStep": "다른 방향을 제안합니다. 이전 후보와 선택은 기록에 남습니다."
                if effective["lastAction"] == "neither"
                else f"저장한 {len(directions)}개 방향을 각각 발전시키고 다른 대안도 함께 제안합니다."
                if directions
                else "서로 다른 실루엣, 얼굴, 머리와 의상 방향을 제안합니다. 정답을 미리 설명하지 않아도 됩니다.",
                "mode": "codex_local" if self.native else "community_prompt_only",
            }

    def persist_candidate(self, project, candidate_id, payload):
        with self.service.database.connect() as db:
            db.execute(
                "UPDATE discovery_candidates SET payload_json=? WHERE project_id=? AND candidate_id=?",
                (canonical(payload), project, candidate_id),
            )

    def references(self, db, project, source_ids, preserved):
        refs = []
        for link_id in dict.fromkeys(
            [*source_ids, *[p["linkId"] for p in preserved.values()]]
        ):
            link = self.link(db, project, link_id)
            parts = [
                PART_NAMES[part]
                for part, p in preserved.items()
                if p["linkId"] == link_id
            ]
            refs.append(
                ReferenceInput(
                    assetId=link["assetId"],
                    role="component" if parts else "identity",
                    instruction=(
                        "Preserve only these explicitly selected visible parts: "
                        + ", ".join(parts)
                        + ". Other parts may vary as proposed."
                        if parts
                        else "Use this image as visual direction and identity inspiration for the stated design changes. Do not infer hidden geometry."
                    ),
                )
            )
        return refs[:10]

    def compile_candidate(self, principal, project, candidate):
        with self.service.database.connect() as db:
            state = self.service.owned(db, principal, project)
            refs = self.references(
                db,
                project,
                candidate.get("sourceLinkIds", []),
                candidate.get("preserved", {}),
            )
        return self.planning.compile(
            principal,
            project,
            PlanInput(
                targetVersionId=candidate["version_id"],
                purpose="additional_view"
                if candidate["kind"] == "observation"
                else "depiction_correction"
                if candidate["kind"] == "correction"
                else "additional_view",
                recipe=RecipeInput(view=candidate.get("view", "front")),
                references=refs,
                expectedEventSequence=state["event_sequence"],
            ),
        )

    def prepare(self, principal, project, data):
        s = self.service
        with s.database.connect() as db:
            workspace = self.workspace(db, principal, project)
            old = db.execute(
                "SELECT * FROM discovery_rounds WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if old:
                require(
                    old["request_hash"] == digest(data.model_dump()),
                    "같은 요청 번호로 다른 작업을 요청할 수 없습니다.",
                    409,
                )
                return old["round_id"]
            require(
                workspace["revision"] == data.expectedRevision,
                "다른 창에서 선택이 바뀌었습니다. 새로고침해 주세요.",
                409,
            )
            effective = self.effective(db, project)
            sources = []
            if data.candidateId:
                sources = [self.candidate(db, project, data.candidateId)]
            elif data.intent != "different" and effective["lastAction"] != "neither":
                sources = [
                    self.candidate(db, project, cid)
                    for did, cid in effective["directions"].items()
                    if data.directionId is None or did == data.directionId
                ]
            if data.intent in ("focus", "observe", "correct", "adopt"):
                require(sources, "먼저 후보를 선택해 주세요.")
            if data.preservePart:
                require(
                    sources and self.card(db, project, sources[0])["image"],
                    "보존할 부분이 보이는 후보를 선택해 주세요.",
                )
            seen = {
                signature(s.version(db, project, row[0])["spec"])
                for row in db.execute(
                    "SELECT version_id FROM discovery_candidates WHERE project_id=?",
                    (project,),
                )
            }
            ordinal = db.execute(
                "SELECT COALESCE(MAX(ordinal),0)+1 FROM discovery_rounds WHERE project_id=?",
                (project,),
            ).fetchone()[0]
            rid = uid()
            explanation = (
                "저장한 방향을 각각 발전시키고 다른 대안도 함께 준비했습니다."
                if sources and data.intent == "continue"
                else "보존할 부분과 바꿀 부분을 구분한 새 조합입니다. 전체 결과를 다시 판단해 주세요."
                if data.intent == "focus"
                else "같은 디자인을 다른 조건에서 확인합니다. 새로운 스타일 후보가 아닙니다."
                if data.intent in ("observe", "correct")
                else "이전 반응과 구분되는 새로운 디자인 방향입니다."
            )
            payload = {
                "explanation": explanation,
                "intent": data.intent,
                "preparation": "preparing",
                "brief": data.brief,
            }
            db.execute(
                "INSERT INTO discovery_rounds VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    rid,
                    ordinal,
                    data.requestId,
                    digest(data.model_dump()),
                    workspace["revision"],
                    effective["feedbackHash"],
                    canonical(payload),
                ),
            )
            db.execute(
                "UPDATE discovery_workspace SET active_round_id=?,revision=revision+1 WHERE project_id=?",
                (rid, project),
            )
        try:
            count = 1 if data.intent in ("observe", "correct", "adopt") else data.count
            for position in range(count):
                # Always keep a genuinely different alternative in a broad development round.
                source = (
                    sources[position % len(sources)]
                    if sources
                    and (
                        data.intent != "continue" or position < count - 1 or count == 1
                    )
                    else None
                )
                preserved = (
                    deepcopy(effective["preserved"].get(source["direction_id"], {}))
                    if source
                    else {}
                )
                source_links = []
                source_version = None
                frozen = []
                if source:
                    with s.database.connect() as db:
                        source_version = s.version(db, project, source["version_id"])
                        card = self.card(db, project, source)
                        if card["image"]:
                            source_links = [card["image"]["linkId"]]
                        lineage = s.get(
                            db,
                            "designs",
                            project,
                            "design_id",
                            source_version["design_id"],
                        )
                        frozen = s.inherited_locks(
                            db,
                            project,
                            source["version_id"],
                            s.reduce(db, project, lineage["branch_id"])["locks"],
                        )
                    if data.preservePart:
                        preserved[data.preservePart] = {
                            "linkId": source_links[0],
                            "candidateId": source["candidate_id"],
                            "temporary": True,
                        }
                kind = "design"
                vary = "whole"
                direction = source["direction_id"] if source else uid()
                if source and data.intent in ("observe", "correct"):
                    if data.intent == "correct":
                        with s.database.connect() as db:
                            attempts = [
                                json.loads(row[0])
                                for row in db.execute(
                                    "SELECT payload_json FROM discovery_candidates WHERE project_id=? AND version_id=?",
                                    (project, source["version_id"]),
                                )
                            ]
                            require(
                                sum(
                                    p.get("kind") == "correction"
                                    and (p.get("primaryLinkId") or p.get("jobId"))
                                    for p in attempts
                                )
                                < 2,
                                "이미 두 번 확인을 요청했습니다. 문제를 보류하거나 외부 도구/다른 제작 방법을 선택해 주세요.",
                                409,
                            )
                    version = source_version
                    kind = "observation" if data.intent == "observe" else "correction"
                    label = (
                        source["label"]
                        + " · "
                        + ("다른 모습 확인" if kind == "observation" else "이미지 수정")
                    )
                elif source and data.intent != "adopt":
                    requested = (
                        data.part
                        if data.intent == "focus"
                        else ("hair", "outfit", "body", "face", "accessories")[
                            ((ordinal - 2) + position // max(1, len(sources))) % 5
                        ]
                    )
                    locked_parts = {
                        part
                        for part, key in PART_KEYS.items()
                        if any(
                            k == key
                            or k.startswith(part + ".")
                            or k == "preservation." + part
                            for k in frozen
                        )
                    }
                    if data.intent == "focus":
                        require(
                            requested not in locked_parts
                            and requested not in preserved,
                            "보존한 부분입니다. 먼저 보존을 해제하거나 다른 부분/새로운 방향을 선택해 주세요.",
                            409,
                        )
                    options = [requested] + [
                        part for part in PART_KEYS if part != requested
                    ]
                    part = next(
                        (
                            part
                            for part in options
                            if part not in preserved and part not in locked_parts
                        ),
                        None,
                    )
                    require(
                        part,
                        "모든 부분이 보존되어 있습니다. 바꿀 부분의 보존을 명시적으로 해제해 주세요.",
                        409,
                    )
                    base_spec = deepcopy(source_version["spec"])
                    for key in list(base_spec["properties"]):
                        if (
                            key.startswith("discovery.anchor_")
                            and key.removeprefix("discovery.anchor_") not in preserved
                        ):
                            del base_spec["properties"][key]
                    spec = None
                    for step in range(
                        ordinal * 3 + position, ordinal * 3 + position + 12
                    ):
                        proposed = develop(base_spec, part, step, preserved, frozen)
                        for name, anchor in preserved.items():
                            proposed["properties"]["discovery.anchor_" + name] = {
                                "value": "Preserve the "
                                + name
                                + " visibly shown in the selected reference. Hidden construction stays unspecified.",
                                "state": "proposed",
                                "sourceEventIds": [],
                                "sourceDepictionLinkIds": [anchor["linkId"]],
                                "notes": "User-selected visible scope, not a claim that every source feature is desired.",
                            }
                        if signature(proposed) not in seen:
                            spec = proposed
                            break
                    require(
                        spec,
                        "이 조합은 이미 살펴봤습니다. 다른 부분이나 새로운 방향을 선택해 주세요.",
                        409,
                    )
                    label = (
                        source["label"].split(" · ")[0]
                        + " · "
                        + PART_NAMES[part]
                        + " 대안"
                    )
                    vary = part
                    version = s.create_design(
                        principal,
                        project,
                        DesignInput(
                            title=label,
                            basedOnVersionId=source["version_id"],
                            branchId=lineage["branch_id"],
                            reason="Discovery proposal from explicit exploratory reactions; no verified preference claim.",
                            spec=CanonicalInput.model_validate(spec),
                        ),
                    )
                else:
                    index = (ordinal - 1) * count + position
                    for attempt in range(32):
                        label, spec = seed(index + attempt, data.brief)
                        if data.intent == "adopt" and source:
                            spec = {
                                "morphology": "unspecified",
                                "properties": {
                                    "design.description": prop(
                                        "Independent provisional character interpretation of the selected unexpected reference. Do not assume it follows the previous target."
                                    )
                                },
                                "componentRelations": [],
                                "unresolvedDecisions": [
                                    "Visible design details need interpretation; unseen construction remains unspecified."
                                ],
                            }
                            label = "새로 살펴볼 참고 방향"
                            kind = "inspiration"
                            direction = uid()
                        if signature(spec) not in seen:
                            break
                    require(
                        signature(spec) not in seen,
                        "준비된 방향을 모두 살펴봤습니다. 저장한 방향이나 참고 이미지를 선택해 다음 대안을 발전시켜 주세요.",
                        409,
                    )
                    version = s.create_design(
                        principal,
                        project,
                        DesignInput(
                            title=label, spec=CanonicalInput.model_validate(spec)
                        ),
                    )
                seen.add(signature(version["spec"]))
                cid = uid()
                payload = {
                    "label": label,
                    "purpose": explanation,
                    "kind": kind,
                    "preserveParts": list(preserved),
                    "preserved": preserved,
                    "varyPart": vary,
                    "sourceCandidateId": source["candidate_id"] if source else None,
                    "sourceVersionId": source["version_id"] if source else None,
                    "sourceLinkIds": source_links,
                    "owner": principal,
                    "view": data.view
                    if kind in ("observation", "correction")
                    else "front",
                    "needsNewResult": True,
                    "returnName": f"option-{ordinal}-{cid[:10]}.png",
                }
                with s.database.connect() as db:
                    db.execute(
                        "INSERT INTO discovery_candidates VALUES (?,?,?,?,?,?,?)",
                        (
                            project,
                            cid,
                            rid,
                            position,
                            direction,
                            version["version_id"],
                            canonical(payload),
                        ),
                    )
            # Compile after all design events, so each pack is current at preparation.
            with s.database.connect() as db:
                candidates = [
                    self.candidate(db, project, row[0])
                    for row in db.execute(
                        "SELECT candidate_id FROM discovery_candidates WHERE project_id=? AND round_id=? ORDER BY position",
                        (project, rid),
                    )
                ]
            for candidate in candidates:
                prompt = self.compile_candidate(principal, project, candidate)
                payload = json.loads(candidate["payload_json"])
                payload["prompt"] = prompt
                self.persist_candidate(project, candidate["candidate_id"], payload)
            with s.database.connect() as db:
                payload = json.loads(
                    db.execute(
                        "SELECT payload_json FROM discovery_rounds WHERE project_id=? AND round_id=?",
                        (project, rid),
                    ).fetchone()[0]
                )
                payload["preparation"] = "ready"
                db.execute(
                    "UPDATE discovery_rounds SET payload_json=? WHERE project_id=? AND round_id=?",
                    (canonical(payload), project, rid),
                )
            return rid
        except (DomainError, ValueError) as exc:
            with s.database.connect() as db:
                payload = json.loads(
                    db.execute(
                        "SELECT payload_json FROM discovery_rounds WHERE project_id=? AND round_id=?",
                        (project, rid),
                    ).fetchone()[0]
                )
                payload.update(preparation="incomplete", error=str(exc))
                db.execute(
                    "UPDATE discovery_rounds SET payload_json=? WHERE project_id=? AND round_id=?",
                    (canonical(payload), project, rid),
                )
            raise DomainError(str(exc), 409) from exc

    def react(self, principal, project, data):
        s = self.service
        selection_coverage = None
        if data.action == "use_design":
            with s.database.connect() as db:
                s.owned(db, principal, project)
                subject = self.candidate(db, project, data.candidateIds[0])
            selection_coverage = s.evidence(principal, project, subject["version_id"])
        with s.database.connect() as db:
            workspace = self.workspace(db, principal, project)
            old = db.execute(
                "SELECT * FROM discovery_reactions WHERE project_id=? AND reaction_id=?",
                (project, data.requestId),
            ).fetchone()
            if old:
                require(
                    old["request_hash"] == digest(data.model_dump()),
                    "반응 요청 번호가 다른 내용에 재사용되었습니다.",
                    409,
                )
                return json.loads(old["payload_json"])
            require(
                workspace["revision"] == data.expectedRevision,
                "다른 창에서 선택이 바뀌었습니다. 새로고침해 주세요.",
                409,
            )
            effective = self.effective(db, project)
            if data.action == "undo":
                target = next(
                    (
                        r
                        for r in effective["active"]
                        if r["reaction_id"] == data.targetReactionId
                    ),
                    None,
                )
                require(target, "이미 되돌렸거나 이 프로젝트의 반응이 아닙니다.", 409)
                payload = {"targetReactionId": data.targetReactionId}
            else:
                require(
                    len(set(data.candidateIds)) == len(data.candidateIds),
                    "같은 후보를 중복 선택할 수 없습니다.",
                )
                candidates = [
                    self.candidate(db, project, cid) for cid in data.candidateIds
                ]
                require(
                    len(data.linkIds) == len(candidates),
                    "반응할 때 실제로 보인 이미지를 함께 기록해 주세요.",
                )
                shown = []
                for candidate, link_id in zip(candidates, data.linkIds):
                    link = self.link(db, project, link_id)
                    require(
                        link["versionId"] == candidate["version_id"],
                        "다른 후보의 이미지는 반응 근거로 사용할 수 없습니다.",
                        403,
                    )
                    shown.append(link)
                payload = {
                    "candidates": [
                        {
                            "candidateId": c["candidate_id"],
                            "directionId": c["direction_id"],
                            "versionId": c["version_id"],
                            "label": c["label"],
                        }
                        for c in candidates
                    ],
                    "linkIds": data.linkIds,
                    "scope": data.part or "whole_impression",
                    "classification": "exploratory_interest_not_qualified_training",
                    "frozenShownEvidence": shown,
                    "part": data.part,
                    "name": data.name,
                }
                if data.action == "use_design":
                    selected = effective["selection"]
                    require(
                        selected is None
                        or selected["versionId"] == candidates[0]["version_id"]
                        or data.replaceSelection,
                        "이미 선택한 디자인이 있습니다. 선택 교체를 명시적으로 확인해 주세요.",
                        409,
                    )
                    version = s.version(db, project, candidates[0]["version_id"])
                    payload["selection"] = {
                        "selectionId": data.requestId,
                        "candidateId": candidates[0]["candidate_id"],
                        "versionId": version["version_id"],
                        "canonicalHash": version["canonical_hash"],
                        "spec": version["spec"],
                        "image": shown[0],
                        "label": candidates[0]["label"],
                        "preserved": effective["preserved"].get(
                            candidates[0]["direction_id"], {}
                        ),
                        "otherDirections": dict(effective["directions"]),
                        "status": "design_chosen",
                        "unresolved": version["spec"]["unresolvedDecisions"],
                        "uncheckedViews": [
                            slot
                            for slot in selection_coverage["slots"]
                            if slot["status"] in ("missing", "imported_unreviewed")
                        ],
                        "modelChecks": "Actual 3D geometry, rigging and production readiness remain unverified.",
                        "geometricVerification": "none",
                    }
                if data.action == "rename_direction":
                    require(data.name, "방향 이름을 입력해 주세요.")
            db.execute(
                "INSERT INTO discovery_reactions VALUES (?,?,?,?,?,?,?)",
                (
                    project,
                    data.requestId,
                    workspace["revision"] + 1,
                    digest(data.model_dump()),
                    data.action,
                    data.targetReactionId,
                    canonical(payload),
                ),
            )
            db.execute(
                "UPDATE discovery_workspace SET revision=revision+1 WHERE project_id=?",
                (project,),
            )
        return payload

    def activate(self, principal, project, round_id):
        with self.service.database.connect() as db:
            self.workspace(db, principal, project)
            self.service.get(db, "discovery_rounds", project, "round_id", round_id)
            db.execute(
                "UPDATE discovery_workspace SET active_round_id=? WHERE project_id=?",
                (round_id, project),
            )

    def use_library(self, principal, project, data):
        with self.service.database.connect() as db:
            workspace = self.workspace(db, principal, project)
            old = db.execute(
                "SELECT round_id,request_hash FROM discovery_rounds WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if old:
                require(
                    old["request_hash"] == digest(data.model_dump()),
                    "요청 번호가 재사용되었습니다.",
                    409,
                )
                return old["round_id"]
            require(
                workspace["revision"] == data.expectedRevision,
                "새로고침 후 다시 선택해 주세요.",
                409,
            )
            version = self.service.version(db, project, data.versionId)
            design = self.service.get(
                db, "designs", project, "design_id", version["design_id"]
            )
            image = self.representative(db, project, data.versionId)
            require(image, "실제 이미지가 있는 기존 후보를 선택해 주세요.")
            rid, cid, direction = uid(), uid(), uid()
            ordinal = db.execute(
                "SELECT COALESCE(MAX(ordinal),0)+1 FROM discovery_rounds WHERE project_id=?",
                (project,),
            ).fetchone()[0]
            db.execute(
                "INSERT INTO discovery_rounds VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    rid,
                    ordinal,
                    data.requestId,
                    digest(data.model_dump()),
                    workspace["revision"],
                    self.effective(db, project)["feedbackHash"],
                    canonical(
                        {
                            "preparation": "ready",
                            "intent": "library",
                            "explanation": "기존 작업을 그대로 이어서 탐색합니다. 과거 반응이나 라운드는 추측하지 않습니다.",
                        }
                    ),
                ),
            )
            payload = {
                "label": design["title"],
                "purpose": "기존 라이브러리에서 선택한 방향",
                "kind": "existing",
                "primaryLinkId": image["linkId"],
                "owner": principal,
                "returnName": f"option-{ordinal}-{cid[:10]}.png",
                "preserveParts": [],
                "sourceLinkIds": [],
            }
            db.execute(
                "INSERT INTO discovery_candidates VALUES (?,?,?,?,?,?,?)",
                (project, cid, rid, 0, direction, data.versionId, canonical(payload)),
            )
            db.execute(
                "UPDATE discovery_workspace SET revision=revision+1,active_round_id=? WHERE project_id=?",
                (rid, project),
            )
            return rid

    def import_results(self, principal, project, data):
        # Imported filenames supply return context, never identity approval.
        s = self.service
        with s.database.connect() as db:
            self.workspace(db, principal, project)
            old = db.execute(
                "SELECT * FROM discovery_imports WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if old:
                require(
                    old["request_hash"] == digest(data.model_dump()),
                    "가져오기 요청 번호가 재사용되었습니다.",
                    409,
                )
                return json.loads(old["result_json"])
            candidates = (
                [
                    self.candidate(db, project, row[0])
                    for row in db.execute(
                        "SELECT candidate_id FROM discovery_candidates WHERE project_id=? AND round_id=?",
                        (project, data.roundId),
                    )
                ]
                if data.roundId
                else []
            )
            prepared = []
            for item in data.items:
                s.get(db, "assets", project, "asset_id", item.assetId)
                candidate = (
                    self.candidate(db, project, item.candidateId)
                    if item.candidateId
                    else None
                )
                if candidate and data.roundId:
                    require(
                        candidate["round_id"] == data.roundId,
                        "다른 묶음의 후보입니다.",
                        409,
                    )
                if not candidate and not item.independentReference:
                    matches = [
                        c
                        for c in candidates
                        if Path(c["returnName"]).stem == Path(item.filename).stem
                    ]
                    if len(matches) == 1:
                        candidate = matches[0]
                    else:
                        require(
                            item.independentReference,
                            "대상이 모호한 이미지입니다. 썸네일로 후보를 지정하거나 독립 참고자료로 선택해 주세요.",
                            409,
                        )
                prepared.append((item, candidate))
        results = []
        for item, candidate in prepared:
            dep = s.create_depiction(
                principal,
                project,
                DepictionInput(
                    assetId=item.assetId,
                    sourceKind="external_result"
                    if candidate and candidate.get("prompt")
                    else "reference",
                    originPlanId=candidate["prompt"]["planId"]
                    if candidate and candidate.get("prompt")
                    else None,
                    originPromptRevision=candidate["prompt"]["revision"]
                    if candidate and candidate.get("prompt")
                    else None,
                    explicitlyUnassociated=not candidate,
                    exportPermission=item.exportPermission,
                    caption="User-imported discovery result; adherence not reviewed.",
                ),
            )
            if candidate:
                linked = s.create_link(
                    principal,
                    project,
                    LinkInput(
                        depictionId=dep["depictionId"],
                        versionId=candidate["version_id"],
                    ),
                )
                payload = json.loads(candidate["payload_json"])
                payload["primaryLinkId"] = linked["linkId"]
                self.persist_candidate(project, candidate["candidate_id"], payload)
                results.append(
                    {
                        "candidateId": candidate["candidate_id"],
                        "linkId": linked["linkId"],
                        "assetId": item.assetId,
                    }
                )
            else:
                with s.database.connect() as db:
                    db.execute(
                        "INSERT INTO discovery_inspirations VALUES (?,?,?,?)",
                        (project, uid(), item.assetId, dep["depictionId"]),
                    )
                results.append({"candidateId": None, "assetId": item.assetId})
        with s.database.connect() as db:
            db.execute(
                "INSERT INTO discovery_imports VALUES (?,?,?,?)",
                (
                    project,
                    data.requestId,
                    digest(data.model_dump()),
                    canonical(results),
                ),
            )
        return results

    def round_pack(self, principal, project, round_id):
        state = self.state(principal, project)
        round = next((r for r in state["rounds"] if r["roundId"] == round_id), None)
        require(round, "후보 묶음을 찾을 수 없습니다.", 404)
        stream = io.BytesIO()
        manifest = []
        written_references = set()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "README.md",
                "# Discovery prompt pack\n\nGenerate each option independently outside this app. Return images with the exact filenames below. Every result is provisional; imported images do not prove adherence or 3D readiness.\n\n"
                + round["explanation"],
            )
            for candidate in round["candidates"]:
                prompt = candidate.get("prompt")
                if not prompt:
                    continue
                name = Path(candidate["returnName"]).stem
                archive.writestr(
                    name + ".md",
                    candidate["label"]
                    + "\n\n"
                    + candidate["purpose"]
                    + "\n\n"
                    + prompt["promptText"]
                    + "\n\nSAVE RETURN AS: "
                    + candidate["returnName"],
                )
                refs = []
                with self.service.database.connect() as db:
                    for ref in prompt["references"]:
                        source_ids = list(
                            dict.fromkeys(
                                [
                                    *candidate.get("sourceLinkIds", []),
                                    *[
                                        anchor["linkId"]
                                        for anchor in self.candidate(
                                            db, project, candidate["candidateId"]
                                        )
                                        .get("preserved", {})
                                        .values()
                                    ],
                                ]
                            )
                        )
                        sources = [self.link(db, project, lid) for lid in source_ids]
                        matching_sources = [
                            source
                            for source in sources
                            if source["assetId"] == ref["assetId"]
                        ]
                        allowed = bool(matching_sources) and all(
                            source["exportPermission"] for source in matching_sources
                        )
                        refs.append({**ref, "included": allowed})
                        if allowed and ref["assetId"] not in written_references:
                            written_references.add(ref["assetId"])
                            asset = self.service.get(
                                db, "assets", project, "asset_id", ref["assetId"]
                            )
                            archive.write(
                                self.assets.root / f"{asset['storage_key']}.png",
                                f"references/{ref['assetId']}.png",
                            )
                manifest.append(
                    {
                        "candidateId": candidate["candidateId"],
                        "label": candidate["label"],
                        "returnName": candidate["returnName"],
                        "versionId": candidate["versionId"],
                        "references": refs,
                    }
                )
            archive.writestr("return-manifest.json", canonical(manifest))
        return stream.getvalue()

    async def generate(self, principal, project, round_id, data):
        require(
            self.native is not None,
            "이 모드에서는 프롬프트만 준비하며 이미지를 생성하지 않습니다.",
            403,
        )
        with self.service.database.connect() as db:
            self.workspace(db, principal, project)
            previous = db.execute(
                "SELECT * FROM discovery_batches WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if previous:
                require(
                    previous["request_hash"] == digest(data.model_dump()),
                    "생성 요청 번호가 다른 내용에 재사용되었습니다.",
                    409,
                )
                return previous["batch_id"]
            require(
                not db.execute(
                    "SELECT 1 FROM discovery_batches WHERE principal_id=? AND state IN ('queued','running')",
                    (principal,),
                ).fetchone(),
                "이미 후보 생성이 진행 중입니다.",
                409,
            )
            candidates = [self.candidate(db, project, cid) for cid in data.candidateIds]
            for c in candidates:
                require(c["round_id"] == round_id, "다른 후보 묶음입니다.", 403)
                require(
                    not self.card(db, project, c)["image"],
                    "이미 결과가 있는 후보는 다시 생성하지 않습니다.",
                    409,
                )
                require(
                    not (c.get("sourceLinkIds") or c.get("preserved"))
                    or data.approveReferenceTransmission,
                    "표시된 참조 이미지 전송에 동의해 주세요.",
                    403,
                )
            effective = self.effective(db, project)
            batch = uid()
            payload = {
                "candidateIds": data.candidateIds,
                "authorizedTurns": data.authorizeTurns,
                "completed": 0,
                "currentJobId": None,
                "feedbackHash": effective["feedbackHash"],
                "input": data.model_dump(),
                "message": "명시적으로 승인한 유한한 후보 묶음입니다.",
            }
            db.execute(
                "INSERT INTO discovery_batches VALUES (?,?,?,?,?,?,?,?)",
                (
                    project,
                    batch,
                    principal,
                    round_id,
                    data.requestId,
                    digest(data.model_dump()),
                    "queued",
                    canonical(payload),
                ),
            )
        self.tasks[batch] = asyncio.create_task(
            self.run_batch(principal, project, batch)
        )
        self.tasks[batch].add_done_callback(lambda _: self.tasks.pop(batch, None))
        return batch

    def batch_update(self, project, batch, state, payload):
        with self.service.database.connect() as db:
            db.execute(
                "UPDATE discovery_batches SET state=?,payload_json=? WHERE project_id=? AND batch_id=?",
                (state, canonical(payload), project, batch),
            )

    async def run_batch(self, principal, project, batch):
        payload = {}
        current_job = None
        try:
            with self.service.database.connect() as db:
                row = self.service.get(
                    db, "discovery_batches", project, "batch_id", batch
                )
                payload = json.loads(row["payload_json"])
            catalog = await self.native.models()
            selected = payload["input"].get("model") or next(
                (m["slug"] for m in catalog if m.get("isDefault")),
                catalog[0]["slug"] if catalog else "",
            )
            require(
                selected and any(m["slug"] == selected for m in catalog),
                "사용 가능한 Codex 모델을 확인해 주세요.",
                401,
            )
            self.batch_update(project, batch, "running", payload)
            for candidate_id in payload["candidateIds"]:
                with self.service.database.connect() as db:
                    self.service.owned(db, principal, project)
                    require(
                        self.effective(db, project)["feedbackHash"]
                        == payload["feedbackHash"],
                        "선택이나 보존 조건이 바뀌어 남은 생성을 중지했습니다. 완료된 결과는 원래 자리에 남습니다.",
                        409,
                    )
                    candidate = self.candidate(db, project, candidate_id)
                plan = self.compile_candidate(principal, project, candidate)
                stored = json.loads(candidate["payload_json"])
                stored["prompt"] = plan
                self.persist_candidate(project, candidate_id, stored)
                job = await self.native.enqueue(
                    principal,
                    project,
                    CodexGenerationInput(
                        requestId=f"{batch}:{candidate_id}",
                        planId=plan["planId"],
                        promptRevision=plan["revision"],
                        model=selected,
                        authorizeOneTurn=True,
                        approveReferenceTransmission=payload["input"][
                            "approveReferenceTransmission"
                        ],
                        exportPermission=payload["input"]["exportPermission"],
                        expectedEventSequence=plan["basedOnEventSequence"],
                    ),
                )
                current_job = job["jobId"]
                payload["currentJobId"] = current_job
                stored["jobId"] = current_job
                self.persist_candidate(project, candidate_id, stored)
                self.batch_update(project, batch, "running", payload)
                if task := self.native.tasks.get(current_job):
                    await asyncio.shield(task)
                finished = self.native.read(principal, project, current_job)
                if (finished.get("result") or {}).get("linkId"):
                    stored["primaryLinkId"] = finished["result"]["linkId"]
                else:
                    stored["error"] = (finished.get("result") or {}).get(
                        "error",
                        "이미지를 만들지 못했습니다. 명시적으로 다시 요청할 수 있습니다.",
                    )
                self.persist_candidate(project, candidate_id, stored)
                payload["completed"] += 1
                payload["currentJobId"] = None
                current_job = None
                self.batch_update(project, batch, "running", payload)
                require(
                    finished["state"] not in ("needs_reauth", "cancelled", "stale"),
                    "연결이나 작업 조건이 바뀌었습니다. 남은 후보는 자동 요청하지 않습니다.",
                    409,
                )
                with self.service.database.connect() as db:
                    jobrow = self.service.get(
                        db, "codex_jobs", project, "job_id", job["jobId"]
                    )
                    state = self.service.owned(db, principal, project)
                    require(
                        state["event_sequence"]
                        == jobrow["input_sequence"]
                        + (1 if (finished.get("result") or {}).get("linkId") else 0),
                        "작업 중 프로젝트가 변경되어 남은 생성을 멈췄습니다.",
                        409,
                    )
            payload["message"] = (
                "요청한 후보 작업이 끝났습니다. 성공한 이미지부터 비교할 수 있습니다."
            )
            self.batch_update(project, batch, "completed", payload)
        except asyncio.CancelledError:
            if current_job:
                self.native.cancel(principal, project, current_job)
            payload["message"] = (
                "남은 요청을 취소했습니다. 이미 제출된 작업은 사용량을 소비하거나 완료될 수 있습니다."
            )
            self.batch_update(project, batch, "cancelled", payload)
        except (DomainError, OSError, ValueError, IndexError, KeyError) as exc:
            if current_job:
                self.native.cancel(principal, project, current_job)
            payload["message"] = str(exc)
            self.batch_update(project, batch, "stopped", payload)

    def cancel(self, principal, project, batch):
        with self.service.database.connect() as db:
            self.workspace(db, principal, project)
            row = self.service.get(db, "discovery_batches", project, "batch_id", batch)
            require(row["principal_id"] == principal, "작업을 찾을 수 없습니다.", 404)
        if row["state"] in ("queued", "running"):
            payload = json.loads(row["payload_json"])
            payload["message"] = (
                "남은 요청을 취소했습니다. 이미 제출된 작업은 사용량을 소비하거나 완료될 수 있습니다."
            )
            self.batch_update(project, batch, "cancelled", payload)
            if payload.get("currentJobId") and self.native:
                self.native.cancel(principal, project, payload["currentJobId"])
            if task := self.tasks.get(batch):
                task.cancel()
        return {"cancelRequested": True}

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
