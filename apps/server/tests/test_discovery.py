"""Discovery workflow invariants; fixture images do not establish visual quality."""

import asyncio
import io
import json
import zipfile

import pytest
from app.common import DomainError, uid
from app.discovery import Discovery
from app.discovery_contracts import (
    DiscoveryGenerationInput,
    DiscoveryImportInput,
    DiscoveryLibraryInput,
    DiscoveryReactionInput,
    DiscoveryRoundInput,
)
from app.discovery_planner import signature
from app.planning import Planning
from app.storage.assets import Assets
from test_domain import design, evidence, image_bytes


@pytest.fixture
def discovery(service, tmp_path):
    return Discovery(service, Assets(service, tmp_path / "images"), Planning(service))


def prepare(d, project, **kw):
    return d.prepare(
        "alice",
        project,
        DiscoveryRoundInput(
            requestId=uid(),
            expectedRevision=d.state("alice", project)["revision"],
            **kw,
        ),
    )


def board(d, project):
    state = d.state("alice", project)
    return next(r for r in state["rounds"] if r["roundId"] == state["activeRoundId"])[
        "candidates"
    ]


def reaction(d, project, action, candidates=(), **kw):
    data = DiscoveryReactionInput(
        requestId=uid(),
        expectedRevision=d.state("alice", project)["revision"],
        action=action,
        candidateIds=[c["candidateId"] for c in candidates],
        linkIds=[c["image"]["linkId"] for c in candidates],
        **kw,
    )
    return data, d.react("alice", project, data)


def returned(d, project, candidates):
    items = []
    for i, c in enumerate(candidates):
        asset = d.assets.import_image(
            "alice", project, image_bytes((20 + i * 20, 80, 90))
        )
        items.append({"assetId": asset["assetId"], "filename": c["returnName"]})
    data = DiscoveryImportInput(
        requestId=uid(), roundId=candidates[0]["roundId"], items=items
    )
    result = d.import_results("alice", project, data)
    assert d.import_results("alice", project, data) == result
    return board(d, project)


def specs(d, project, candidates):
    with d.service.database.connect() as db:
        return [
            d.service.version(db, project, c["versionId"])["spec"] for c in candidates
        ]


def test_blank_round_is_diverse_provisional_and_has_actionable_pack(discovery, project):
    d = discovery
    request = DiscoveryRoundInput(requestId=uid(), expectedRevision=0)
    rid = d.prepare("alice", project, request)
    assert d.prepare("alice", project, request) == rid
    options = board(d, project)
    assert len(options) == 4 and all(c["image"] is None for c in options)
    assert len({signature(s) for s in specs(d, project, options)}) == 4
    assert all(
        p["state"] == "proposed"
        for s in specs(d, project, options)
        for p in s["properties"].values()
    )
    with zipfile.ZipFile(io.BytesIO(d.round_pack("alice", project, rid))) as pack:
        manifest = json.loads(pack.read("return-manifest.json"))
        assert len(manifest) == 4
        assert (
            len([name for name in pack.namelist() if name.startswith("option-")]) == 4
        )
        assert "full_body" in options[0]["prompt"]["promptText"]
    with pytest.raises(DomainError):
        d.react(
            "alice",
            project,
            DiscoveryReactionInput(
                requestId=uid(),
                expectedRevision=1,
                action="interest",
                candidateIds=[options[0]["candidateId"]],
            ),
        )
    with pytest.raises(DomainError):
        d.state("bob", project)


def test_unreviewed_both_develops_independent_directions_and_not_losers(
    discovery, project
):
    d = discovery
    prepare(d, project)
    first = returned(d, project, board(d, project))
    _, saved = reaction(d, project, "both", first[:2])
    assert all(e["status"] == "unreviewed" for e in saved["frozenShownEvidence"])
    assert saved["classification"] == "exploratory_interest_not_qualified_training"
    prepare(d, project)
    second = board(d, project)
    assert {c["sourceCandidateId"] for c in second[:2]} == {
        c["candidateId"] for c in first[:2]
    }
    assert second[-1]["sourceCandidateId"] is None
    assert len(d.state("alice", project)["directions"]) == 2
    assert d.state("alice", project)["rejected"] == []
    assert {signature(s) for s in specs(d, project, first)}.isdisjoint(
        signature(s) for s in specs(d, project, second)
    )
    with d.service.database.connect() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM observations WHERE project_id=?", (project,)
            ).fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT count(*) FROM events WHERE project_id=? AND action IN ('choose_a','choose_b','tie','neither')",
                (project,),
            ).fetchone()[0]
            == 0
        )


