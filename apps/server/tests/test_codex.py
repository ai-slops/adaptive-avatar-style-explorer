import asyncio
import base64
import json
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest
from app.codex_jobs import CodexJobs
from app.common import DomainError
from app.contracts import (
    CodexAnalysisInput,
    CodexGenerationInput,
    PlanInput,
    RecipeInput,
)
from app.jobs import Jobs
from app.main import create_app
from app.planning import Planning
from app.providers.codex import CodexRPC
from app.storage.assets import Assets
from fastapi.testclient import TestClient
from test_domain import design, image_bytes, sequence


class FakeCodex:
    calls = 0
    gate = None
    failure = None
    account_value: ClassVar[dict] = {
        "type": "chatgpt",
        "email": "owner@example.test",
        "planType": "plus",
    }

    def __init__(self, cwd, *, images=False):
        self.cwd, self.images = Path(cwd), images
        self.process = SimpleNamespace(returncode=None)

    async def start(self):
        self.cwd.mkdir(parents=True, exist_ok=True)
        return self

    async def account(self):
        return self.account_value

    async def models(self):
        return [{"slug": "test-model", "display_name": "Test model", "isDefault": True}]

    async def turn(self, model, text, images=(), schema=None, progress=None):
        type(self).calls += 1
        if progress:
            await progress(
                {
                    "phase": "generating_image",
                    "threadId": "thread-test",
                    "turnId": "turn-test",
                }
            )
        if self.gate:
            await self.gate.wait()
        if self.failure:
            raise DomainError(self.failure, 502)
        return {
            "threadId": "thread-test",
            "turnId": "turn-test",
            "images": [
                {
                    "id": "image-test",
                    "status": "completed",
                    "result": base64.b64encode(image_bytes()).decode(),
                }
            ]
            if self.images
            else [],
            "text": json.dumps(
                {
                    "summary": "Proposal only",
                    "observations": [],
                    "findings": [],
                    "nextActions": [],
                }
            ),
        }

    def image_bytes(self, item):
        return base64.b64decode(item["result"])

    async def close(self):
        pass

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, *exc):
        await self.close()


@pytest.fixture(autouse=True)
def reset_fake():
    FakeCodex.calls, FakeCodex.gate, FakeCodex.failure = 0, None, None


def setup(service, project, tmp_path):
    assets = Assets(service, tmp_path / "assets")
    native = CodexJobs(
        service, assets, Jobs(service, None, assets, {}), tmp_path / "runs", FakeCodex
    )
    version = design(service, project)
    plan = Planning(service).compile(
        "alice",
        project,
        PlanInput(
            targetVersionId=version["version_id"],
            purpose="additional_view",
            recipe=RecipeInput(view="front"),
            expectedEventSequence=sequence(service, project),
        ),
    )
    data = CodexGenerationInput(
        requestId="request-1",
        planId=plan["planId"],
        promptRevision=1,
        model="test-model",
        authorizeOneTurn=True,
        expectedEventSequence=sequence(service, project),
    )
    return native, version, data


def test_generation_terminal_artifact_is_exact_version_unreviewed_and_idempotent(
    service, project, tmp_path
):
    async def scenario():
        native, version, data = setup(service, project, tmp_path)
        first = await native.enqueue("alice", project, data)
        duplicate = await native.enqueue("alice", project, data)
        assert duplicate["jobId"] == first["jobId"]
        await asyncio.gather(*list(native.tasks.values()))
        result = native.read("alice", project, first["jobId"])
        assert result["state"] == "succeeded", result
        assert result["result"]["imageStatus"] == "generated_unreviewed"
        assert result["result"]["canonicalHash"] == version["canonical_hash"]
        evidence = service.evidence("alice", project, version["version_id"])
        assert len(evidence["links"]) == 1
        assert evidence["links"][0]["status"] == "unreviewed"
        assert evidence["links"][0]["observations"] == []
        assert not any(slot["status"] == "satisfied" for slot in evidence["slots"])
        again = await native.enqueue("alice", project, data)
        assert again["jobId"] == first["jobId"] and FakeCodex.calls == 1
        with pytest.raises(DomainError):
            native.read("bob", project, first["jobId"])
        with pytest.raises(DomainError, match="reused"):
            await native.enqueue(
                "alice", project, data.model_copy(update={"exportPermission": True})
            )
        await native.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("action", ["cancel", "stale", "failure"])
