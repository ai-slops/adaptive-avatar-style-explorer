import pytest
from app.common import DomainError
from app.contracts import CanonicalInput, DesignInput, JobInput, Property
from app.jobs import Jobs
from app.storage.assets import Assets
from test_domain import design, evidence, sequence


def test_context_transmits_only_selected_current_reviewed_observations(
    service, project, tmp_path
):
    version = service.create_design(
        "alice",
        project,
        DesignInput(
            title="Intent and observation",
            spec=CanonicalInput(
                morphology="humanoid",
                properties={"hair.volume": Property(value=0.9, state="proposed")},
            ),
        ),
    )
    root = tmp_path / "images"
    selected = evidence(service, project, version["version_id"], root, amount=0.2)
    unselected = evidence(service, project, version["version_id"], root, amount=0.8)
    other = design(service, project, "gold")
    jobs = Jobs(service, None, Assets(service, root), {})
    request = JobInput(
        requestId="context-check",
        task="review_design_consistency",
        versionId=version["version_id"],
        model="test-model",
        depictionLinkIds=[selected],
        expectedEventSequence=sequence(service, project),
    )
    with service.database.connect() as db:
        context = jobs.context(db, "alice", project, request)
        assert (
            context["canonicalSpec"]["spec"]["properties"]["hair.volume"]["value"]
            == 0.9
        )
        assert len(context["selectedEvidence"]) == 1
        item = context["selectedEvidence"][0]
        assert item["linkId"] == selected and item["linkId"] != unselected
        assert item["assessment"]["reviewedRegions"] == ["hair"]
        assert item["geometricVerification"] == "none"
        assert len(item["observations"]) == 1
        observation = item["observations"][0]
        assert observation["attributes"]["hair.volume"]["value"] == 0.2
        assert observation["observedPresentation"]["view"] == "front"
        assert observation["observedPresentation"]["projection"] == "orthographic"
        assert observation["featureSchemaVersion"] == "design-features-v2"
        assert observation["extractorVersion"] == "manual-v1"
        assert observation["authority"] == "reviewed_2d_observation"
        assert observation["geometricVerification"] == "none"
        assert observation["observationId"]
        assert (
            jobs.context(
                db,
                "alice",
                project,
                request.model_copy(update={"depictionLinkIds": []}),
            )["selectedEvidence"]
            == []
        )
        with pytest.raises(DomainError):
            jobs.context(db, "bob", project, request)
        with pytest.raises(DomainError, match="another version"):
            jobs.context(
                db,
                "alice",
                project,
                request.model_copy(update={"versionId": other["version_id"]}),
            )
        historical = service.get(db, "depiction_links", project, "link_id", selected)[
            "supersedes_link_id"
        ]
        with pytest.raises(DomainError, match="superseded"):
            jobs.context(
                db,
                "alice",
                project,
                request.model_copy(update={"depictionLinkIds": [historical]}),
            )