def test_keep_face_change_hair_unlock_and_undo_affect_proposals(discovery, project):
    d = discovery
    prepare(d, project)
    first = returned(d, project, board(d, project))
    reaction(d, project, "interest", [first[0]])
    keep, _ = reaction(d, project, "keep_part", [first[0]], part="face")
    prepare(
        d,
        project,
        intent="focus",
        candidateId=first[0]["candidateId"],
        part="hair",
        count=1,
    )
    changed = board(d, project)[0]
    original_spec, changed_spec = specs(d, project, [first[0], changed])
    assert (
        original_spec["properties"]["face.design"]
        == changed_spec["properties"]["face.design"]
    )
    assert (
        original_spec["properties"]["hair.design"]
        != changed_spec["properties"]["hair.design"]
    )
    assert changed["preserveParts"] == ["face"]
    assert changed_spec["properties"]["discovery.anchor_face"]["state"] == "proposed"
    reaction(d, project, "undo", targetReactionId=keep.requestId)
    assert d.state("alice", project)["directions"][0]["preserved"] == {}
    prepare(
        d,
        project,
        intent="focus",
        candidateId=changed["candidateId"],
        part="face",
        count=1,
    )
    unlocked_spec = specs(d, project, board(d, project))[0]
    assert "discovery.anchor_face" not in unlocked_spec["properties"]
    assert (
        changed_spec["properties"]["face.design"]
        != unlocked_spec["properties"]["face.design"]
    )


def test_neither_and_undo_do_not_destroy_round(discovery, project):
    d = discovery
    prepare(d, project)
    initial = returned(d, project, board(d, project))
    reject, _ = reaction(d, project, "neither", initial)
    assert set(d.state("alice", project)["rejected"]) == {
        c["candidateId"] for c in initial
    }
    prepare(d, project, intent="different")
    assert all(c["sourceCandidateId"] is None for c in board(d, project))
    reaction(d, project, "undo", targetReactionId=reject.requestId)
    assert not d.state("alice", project)["rejected"]
    d.activate("alice", project, initial[0]["roundId"])
    assert board(d, project) == initial


def test_choice_is_frozen_with_gaps_and_explicit_replacement(discovery, project):
    d = discovery
    prepare(d, project)
    first = returned(d, project, board(d, project))
    chosen, payload = reaction(d, project, "use_design", [first[0]])
    snapshot = payload["selection"]
    assert snapshot["status"] == "design_chosen"
    assert snapshot["geometricVerification"] == "none"
    assert snapshot["uncheckedViews"]
    assert d.react("alice", project, chosen) == payload
    prepare(d, project, intent="different", count=1)
    assert d.state("alice", project)["selection"] == snapshot
    with pytest.raises(DomainError, match="교체"):
        reaction(d, project, "use_design", [first[1]])
    reaction(d, project, "use_design", [first[1]], replaceSelection=True)
    assert (
        d.state("alice", project)["selection"]["candidateId"] == first[1]["candidateId"]
    )


