from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PairwiseFit:
    coefficients: np.ndarray
    hessian: np.ndarray
    converged: bool
    effective_weight: float


def fit_pairwise(
    differences: np.ndarray,
    targets: np.ndarray,
    weights: np.ndarray | None = None,
    l2: float = 1.0,
    max_steps: int = 50,
    tolerance: float = 1e-8,
) -> PairwiseFit:
    """Fit on observed feature differences; never synthesize user labels."""
    D = np.asarray(differences, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    if D.ndim != 2 or D.shape[1] < 1 or y.shape != (D.shape[0],):
        raise ValueError("Expected differences (n,d), d>=1, and targets (n,).")
    a = np.ones(len(y)) if weights is None else np.asarray(weights, dtype=np.float64)
    if a.shape != y.shape:
        raise ValueError("Weights must have shape (n,).")
    if not all(np.isfinite(v).all() for v in (D, y, a)):
        raise ValueError("All training values must be finite.")
    if np.any((y < 0) | (y > 1)) or np.any(a < 0):
        raise ValueError("Targets must be in [0,1]; weights must be nonnegative.")
    if not np.isfinite(l2) or l2 <= 0 or max_steps < 1:
        raise ValueError("Use positive finite regularization and at least one step.")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Tolerance must be positive and finite.")
    if np.any(np.abs(D) > 2.00000001):
        raise ValueError("Feature differences must use the specified [-2,2] scale.")

    w = np.zeros(D.shape[1], dtype=np.float64)
    prior = l2 * np.eye(D.shape[1], dtype=np.float64)

    def objective(v: np.ndarray) -> float:
        z = D @ v
        return float(0.5 * l2 * (v @ v) + a @ (np.logaddexp(0, z) - y * z))

    def derivatives(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = D @ v
        p = np.exp(-np.logaddexp(0, -z))
        gradient = l2 * v + D.T @ (a * (p - y))
        curvature = a * p * (1 - p)
        hessian = prior + D.T @ (curvature[:, None] * D)
        return gradient, hessian

    if a.sum() == 0:
        return PairwiseFit(w, prior, True, 0.0)

    for _ in range(max_steps):
        gradient, hessian = derivatives(w)
        if np.linalg.norm(gradient, ord=np.inf) <= tolerance:
            break
        step = np.linalg.solve(hessian, gradient)
        current_loss = objective(w)
        decrease = float(gradient @ step)
        rate = 1.0
        while rate >= 2.0**-20:
            trial = w - rate * step
            if objective(trial) <= current_loss - 1e-4 * rate * decrease:
                w = trial
                break
            rate *= 0.5
        else:
            break

    gradient, hessian = derivatives(w)
    return PairwiseFit(
        coefficients=w,
        hessian=hessian,
        converged=bool(np.linalg.norm(gradient, ord=np.inf) <= tolerance),
        effective_weight=float(a.sum()),
    )


def comparison_prediction(
    model: PairwiseFit, difference: np.ndarray
) -> tuple[float, float]:
    """Return relative A-over-B probability and the stated acquisition heuristic."""
    d = np.asarray(difference, dtype=np.float64)
    if d.shape != model.coefficients.shape or not np.isfinite(d).all():
        raise ValueError("Comparison vector has an invalid shape or value.")
    if np.any(np.abs(d) > 2.00000001):
        raise ValueError("Comparison vector must use the specified [-2,2] scale.")
    logit = float(model.coefficients @ d)
    p = float(np.exp(-np.logaddexp(0, -logit)))
    variance = max(0.0, float(d @ np.linalg.solve(model.hessian, d)))
    information = 0.5 * float(np.log1p(p * (1 - p) * variance))
    return p, information


# Fixed design-only schema. Never derive this list from arbitrary LLM output.
NUMERIC = {
    "body.head_ratio": (0.08, 0.60),
    "face.angularity": (0.0, 1.0),
    "face.eye_exaggeration": (0.0, 1.0),
    "hair.volume": (0.0, 1.0),
    "outfit.ornament_density": (0.0, 1.0),
    "outfit.layering": (0.0, 1.0),
    "palette.saturation": (0.0, 1.0),
    "palette.lightness": (0.0, 1.0),
    "palette.contrast": (0.0, 1.0),
    "material.gloss": (0.0, 1.0),
}
CATEGORIES = {
    "form.stylization": (
        "anime_proportioned",
        "cartoon_proportioned",
        "naturalistic",
        "chibi",
        "geometric",
        "hybrid",
        "other",
    ),
    "hair.length": (
        "bald",
        "very_short",
        "short",
        "medium",
        "long",
        "very_long",
        "other",
    ),
    "hair.structure": (
        "straight",
        "wavy",
        "curly",
        "coiled",
        "spiky",
        "mixed",
        "other",
    ),
    "outfit.structure": (
        "casual",
        "formal",
        "uniform",
        "fantasy",
        "techwear",
        "historical",
        "minimal",
        "other",
    ),
}
FEATURE_NAMES = tuple(NUMERIC) + tuple(
    f"{key}={value}" for key, values in CATEGORIES.items() for value in values
)


def encode_observed(
    attributes: dict, min_confidence: float = 0.6
) -> tuple[np.ndarray, np.ndarray]:
    """Encode reviewed visual observations, not canonical intentions or render settings.

    Each attribute is {value, confidence, visibility}. Missing/occluded entries
    have an all-false mask. The caller first enforces provenance and comparability.
    """
    if not np.isfinite(min_confidence) or not 0 <= min_confidence <= 1:
        raise ValueError("Invalid extraction-confidence threshold.")
    if not isinstance(attributes, dict):
        raise ValueError("Attributes must be an object.")
    unknown = set(attributes) - (set(NUMERIC) | set(CATEGORIES))
    if unknown:
        raise ValueError(f"Unknown or non-design feature keys: {sorted(unknown)}")
    x = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    mask = np.zeros(len(FEATURE_NAMES), dtype=bool)
    offset = 0
    for key in (*NUMERIC, *CATEGORIES):
        width = 1 if key in NUMERIC else len(CATEGORIES[key])
        row = attributes.get(key)
        if row is None:
            offset += width
            continue
        if not isinstance(row, dict) or set(row) != {
            "value",
            "confidence",
            "visibility",
        }:
            raise ValueError(
                "Use exactly value, confidence, and visibility per attribute."
            )
        c, vis, value = row["confidence"], row["visibility"], row["value"]
        if (
            isinstance(c, bool)
            or not isinstance(c, (int, float))
            or not np.isfinite(c)
            or not 0 <= c <= 1
        ):
            raise ValueError("Invalid extraction confidence.")
        if vis not in ("visible", "occluded", "out_of_frame", "unknown"):
            raise ValueError("Invalid visibility.")
        if value is not None:
            if key in NUMERIC:
                lo, hi = NUMERIC[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("Numeric attribute requires a real number.")
                if not np.isfinite(value) or not lo <= value <= hi:
                    raise ValueError("Numeric attribute outside fixed schema bounds.")
            elif not isinstance(value, str) or value not in CATEGORIES[key]:
                raise ValueError("Unknown categorical value.")
        if value is not None and vis == "visible" and c >= min_confidence:
            if key in NUMERIC:
                lo, hi = NUMERIC[key]
                x[offset] = 2 * (value - lo) / (hi - lo) - 1
            else:
                x[offset + CATEGORIES[key].index(value)] = 1
            mask[offset : offset + width] = True
        offset += width
    return x, mask


def masked_difference(
    left: tuple[np.ndarray, np.ndarray],
    right: tuple[np.ndarray, np.ndarray],
    scope: np.ndarray | None = None,
) -> np.ndarray:
    """Use only jointly visible, reliable features within the qualified scope."""
    xa, ma = left
    xb, mb = right
    expected = (len(FEATURE_NAMES),)
    for x, m in (left, right):
        if x.shape != expected or m.shape != expected or m.dtype != bool:
            raise ValueError("Invalid feature vector/mask shape or dtype.")
        if not np.isfinite(x).all() or np.any(np.abs(x) > 1.00000001):
            raise ValueError("Invalid normalized feature vector.")
    if scope is None:
        scope = np.ones(expected, dtype=bool)
    if scope.shape != expected or scope.dtype != bool:
        raise ValueError("Invalid scope mask.")
    return (xa - xb) * (ma & mb & scope)


def family_weights(families: list[str], base_weights: np.ndarray) -> np.ndarray:
    """Cap correlated evidence at total weight 1 per server-derived family."""
    base = np.asarray(base_weights, dtype=np.float64)
    if (
        base.shape != (len(families),)
        or not np.isfinite(base).all()
        or np.any(base < 0)
    ):
        raise ValueError("Invalid family weights.")
    if any(not isinstance(f, str) or not f for f in families):
        raise ValueError("Each row requires a nonempty server-derived family.")
    totals: dict[str, float] = {}
    for family, weight in zip(families, base):
        totals[family] = totals.get(family, 0.0) + float(weight)
    return np.array(
        [weight / max(1.0, totals[family]) for family, weight in zip(families, base)],
        dtype=np.float64,
    )


def observed_controls_match(
    left: dict, right: dict, required_keys: tuple[str, ...]
) -> bool:
    """Small per-slot check; full qualification also checks identity and visibility.

    Pass observed controls only. Matching requested recipes is not evidence.
    Exact numeric camera parameters require a different tolerance-aware policy.
    """
    if not required_keys:
        raise ValueError("A comparison policy must declare its relevant controls.")
    for key in required_keys:
        a, b = left.get(key), right.get(key)
        if a is None or b is None or a == "unknown" or b == "unknown" or a != b:
            return False
    return True
