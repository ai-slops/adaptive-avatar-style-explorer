import io

import pytest
from app.common import DomainError, uid
from app.contracts import (
    Attribute,
    CanonicalInput,
    DepictionInput,
    DesignInput,
    EvidenceReviewInput,
    FeedbackInput,
    FindingInput,
    LinkInput,
    Observation,
    Presentation,
    Property,
    ReviewInput,
    VersionInput,
)
from app.storage.assets import Assets
from PIL import Image
from pydantic import ValidationError


def sequence(s, p):
    return next(
        x["event_sequence"] for x in s.projects("alice") if x["project_id"] == p
    )


def design(s, p, value="silver", branch="main"):
    return s.create_design(
        "alice",
        p,
        DesignInput(
            title="Design",
            branchId=branch,
            spec=CanonicalInput(
                morphology="humanoid",
                properties={"hair.color": Property(value=value, state="proposed")},
            ),
        ),
    )


def image_bytes(color="white"):
    data = io.BytesIO()
    Image.new("RGB", (16, 24), color).save(data, "PNG")
    return data.getvalue()


def evidence(
    s,
    p,
    version,
    tmp,
    amount=0.2,
    view="front",
    region="hair",
    status="compatible",
    findings=None,
):
    asset = Assets(s, tmp).import_image(
        "alice", p, image_bytes((int(amount * 200) + 20, 100, 100))
    )["assetId"]
    depiction = s.create_depiction("alice", p, DepictionInput(assetId=asset))[
        "depictionId"
    ]
    link = s.create_link(
        "alice", p, LinkInput(depictionId=depiction, versionId=version)
    )["linkId"]
    obs = Observation(
        region=region,
        attributes={
            "hair.volume": Attribute(value=amount, confidence=0.9, visibility="visible")
        },
        observedPresentation=Presentation(
            view=view,
            projection="orthographic",
            framing="full_body",
            poseId="neutral",
            expressionId="neutral",
            lightingClass="neutral",
            backgroundClass="plain",
        ),
    )
    return s.evidence_review(
        "alice",
        p,
        EvidenceReviewInput(
            linkId=link,
            status=status,
            reviewedRegions=[region],
            observations=[] if status == "mismatch" else [obs],
            findings=findings or [],
            expectedEventSequence=sequence(s, p),
        ),
    )["linkId"]


def compare(s, p, a, b, la, lb, outcome="A", region="hair", branch="main"):
    review = s.review(
        "alice",
        p,
        ReviewInput(
            versionA=a,
            versionB=b,
            region=region,
            branchId=branch,
            linkIdsA=[la],
            linkIdsB=[lb],
            expectedEventSequence=sequence(s, p),
        ),
    )
    result = s.feedback(
        "alice",
        p,
        FeedbackInput(
            eventId=uid(),
            action="compare",
            domain="visual_design",
            reviewSessionId=review["reviewSessionId"],
            region=region,
            outcome=outcome,
            branchId=branch,
            expectedEventSequence=sequence(s, p),
        ),
    )
    return review, result


def test_ownership_and_strict_contracts(service, project):
    with pytest.raises(DomainError, match="not found"):
        service.designs("bob", project)
    with pytest.raises(ValidationError):
        DesignInput(title="x", spec={}, principalId="bob")
    with pytest.raises(ValidationError):
        CanonicalInput(
            properties={"camera.angle": Property(value="front", state="proposed")}
        )
    with pytest.raises(ValidationError):
        Observation(
            region="hair",
            observedPresentation=Presentation(),
            attributes={
                "pose.angle": Attribute(value=0.3, confidence=0.9, visibility="visible")
            },
        )