def test_delayed_partial_ambiguous_imports_and_existing_library(
    discovery, project, tmp_path
):
    d = discovery
    old = design(d.service, project)
    old_link = evidence(d.service, project, old["version_id"], tmp_path / "images")
    assert not d.state("alice", project)["rounds"]
    d.use_library(
        "alice",
        project,
        DiscoveryLibraryInput(
            requestId=uid(), expectedRevision=0, versionId=old["version_id"]
        ),
    )
    assert board(d, project)[0]["image"]["linkId"] == old_link
    assert not d.state("alice", project)["directions"]
    prepare(d, project)
    first = board(d, project)
    returned(d, project, first[:1])
    asset = d.assets.import_image("alice", project, image_bytes("purple"))["assetId"]
    with pytest.raises(DomainError, match="모호"):
        d.import_results(
            "alice",
            project,
            DiscoveryImportInput(
                requestId=uid(),
                roundId=first[0]["roundId"],
                items=[{"assetId": asset, "filename": "unknown.png"}],
            ),
        )
    d.import_results(
        "alice",
        project,
        DiscoveryImportInput(
            requestId=uid(), items=[{"assetId": asset, "independentReference": True}]
        ),
    )
    assert len(d.state("alice", project)["inspirations"]) == 1
    returned(d, project, first[1:2])
    assert all(c["image"] for c in board(d, project)[:2])
    assert all(c["image"] is None for c in board(d, project)[2:])


def test_feedback_evidence_cannot_cross_candidate_or_owner(discovery, project):
    d = discovery
    prepare(d, project)
    first = returned(d, project, board(d, project))
    data = DiscoveryReactionInput(
        requestId=uid(),
        expectedRevision=1,
        action="interest",
        candidateIds=[first[0]["candidateId"]],
        linkIds=[first[1]["image"]["linkId"]],
    )
    with pytest.raises(DomainError, match="다른 후보"):
        d.react("alice", project, data)
    with pytest.raises(DomainError):
        d.react("bob", project, data)


def test_community_has_no_generation_and_reload_does_not_submit(discovery, project):
    async def scenario():
        prepare(discovery, project, count=1)
        c = board(discovery, project)[0]
        request = DiscoveryGenerationInput(
            requestId=uid(), candidateIds=[c["candidateId"]], authorizeTurns=1
        )
        with pytest.raises(DomainError, match="생성하지"):
            await discovery.generate("alice", project, c["roundId"], request)
        restored = Discovery(discovery.service, discovery.assets, discovery.planning)
        assert restored.state("alice", project)["activeRoundId"] == c["roundId"]
        assert not restored.tasks

    asyncio.run(scenario())


def test_native_finite_batch_partial_failure_and_explicit_missing_retry(
    service, project, tmp_path
):
    from app.codex_jobs import CodexJobs
    from app.jobs import Jobs
    from test_codex import FakeCodex

    class PartialCodex(FakeCodex):
        calls = 0
        gate = None
        failure = None

        async def turn(self, *args, **kw):
            if type(self).calls == 1:
                type(self).calls += 1
                raise DomainError("one fixture failure", 502)
            return await super().turn(*args, **kw)

    async def scenario():
        assets = Assets(service, tmp_path / "assets")
        native = CodexJobs(
            service,
            assets,
            Jobs(service, None, assets, {}),
            tmp_path / "runs",
            PartialCodex,
        )
        d = Discovery(service, assets, Planning(service), native)
        prepare(d, project, count=3)
        first = board(d, project)
        data = DiscoveryGenerationInput(
            requestId=uid(),
            candidateIds=[c["candidateId"] for c in first],
            authorizeTurns=3,
        )
        batch = await d.generate("alice", project, first[0]["roundId"], data)
        assert await d.generate("alice", project, first[0]["roundId"], data) == batch
        await asyncio.wait_for(d.tasks[batch], 5)
        results = board(d, project)
        assert [bool(c["image"]) for c in results] == [True, False, True], d.state(
            "alice", project
        )["batches"]
        assert [c["candidateId"] for c in results] == [c["candidateId"] for c in first]
        assert PartialCodex.calls == 3
        retry = DiscoveryGenerationInput(
            requestId=uid(), candidateIds=[results[1]["candidateId"]], authorizeTurns=1
        )
        retry_batch = await d.generate("alice", project, first[0]["roundId"], retry)
        await asyncio.wait_for(d.tasks[retry_batch], 5)
        assert all(c["image"] for c in board(d, project))
        assert PartialCodex.calls == 4
        with pytest.raises(DomainError, match="이미 결과"):
            await d.generate(
                "alice",
                project,
                first[0]["roundId"],
                data.model_copy(update={"requestId": uid()}),
            )
        await d.close()
        await native.close()

    asyncio.run(scenario())


