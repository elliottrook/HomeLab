"""Admit a labelled NLU calibration before any model execution.

Coverage retains its owner-accepted meaning: routed cases divided by all
calibration cases. A corpus therefore needs enough independently labelled safe
route targets to make the minimum coverage possible without unsafe routing.
"""
from __future__ import annotations

from collections import Counter

from nlu_calibration_feasibility import assess


FAMILIES = (
    "change-request", "external-research", "general-answer",
    "household-command", "read-only-investigation", "unsupported",
)


def admit(labels: list[dict], policy: dict) -> dict:
    if not isinstance(policy, dict) or set(policy) != {
        "minimum_calibration_cases", "minimum_cases_per_family", "constraints",
    }:
        raise ValueError("calibration admission policy differs")
    minimum = policy["minimum_calibration_cases"]
    family_minimums = policy["minimum_cases_per_family"]
    if type(minimum) is not int or minimum < 1:
        raise ValueError("minimum calibration size differs")
    if not isinstance(family_minimums, dict) or set(family_minimums) != set(FAMILIES):
        raise ValueError("family admission policy differs")
    if any(type(value) is not int or value < 1 for value in family_minimums.values()):
        raise ValueError("family minimum differs")
    if not isinstance(labels, list) or len(labels) < minimum:
        raise ValueError("calibration is below the accepted total minimum")
    counts = Counter()
    identities = set()
    for row in labels:
        if not isinstance(row, dict) or set(row) != {"id", "family", "label"}:
            raise ValueError("calibration label envelope differs")
        if row["id"] in identities:
            raise ValueError("calibration identity is duplicated")
        identities.add(row["id"])
        if row["family"] not in FAMILIES:
            raise ValueError("calibration family differs")
        counts[row["family"]] += 1
    for family in FAMILIES:
        if counts[family] < family_minimums[family]:
            raise ValueError(f"calibration is below the accepted {family} minimum")
    feasibility = assess(labels, policy["constraints"])
    if not feasibility["feasible"]:
        raise ValueError("calibration cannot satisfy total-case coverage safely")
    return {
        "case_count": len(labels),
        "family_counts": {family: counts[family] for family in FAMILIES},
        "coverage_denominator": "all-calibration-cases",
        "safe_route_targets": feasibility["safe_route_targets"],
        "minimum_safe_route_targets": feasibility["required_routed"],
        "feasible": True,
        "authority": "not-granted",
    }