def test_version_and_lock_invariants(service, project):
    v = design(service, project)
    with pytest.raises(DomainError, match="No design change"):
        service.new_version(
            "alice",
            project,
            v["design_id"],
            VersionInput(
                parentVersionId=v["version_id"],
                spec=CanonicalInput.model_validate(v["spec"]),
                expectedEventSequence=sequence(service, project),
                reason="another angle",
            ),
        )
    lock = service.feedback(
        "alice",
        project,
        FeedbackInput(
            eventId=uid(),
            action="lock_property",
            subjectVersionIds=[v["version_id"]],
            propertyKey="hair.color",
            expectedEventSequence=sequence(service, project),
        ),
    )
    changed = CanonicalInput(
        morphology="humanoid",
        properties={"hair.color": Property(value="gold", state="proposed")},
    )
    with pytest.raises(DomainError, match="Unlock"):
        service.new_version(
            "alice",
            project,
            v["design_id"],
            VersionInput(
                parentVersionId=v["version_id"],
                spec=changed,
                reason="change",
                expectedEventSequence=sequence(service, project),
            ),
        )
    service.feedback(
        "alice",
        project,
        FeedbackInput(
            eventId=uid(),
            action="undo",
            targetEventId=lock["eventId"],
            expectedEventSequence=sequence(service, project),
        ),
    )
    new = service.new_version(
        "alice",
        project,
        v["design_id"],
        VersionInput(
            parentVersionId=v["version_id"],
            spec=changed,
            reason="change",
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert new["revision"] == 2 and new["parent_version_id"] == v["version_id"]
    assert service.designs("alice", project)[0]["versions"][1]["spec"] == v["spec"]


def test_multiple_depictions_one_candidate(service, project, tmp_path):
    v = design(service, project)["version_id"]
    for _ in range(6):
        evidence(service, project, v, tmp_path, region="whole")
    assert len(service.designs("alice", project)) == 1
    assert len(service.evidence("alice", project, v)["links"]) == 6
    assert service.evidence("alice", project, v)["referenceCoverage"] == 0.25
    with service.database.connect() as db:
        assert db.execute("SELECT count(*) FROM assets").fetchone()[0] == 1


def test_matched_evidence_learning_and_family_caps(service, project, tmp_path):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la, lb = (
        evidence(service, project, a, tmp_path, 0.2),
        evidence(service, project, b, tmp_path, 0.8),
    )
    first, _ = compare(service, project, a, b, la, lb)
    assert first["qualification"]["eligible"]
    for _ in range(3):
        compare(service, project, b, a, lb, la, outcome="B")
    model = service.preferences("alice", project)["models"]["hair"]
    assert model["effectiveWeight"] == 1
    assert model["coefficients"][3] < 0
    assert all(
        v == 0
        for i, v in enumerate(model["coefficients"])
        if not model["featureNames"][i].startswith("hair.")
    )
    with service.database.connect() as db:
        old = db.execute(
            "SELECT frozen_json FROM evidence_bundles WHERE bundle_id=?",
            (first["bundles"]["A"],),
        ).fetchone()[0]
    evidence(service, project, a, tmp_path, 0.9, "back")
    with service.database.connect() as db:
        assert (
            db.execute(
                "SELECT frozen_json FROM evidence_bundles WHERE bundle_id=?",
                (first["bundles"]["A"],),
            ).fetchone()[0]
            == old
        )


def test_observed_mismatch_and_drift_do_not_train(service, project, tmp_path):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la = evidence(service, project, a, tmp_path, 0.2)
    lb = evidence(service, project, b, tmp_path, 0.8, "back")
    r, result = compare(service, project, a, b, la, lb)
    assert not r["qualification"]["eligible"]
    assert result["trainingStatus"] == "provisional_not_trained"
    assert service.preferences("alice", project)["state"] == "insufficient_evidence"
    drift = evidence(
        service,
        project,
        b,
        tmp_path,
        0.8,
        findings=[
            FindingInput(
                kind="identity_or_design_drift",
                region="hair",
                severity="blocking",
                description="Hair ornament changed side",
            )
        ],
    )
    r, _ = compare(service, project, a, b, la, drift)
    assert not r["qualification"]["eligible"]
    assert (
        service.evidence("alice", project, b)["referenceCoverage"] == 0
    )  # hair-only reviews cannot satisfy whole-body slots


def test_correction_retires_training_not_historical_action(service, project, tmp_path):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la, lb = (
        evidence(service, project, a, tmp_path, 0.2),
        evidence(service, project, b, tmp_path, 0.8),
    )
    _, event = compare(service, project, a, b, la, lb)
    service.evidence_review(
        "alice",
        project,
        EvidenceReviewInput(
            linkId=la,
            status="mismatch",
            reviewedRegions=["hair"],
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert service.preferences("alice", project)["state"] == "insufficient_evidence"
    assert event["eventId"] in service.preferences("alice", project)["activeEventIds"]
    with pytest.raises(DomainError):
        service.review(
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


def test_neither_skip_tie_undo_and_idempotency(service, project, tmp_path):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la, lb = (
        evidence(service, project, a, tmp_path, 0.2),
        evidence(service, project, b, tmp_path, 0.8),
    )
    for outcome in ("neither", "skip"):
        compare(service, project, a, b, la, lb, outcome=outcome)
    assert not service.preferences("alice", project)["models"]
    _, event = compare(service, project, a, b, la, lb, outcome="tie")
    assert (
        service.preferences("alice", project)["models"]["hair"]["effectiveWeight"]
        == 0.5
    )
    action = FeedbackInput(
        eventId=uid(),
        action="undo",
        targetEventId=event["eventId"],
        expectedEventSequence=sequence(service, project),
    )
    first = service.feedback("alice", project, action)
    assert service.feedback("alice", project, action) == first
    assert not service.preferences("alice", project)["models"]
    with pytest.raises(DomainError, match="different request"):
        service.feedback(
            "alice", project, action.model_copy(update={"preserveLocks": False})
        )
    with pytest.raises(DomainError, match="already undone"):
        service.feedback(
            "alice",
            project,
            action.model_copy(
                update={
                    "eventId": uid(),
                    "expectedEventSequence": sequence(service, project),
                }
            ),
        )


def test_branch_exact_boundary_and_reset(service, project, tmp_path):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la, lb = (
        evidence(service, project, a, tmp_path, 0.2),
        evidence(service, project, b, tmp_path, 0.8),
    )
    compare(service, project, a, b, la, lb)
    fork = service.feedback(
        "alice",
        project,
        FeedbackInput(
            eventId=uid(),
            action="fork_branch",
            expectedEventSequence=sequence(service, project),
        ),
    )["childBranchId"]
    service.feedback(
        "alice",
        project,
        FeedbackInput(
            eventId=uid(),
            action="reset",
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert service.preferences("alice", project)["state"] == "insufficient_evidence"
    assert (
        service.preferences("alice", project, fork)["models"]["hair"]["effectiveWeight"]
        == 1
    )
    c = design(service, project, "later")["version_id"]
    with pytest.raises(DomainError, match="outside"):
        service.review(
            "alice",
            project,
            ReviewInput(
                versionA=a,
                versionB=c,
                branchId=fork,
                region="hair",
                expectedEventSequence=sequence(service, project),
            ),
        )


def test_cross_project_sources_and_rollback(service, project):
    a = design(service, project)
    p2 = service.create_project("bob", "Other")["project_id"]
    with pytest.raises(DomainError):
        service.create_link(
            "bob", p2, LinkInput(depictionId="missing", versionId=a["version_id"])
        )
    before = sequence(service, project)
    with pytest.raises(DomainError):
        service.create_design(
            "alice",
            project,
            DesignInput(
                title="Invalid",
                spec=CanonicalInput(
                    properties={
                        "hair.color": Property(
                            value="gold", state="inferred", sourceEventIds=["missing"]
                        )
                    }
                ),
            ),
        )
    assert sequence(service, project) == before


def test_no_same_version_and_stale_feedback(service, project, tmp_path):
    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    with pytest.raises(DomainError):
        service.review(
            "alice",
            project,
            ReviewInput(
                versionA=a,
                versionB=a,
                region="hair",
                expectedEventSequence=sequence(service, project),
            ),
        )
    r = service.review(
        "alice",
        project,
        ReviewInput(
            versionA=a,
            versionB=b,
            region="hair",
            expectedEventSequence=sequence(service, project),
        ),
    )
    design(service, project, "another")
    with pytest.raises(DomainError, match="stale"):
        service.feedback(
            "alice",
            project,
            FeedbackInput(
                eventId=uid(),
                action="compare",
                domain="visual_design",
                reviewSessionId=r["reviewSessionId"],
                region="hair",
                outcome="A",
                expectedEventSequence=sequence(service, project),
            ),
        )


def test_images_are_safe_and_scoped(service, project, tmp_path):
    assets = Assets(service, tmp_path / "images")
    with pytest.raises(DomainError):
        assets.import_image("alice", project, b"<svg><script/></svg>")
    with pytest.raises(DomainError):
        assets.import_image("bob", project, image_bytes())
    asset = assets.import_image("alice", project, image_bytes())["assetId"]
    with pytest.raises(DomainError):
        assets.display_path("bob", project, asset)
    assert Image.open(assets.display_path("alice", project, asset)).info == {}


def test_nonhumanoid_profile_not_invented(service, project):
    v = service.create_design(
        "alice",
        project,
        DesignInput(title="Orb", spec=CanonicalInput(morphology="non_humanoid")),
    )
    result = service.evidence("alice", project, v["version_id"])
    assert result["referenceCoverage"] is None and result["slots"] == []


def test_preserved_properties_propagate_and_require_explicit_unlock(service, project):
    original = design(service, project)
    service.feedback(
        "alice",
        project,
        FeedbackInput(
            eventId=uid(),
            action="lock_property",
            subjectVersionIds=[original["version_id"]],
            propertyKey="hair.color",
            expectedEventSequence=sequence(service, project),
        ),
    )
    spec = CanonicalInput.model_validate(original["spec"])
    spec.properties["outfit.layer"] = Property(value="cape", state="proposed")
    child = service.new_version(
        "alice",
        project,
        original["design_id"],
        VersionInput(
            parentVersionId=original["version_id"],
            spec=spec,
            reason="Add a cape",
            expectedEventSequence=sequence(service, project),
        ),
    )
    assert (
        "hair.color"
        in service.preferences("alice", project)["locks"][child["version_id"]]
    )
    spec.properties["hair.color"] = Property(value="gold", state="proposed")
    data = VersionInput(
        parentVersionId=child["version_id"],
        spec=spec,
        reason="Revise hair",
        expectedEventSequence=sequence(service, project),
    )
    with pytest.raises(DomainError, match="Unlock"):
        service.new_version("alice", project, original["design_id"], data)
    service.feedback(
        "alice",
        project,
        FeedbackInput(
            eventId=uid(),
            action="unlock_property",
            subjectVersionIds=[child["version_id"]],
            propertyKey="hair.color",
            expectedEventSequence=sequence(service, project),
        ),
    )
    updated = service.new_version(
        "alice",
        project,
        original["design_id"],
        data.model_copy(update={"expectedEventSequence": sequence(service, project)}),
    )
    assert updated["revision"] == 3


def test_confirmed_intent_becomes_user_lock(service, project):
    original = service.create_design(
        "alice",
        project,
        DesignInput(
            title="Confirmed",
            spec=CanonicalInput(
                properties={
                    "accessory.side": Property(
                        value="character-left", state="user_confirmed"
                    )
                }
            ),
        ),
    )
    assert service.preferences("alice", project)["locks"][original["version_id"]] == [
        "accessory.side"
    ]


def test_predictions_precede_feedback_and_disagreement_is_explicit(
    service, project, tmp_path
):
    from app.quality import quality_report

    a, b = (
        design(service, project)["version_id"],
        design(service, project, "gold")["version_id"],
    )
    la, lb = (
        evidence(service, project, a, tmp_path, 0.2),
        evidence(service, project, b, tmp_path, 0.8),
    )
    first, _ = compare(service, project, a, b, la, lb)
    assert first["qualification"]["preFeedbackPrediction"] is None
    second, _ = compare(service, project, a, b, la, lb, outcome="B")
    assert second["qualification"]["preFeedbackPrediction"]["recordedBeforeFeedback"]
    assert second["qualification"]["preFeedbackPrediction"]["probabilityA"] > 0.5
    pref = service.preferences("alice", project)
    assert len(pref["contextualDisagreements"]) == 1
    assert pref["models"]["hair"]["effectiveWeight"] == 1
    with service.database.connect() as db:
        report = quality_report(service, db, project, "main")
    assert report["allPrequential"]["count"] == 1
    assert report["heldOutLineageAndExactSource"]["count"] == 0
    assert report["status"] == "inconclusive_observational_evidence"