def test_cancel_before_batch_starts_prevents_every_turn(service, project, tmp_path):
    from app.codex_jobs import CodexJobs
    from app.jobs import Jobs
    from test_codex import FakeCodex

    class CountCodex(FakeCodex):
        calls = 0
        gate = None
        failure = None

    async def scenario():
        assets = Assets(service, tmp_path / "assets")
        native = CodexJobs(
            service,
            assets,
            Jobs(service, None, assets, {}),
            tmp_path / "runs",
            CountCodex,
        )
        d = Discovery(service, assets, Planning(service), native)
        prepare(d, project, count=2)
        first = board(d, project)
        batch = await d.generate(
            "alice",
            project,
            first[0]["roundId"],
            DiscoveryGenerationInput(
                requestId=uid(),
                candidateIds=[c["candidateId"] for c in first],
                authorizeTurns=2,
            ),
        )
        task = d.tasks[batch]
        d.cancel("alice", project, batch)
        await asyncio.gather(task, return_exceptions=True)
        assert CountCodex.calls == 0
        assert d.state("alice", project)["batches"][0]["state"] == "cancelled"
        assert not d.state("alice", project)["batches"][0]["currentJobId"]
        await d.close()
        await native.close()

    asyncio.run(scenario())


def test_changed_favorite_changes_intended_design_and_reference(discovery, project):
    d = discovery
    prepare(d, project)
    first = returned(d, project, board(d, project))
    liked_a, _ = reaction(d, project, "interest", [first[0]])
    prepare(d, project, count=1)
    result_a = board(d, project)[0]
    reaction(d, project, "undo", targetReactionId=liked_a.requestId)
    reaction(d, project, "interest", [first[1]])
    prepare(d, project, count=1)
    result_b = board(d, project)[0]
    a, b = specs(d, project, [result_a, result_b])
    assert a["properties"]["face.design"] != b["properties"]["face.design"]
    assert result_a["sourceLinkIds"] == [first[0]["image"]["linkId"]]
    assert result_b["sourceLinkIds"] == [first[1]["image"]["linkId"]]


def test_reference_export_uses_selected_source_permission_and_no_duplicate_paths(
    discovery, project
):
    d = discovery
    prepare(d, project, count=1)
    first = returned(d, project, board(d, project))[0]
    reaction(d, project, "interest", [first])
    rid = prepare(d, project, count=3)
    with zipfile.ZipFile(io.BytesIO(d.round_pack("alice", project, rid))) as pack:
        manifest = json.loads(pack.read("return-manifest.json"))
        assert any(c["references"] for c in manifest)
        assert not any(ref["included"] for c in manifest for ref in c["references"])
        assert not any(n.startswith("references/") for n in pack.namelist())
    # Explicitly permitted new source; several variants can reference its one file.
    asset = first["image"]["assetId"]
    d.import_results(
        "alice",
        project,
        DiscoveryImportInput(
            requestId=uid(),
            roundId=first["roundId"],
            items=[
                {
                    "assetId": asset,
                    "candidateId": first["candidateId"],
                    "exportPermission": True,
                }
            ],
        ),
    )
    d.activate("alice", project, first["roundId"])
    permitted = board(d, project)[0]
    reaction(d, project, "interest", [permitted])
    rid = prepare(d, project, count=3)
    with zipfile.ZipFile(io.BytesIO(d.round_pack("alice", project, rid))) as pack:
        files = [n for n in pack.namelist() if n.startswith("references/")]
        assert files == [f"references/{asset}.png"]


