"""Versioned conservative qualification over reviewed observations only."""

import numpy as np

from .reference import (
    FEATURE_NAMES,
    encode_observed,
    masked_difference,
    observed_controls_match,
)

POLICY_VERSION = "matched-observed-v1"
PREFIXES = {
    "face": ("face.",),
    "hair": ("hair.",),
    "body": ("body.", "form."),
    "outfit": ("outfit.",),
    "palette": ("palette.",),
    "surface": ("material.",),
}


def scope_mask(region):
    prefixes = PREFIXES.get(region, () if region != "whole" else ("",))
    return np.array(
        [any(name.startswith(p) for p in prefixes) for name in FEATURE_NAMES],
        dtype=bool,
    )


def controls(region):
    base = ("view", "projection", "framing", "poseId", "expressionId")
    return base + (
        ("lightingClass", "backgroundClass")
        if region in ("whole", "palette", "surface")
        else ()
    )


def qualify(left, right, region, domain):
    reasons, differences, used = [], [], []
    if domain != "visual_design":
        return {
            "eligible": False,
            "reasons": ["Written intent is not visual evidence"],
            "policy": POLICY_VERSION,
            "difference": [0.0] * len(FEATURE_NAMES),
            "basis": [],
        }
    # Whole-character decisions need structural multiview evidence, including body and face.
    if region == "whole":
        required_views = {"front", "character_left_profile", "back"}
        for side in (left, right):
            views = {o["observedPresentation"]["view"] for o in side}
            if not required_views <= views:
                reasons.append(
                    "Whole-character comparison requires matched front, left profile and back evidence"
                )
    for a in left:
        for b in right:
            pa, pb = a["observedPresentation"], b["observedPresentation"]
            if a["region"] != b["region"] or (
                region != "whole" and a["region"] not in (region, "whole")
            ):
                continue
            if not observed_controls_match(pa, pb, controls(region)):
                continue
            aa, bb = dict(a["attributes"]), dict(b["attributes"])
            # Never infer proportions from a crop, neutral eyes from a blink, or gloss from unknown light.
            for attrs, presentation in ((aa, pa), (bb, pb)):
                if (
                    presentation["framing"] != "full_body"
                    or presentation["poseId"] != "neutral"
                    or presentation["view"] not in ("front", "front_three_quarter")
                ):
                    attrs.pop("body.head_ratio", None)
                if presentation["expressionId"] != "neutral":
                    attrs.pop("face.eye_exaggeration", None)
                    attrs.pop("face.angularity", None)
                if presentation["lightingClass"] != "neutral":
                    for key in (
                        "material.gloss",
                        "palette.saturation",
                        "palette.lightness",
                        "palette.contrast",
                    ):
                        attrs.pop(key, None)
            xa, ma = encode_observed(aa)
            xb, mb = encode_observed(bb)
            mask = ma & mb & scope_mask(region) & scope_mask(a["region"])
            if np.any(mask):
                differences.append(masked_difference((xa, ma), (xb, mb), mask))
                used.append(mask)
    if not differences:
        reasons.append(
            "No reliable jointly visible features under matched observed conditions"
        )
        delta = np.zeros(len(FEATURE_NAMES))
        basis = np.zeros(len(FEATURE_NAMES), dtype=bool)
    else:
        stack, masks = np.array(differences), np.array(used)
        delta, basis = np.zeros(len(FEATURE_NAMES)), np.any(masks, axis=0)
        # Conflicting observations are unknown, never averaged across incompatible views.
        for i in range(len(delta)):
            values = stack[masks[:, i], i]
            if len(values) and np.ptp(values) <= 1e-8:
                delta[i] = values[0]
            else:
                basis[i] = False
        if not np.any(np.abs(delta) > 1e-8):
            reasons.append("No consistent observable design-feature difference")
        if region == "whole" and not all(
            any(
                basis[i]
                for i, name in enumerate(FEATURE_NAMES)
                if name.startswith(prefix)
            )
            for prefix in ("body.", "face.")
        ):
            reasons.append("Whole-character basis lacks body or face evidence")
    return {
        "eligible": not reasons,
        "reasons": sorted(set(reasons)),
        "policy": POLICY_VERSION,
        "difference": delta.tolist(),
        "basis": [name for name, ok in zip(FEATURE_NAMES, basis) if ok],
    }
