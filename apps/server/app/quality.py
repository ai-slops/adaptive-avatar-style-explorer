"""Pre-feedback prediction audit. Observational metrics never certify preference quality."""

import json
import math

import numpy as np

from .learning.reference import family_weights


def quality_report(service, db, project, branch_id):
    state = service.reduce(db, project, branch_id)
    effective = service._preferences(db, project, branch_id)
    qualified_ids = {
        event_id
        for model in effective["models"].values()
        for event_id in model["eventIds"]
    }
    records = []
    for event in state["comparisons"]:
        payload = json.loads(event["payload_json"])
        if event["event_id"] not in qualified_ids or payload["outcome"] not in (
            "A",
            "B",
        ):
            continue
        review = service.get(
            db, "review_sessions", project, "review_id", event["review_id"]
        )
        qualification = json.loads(review["qualification_json"])
        prediction = qualification.get("preFeedbackPrediction")
        if not prediction:
            continue

        def provenance(review_id):
            lineages, sources, versions = set(), set(), []
            for side in db.execute(
                "SELECT * FROM review_items WHERE project_id=? AND review_id=? ORDER BY side",
                (project, review_id),
            ):
                version = service.version(db, project, side["version_id"])
                lineages.add(version["design_id"])
                versions.append(side["version_id"])
                bundle = service.get(
                    db, "evidence_bundles", project, "bundle_id", side["bundle_id"]
                )
                for item in json.loads(bundle["frozen_json"])["items"]:
                    sources.add(
                        service.source_family(db, project, item["link"]["link_id"])
                    )
            return lineages, sources, versions

        lineages, sources, versions = provenance(event["review_id"])
        seen_lineages, seen_sources = set(), set()
        for event_id in prediction["supportingEventIds"]:
            previous = service.get(db, "events", project, "event_id", event_id)
            old_lineages, old_sources, _ = provenance(previous["review_id"])
            seen_lineages |= old_lineages
            seen_sources |= old_sources
        records.append(
            {
                "eventId": event["event_id"],
                "reviewId": event["review_id"],
                "region": review["region"],
                "lineageIds": sorted(lineages),
                "sourceFamilies": sorted(sources),
                "predictedProbabilityA": prediction["probabilityA"],
                "targetA": 1 if payload["outcome"] == "A" else 0,
                "recordedBeforeFeedback": True,
                "heldOutLineages": not bool(lineages & seen_lineages),
                "heldOutExactSourceFamilies": not bool(sources & seen_sources),
                "family": json.dumps(
                    [sorted(versions), state["epoch"], review["region"]]
                ),
            }
        )

    def metrics(rows):
        if not rows:
            return {"count": 0, "effectiveWeight": 0, "brier": None, "logLoss": None}
        weights = family_weights([r["family"] for r in rows], np.ones(len(rows)))
        total = float(weights.sum())
        brier = (
            sum(
                w * (r["predictedProbabilityA"] - r["targetA"]) ** 2
                for w, r in zip(weights, rows)
            )
            / total
        )
        loss = 0.0
        for w, r in zip(weights, rows):
            probability = min(1 - 1e-12, max(1e-12, r["predictedProbabilityA"]))
            loss += w * -(
                r["targetA"] * math.log(probability)
                + (1 - r["targetA"]) * math.log1p(-probability)
            )
        return {
            "count": len(rows),
            "effectiveWeight": total,
            "brier": float(brier),
            "logLoss": float(loss / total),
        }

    held_out = [
        r for r in records if r["heldOutLineages"] and r["heldOutExactSourceFamilies"]
    ]
    return {
        "status": "inconclusive_observational_evidence",
        "branchId": branch_id,
        "epoch": state["epoch"],
        "predictions": records,
        "allPrequential": metrics(records),
        "heldOutLineageAndExactSource": metrics(held_out),
        "uninformedProbabilityBaseline": {
            "probabilityA": 0.5,
            "brier": 0.25,
            "logLoss": math.log(2),
        },
        "limitations": [
            "Small personal samples are inconclusive.",
            "Exact-source grouping does not detect every near-duplicate.",
            "This is not a randomized comparison against a diversity-only acquisition policy.",
            "Reference fixtures and numerical tests do not establish visual preference accuracy.",
        ],
        "laterContextDisagreements": effective["contextualDisagreements"],
    }
