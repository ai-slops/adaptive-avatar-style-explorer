import io
import json
import zipfile

import pytest
from app.common import DomainError
from app.contracts import CheckpointInput, ModelBuildInput, PlanInput, RecipeInput
from app.exports import Exports
from app.main import create_app
from app.planning import Planning
from app.storage.assets import Assets
from fastapi.testclient import TestClient
from pydantic import ValidationError
from test_domain import design, evidence, sequence


def test_observation_prompts_preserve_spec_and_export_honestly(
    service, project, tmp_path
):
    version = design(service, project)
    link = evidence(service, project, version["version_id"], tmp_path / "images")
    planning = Planning(service)
    data = PlanInput(
        targetVersionId=version["version_id"],
        purpose="additional_view",
        recipe=RecipeInput(view="character_left_profile"),
        expectedEventSequence=sequence(service, project),
    )
    plan = planning.compile("alice", project, data)
    assert plan["canonicalSpecHash"] == version["canonical_hash"]
    assert plan["changeDesignProperties"] == []
    assert plan["imageStatus"] == "not_generated"
    assert "NO REDESIGN" in plan["promptText"] and "silver" in plan["promptText"]
    assert len(service.designs("alice", project)[0]["versions"]) == 1
    with pytest.raises(ValidationError):
        PlanInput(**{**data.model_dump(), "changeDesignProperties": ["hair.color"]})
    export = Exports(service, Assets(service, tmp_path / "images"), planning).build(
        "alice", project, version["version_id"]
    )
    with zipfile.ZipFile(io.BytesIO(export)) as archive:
        names = archive.namelist()
        assert "avatar-design-handoff/character-spec.json" in names
        assert not any(
            "/references/" in name for name in names
        )  # no redistribution consent
        assert (
            "Technical checks"
            in archive.read(
                "avatar-design-handoff/modeling-acceptance-checklist.md"
            ).decode()
        )
        manifest = json.loads(
            archive.read("avatar-design-handoff/reference-manifest.json")
        )
        assert manifest[0]["linkId"] == link and not manifest[0]["exportPermission"]
    with pytest.raises(DomainError):
        planning.compile("bob", project, data)


def test_checkpoint_requires_user_acceptance_and_build_evidence(service, project):
    version = design(service, project)
    planning = Planning(service)
    data = {
        "versionId": version["version_id"],
        "stage": "reference_handoff_ready",
        "acceptanceChecks": ["Inspect silhouette"],
        "expectedEventSequence": sequence(service, project),
    }
    with pytest.raises(DomainError, match="accept missing"):
        planning.checkpoint("alice", project, CheckpointInput(**data))
    result = planning.checkpoint(
        "alice",
        project,
        CheckpointInput(
            **data,
            acceptedGaps=["Front/profile/back still missing; concept brief only"],
        ),
    )
    assert result["stage"] == "reference_handoff_ready"
    with pytest.raises(ValidationError):
        CheckpointInput(**{**data, "stage": "production_ready"})
    build = planning.model_build(
        "alice",
        project,
        ModelBuildInput(
            targetVersionId=version["version_id"],
            label="v1",
            testScope="Neutral screenshots only",
        ),
    )
    assert build["artifactInspected"] is False
    with pytest.raises(DomainError, match="Import and review captures"):
        planning.checkpoint(
            "alice",
            project,
            CheckpointInput(
                **{
                    **data,
                    "stage": "prototype_reviewed_external",
                    "expectedEventSequence": sequence(service, project),
                },
                sourceBuildId=build["buildId"],
            ),
        )


def test_api_bootstrap_csrf_origin_and_deletion(tmp_path):
    app = create_app(
        tmp_path / "data",
        origin="http://127.0.0.1:8765",
        bootstrap_secret="test-secret",
    )
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/projects").status_code == 401
        assert (
            client.get("/api/projects", headers={"host": "attacker.test"}).status_code
            == 403
        )
        assert (
            client.post(
                "/api/session/bootstrap", json={"secret": "test-secret"}
            ).status_code
            == 403
        )
        headers = {"origin": "http://127.0.0.1:8765"}
        assert (
            client.post(
                "/api/session/bootstrap", json={"secret": "wrong"}, headers=headers
            ).status_code
            == 401
        )
        signed = client.post(
            "/api/session/bootstrap", json={"secret": "test-secret"}, headers=headers
        )
        assert "HttpOnly" in signed.headers["set-cookie"]
        headers["x-csrf-token"] = signed.json()["csrfToken"]
        assert (
            client.post(
                "/api/projects",
                json={"title": "Avatar"},
                headers={"origin": headers["origin"]},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/projects",
                json={"title": "Avatar"},
                headers={**headers, "origin": "https://attacker.test"},
            ).status_code
            == 403
        )
        project = client.post(
            "/api/projects", json={"title": "Avatar"}, headers=headers
        ).json()["project_id"]
        api = f"/api/projects/{project}"
        created = client.post(
            api + "/designs",
            json={"title": "Silver", "spec": {"morphology": "humanoid"}},
            headers=headers,
        )
        assert created.status_code == 200
        asset = client.post(
            api + "/assets",
            content=__import__("test_domain").image_bytes(),
            headers=headers,
        ).json()["assetId"]
        assert client.get(api + "/assets/" + asset).status_code == 200
        for route in ("generate", "render", "proxy", "shell"):
            assert (
                client.post(api + "/" + route, json={}, headers=headers).status_code
                == 405
            )  # only GET catch-all exists
        assert client.delete(api, headers=headers).status_code == 200
        assert client.get(api + "/designs").status_code == 404
        assert not (tmp_path / "data" / "assets" / project).exists()
        assert client.post("/api/auth/sign-out", headers=headers).status_code == 200
        assert client.get("/api/projects").status_code == 401


