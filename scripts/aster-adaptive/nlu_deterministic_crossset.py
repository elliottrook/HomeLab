"""Content-free cross-set evaluation for deterministic-first NLU challengers."""
from __future__ import annotations

from nlu_deterministic_classifier_v1 import HashedMultiHead
from nlu_deterministic_guard_v1 import apply


FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)
SENSITIVITY = {"public": 0, "internal": 1, "personal": 2}


def _semantic(value: dict) -> dict:
    return {field: value[field] for field in FIELDS}


def summarize(rows: list[tuple[dict, dict]], *, attempted: int) -> dict:
    routed = [(actual, expected) for actual, expected in rows
              if actual["disposition"] == "route"]
    correct = sum(actual == expected for actual, expected in routed)
    unsafe = sum(expected["disposition"] != "route" for _, expected in routed)
    privacy = sum(
        SENSITIVITY[actual["sensitivity"]] < SENSITIVITY[expected["sensitivity"]]
        for actual, expected in routed
    )
    error_rate = (len(routed) - correct) / len(routed) if routed else 0.0
    return {
        "attempted": attempted,
        "valid": len(rows),
        "exact": sum(actual == expected for actual, expected in rows),
        "routed": len(routed),
        "safe_and_correct_routed": correct,
        "unsafe_false_routes": unsafe,
        "privacy_underclassification_on_routed": privacy,
        "coverage": len(routed) / attempted,
        "selective_error_rate": error_rate,
        "eligible": (
            len(routed) / attempted >= 0.6 and error_rate <= 0.1
            and unsafe == 0 and privacy == 0
        ),
    }


def leave_one_set_out(calibrations: list[list[dict]]) -> list[dict]:
    """Train on every other spent set and evaluate one held-out set."""
    if len(calibrations) < 2 or any(not rows for rows in calibrations):
        raise ValueError("at least two nonempty calibration sets are required")
    results = []
    for held, test_rows in enumerate(calibrations):
        training = [
            (row["text"], row["label"])
            for index, rows in enumerate(calibrations) if index != held
            for row in rows
        ]
        classifier = HashedMultiHead().fit(training)
        evaluated = []
        for row in test_rows:
            proposal, _ = classifier.predict(row["text"])
            evaluated.append((_semantic(apply(row["text"], proposal)), row["label"]))
        results.append(summarize(evaluated, attempted=len(test_rows)))
    return results


def guarded_model(calibration: list[dict]) -> dict:
    """Evaluate one spent model run after the deterministic guard."""
    evaluated = []
    for row in calibration:
        if row["proposal"] is None:
            continue
        evaluated.append((
            _semantic(apply(row["text"], row["proposal"])), row["label"],
        ))
    return summarize(evaluated, attempted=len(calibration))
