"""Rank only a shared observed basis, with separate unranked evidence gaps."""

import numpy as np

from .policy import qualify
from .reference import FEATURE_NAMES, PairwiseFit, comparison_prediction


def rank_cohort(candidates, model, region):
    empty = {
        "state": "insufficient_evidence",
        "region": region,
        "basis": [],
        "ranked": [],
        "unranked": [
            {
                "versionId": c["versionId"],
                "reason": "No valid region model or common observed basis",
            }
            for c in candidates
        ],
        "informativePairs": [],
        "boardVersionIds": [c["versionId"] for c in candidates[:6]],
    }
    if not model or model["state"] != "fitted" or len(candidates) < 2:
        return empty
    anchor = max(candidates, key=lambda c: len(c["observations"]))
    qualified, unranked = [], []
    for candidate in candidates:
        result = qualify(
            candidate["observations"], anchor["observations"], region, "visual_design"
        )
        reasons = [
            r
            for r in result["reasons"]
            if r != "No consistent observable design-feature difference"
        ]
        if candidate["versionId"] != anchor["versionId"] and set(
            candidate["sourceFamilies"]
        ) & set(anchor["sourceFamilies"]):
            reasons.append("Shares an original source with another candidate")
        if reasons:
            unranked.append(
                {"versionId": candidate["versionId"], "reason": "; ".join(reasons)}
            )
        else:
            qualified.append((candidate, result))
    if len(qualified) < 2:
        return {**empty, "unranked": unranked or empty["unranked"]}
    basis = set(qualified[0][1]["basis"])
    for _, result in qualified[1:]:
        basis &= set(result["basis"])
    if not basis:
        return empty
    mask = np.array([name in basis for name in FEATURE_NAMES], dtype=bool)
    fit = PairwiseFit(
        np.array(model["coefficients"]),
        np.array(model["hessian"]),
        True,
        model["effectiveWeight"],
    )
    vectors = {c["versionId"]: np.array(q["difference"]) * mask for c, q in qualified}
    ranked = sorted(
        [
            {"versionId": v, "relativeScore": float(fit.coefficients @ x)}
            for v, x in vectors.items()
        ],
        key=lambda row: (-row["relativeScore"], row["versionId"]),
    )
    pairs = []
    for i, a in enumerate(ranked):
        for b in ranked[i + 1 :]:
            delta = vectors[a["versionId"]] - vectors[b["versionId"]]
            p, information = comparison_prediction(fit, delta)
            pairs.append(
                {
                    "versionA": a["versionId"],
                    "versionB": b["versionId"],
                    "predictedRelativePreference": p,
                    "informationHeuristic": information,
                }
            )
    pairs.sort(key=lambda row: -row["informationHeuristic"])
    selected = [r["versionId"] for r in ranked[:3]]
    if pairs:
        selected.extend([pairs[0]["versionA"], pairs[0]["versionB"]])
    selected = list(dict.fromkeys(selected))
    remaining = [v for v in vectors if v not in selected]
    if remaining:
        alternative = max(
            remaining,
            key=lambda v: min(
                float(np.linalg.norm(vectors[v] - vectors[s])) for s in selected
            ),
        )
        selected.append(alternative)
    selected = list(
        dict.fromkeys(
            selected
            + [r["versionId"] for r in unranked]
            + [r["versionId"] for r in ranked]
        )
    )[:6]
    return {
        "state": "ranked_on_common_basis",
        "region": region,
        "basis": [name for name in FEATURE_NAMES if name in basis],
        "ranked": ranked,
        "unranked": unranked,
        "informativePairs": pairs[:3],
        "boardVersionIds": selected,
        "meaning": "Relative scores apply only within this observed cohort and region. They are not universal aesthetic scores or geometric confidence.",
    }
