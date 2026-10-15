"""Single-owner native Codex jobs. Generated images are unreviewed evidence."""

import asyncio
import json
import shutil
from pathlib import Path

from pydantic import ValidationError

from .common import DomainError, canonical, digest, require, uid
from .contracts import (
    CodexGenerationInput,
    LinkInput,
)
from .providers.codex import CodexRPC
from .providers.codex_output import reasoning_schema, validate_reasoning


class CodexJobs:
    def __init__(self, service, assets, context_builder, root, rpc_factory=CodexRPC):
        self.service, self.assets, self.context_builder = (
            service,
            assets,
            context_builder,
        )
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.rpc_factory = rpc_factory
        self.tasks = {}
        self.control = None
        self.control_lock = asyncio.Lock()
        with service.database.connect() as db:
            db.execute(
                "UPDATE codex_jobs SET state='failed',result_json=? WHERE state IN ('queued','running')",
                (
                    canonical(
                        {
                            "error": "process_interrupted_completion_unknown",
                            "message": "No automatic retry. Codex may already have consumed usage.",
                        }
                    ),
                ),
            )

    async def control_client(self):
        async with self.control_lock:
            if self.control is None or (
                self.control.process and self.control.process.returncode is not None
            ):
                if self.control:
                    await self.control.close()
                control = self.rpc_factory(self.root / "control", images=False)
                await control.start()
                self.control = control
            return self.control

    async def status(self):
        client = await self.control_client()
        account = await client.account()
        return {
            "installed": True,
            "connected": account is not None,
            "account": account,
            "mode": "codex_local",
            "imageGeneration": "native_tool_available_subject_to_completed_turn",
            "credentials": "managed_by_local_codex",
            "usageMeaning": "Each individual job authorizes one Codex turn; a discovery batch explicitly authorizes its finite displayed candidate count. No automatic retry or passive generation.",
        }

    async def models(self):
        client = await self.control_client()
        require(await client.account(), "Sign in to local Codex first", 401)
        return await client.models()

    async def login(self):
        client = await self.control_client()
        result = await client.request("account/login/start", {"type": "chatgpt"})
        return {
            "authorizationUrl": result.get("authUrl"),
            "loginId": result.get("loginId"),
        }

    def read(self, principal, project, job_id):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            row = self.service.get(db, "codex_jobs", project, "job_id", job_id)
            require(row["principal_id"] == principal, "Job not found", 404)
            return {
                "jobId": job_id,
                "task": row["task"],
                "state": row["state"],
                "versionId": row["version_id"],
                "model": row["model"],
                "threadId": row["thread_id"],
                "turnId": row["turn_id"],
                "planId": json.loads(row["request_json"])["input"].get("planId"),
                "promptRevision": json.loads(row["request_json"])["input"].get(
                    "promptRevision"
                ),
                "result": json.loads(row["result_json"])
                if row["result_json"]
                else None,
            }

    def list(self, principal, project):
        with self.service.database.connect() as db:
            self.service.owned(db, principal, project)
            ids = [
                r[0]
                for r in db.execute(
                    "SELECT job_id FROM codex_jobs WHERE project_id=? AND principal_id=? ORDER BY rowid DESC LIMIT 50",
                    (project, principal),
                )
            ]
        return [self.read(principal, project, job) for job in ids]

    async def enqueue(self, principal, project, data):
        s = self.service
        request_hash = digest(data.model_dump())
        with s.database.connect() as db:
            s.owned(db, principal, project)
            previous = db.execute(
                "SELECT * FROM codex_jobs WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if previous:
                require(
                    previous["request_hash"] == request_hash,
                    "Request ID reused with different payload",
                    409,
                )
                existing = previous["job_id"]
            else:
                existing = None
        if existing:
            return self.read(principal, project, existing)
        client = await self.control_client()
        account = await client.account()
        require(account, "Sign in to local Codex first", 401)
        models = await client.models()
        require(
            any(model["slug"] == data.model for model in models),
            "Select a model from the local Codex catalog",
        )
        with s.database.connect() as db:
            state = s.owned(db, principal, project)
            previous = db.execute(
                "SELECT * FROM codex_jobs WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()
            if previous:
                require(
                    previous["request_hash"] == request_hash,
                    "Request ID reused with different payload",
                    409,
                )
                existing = previous["job_id"]
            else:
                existing = None
            if not existing:
                self._insert(db, state, principal, project, data, request_hash, account)
        if existing:
            return self.read(principal, project, existing)
        with s.database.connect() as db:
            job = db.execute(
                "SELECT job_id FROM codex_jobs WHERE project_id=? AND request_id=?",
                (project, data.requestId),
            ).fetchone()[0]
        self.tasks[job] = asyncio.create_task(self.execute(principal, project, job))
        self.tasks[job].add_done_callback(lambda _: self.tasks.pop(job, None))
        return self.read(principal, project, job)

    def _insert(self, db, state, principal, project, data, request_hash, account):
        s = self.service
        s.sequence(state, data.expectedEventSequence)
        require(
            not db.execute(
                "SELECT 1 FROM codex_jobs WHERE principal_id=? AND state IN ('queued','running')",
                (principal,),
            ).fetchone(),
            "A local Codex job is already active",
            409,
        )
        if isinstance(data, CodexGenerationInput):
            plan = db.execute(
                "SELECT * FROM prompt_plans WHERE project_id=? AND plan_id=? AND revision=?",
                (project, data.planId, data.promptRevision),
            ).fetchone()
            require(plan, "Unknown prompt revision", 404)
            require(
                plan["input_sequence"] == state["event_sequence"]
                and plan["constraints_version"] == state["constraints_version"],
                "Prompt is historical. Prepare a current prompt before generating.",
                409,
            )
            version = s.version(db, project, plan["target_version_id"])
            payload = json.loads(plan["payload_json"])
            references = payload["references"]
            require(
                not references or data.approveReferenceTransmission,
                "Approve sending the listed reference images through Codex",
                403,
            )
            refs = []
            for reference in references:
                asset = s.get(db, "assets", project, "asset_id", reference["assetId"])
                refs.append(
                    {
                        "assetId": asset["asset_id"],
                        "path": str(self.assets.root / f"{asset['storage_key']}.png"),
                    }
                )
            request = {
                "input": data.model_dump(),
                "prompt": payload["promptText"],
                "references": refs,
                "purpose": payload["purpose"],
            }
            task = "generate_image"
        else:
            version = s.version(db, project, data.versionId)
            require(
                not data.depictionLinkIds or data.approveReferenceTransmission,
                "Approve sending selected images through Codex",
                403,
            )
            context = self.context_builder.context(db, principal, project, data)
            refs = [
                {"assetId": e["assetId"], "path": e.pop("derivativePath")}
                for e in context["selectedEvidence"]
            ]
            request = {
                "input": data.model_dump(),
                "context": context,
                "references": refs,
            }
            task = data.task
        job = uid()
        db.execute(
            "INSERT INTO codex_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                project,
                job,
                principal,
                data.requestId,
                request_hash,
                task,
                "queued",
                version["version_id"],
                version["canonical_hash"],
                state["event_sequence"],
                state["constraints_version"],
                data.model,
                digest(account),
                None,
                None,
                canonical(request),
                None,
            ),
        )

    def update(self, project, job, state=None, result=None, thread=None, turn=None):
        with self.service.database.connect() as db:
            row = db.execute(
                "SELECT state FROM codex_jobs WHERE project_id=? AND job_id=?",
                (project, job),
            ).fetchone()
            if row and row[0] in ("queued", "running"):
                db.execute(
                    "UPDATE codex_jobs SET state=COALESCE(?,state),result_json=?,thread_id=COALESCE(?,thread_id),turn_id=COALESCE(?,turn_id) WHERE project_id=? AND job_id=?",
                    (
                        state,
                        canonical(result) if result is not None else None,
                        thread,
                        turn,
                        project,
                        job,
                    ),
                )

    async def execute(self, principal, project, job_id):
        s = self.service
        directory = self.root / project / job_id
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            with s.database.connect() as db:
                state = s.owned(db, principal, project)
                job = s.get(db, "codex_jobs", project, "job_id", job_id)
                require(
                    job["principal_id"] == principal and job["state"] == "queued",
                    "Codex job binding is no longer active",
                    409,
                )
                require(
                    state["event_sequence"] == job["input_sequence"]
                    and state["constraints_version"] == job["constraints_version"],
                    "Design/evidence changed before execution",
                    409,
                )
            request = json.loads(job["request_json"])
            paths = []
            for i, reference in enumerate(request["references"], 1):
                path = directory / f"reference-{i}.png"
                shutil.copyfile(reference["path"], path)
                path.chmod(0o600)
                paths.append(path)
            async with self.rpc_factory(
                directory, images=job["task"] == "generate_image"
            ) as rpc:
                require(
                    digest(await rpc.account()) == job["account_fingerprint"],
                    "Codex account changed before execution",
                    401,
                )
                self.update(project, job_id, "running", {"phase": "starting_turn"})

                async def progress(value):
                    self.update(
                        project,
                        job_id,
                        "running",
                        {"phase": value["phase"]},
                        value.get("threadId"),
                        value.get("turnId"),
                    )

                if job["task"] == "generate_image":
                    text = (
                        "Generate exactly one image using the native image-generation tool for the following self-contained prompt. Use the attached reference images in the stated order. Do not use shell, code drawings, SVG, external apps, browser, or delegated agents.\n\n"
                        + request["prompt"]
                    )
                    completed = await rpc.turn(
                        job["model"], text, paths, progress=progress
                    )
                    require(
                        len(completed["images"]) == 1,
                        "Codex did not return exactly one completed native image artifact",
                        502,
                    )
                    item = completed["images"][0]
                    content = rpc.image_bytes(item)
                    # Capture staleness before appending this job's own import events.
                    with s.database.connect() as db:
                        state = s.owned(db, principal, project)
                        stale = (
                            state["event_sequence"] != job["input_sequence"]
                            or state["constraints_version"]
                            != job["constraints_version"]
                        )
                    asset = self.assets.import_image(principal, project, content)
                    depiction = uid()
                    with s.database.connect() as db:
                        s.owned(db, principal, project)
                        current = s.get(db, "codex_jobs", project, "job_id", job_id)
                        require(
                            current["state"] == "running",
                            "Job was cancelled before artifact import",
                            409,
                        )
                        metadata = {
                            "provider": "codex_native",
                            "jobId": job_id,
                            "threadId": completed["threadId"],
                            "turnId": completed["turnId"],
                            "toolCallId": item["id"],
                            "revisedPrompt": item.get("revisedPrompt"),
                            "exportPermission": request["input"]["exportPermission"],
                            "caption": "Codex-generated concept; unreviewed adherence",
                            "geometricVerification": "none",
                            "staleAtCompletion": stale,
                        }
                        db.execute(
                            "INSERT INTO depictions VALUES (?,?,?,?,?,?,?,?)",
                            (
                                project,
                                depiction,
                                asset["assetId"],
                                "private_owner_result",
                                request["input"]["planId"],
                                request["input"]["promptRevision"],
                                None,
                                canonical(metadata),
                            ),
                        )
                    link = s.create_link(
                        principal,
                        project,
                        LinkInput(depictionId=depiction, versionId=job["version_id"]),
                    )
                    result = {
                        "assetId": asset["assetId"],
                        "depictionId": depiction,
                        "linkId": link["linkId"],
                        "versionId": job["version_id"],
                        "canonicalHash": job["canonical_hash"],
                        "imageStatus": "generated_unreviewed",
                        "geometricVerification": "none",
                    }
                else:
                    schema = reasoning_schema()
                    context = {**request["context"], "outputSchema": schema}
                    text = (
                        "Perform only this reasoning task: "
                        + job["task"]
                        + ". Return JSON matching outputSchema. Do not generate images, use tools, infer hidden geometry or confirm user intent.\n"
                        + canonical(context)
                    )
                    completed = await rpc.turn(
                        job["model"],
                        text,
                        paths,
                        schema=schema,
                        progress=progress,
                    )
                    require(
                        not completed["images"],
                        "Analysis returned unexpected image output",
                        502,
                    )
                    output = validate_reasoning(json.loads(completed["text"]))
                    allowed = set(request["input"]["depictionLinkIds"])
                    require(
                        all(o["linkId"] in allowed for o in output["observations"]),
                        "Codex invented evidence IDs",
                        502,
                    )
                    require(
                        all(
                            f["linkId"] is None or f["linkId"] in allowed
                            for f in output["findings"]
                        ),
                        "Codex invented finding IDs",
                        502,
                    )
                    with s.database.connect() as db:
                        state = s.owned(db, principal, project)
                        stale = (
                            state["event_sequence"] != job["input_sequence"]
                            or state["constraints_version"]
                            != job["constraints_version"]
                        )
                    result = {
                        "suggestions": output,
                        "authority": "unconfirmed_model_suggestions",
                        "geometricVerification": "none",
                    }
                self.update(
                    project,
                    job_id,
                    "stale" if stale else "succeeded",
                    result,
                    completed["threadId"],
                    completed["turnId"],
                )
        except asyncio.CancelledError:
            self.update(
                project,
                job_id,
                "cancelled",
                {
                    "message": "Local Codex turn cancelled; usage may already have occurred."
                },
            )
        except DomainError as exc:
            self.update(
                project,
                job_id,
                "needs_reauth"
                if exc.status == 401
                else "stale"
                if exc.status == 409
                else "failed",
                {"error": exc.message},
            )
        except ValidationError as exc:
            self.update(
                project,
                job_id,
                "failed",
                {
                    "error": "Codex output failed application validation",
                    "validationIssues": [
                        {"location": list(error["loc"]), "type": error["type"]}
                        for error in exc.errors(include_input=False, include_url=False)
                    ][:12],
                },
            )
        except (ValueError, KeyError, TypeError):
            self.update(
                project,
                job_id,
                "failed",
                {"error": "Codex output failed application validation"},
            )
        except (OSError, TimeoutError):
            self.update(
                project,
                job_id,
                "failed",
                {
                    "error": "Codex process interrupted or timed out. No automatic retry."
                },
            )
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def cancel(self, principal, project, job_id):
        self.read(principal, project, job_id)
        if task := self.tasks.get(job_id):
            task.cancel()
        self.update(
            project,
            job_id,
            "cancelled",
            {"message": "Local cancellation does not guarantee zero Codex usage."},
        )
        return self.read(principal, project, job_id)

    async def close(self):
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if self.control:
            await self.control.close()