def test_cancel_stale_and_failure_never_retry_or_confirm(
    service, project, tmp_path, action
):
    async def scenario():
        native, version, data = setup(service, project, tmp_path)
        FakeCodex.gate = asyncio.Event()
        first = await native.enqueue("alice", project, data)
        for _ in range(30):
            await asyncio.sleep(0)
            if FakeCodex.calls:
                break
        assert FakeCodex.calls == 1
        if action == "cancel":
            native.cancel("alice", project, first["jobId"])
        elif action == "stale":
            design(service, project, "gold")
        else:
            FakeCodex.failure = "terminal image failure"
        FakeCodex.gate.set()
        await asyncio.gather(*list(native.tasks.values()))
        result = native.read("alice", project, first["jobId"])
        assert (
            result["state"]
            == {"cancel": "cancelled", "stale": "stale", "failure": "failed"}[action]
        )
        assert FakeCodex.calls == 1
        links = service.evidence("alice", project, version["version_id"])["links"]
        assert len(links) == (1 if action == "stale" else 0)
        assert all(link["status"] == "unreviewed" for link in links)
        await native.close()

    asyncio.run(scenario())


def test_analysis_suggestions_are_unconfirmed_and_mode_is_server_selected(
    service, project, tmp_path
):
    async def scenario():
        native, version, _ = setup(service, project, tmp_path)
        data = CodexAnalysisInput(
            requestId="analysis-1",
            task="propose_next_actions",
            versionId=version["version_id"],
            model="test-model",
            authorizeOneTurn=True,
            expectedEventSequence=sequence(service, project),
        )
        job = await native.enqueue("alice", project, data)
        await asyncio.gather(*list(native.tasks.values()))
        result = native.read("alice", project, job["jobId"])
        assert result["state"] == "succeeded", result
        assert result["result"]["authority"] == "unconfirmed_model_suggestions"
        await native.close()

    asyncio.run(scenario())
    for mode in ("community_prompt_only", "codex_local"):
        app = create_app(
            tmp_path / mode,
            origin="http://testserver",
            bootstrap_secret="launch",
            execution_mode=mode,
            codex_rpc_factory=FakeCodex,
        )
        with TestClient(app) as client:
            response = client.post(
                "/api/session/bootstrap",
                json={"secret": "launch"},
                headers={"origin": "http://testserver"},
            )
            assert response.json()["allowImageGeneration"] is (mode == "codex_local")
            status = client.get("/api/codex/status")
            assert status.status_code == (200 if mode == "codex_local" else 404)
            assert client.post("/api/codex/login", json={}).status_code == 403


def test_native_artifact_paths_and_key_fallback_are_rejected(tmp_path):
    rpc = CodexRPC(tmp_path / "worker")
    outside = tmp_path / "outside.png"
    outside.write_bytes(image_bytes())
    with pytest.raises(DomainError, match="outside"):
        rpc.image_bytes(
            {"status": "completed", "result": "", "savedPath": str(outside)}
        )
    rpc.cwd.mkdir()
    (rpc.cwd / "link.png").symlink_to(outside)
    with pytest.raises(DomainError, match="outside"):
        rpc.image_bytes(
            {
                "status": "completed",
                "result": "",
                "savedPath": str(rpc.cwd / "link.png"),
            }
        )
    with pytest.raises(DomainError, match="did not complete"):
        rpc.image_bytes(
            {"status": "failed", "result": base64.b64encode(image_bytes()).decode()}
        )

    async def request(*args, **kwargs):
        return {"account": {"type": "apiKey"}}

    rpc.request = request
    with pytest.raises(DomainError, match="API-key fallback"):
        asyncio.run(rpc.account())


def test_native_reasoning_schema_is_closed_and_sparse_attributes_round_trip():
    from app.providers.codex_output import reasoning_schema, validate_reasoning

    schema = reasoning_schema()

    def check(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert set(node["required"]) == set(node["properties"])
                assert node["additionalProperties"] is False
            for value in node.values():
                check(value)
        elif isinstance(node, list):
            for value in node:
                check(value)

    check(schema)
    payload = {
        "summary": "Only visible hair",
        "observations": [
            {
                "linkId": "link-1",
                "observation": {
                    "region": "hair",
                    "attributes": [
                        {
                            "key": "hair.volume",
                            "attribute": {
                                "value": 0.4,
                                "confidence": 0.8,
                                "visibility": "visible",
                            },
                        }
                    ],
                    "observedPresentation": {"view": "front"},
                },
            }
        ],
        "findings": [],
        "nextActions": [],
    }
    result = validate_reasoning(payload)
    assert (
        result["observations"][0]["observation"]["attributes"]["hair.volume"]["value"]
        == 0.4
    )
