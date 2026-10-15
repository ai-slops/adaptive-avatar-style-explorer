import pytest
from app.contracts import (
    CanonicalInput,
    DesignInput,
    EvaluationProfileInput,
    EvaluationSlotInput,
    EvidenceReviewInput,
    FindingInput,
    FindingResolutionInput,
    Observation,
    Presentation,
    ReviewInput,
)
from app.evaluation import Evaluation
from pydantic import ValidationError
from test_domain import design, evidence, sequence


def test_nonhumanoid_custom_profile_and_applicability(service, project, tmp_path):
    version = service.create_design(
        "alice",
        project,
        DesignInput(title="Orb", spec=CanonicalInput(morphology="non_humanoid")),
    )["version_id"]
    assert service.evidence("alice", project, version)["referenceCoverage"] is None
    slots = [
        EvaluationSlotInput(id="front", view="front", framing="full_body"),
        EvaluationSlotInput(
            id="mouth",
            view="front",
            framing="face",
            notApplicableReason="This spherical design has no mouth or face.",
            notApplicableBasis="morphology",
        ),
    ]
    result = Evaluation(service).publish_profile(
        "alice",
        project,
        EvaluationProfileInput(
            versionId=version,
            stage="custom",
            slots=slots,
            changeRationale="Test the whole spherical surface instead of humanoid anatomy.",
            expectedEventSequence=sequence(service, project),
        ),
    )
    evidence(service, project, version, tmp_path, region="whole")
    current = service.evidence("alice", project, version)
    assert current["evaluationProfileId"] == result["profileId"]
    assert current["referenceCoverage"] == 1
    assert current["slots"][1]["status"] == "not_applicable"
    with pytest.raises(ValidationError):
        EvaluationSlotInput(
            id="face",
            view="front",
            framing="face",
            notApplicableReason="No face is present",
        )
    Evaluation(service).publish_profile(
        "alice",
        project,
        EvaluationProfileInput(
            versionId=version,
            stage="custom",
            slots=[],
            changeRationale="Temporarily no profile configured for this design.",
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert service.evidence("alice", project, version)["referenceCoverage"] is None


def test_state_studies_match_observed_state_and_bundles_keep_profile(
    service, project, tmp_path
):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la, lb = (
        evidence(service, project, a, tmp_path, 0.2, region="whole"),
        evidence(service, project, b, tmp_path, 0.8, region="whole"),
    )
    old = service.review(
        "alice",
        project,
        ReviewInput(
            versionA=a,
            versionB=b,
            region="hair",
            linkIdsA=[la],
            linkIdsB=[lb],
            expectedEventSequence=sequence(service, project),
        ),
    )
    Evaluation(service).publish_profile(
        "alice",
        project,
        EvaluationProfileInput(
            versionId=a,
            stage="finalist",
            slots=[
                EvaluationSlotInput(
                    id="raised", view="front", framing="full_body", poseId="raised_arm"
                )
            ],
            changeRationale="Inspect sleeve volume with an arm raised.",
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert service.evidence("alice", project, a)["referenceCoverage"] == 0
    service.evidence_review(
        "alice",
        project,
        EvidenceReviewInput(
            linkId=la,
            status="compatible",
            reviewedRegions=["whole"],
            observations=[
                Observation(
                    region="whole",
                    attributes={},
                    observedPresentation=Presentation(
                        view="front",
                        projection="unknown",
                        framing="full_body",
                        poseId="raised_arm",
                        expressionId="neutral",
                    ),
                )
            ],
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert service.evidence("alice", project, a)["referenceCoverage"] == 1
    with service.database.connect() as db:
        bundle = db.execute(
            "SELECT * FROM evidence_bundles WHERE bundle_id=?", (old["bundles"]["A"],)
        ).fetchone()
        assert bundle["profile_id"] == "structure-v1"
        assert "raised_arm" not in bundle["frozen_json"]


def test_accepting_drift_does_not_make_it_valid_evidence(service, project, tmp_path):
    version = design(service, project)["version_id"]
    evidence(
        service,
        project,
        version,
        tmp_path,
        region="whole",
        findings=[
            FindingInput(
                kind="identity_or_design_drift",
                region="hair",
                severity="blocking",
                description="The back changed the hair attachment.",
            )
        ],
    )
    current = service.evidence("alice", project, version)
    assert current["referenceCoverage"] == 0
    finding = current["findings"][0]["finding_id"]
    Evaluation(service).resolve(
        "alice",
        project,
        finding,
        FindingResolutionInput(
            state="accepted_tradeoff",
            rationale="Keep as inspiration but do not treat as faithful reference.",
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert service.evidence("alice", project, version)["referenceCoverage"] == 0


def test_duplicate_original_cannot_fill_multiple_views(service, project, tmp_path):
    version = design(service, project)["version_id"]
    evidence(service, project, version, tmp_path, view="front", region="whole")
    evidence(service, project, version, tmp_path, view="back", region="whole")
    result = service.evidence("alice", project, version)
    assert result["referenceCoverage"] == 0.25
    assert result["slots"][3]["status"] == "missing"


def test_same_decoded_image_does_not_create_feature_difference(
    service, project, tmp_path
):
    import io

    from app.contracts import Attribute, DepictionInput, LinkInput
    from app.storage.assets import Assets
    from PIL import Image, PngImagePlugin

    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    links = []
    for version, amount, caption in [(a, 0.2, "one"), (b, 0.8, "two")]:
        data = io.BytesIO()
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Comment", caption)
        Image.new("RGB", (12, 12), "white").save(data, "PNG", pnginfo=metadata)
        asset = Assets(service, tmp_path).import_image(
            "alice", project, data.getvalue()
        )["assetId"]
        depiction = service.create_depiction(
            "alice", project, DepictionInput(assetId=asset)
        )["depictionId"]
        link = service.create_link(
            "alice", project, LinkInput(depictionId=depiction, versionId=version)
        )["linkId"]
        links.append(
            service.evidence_review(
                "alice",
                project,
                EvidenceReviewInput(
                    linkId=link,
                    status="compatible",
                    reviewedRegions=["hair"],
                    observations=[
                        Observation(
                            region="hair",
                            attributes={
                                "hair.volume": Attribute(
                                    value=amount, confidence=0.9, visibility="visible"
                                )
                            },
                            observedPresentation=Presentation(
                                view="front",
                                projection="orthographic",
                                framing="full_body",
                                poseId="neutral",
                                expressionId="neutral",
                            ),
                        )
                    ],
                    expectedEventSequence=sequence(service, project),
                ),
            )["linkId"]
        )
    comparison = service.review(
        "alice",
        project,
        ReviewInput(
            versionA=a,
            versionB=b,
            region="hair",
            linkIdsA=[links[0]],
            linkIdsB=[links[1]],
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert not comparison["qualification"]["eligible"]
    assert any(
        "original image source" in reason
        for reason in comparison["qualification"]["reasons"]
    )
