"""Durable owner/payer-bound reasoning jobs. Restart never repeats provider work."""

import asyncio
import base64
import json

import httpx
from pydantic import ValidationError

from .common import DomainError, canonical, digest, require, uid
from .contracts import JobInput, ReasoningOutput
from .providers.siwc import TASKS, ProviderError


class Jobs:
    def __init__(self, service, provider, assets, sessions):
        self.service, self.provider, self.assets, self.sessions = (
            service,
            provider,
            assets,
            sessions,
        )
        self.tasks = {}
        with service.database.connect() as db:
            db.execute(
                "UPDATE jobs SET state='failed',result_json=? WHERE state IN ('queued','running')",
                (
                    canonical(
                        {
                            "error": "process_interrupted_completion_unknown",
                            "message": "No automatic resubmission. A new explicit attempt may consume additional provider usage.",
                        }
                    ),
                ),
            )

    def consent(self, principal, project, allowed):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            db.execute(
                "INSERT INTO project_settings VALUES (?,?) ON CONFLICT(project_id) DO UPDATE SET allow_image_analysis=excluded.allow_image_analysis",
                (project, int(allowed)),
            )
            db.execute(
                "UPDATE projects SET constraints_version=constraints_version+1 WHERE project_id=?",
                (project,),
            )
        return {"allowImageAnalysis": allowed}

    def context(self, db, principal, project, data):
        s = self.service
        s.owned(db, principal, project)
        version = s.version(db, project, data.versionId)
        links = []
        current = {
            l["link_id"]: l for l in s.current_links(db, project, data.versionId)
        }
        require(
            len(set(data.depictionLinkIds)) == len(data.depictionLinkIds),
            "Duplicate image selection",
        )
        for link_id in data.depictionLinkIds:
            require(
                link_id in current,
                "Selected evidence belongs to another version or is superseded",
            )
            link = current[link_id]
            depiction = s.get(
                db, "depictions", project, "depiction_id", link["depiction_id"]
            )
            asset = s.get(db, "assets", project, "asset_id", depiction["asset_id"])
            links.append(
                {
                    "linkId": link_id,
                    "status": link["status"],
                    "assessment": json.loads(link["assessment_json"]),
                    "observations": [
                        {
                            "observationId": row["observation_id"],
                            "featureSchemaVersion": row["feature_schema"],
                            "extractorVersion": row["extractor_version"],
                            "authority": "reviewed_2d_observation",
                            "geometricVerification": "none",
                            **json.loads(row["observed_json"]),
                        }
                        for row in db.execute(
                            "SELECT * FROM observations WHERE project_id=? AND link_id=? ORDER BY rowid",
                            (project, link_id),
                        )
                    ],
                    "geometricVerification": "none",
                    "caption": json.loads(depiction["metadata_json"])["caption"],
                    "assetId": asset["asset_id"],
                    "derivativePath": str(
                        self.assets.root / f"{asset['storage_key']}.png"
                    ),
                    "sha256": asset["digest"],
                }
            )
        design = s.get(db, "designs", project, "design_id", version["design_id"])
        history = s.history(db, project, design["branch_id"])
        state = s.reduce(db, project, design["branch_id"])
        findings = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM findings WHERE project_id=? AND version_id=? AND state='open'",
                (project, data.versionId),
            )
        ]
        return {
            "objective": "reusable_3d_avatar",
            "canonicalSpec": version,
            "confirmedLocks": state["locks"],
            "feedback": [
                {
                    "eventId": e["event_id"],
                    "action": e["action"],
                    "payload": json.loads(e["payload_json"]),
                }
                for e in history[-100:]
                if e["event_id"] in state["activeEventIds"]
            ],
            "findings": findings,
            "selectedEvidence": links,
            "outputSchema": ReasoningOutput.model_json_schema(),
        }

    def read(self, principal, project, job_id):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            row = self.service.get(db, "jobs", project, "job_id", job_id)
            require(row["principal_id"] == principal, "Job not found", 404)
            request = json.loads(row["request_json"])
            return {
                "jobId": job_id,
                "state": row["state"],
                "task": row["task"],
                "versionId": request["versionId"],
                "registrationId": row["registration_id"],
                "result": json.loads(row["result_json"])
                if row["result_json"]
                else None,
                "inputEventSequence": row["input_sequence"],
            }

    async def enqueue(self, session_id, project, data: JobInput):
        session = self.sessions[session_id]
        principal, registration = session["principal"], session.get("registration")
        require(registration, "Connect your own ChatGPT registration first", 401)
        require(
            not session.get("usagePaused"),
            "Provider usage is paused for this session",
            409,
        )
        require(data.task in TASKS, "Task not allowed", 403)
        s = self.service
        with s.database.connect() as db:
            state = s.owned(db, principal, project)
            old = db.execute(
                "SELECT * FROM job_requests WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if old:
                require(
                    old["request_hash"] == digest(data.model_dump()),
                    "Request ID reused with another payload",
                    409,
                )
                old_job = old["job_id"]
            else:
                old_job = None
            if not old_job:
                s.sequence(state, data.expectedEventSequence)
        if old_job:
            return self.read(principal, project, old_job)
        # Model catalog lookup uses the same validated registration as inference.
        try:
            admitted = await self.provider.models(principal, registration)
        except ProviderError as exc:
            if exc.code == "subscription_sharing_usage_limit_exceeded":
                session["usagePaused"] = True
                session["remainingRequests"] = 0
            raise
        require(
            any(m["slug"] == data.model for m in admitted),
            "Select an admitted model from this registration catalog",
        )
        require(
            session.get("registration") == registration
            and session["principal"] == principal,
            "Account changed while preparing job",
            409,
        )
        require(
            session.get("remainingRequests", 0) > 0,
            "Set an explicit session request budget first",
            409,
        )
        with s.database.connect() as db:
            state = s.owned(db, principal, project)
            s.sequence(state, data.expectedEventSequence)
            reg = db.execute(
                "SELECT * FROM registrations WHERE registration_id=? AND principal_id=?",
                (registration, principal),
            ).fetchone()
            require(
                reg and reg["grant_state"] == "plan_enabled",
                "Registration lacks plan permission",
                401,
            )
            require(
                not db.execute(
                    "SELECT 1 FROM jobs WHERE registration_id=? AND state IN ('queued','running')",
                    (registration,),
                ).fetchone(),
                "A request is already active for this account",
                409,
            )
            if data.depictionLinkIds:
                consent = db.execute(
                    "SELECT allow_image_analysis FROM project_settings WHERE project_id=?",
                    (project,),
                ).fetchone()
                require(
                    consent and consent[0] == 1,
                    "Project consent is required to send selected images",
                    403,
                )
            context = self.context(db, principal, project, data)
            job_id = uid()
            version = s.version(db, project, data.versionId)
            request = {
                "versionId": data.versionId,
                "canonicalHash": version["canonical_hash"],
                "constraintsVersion": state["constraints_version"],
                "model": data.model,
                "input": data.model_dump(),
                "context": context,
                "sessionIdHash": digest(session_id),
            }
            db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    project,
                    job_id,
                    principal,
                    registration,
                    data.task,
                    "prompt_only",
                    "queued",
                    state["event_sequence"],
                    canonical(request),
                    None,
                ),
            )
            db.execute(
                "INSERT INTO job_requests VALUES (?,?,?,?)",
                (project, data.requestId, digest(data.model_dump()), job_id),
            )
            session["remainingRequests"] -= 1
        self.tasks[job_id] = asyncio.create_task(
            self.execute(session_id, principal, registration, project, job_id)
        )
        self.tasks[job_id].add_done_callback(lambda _: self.tasks.pop(job_id, None))
        return self.read(principal, project, job_id)

    def set_state(self, project, job_id, state, result=None):
        with self.service.database.connect() as db:
            # Terminal states are never revived by a racing completion/cancellation.
            db.execute(
                "UPDATE jobs SET state=?,result_json=? WHERE project_id=? AND job_id=? AND state IN ('queued','running')",
                (
                    state,
                    canonical(result) if result is not None else None,
                    project,
                    job_id,
                ),
            )

    async def execute(self, session_id, principal, registration, project, job_id):
        try:
            session = self.sessions.get(session_id)
            require(
                session
                and session["principal"] == principal
                and session.get("registration") == registration
                and not session.get("usagePaused"),
                "Job account/session is no longer active",
                401,
            )
            with self.service.database.connect() as db:
                current = self.service.owned(db, principal, project)
                job = self.service.get(db, "jobs", project, "job_id", job_id)
                require(
                    job["principal_id"] == principal
                    and job["registration_id"] == registration
                    and job["task"] in TASKS,
                    "Job payer/task binding failed",
                    403,
                )
                require(job["state"] == "queued", "Job is no longer queued", 409)
                request = json.loads(job["request_json"])
                require(
                    current["event_sequence"] == job["input_sequence"]
                    and current["constraints_version"] == request["constraintsVersion"],
                    "Input changed before execution",
                    409,
                )
                reg = db.execute(
                    "SELECT * FROM registrations WHERE principal_id=? AND registration_id=?",
                    (principal, registration),
                ).fetchone()
                require(
                    reg and reg["grant_state"] == "plan_enabled",
                    "Registration requires reauthorization",
                    401,
                )
                if request["input"]["depictionLinkIds"]:
                    consent = db.execute(
                        "SELECT allow_image_analysis FROM project_settings WHERE project_id=?",
                        (project,),
                    ).fetchone()
                    require(
                        consent and consent[0],
                        "Image transmission consent was withdrawn",
                        403,
                    )
                db.execute(
                    "UPDATE jobs SET state='running' WHERE project_id=? AND job_id=?",
                    (project, job_id),
                )
            context = request["context"]
            images = []
            from pathlib import Path

            for evidence in context["selectedEvidence"]:
                images.append(
                    "data:image/png;base64,"
                    + base64.b64encode(
                        Path(evidence.pop("derivativePath")).read_bytes()
                    ).decode()
                )
            # Paths and internal session binding never enter model context.
            raw = await self.provider.reason(
                principal, registration, request["model"], job["task"], context, images
            )
            result = ReasoningOutput.model_validate(raw).model_dump()
            allowed_links = set(request["input"]["depictionLinkIds"])
            require(
                all(obs["linkId"] in allowed_links for obs in result["observations"]),
                "Provider invented an evidence reference",
                502,
            )
            require(
                all(
                    f["linkId"] is None or f["linkId"] in allowed_links
                    for f in result["findings"]
                ),
                "Provider invented a finding reference",
                502,
            )
            session = self.sessions.get(session_id)
            with self.service.database.connect() as db:
                state = self.service.owned(db, principal, project)
                stale = (
                    state["event_sequence"] != job["input_sequence"]
                    or state["constraints_version"] != request["constraintsVersion"]
                )
            stale = (
                stale
                or not session
                or session["principal"] != principal
                or session.get("registration") != registration
            )
            self.set_state(
                project,
                job_id,
                "stale" if stale else "succeeded",
                {
                    "suggestions": result,
                    "authority": "unconfirmed_model_suggestions",
                    "geometricVerification": "none",
                },
            )
        except asyncio.CancelledError:
            self.set_state(
                project,
                job_id,
                "cancelled",
                {
                    "message": "Local request stopped. Provider usage may already have occurred."
                },
            )
        except ProviderError as exc:
            if exc.code == "subscription_sharing_usage_limit_exceeded":
                session = self.sessions.get(session_id)
                if session:
                    session["usagePaused"] = True
                    session["remainingRequests"] = 0
            self.set_state(
                project,
                job_id,
                "failed",
                {
                    "error": exc.code,
                    "requestId": exc.request_id,
                    "message": exc.message,
                },
            )
        except DomainError as exc:
            self.set_state(
                project,
                job_id,
                "needs_reauth"
                if exc.status == 401
                else "stale"
                if exc.status == 409
                else "failed",
                {"error": exc.message},
            )
        except (ValidationError, ValueError, KeyError, TypeError, AttributeError):
            self.set_state(
                project,
                job_id,
                "failed",
                {"error": "Provider output failed strict application validation"},
            )
        except (httpx.HTTPError, OSError):
            self.set_state(
                project,
                job_id,
                "failed",
                {
                    "error": "Request interrupted; completion is unknown. No automatic retry."
                },
            )

    def cancel(self, principal, project, job_id):
        self.read(principal, project, job_id)
        if task := self.tasks.get(job_id):
            task.cancel()
        self.set_state(
            project,
            job_id,
            "cancelled",
            {"message": "Local cancellation does not guarantee zero provider usage."},
        )
        return self.read(principal, project, job_id)

    def pause_session(self, session_id):
        session = self.sessions.get(session_id)
        if session:
            session["remainingRequests"] = 0
        with self.service.database.connect() as db:
            matching = [
                (row["project_id"], row["job_id"])
                for row in db.execute(
                    "SELECT * FROM jobs WHERE state IN ('queued','running')"
                )
                if json.loads(row["request_json"]).get("sessionIdHash")
                == digest(session_id)
            ]
        for project, job in matching:
            if task := self.tasks.get(job):
                task.cancel()
            self.set_state(
                project,
                job,
                "cancelled",
                {
                    "message": "Session/account changed; request was not moved to another payer."
                },
            )

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