def test_canonical_adoption_preserves_typed_sources_and_handoff_relations(
    service, project, tmp_path
):
    from copy import deepcopy

    from app.contracts import CanonicalInput, Property, VersionInput
    from test_domain import image_bytes

    original = design(service, project)
    assets = Assets(service, tmp_path / "adoption-images")
    asset = assets.import_image("alice", project, image_bytes())["assetId"]
    from app.contracts import DepictionInput, LinkInput

    depiction = service.create_depiction(
        "alice", project, DepictionInput(assetId=asset, exportPermission=True)
    )["depictionId"]
    link = service.create_link(
        "alice",
        project,
        LinkInput(depictionId=depiction, versionId=original["version_id"]),
    )["linkId"]
    with service.database.connect() as db:
        event = db.execute(
            "SELECT event_id FROM events WHERE project_id=? AND sequence=?",
            (project, original["created_sequence"]),
        ).fetchone()[0]
    spec = deepcopy(original["spec"])
    spec["properties"].update(
        {
            "body.head_ratio": Property(value=0.18, state="proposed").model_dump(),
            "face.blink_capability": Property(
                value=True, state="user_confirmed"
            ).model_dump(),
            "outfit.layers": Property(
                value=["tunic", "cape"],
                state="user_confirmed",
                notes="Separate construction; rear clasp is a deliberate adoption",
                sourceEventIds=[event],
                sourceDepictionLinkIds=[link],
            ).model_dump(),
        }
    )
    spec["componentRelations"] = [
        {
            "component": "cape",
            "relation": "layered_over",
            "target": "tunic",
            "state": "user_confirmed",
        },
        {
            "component": "rear clasp",
            "relation": "attached_to",
            "target": "cape",
            "state": "proposed",
        },
    ]
    revised = service.new_version(
        "alice",
        project,
        original["design_id"],
        VersionInput(
            parentVersionId=original["version_id"],
            spec=CanonicalInput.model_validate(spec),
            expectedEventSequence=sequence(service, project),
            reason="Choose layered construction and retain uncertain clasp",
        ),
    )
    assert (
        service.designs("alice", project)[0]["versions"][1]["spec"] == original["spec"]
    )
    with service.database.connect() as db:
        adoption = json.loads(
            db.execute(
                "SELECT payload_json FROM events WHERE project_id=? AND sequence=?",
                (project, revised["created_sequence"]),
            ).fetchone()[0]
        )
        assert adoption["changeSet"]["componentRelations"]["before"] == []
        assert (
            adoption["changeSet"]["componentRelations"]["after"]
            == spec["componentRelations"]
        )
    # Historical decision sources travel with the handoff without being promoted
    # to evidence or coverage for the revised character.
    output = Exports(service, assets, Planning(service)).build(
        "alice", project, revised["version_id"]
    )
    with zipfile.ZipFile(io.BytesIO(output)) as archive:
        prefix = "avatar-design-handoff/"
        saved = json.loads(archive.read(prefix + "character-spec.json"))["spec"]
        assert saved == spec
        assert saved["properties"]["face.blink_capability"]["value"] is True
        assert saved["properties"]["body.head_ratio"]["value"] == 0.18
        assert saved["properties"]["outfit.layers"]["sourceDepictionLinkIds"] == [link]
        assert (
            json.loads(archive.read(prefix + "component-relations.json"))
            == spec["componentRelations"]
        )
        assert "rear clasp" in archive.read(prefix + "unresolved-decisions.md").decode()
        assert (
            revised["canonical_hash"]
            in archive.read(prefix + "character-spec.md").decode()
        )
        requirements = json.loads(archive.read(prefix + "confirmed-requirements.json"))
        assert "outfit.layers" in requirements["preservedPropertiesForSelectedVersion"]
        manifest = json.loads(archive.read(prefix + "reference-manifest.json"))
        assert len(manifest) == 1
        assert manifest[0]["canonicalPropertyKeys"] == ["outfit.layers"]
        assert manifest[0]["referenceRole"] == "design_decision_source"
        assert manifest[0]["versionId"] == original["version_id"]
        assert manifest[0]["targetVersionId"] == revised["version_id"]
        assert manifest[0]["countsAsCurrentEvidence"] is False
        assert manifest[0]["file"] in {
            name.removeprefix(prefix) for name in archive.namelist()
        }
        coverage = json.loads(archive.read(prefix + "view-and-state-coverage.json"))
        assert coverage["referenceCoverage"] == 0
