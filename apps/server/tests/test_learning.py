import numpy as np
import pytest
from app.learning.reference import (
    FEATURE_NAMES,
    comparison_prediction,
    encode_observed,
    family_weights,
    fit_pairwise,
    masked_difference,
    observed_controls_match,
)


def attribute(value, confidence=0.9, visibility="visible"):
    return {"value": value, "confidence": confidence, "visibility": visibility}


def test_fixed_features_and_joint_category_masks():
    assert len(FEATURE_NAMES) == 39
    left = encode_observed(
        {"hair.structure": attribute("wavy"), "face.angularity": attribute(0.2)}
    )
    right = encode_observed(
        {
            "hair.structure": attribute("curly"),
            "face.angularity": attribute(0.8, visibility="occluded"),
        }
    )
    delta = masked_difference(left, right)
    assert np.count_nonzero(delta) == 2
    assert delta[1] == 0
    assert sum(left[1]) == 8


@pytest.mark.parametrize(
    "features",
    [
        {"camera.angle": attribute(0.5)},
        {"pose": attribute("sitting")},
        {"face.angularity": attribute(1.1)},
        {"hair.length": attribute("missing")},
        {"hair.volume": attribute(0.5, confidence=float("nan"))},
        {"hair.volume": attribute(True)},
        {
            "hair.volume": {
                "value": 0.5,
                "confidence": 0.8,
                "visibility": "visible",
                "weight": 100,
            }
        },
    ],
)
def test_invalid_features_rejected(features):
    with pytest.raises(ValueError):
        encode_observed(features)


@pytest.mark.parametrize("visibility", ["occluded", "out_of_frame", "unknown"])
def test_unknown_is_masked(visibility):
    assert not encode_observed({"hair.volume": attribute(0.9, visibility=visibility)})[
        1
    ].any()


def test_pair_reversal_and_identical_features():
    D = np.array([[0.2, -0.3], [0.4, 0.5]])
    y = np.array([1.0, 0.0])
    a, b = fit_pairwise(D, y), fit_pairwise(-D, 1 - y)
    assert a.converged and b.converged
    np.testing.assert_allclose(a.coefficients, b.coefficients)
    assert np.linalg.eigvalsh(a.hessian).min() >= 1
    p, info = comparison_prediction(a, np.zeros(2))
    assert p == 0.5 and info == 0
    empty = fit_pairwise(np.empty((0, 2)), np.empty(0))
    assert empty.converged and empty.effective_weight == 0


def test_repeats_do_not_inflate_curvature():
    single = fit_pairwise(np.array([[1.0, -0.5]]), np.array([1.0]))
    weights = family_weights(["same"] * 10, np.ones(10))
    repeated = fit_pairwise(np.array([[1.0, -0.5]] * 10), np.ones(10), weights)
    np.testing.assert_allclose(single.coefficients, repeated.coefficients)
    np.testing.assert_allclose(single.hessian, repeated.hessian)


def test_controls_use_observed_unknowns_fail():
    assert not observed_controls_match(
        {"view": "unknown"}, {"view": "unknown"}, ("view",)
    )
    assert not observed_controls_match({"view": "front"}, {"view": "back"}, ("view",))
    assert observed_controls_match({"view": "front"}, {"view": "front"}, ("view",))


def test_ranking_uses_common_observed_basis_and_keeps_unknown_unranked():
    from app.learning.ranking import rank_cohort

    def candidate(version, value):
        obs = {
            "region": "hair",
            "attributes": {"hair.volume": attribute(value)},
            "observedPresentation": {
                "view": "front",
                "projection": "orthographic",
                "framing": "full_body",
                "poseId": "neutral",
                "expressionId": "neutral",
                "lightingClass": "neutral",
                "backgroundClass": "plain",
            },
        }
        return {
            "versionId": version,
            "observations": [obs],
            "sourceFamilies": [version],
        }

    coefficients = np.zeros(39)
    coefficients[3] = -1
    model = {
        "state": "fitted",
        "coefficients": coefficients.tolist(),
        "hessian": np.eye(39).tolist(),
        "effectiveWeight": 1,
    }
    result = rank_cohort(
        [
            candidate("low", 0.2),
            candidate("high", 0.8),
            {"versionId": "unknown", "observations": [], "sourceFamilies": []},
        ],
        model,
        "hair",
    )
    assert result["state"] == "ranked_on_common_basis"
    assert [r["versionId"] for r in result["ranked"]] == ["low", "high"]
    assert result["unranked"][0]["versionId"] == "unknown"
    assert result["basis"] == ["hair.volume"]
    assert result["informativePairs"][0]["informationHeuristic"] > 0