def test_native_reference_consent_is_required_before_scheduling(discovery, project):
    async def scenario():
        d = discovery
        prepare(d, project, count=1)
        first = returned(d, project, board(d, project))[0]
        reaction(d, project, "interest", [first])
        prepare(d, project, count=1)
        second = board(d, project)[0]
        d.native = object()  # No operation may reach a provider without consent.
        with pytest.raises(DomainError, match="전송"):
            await d.generate(
                "alice",
                project,
                second["roundId"],
                DiscoveryGenerationInput(
                    requestId=uid(),
                    candidateIds=[second["candidateId"]],
                    authorizeTurns=1,
                ),
            )
        assert not d.tasks
        assert not d.state("alice", project)["batches"]

    asyncio.run(scenario())


def test_inflight_cancel_stops_remaining_and_restart_never_resubmits(
    service, project, tmp_path
):
    from app.codex_jobs import CodexJobs
    from app.jobs import Jobs
    from test_codex import FakeCodex

    class WaitingCodex(FakeCodex):
        calls = 0
        gate = None
        failure = None

    async def scenario():
        WaitingCodex.gate = asyncio.Event()
        assets = Assets(service, tmp_path / "assets")
        native = CodexJobs(
            service,
            assets,
            Jobs(service, None, assets, {}),
            tmp_path / "runs",
            WaitingCodex,
        )
        d = Discovery(service, assets, Planning(service), native)
        prepare(d, project, count=3)
        candidates = board(d, project)
        batch = await d.generate(
            "alice",
            project,
            candidates[0]["roundId"],
            DiscoveryGenerationInput(
                requestId=uid(),
                candidateIds=[c["candidateId"] for c in candidates],
                authorizeTurns=3,
            ),
        )
        task = d.tasks[batch]

        async def started():
            while WaitingCodex.calls == 0:
                await asyncio.sleep(0.001)

        await asyncio.wait_for(started(), 2)
        d.cancel("alice", project, batch)
        await asyncio.gather(task, return_exceptions=True)
        WaitingCodex.gate.set()
        await asyncio.gather(*list(native.tasks.values()), return_exceptions=True)
        assert WaitingCodex.calls == 1
        assert d.state("alice", project)["batches"][0]["state"] == "cancelled"
        restored = Discovery(service, assets, Planning(service), native)
        assert (
            restored.state("alice", project)["activeRoundId"]
            == candidates[0]["roundId"]
        )
        assert not restored.tasks
        assert WaitingCodex.calls == 1
        # Simulate a process that died with a durable queued batch.
        with service.database.connect() as db:
            db.execute(
                "UPDATE discovery_batches SET state='queued' WHERE batch_id=?", (batch,)
            )
        after_crash = Discovery(service, assets, Planning(service), native)
        assert (
            after_crash.state("alice", project)["batches"][0]["state"] == "interrupted"
        )
        assert not after_crash.tasks
        assert WaitingCodex.calls == 1
        await d.close()
        await native.close()

    asyncio.run(scenario())


def test_community_api_cannot_reach_native_generation(tmp_path):
    from app.main import create_app
    from fastapi.testclient import TestClient

    app = create_app(tmp_path / "app", bootstrap_secret="discovery-test")
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        headers = {"origin": "http://127.0.0.1:8765"}
        signed = client.post(
            "/api/session/bootstrap", json={"secret": "discovery-test"}, headers=headers
        )
        headers["x-csrf-token"] = signed.json()["csrfToken"]
        project = client.post(
            "/api/projects", json={"title": "새 탐색"}, headers=headers
        ).json()["project_id"]
        base = f"/api/projects/{project}/discovery"
        rid = client.post(
            base + "/rounds",
            json={"requestId": "start", "expectedRevision": 0},
            headers=headers,
        ).json()["roundId"]
        state = client.get(base).json()
        assert state["mode"] == "community_prompt_only"
        candidate = state["rounds"][0]["candidates"][0]
        assert (
            client.post(
                base + f"/rounds/{rid}/generate",
                json={
                    "requestId": "no",
                    "candidateIds": [candidate["candidateId"]],
                    "authorizeTurns": 1,
                },
                headers=headers,
            ).status_code
            in (404, 405)  # The SPA GET fallback may report method-not-allowed.
        )
        assert (
            client.post(base + f"/rounds/{rid}/export", headers=headers).status_code
            == 200
        )
